#include "rotary/Simulation.hpp"
#include "rotary/Thermodynamics.hpp"
#include <Eigen/Dense>
#include <algorithm>
#include <array>
#include <boost/fusion/include/make_vector.hpp>
#include <boost/numeric/odeint.hpp>
#include <boost/numeric/odeint/stepper/explicit_generic_rk.hpp>
#include <boost/version.hpp>
#include <chrono>
#include <cmath>
#include <numeric>
#include <stdexcept>
#include <thread>
#ifdef _OPENMP
#include <omp.h>
#endif

#ifndef ROTARY_SOURCE_FINGERPRINT
#define ROTARY_SOURCE_FINGERPRINT "development"
#endif

namespace rotary {
namespace {
using State = std::vector<double>;
using Clock = std::chrono::steady_clock;
double sum(const State &x) {
    return std::accumulate(x.begin(), x.end(), 0.0);
}
double dot(const State &a, const State &b) {
    return std::inner_product(a.begin(), a.end(), b.begin(), 0.0);
}
double minimum(const State &x) {
    return *std::min_element(x.begin(), x.end());
}
double maximum(const State &x) {
    return *std::max_element(x.begin(), x.end());
}

struct Rates {
    double near_mean{}, core_mean{}, melt{}, bed_heat{}, product_heat{}, source{}, convection{}, radiation{},
        extra{}, loss{};
    double inlet{}, outlet{}, wet_fraction{}, near_surface{}, core_surface{}, evaluation_time{};
    BedProperties bed;
};

class ThermalSystem {
  public:
    const ThermalSpec &s;
    const Configuration &c;
    const SimulationOptions &options;
    const int K, B, N, A, P, I, J, O, D;
    State temperatures, phase, product_flux, convection_flux, radiation_flux, surface_temperatures;
    Rates last;

    ThermalSystem(const ThermalSpec &spec, const SimulationOptions &settings)
        : s(spec), c(spec.c), options(settings), K(spec.radial), B(2 * K), N(spec.mesh.cells),
          A(spec.mesh.axial), P(spec.mesh.angular), I(B), J(B + N), O(B + N + A), D(B + 2 * N + A),
          temperatures(B), phase(B), product_flux(N), convection_flux(N), radiation_flux(N),
          surface_temperatures(N) {}

    State initial() const {
        State y(D + 5, 0);
        const double h = enthalpy(c, c.initial);
        for (int i = 0; i < B; ++i)
            y[i] = s.mass[i] * h;
        for (int k = 0; k < N; ++k) {
            y[I + k] = c.metalInitial;
            y[O + k] = c.metalInitial;
        }
        for (int a = 0; a < A; ++a)
            y[J + a] = c.waterInitial;
        return y;
    }

    void operator()(const State &v, State &out, double time) {
        out.assign(D + 5, 0);
        Rates q;
        q.evaluation_time = time;
        for (int i = 0; i < B; ++i) {
            temperatures[i] = temperature(c, v[i] / s.mass[i]);
            phase[i] = liquid_fraction(c, temperatures[i]);
            q.melt += s.mass[i] * phase[i] / c.mass;
            if (i < K)
                q.near_mean += s.radial_weights[i] * temperatures[i];
            else
                q.core_mean += s.radial_weights[i - K] * temperatures[i];
        }
        q.melt = std::clamp(q.melt, 0.0, 1.0);
        q.bed = bed_properties(c, q.melt, s.geometry);
        const double index = q.melt * 8;
        const int wet_index = std::min(7, static_cast<int>(std::floor(index)));
        const double blend = index - wet_index;
        auto wet = [&](int k) {
            return s.mesh.wet[wet_index][k] * (1 - blend) + s.mesh.wet[wet_index + 1][k] * blend;
        };
        double film = 0, film_temperature = 0;
        for (int k = 0; k < N; ++k) {
            const double g = s.product_g[k] * wet(k);
            film += g;
            film_temperature += g * v[I + k];
        }
        const double near_g = s.surface_base[0] * (c.ks * (1 - phase[K - 1]) + c.kl * phase[K - 1]);
        const double core_g = s.surface_base[1] * (c.ks * (1 - phase[B - 1]) + c.kl * phase[B - 1]);
        const double bed_g = q.bed.conductance;
        Eigen::Matrix2d matrix;
        matrix << near_g + film + bed_g, -bed_g, -bed_g, core_g + bed_g;
        const Eigen::Vector2d rhs(near_g * temperatures[K - 1] + film_temperature,
                                  core_g * temperatures[B - 1]);
        const Eigen::Vector2d boundary = matrix.ldlt().solve(rhs);
        if (!boundary.allFinite())
            throw std::runtime_error("granule surface balance is singular");
        q.near_surface = boundary[0];
        q.core_surface = boundary[1];
        q.bed_heat = bed_g * (boundary[0] - boundary[1]);
        out[K - 1] -= q.bed_heat;
        out[B - 1] += q.bed_heat;
        for (int pop = 0; pop < 2; ++pop)
            for (int j = 0; j < K - 1; ++j) {
                const int i = pop * K + j;
                const double k1 = c.ks * (1 - phase[i]) + c.kl * phase[i],
                             k2 = c.ks * (1 - phase[i + 1]) + c.kl * phase[i + 1];
                const double heat =
                    s.radial_base[pop][j] * 2 * k1 * k2 / (k1 + k2) * (temperatures[i + 1] - temperatures[i]);
                out[i] += heat;
                out[i + 1] -= heat;
            }
        for (int j = 0; j < K; ++j) {
            const double heat =
                s.exchange_mass_flow * s.radial_weights[j] * (v[j] / s.mass[j] - v[K + j] / s.mass[K + j]);
            out[j] -= heat;
            out[K + j] += heat;
        }
        q.outlet = v[J + A - 1];
        const double requested = std::max(0.0, s.flow_capacity * (c.tin - q.outlet));
        q.source = c.sourceMode ? requested : std::min(requested, c.boiler * 1000 * c.efficiency);
        q.inlet = q.outlet + q.source / s.flow_capacity;

        // Gather form: each surface iteration writes its own derivative and flux slots.
        // Shared reductions occur afterwards in a fixed order for deterministic results.
        auto cell = [&](int k) {
            const int a = k / P, j = k % P;
            const double water = v[J + a], inner = v[I + k], outer = v[O + k];
            const double qw = s.water_inner_g[k] * (water - inner), qo = s.water_outer_g[k] * (water - outer);
            product_flux[k] = s.product_g[k] * wet(k) * (inner - q.near_surface);
            const auto exterior = exterior_flux(c, s.outer_area[k], outer);
            convection_flux[k] = exterior.convection;
            radiation_flux[k] = exterior.radiation;
            surface_temperatures[k] = exterior.surface;
            double di = qw - product_flux[k], dout = qo - exterior.convection - exterior.radiation;
            const int upstream = a * P + (j + P + c.rotationDirection) % P;
            di += s.inner_capacity[k] * s.rotation_rate * (v[I + upstream] - inner);
            dout += s.outer_capacity[k] * s.rotation_rate * (v[O + upstream] - outer);
            const int left = a * P + (j + P - 1) % P, right = a * P + (j + 1) % P;
            di +=
                s.inner_angular_g[a] * (v[I + left] - inner) + s.inner_angular_g[a] * (v[I + right] - inner);
            dout +=
                s.outer_angular_g[a] * (v[O + left] - outer) + s.outer_angular_g[a] * (v[O + right] - outer);
            if (a) {
                di += s.inner_axial_g[a - 1] * (v[I + k - P] - inner);
                dout += s.outer_axial_g[a - 1] * (v[O + k - P] - outer);
            }
            if (a < A - 1) {
                di += s.inner_axial_g[a] * (v[I + k + P] - inner);
                dout += s.outer_axial_g[a] * (v[O + k + P] - outer);
            }
            out[I + k] = di / s.inner_capacity[k];
            out[O + k] = dout / s.outer_capacity[k];
        };
#ifdef _OPENMP
        if (options.parallel_kernel && options.threads > 1 && N >= 4096) {
#pragma omp parallel for schedule(static) num_threads(options.threads)
            for (int k = 0; k < N; ++k)
                cell(k);
        } else
#endif
        {
            for (int k = 0; k < N; ++k)
                cell(k);
        }
        double wet_area = 0;
        for (int a = 0; a < A; ++a) {
            const double water = v[J + a], leak = c.extraUA * s.mesh.weights[a] * (water - c.ambient);
            double water_heat = s.flow_capacity * ((a ? v[J + a - 1] : q.inlet) - water) - leak;
            q.extra += leak;
            for (int j = 0; j < P; ++j) {
                const int k = a * P + j;
                water_heat -=
                    s.water_inner_g[k] * (water - v[I + k]) + s.water_outer_g[k] * (water - v[O + k]);
                out[K - 1] += product_flux[k];
                q.product_heat += product_flux[k];
                q.convection += convection_flux[k];
                q.radiation += radiation_flux[k];
                wet_area += wet(k) * s.inner_area[k];
            }
            out[J + a] = water_heat / s.water_capacity[a];
        }
        q.loss = q.convection + q.radiation + q.extra;
        q.wet_fraction = wet_area / s.geometry.area;
        out[D] = q.source;
        out[D + 1] = q.loss;
        out[D + 2] = q.convection;
        out[D + 3] = q.radiation;
        out[D + 4] = q.extra;
        last = q;
    }

    bool reached(const State &y, double target) const {
        const double h = enthalpy(c, target);
        for (int i = 0; i < B; ++i)
            if (y[i] < s.mass[i] * h)
                return false;
        return true;
    }

    Json snapshot(const State &y, double time) {
        State dy;
        (*this)(y, dy, time);
        const auto &q = last;
        State inner(y.begin() + I, y.begin() + I + N), outer(y.begin() + O, y.begin() + O + N),
            water(y.begin() + J, y.begin() + J + A);
        State near(temperatures.begin(), temperatures.begin() + K),
            core(temperatures.begin() + K, temperatures.end());
        double water_metal = 0, water_storage = 0;
        for (int a = 0; a < A; ++a) {
            water_storage += s.water_capacity[a] * dy[J + a];
            for (int j = 0; j < P; ++j) {
                const int k = a * P + j;
                water_metal +=
                    s.water_inner_g[k] * (y[J + a] - y[I + k]) + s.water_outer_g[k] * (y[J + a] - y[O + k]);
            }
        }
        const double water_flow = s.flow_capacity * (q.inlet - q.outlet);
        return {{"seconds", time},
                {"product", c.nearFraction * q.near_mean + (1 - c.nearFraction) * q.core_mean},
                {"nearProduct", q.near_mean},
                {"coreProduct", std::min(temperatures[0], temperatures[K])},
                {"coreMean", q.core_mean},
                {"nearSurfaceProduct", q.near_surface},
                {"coreSurfaceProduct", q.core_surface},
                {"radialNear", near},
                {"radialCore", core},
                {"liquidFraction", q.melt},
                {"wetFraction", q.wet_fraction},
                {"bedKW", q.bed_heat / 1000},
                {"bedK", q.bed.conductivity},
                {"wall", dot(inner, s.inner_capacity) / sum(s.inner_capacity)},
                {"shell", dot(outer, s.outer_capacity) / sum(s.outer_capacity)},
                {"surface", dot(surface_temperatures, s.outer_area) / sum(s.outer_area)},
                {"waterIn", q.inlet},
                {"waterOut", q.outlet},
                {"waterMetalKW", water_metal / 1000},
                {"waterStorageKW", water_storage / 1000},
                {"waterExtraKW", q.extra / 1000},
                {"waterFlowKW", water_flow / 1000},
                {"waterBalanceResidualW", water_flow - water_metal - q.extra - water_storage},
                {"productKW", q.product_heat / 1000},
                {"boilerWaterKW", q.source / 1000},
                {"lossKW", q.loss / 1000},
                {"inputKWh", y[D] / 3.6e6},
                {"lossKWh", y[D + 1] / 3.6e6},
                {"innerSurface", inner},
                {"outerMetal", outer},
                {"outerSurface", surface_temperatures},
                {"waterZones", water},
                {"surfaceMin", minimum(surface_temperatures)},
                {"surfaceMax", maximum(surface_temperatures)},
                {"innerMin", minimum(inner)},
                {"innerMax", maximum(inner)}};
    }
};
} // namespace

SimulationOptions SimulationOptions::from_json(const Json &data) {
    SimulationOptions o;
    o.integrator = data.value("integrator", o.integrator);
    o.water_model = data.value("waterModel", o.water_model);
    o.relative_tolerance = data.value("relativeTolerance", o.relative_tolerance);
    o.absolute_tolerance = data.value("absoluteTolerance", o.absolute_tolerance);
    o.wall_time_limit = data.value("wallTimeLimit", o.wall_time_limit);
    o.threads = data.value("threads", o.threads);
    o.no_history = data.value("noHistory", false);
    o.parallel_kernel = data.value("parallelKernel", false);
    if (o.integrator != "midpoint" && o.integrator != "rk4" && o.integrator != "dopri5")
        throw std::invalid_argument("unknown integrator");
    if (o.water_model != "constant" && o.water_model != "if97_reference")
        throw std::invalid_argument("unknown water-property model");
    if (!std::isfinite(o.relative_tolerance) || !std::isfinite(o.absolute_tolerance) ||
        o.relative_tolerance <= 0 || o.absolute_tolerance <= 0)
        throw std::invalid_argument("integrator tolerances must be finite and positive");
    if (!std::isfinite(o.wall_time_limit) || o.wall_time_limit <= 0)
        throw std::invalid_argument("wall-time limit must be finite and positive");
    o.threads = std::clamp(o.threads, 1, 32);
    return o;
}

Json backend_info() {
    return {{"name", "Rotary Melter C++"},
            {"version", "3.0.0"},
            {"abi", 1},
            {"standard", "C++20"},
            {"compiler", __VERSION__},
            {"sourceFingerprint", ROTARY_SOURCE_FINGERPRINT},
            {"hardwareThreads", std::thread::hardware_concurrency()},
            {"openmp",
#ifdef _OPENMP
             true
#else
             false
#endif
            },
            {"eigenCompatibilityMacros", std::to_string(EIGEN_WORLD_VERSION) + "." +
                                             std::to_string(EIGEN_MAJOR_VERSION) + "." +
                                             std::to_string(EIGEN_MINOR_VERSION)},
            {"libraries",
             {{"Boost", BOOST_LIB_VERSION},
              {"Eigen", "5.0.0"},
              {"IF97", "2.2.1"},
              {"nlohmann_json", std::to_string(NLOHMANN_JSON_VERSION_MAJOR) + "." +
                                    std::to_string(NLOHMANN_JSON_VERSION_MINOR) + "." +
                                    std::to_string(NLOHMANN_JSON_VERSION_PATCH)},
              {"BS_thread_pool", "5.1.0"}}}};
}

Json simulate(Configuration configuration, const SimulationOptions &options, Progress progress,
              Cancel cancel) {
    const auto started = Clock::now();
    Json property_reference = nullptr;
    if (options.water_model == "if97_reference") {
        property_reference =
            water_properties((configuration.waterInitial + configuration.tin) / 2, configuration.pressure);
        configuration.waterRho = property_reference["densityKgM3"].get<double>();
        configuration.waterCp = property_reference["specificHeatJKgK"].get<double>();
        configuration.waterMu = property_reference["dynamicViscosityPaS"].get<double>();
    }
    const auto spec = thermal_spec(configuration);
    const auto &c = spec.c;
    ThermalSystem system(spec, options);
    State y = system.initial();
    const double end = c.maxHours * 3600, initial_h = enthalpy(c, c.initial),
                 target_h = enthalpy(c, c.target);
    const double interval = std::max(1.0, std::min(30.0, end / 1000));
    double time = 0, next = 0, peak = 0, peak_loss = 0;
    Json melt_time = c.initial >= c.liquidus ? Json(0) : Json(nullptr), history = Json::array(),
         trace = Json::array();
    std::size_t steps = 0, rejected = 0, attempts = 0;
    bool stopped = false;
    auto last_progress = Clock::now();
    using namespace boost::numeric::odeint;
    using Midpoint = explicit_generic_rk<2, 2, State>;
    const Midpoint::coef_a_type a = boost::fusion::make_vector(std::array<double, 1>{{.5}});
    const Midpoint::coef_b_type b = {{0, 1}};
    const Midpoint::coef_c_type stage = {{0, .5}};
    Midpoint midpoint(a, b, stage);
    runge_kutta4<State> rk4;
    auto adaptive =
        make_controlled(options.absolute_tolerance, options.relative_tolerance, runge_kutta_dopri5<State>());
    double adaptive_step = spec.dt;
    while (time < end && !system.reached(y, c.target)) {
        if (attempts++ % 256 == 0) {
            if (cancel && cancel()) {
                stopped = true;
                break;
            }
            const double wall = std::chrono::duration<double>(Clock::now() - started).count();
            if (wall > options.wall_time_limit)
                throw std::runtime_error("calculation exceeded its wall-time budget; reduce the mesh or "
                                         "increase the explicit compute budget");
            if (progress && std::chrono::duration<double>(Clock::now() - last_progress).count() > .2) {
                progress({{"seconds", time},
                          {"maxSeconds", end},
                          {"coreTemperature", temperature(c, y[system.K] / spec.mass[system.K])},
                          {"steps", steps}});
                last_progress = Clock::now();
            }
        }
        if (time >= next) {
            if (!options.no_history)
                history.push_back(system.snapshot(y, time));
            next = next < 2 - 1e-8     ? std::min(2.0, next + .1)
                   : next < 20 - 1e-8  ? std::min(20.0, next + .5)
                   : next < 120 - 1e-8 ? std::min(120.0, next + 2)
                                       : next + interval;
        }
        const double old = time, step = std::min(spec.dt, end - time);
        if (options.integrator == "midpoint") {
            midpoint.do_step(std::ref(system), y, time, step);
            time += step;
        } else if (options.integrator == "rk4") {
            rk4.do_step(std::ref(system), y, time, step);
            time += step;
        } else {
            adaptive_step = std::min({adaptive_step, spec.dt, end - time});
            if (!std::isfinite(adaptive_step) || adaptive_step <= 0 || time + adaptive_step == time)
                throw std::runtime_error(
                    "adaptive step underflow; relax tolerances or revise the physical parameters");
            if (adaptive.try_step(std::ref(system), y, time, adaptive_step) == fail) {
                ++rejected;
                continue;
            }
        }
        ++steps;
        const auto &q = system.last;
        peak = std::max(peak, q.source);
        peak_loss = std::max(peak_loss, q.loss);
        if (trace.size() < 4)
            trace.push_back({{"midpointSeconds", q.evaluation_time},
                             {"stepSeconds", time - old},
                             {"Tnear", q.near_mean},
                             {"Tcore", q.core_mean},
                             {"Tin", q.inlet},
                             {"Tout", q.outlet},
                             {"QsourceW", q.source},
                             {"QproductW", q.product_heat},
                             {"QlossW", q.loss},
                             {"QbedW", q.bed_heat}});
        if (melt_time.is_null() && system.reached(y, c.liquidus))
            melt_time = time;
        if (steps % 2048 == 0 &&
            !std::all_of(y.begin(), y.end(), [](double value) { return std::isfinite(value); }))
            throw std::runtime_error("nonfinite state; check physical parameters and integration controls");
    }
    if (!std::all_of(y.begin(), y.end(), [](double value) { return std::isfinite(value); }))
        throw std::runtime_error("non-finite final state rejected");
    const auto last = system.snapshot(y, time);
    if (!options.no_history)
        history.push_back(last);
    double product_energy = 0, metal_energy = 0, water_energy = 0;
    for (int i = 0; i < system.B; ++i)
        product_energy += y[i] - spec.mass[i] * initial_h;
    for (int k = 0; k < system.N; ++k)
        metal_energy += spec.inner_capacity[k] * (y[system.I + k] - c.metalInitial) +
                        spec.outer_capacity[k] * (y[system.O + k] - c.metalInitial);
    for (int a = 0; a < system.A; ++a)
        water_energy += spec.water_capacity[a] * (y[system.J + a] - c.waterInitial);
    const double input = y[system.D], loss = y[system.D + 1],
                 balance = input - loss - product_energy - metal_energy - water_energy;
    const double relative = std::abs(balance) / std::max({1.0, std::abs(input),
                                                          std::abs(product_energy) + std::abs(metal_energy) +
                                                              std::abs(water_energy) + std::abs(loss)});
    Json engine = backend_info();
    engine["integrator"] = options.integrator;
    engine["waterModel"] = options.water_model;
    engine["threadsRequested"] = options.threads;
    engine["parallelKernelActive"] =
        engine["openmp"].get<bool>() && options.parallel_kernel && options.threads > 1 && system.N >= 4096;
    engine["wallSeconds"] = std::chrono::duration<double>(Clock::now() - started).count();
    engine["rejectedSteps"] = rejected;
    engine["propertyReference"] = property_reference;
    Json result = {
        {"c", c.to_json()},
        {"g", spec.geometry.to_json()},
        {"hp", spec.film_coefficient},
        {"dt", spec.dt},
        {"steps", steps},
        {"trace", trace},
        {"hist", history},
        {"last", last},
        {"targetReached", system.reached(y, c.target)},
        {"seconds", time},
        {"meltingTime", melt_time},
        {"cancelled", stopped},
        {"termination", stopped                       ? "cancelled"
                        : system.reached(y, c.target) ? "target"
                                                      : "duration"},
        {"productEnergyKWh", c.mass * (target_h - initial_h) / 3.6e6},
        {"storedProductKWh", product_energy / 3.6e6},
        {"storedMetalKWh", metal_energy / 3.6e6},
        {"storedWaterKWh", water_energy / 3.6e6},
        {"energyInKWh", input / 3.6e6},
        {"sourceEnergyKWh", input / c.efficiency / 3.6e6},
        {"lossKWh", loss / 3.6e6},
        {"convKWh", y[system.D + 2] / 3.6e6},
        {"radKWh", y[system.D + 3] / 3.6e6},
        {"extraKWh", y[system.D + 4] / 3.6e6},
        {"balanceJ", balance},
        {"balanceRelative", relative},
        {"peakKW", peak / 1000},
        {"peakLossKW", peak_loss / 1000},
        {"psat", saturation_pressure_bar(c.tin)},
        {"hydraulics", hydraulics(c)},
        {"requestedMass", spec.geometry.requested_mass},
        {"bed",
         {{"initial", bed_properties(c, 0, spec.geometry).to_json()},
          {"final", bed_properties(c, last["liquidFraction"].get<double>(), spec.geometry).to_json()}}},
        {"mesh",
         {{"axial", system.A},
          {"angular", system.P},
          {"z0", spec.mesh.z0},
          {"z1", spec.mesh.z1},
          {"axialCenters", spec.mesh.centers},
          {"weights", spec.mesh.weights},
          {"nodes", system.D},
          {"radial", system.K}}},
        {"model",
         {{"method", "C++ Boost.Odeint " + options.integrator +
                         "; conservative radial enthalpy finite volume and zonal metal/water"},
          {"waterCircuit", "Separate shaft feed/return; serial jacket zones"},
          {"productMinimumEnergyJ", c.mass * (target_h - initial_h)},
          {"Cinner", sum(spec.inner_capacity)},
          {"Couter", sum(spec.outer_capacity)},
          {"Cwater", sum(spec.water_capacity)},
          {"flowHeatCapacity", spec.flow_capacity},
          {"rotationRate", spec.rotation_rate},
          {"wallFilmGtotal", sum(spec.water_inner_g)},
          {"productFilmGmax", sum(spec.product_g)},
          {"radialNodes", system.K},
          {"granuleDiameterMm", c.particle},
          {"thermalMechanicalCoupling",
           "one-way selected thermal phase; mechanics do not calibrate contact heat transfer"}}},
        {"engine", engine},
        {"validatedExperimentally", false}};
    Json warnings = Json::array();
    if (c.pressure <= saturation_pressure_bar(c.tin))
        warnings.push_back("Specified water pressure does not support the assumed single liquid phase at "
                           "inlet temperature.");
    if (!spec.geometry.feasible)
        warnings.push_back("The selected charge exceeds the configured bulk/liquid freeboard allowance.");
    warnings.push_back(
        "RPM sensitivity, bed contact and population exchange are model assumptions requiring calibration.");
    if (options.water_model == "if97_reference")
        warnings.push_back("Water properties are fixed at the stated IF97 reference temperature, not varied "
                           "independently during the energy integration.");
    result["warnings"] = warnings;
    if (progress)
        progress({{"seconds", time},
                  {"maxSeconds", end},
                  {"coreTemperature", last["coreProduct"]},
                  {"steps", steps},
                  {"complete", true}});
    return result;
}
} // namespace rotary
