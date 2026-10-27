#include "rotary/Geometry.hpp"
#include <algorithm>
#include <boost/math/tools/toms748_solve.hpp>
#include <cmath>
#include <limits>
#include <numeric>

namespace rotary {
namespace {
double sum(const std::vector<double> &values) {
    return std::accumulate(values.begin(), values.end(), 0.0);
}

std::vector<Slice> vessel_slices(const Configuration &c, int count) {
    const double radius = c.diameter / 2000, length = c.length / 1000, head = c.headDepth / 1000;
    std::vector<Slice> slices;
    auto add = [&](double lo, double hi, int n, int kind) {
        if (hi <= lo)
            return;
        const double dz = (hi - lo) / n,
                     sphere = head > 0 ? (radius * radius + head * head) / (2 * head) : radius;
        for (int i = 0; i < n; ++i) {
            const double z = lo + (i + .5) * dz;
            const double t = kind < 0 ? z : kind > 0 ? length - z : 0;
            const double r =
                kind == 0 ? radius
                          : std::sqrt(std::max(0.0, sphere * sphere - std::pow(t - (sphere - head), 2)));
            slices.push_back({z, r, dz, pi * r * r * dz, 2 * pi * (kind == 0 ? r : sphere) * dz});
        }
    };
    const int head_count = std::max(24, static_cast<int>(std::lround(count * head / length)));
    if (c.heads)
        add(-head, 0, head_count, -1);
    add(0, length, count, 0);
    if (c.heads == 2)
        add(length, length + head, head_count, 1);
    return slices;
}

double disk_fraction(double u) {
    if (u <= -1)
        return 0;
    if (u >= 1)
        return 1;
    return .5 + (std::asin(u) + u * std::sqrt(1 - u * u)) / pi;
}

void local_fill(Slice &slice, double plane, double fraction, double sine, double cosine) {
    if (fraction == 0 || fraction == 1) {
        slice.volume_fraction = slice.wet_fraction = fraction;
        slice.u = fraction == 0 ? -1 : 1;
    } else if (cosine < 1e-8) {
        const double full = plane >= slice.z * sine ? 1 : 0;
        slice.volume_fraction = slice.wet_fraction = full;
        slice.u = full ? 1 : -1;
    } else {
        const double u = (plane - slice.z * sine) / (slice.radius * cosine);
        slice.volume_fraction = disk_fraction(u);
        slice.wet_fraction = u <= -1 ? 0 : u >= 1 ? 1 : .5 + std::asin(u) / pi;
        slice.u = std::clamp(u, -1.0, 1.0);
    }
}

double friction_factor(double reynolds, double relative_roughness, double ratio) {
    const double poisson =
        ratio > 0 ? 64 * std::pow(1 - ratio, 2) * (1 - ratio * ratio) /
                        (1 - std::pow(ratio, 4) - std::pow(1 - ratio * ratio, 2) / std::log(1 / ratio))
                  : 64;
    const double laminar = poisson / std::max(reynolds, 1e-12);
    if (reynolds < 2300)
        return laminar;
    auto colebrook = [&](double factor) {
        return 1 / std::sqrt(factor) +
               2 * std::log10(relative_roughness / 3.7 + 2.51 / (reynolds * std::sqrt(factor)));
    };
    std::uintmax_t iterations = 80;
    const auto root = boost::math::tools::toms748_solve(
        colebrook, 1e-5, 1.0, [](double a, double b) { return std::abs(a - b) < 1e-14; }, iterations);
    const double turbulent = (root.first + root.second) / 2;
    if (reynolds >= 4000)
        return turbulent;
    return laminar + (turbulent - laminar) * (reynolds - 2300) / 1700;
}
} // namespace

Json Slice::to_json() const {
    return {{"z", z},     {"r", radius},           {"dz", dz},           {"dV", volume},
            {"dA", area}, {"vf", volume_fraction}, {"wf", wet_fraction}, {"u", u}};
}
Json FillProfile::to_json() const {
    Json profile = Json::array();
    for (const auto &slice : slices)
        profile.push_back(slice.to_json());
    return {{"plane", plane},
            {"fraction", fraction},
            {"wetFraction", wet_fraction},
            {"profile", profile},
            {"quadratureVolume", quadrature_volume}};
}
Json Geometry::to_json() const {
    return {{"volume", volume},
            {"headV", head_volume},
            {"area", area},
            {"heated", heated},
            {"external", external},
            {"waterV", water_volume},
            {"mInner", inner_mass},
            {"mOuter", outer_mass},
            {"liquidV", liquid_volume},
            {"bulkV", bulk_volume},
            {"solidV", solid_volume},
            {"maxMass", max_mass},
            {"feasible", feasible},
            {"bulkFill", bulk_fill},
            {"liquidFill", liquid_fill},
            {"chargeMass", charge_mass},
            {"requestedMass", requested_mass},
            {"fillProfile", tilt_applied ? fill.to_json() : Json(nullptr)},
            {"wetInitial", wet_initial},
            {"tiltApplied", tilt_applied}};
}
Json BedProperties::to_json() const {
    return {{"kBed", conductivity},
            {"kSeries", series},
            {"kParallel", parallel},
            {"conductance", conductance},
            {"mixing", mixing},
            {"total", total},
            {"solidContactK", solid_contact_k},
            {"particleBi", particle_biot}};
}

FillProfile fill_profile(const Configuration &c, double requested, int count) {
    auto slices = vessel_slices(c, count);
    const double angle = c.angle * pi / 180, sine = std::sin(angle), cosine = std::cos(angle);
    const double fraction = std::clamp(requested, 0.0, 1.0);
    double lo = std::numeric_limits<double>::infinity(), hi = -lo, total = 0, area = 0;
    for (const auto &slice : slices) {
        lo = std::min(lo, slice.z * sine - slice.radius * cosine);
        hi = std::max(hi, slice.z * sine + slice.radius * cosine);
        total += slice.volume;
        area += slice.area;
    }
    lo -= 1e-8;
    hi += 1e-8;
    // Keep a bracketed solve for near-vertical discontinuities as well as smooth fills.
    if (fraction > 0 && fraction < 1) {
        auto balance = [&](double plane) {
            double filled = 0;
            for (auto slice : slices) {
                local_fill(slice, plane, fraction, sine, cosine);
                filled += slice.volume * slice.volume_fraction;
            }
            return filled / total - fraction;
        };
        std::uintmax_t iterations = 80;
        const auto bracket = boost::math::tools::toms748_solve(
            balance, lo, hi, [](double a, double b) { return std::abs(a - b) < 1e-14; }, iterations);
        lo = bracket.first;
        hi = bracket.second;
    }
    const double plane = fraction == 0 ? lo : fraction == 1 ? hi : (lo + hi) / 2;
    double volume = 0, wet = 0;
    for (auto &slice : slices) {
        local_fill(slice, plane, fraction, sine, cosine);
        volume += slice.volume * slice.volume_fraction;
        wet += slice.area * slice.wet_fraction;
    }
    return {plane, volume / total, wet / area, total, std::move(slices)};
}

Geometry geometry(const Configuration &c) {
    Geometry g;
    const double r = c.diameter / 2000, length = c.length / 1000, h = c.headDepth / 1000;
    const double wall = c.wall / 1000, gap = c.gap / 1000, shell = c.shell / 1000;
    g.head_volume = c.heads * pi * h * (3 * r * r + h * h) / 6;
    g.volume = pi * r * r * length + g.head_volume;
    g.area = 2 * pi * r * length + c.heads * pi * (r * r + h * h);
    g.heated = g.area * c.coverage;
    const double ro = r + wall + gap + shell, ho = h + wall + gap + shell;
    g.external = (2 * pi * ro * length + c.heads * pi * (ro * ro + ho * ho)) * c.coverage;
    g.water_volume = (pi * (std::pow(r + wall + gap, 2) - std::pow(r + wall, 2)) * length +
                      c.heads * pi * (r * r + h * h) * gap) *
                         c.coverage +
                     c.loopL / 1000;
    g.inner_mass = g.area * wall * c.steelRho;
    g.outer_mass = g.external * shell * c.steelRho;
    g.requested_mass = c.mass;
    g.charge_mass = c.chargeMode == 1 ? g.volume * c.targetFill * c.packing * c.rhos : c.mass;
    g.liquid_volume = g.charge_mass / c.rhol;
    g.bulk_volume = g.charge_mass / (c.rhos * c.packing);
    g.solid_volume = g.charge_mass / c.rhos;
    const double limit = g.volume * (1 - c.freeboard);
    g.max_mass = std::min(limit * c.rhos * c.packing, limit * c.rhol);
    g.feasible = g.bulk_volume <= limit && g.liquid_volume <= limit;
    g.bulk_fill = g.bulk_volume / g.volume;
    g.liquid_fill = g.liquid_volume / g.volume;
    g.tilt_applied = c.tiltModel == 1;
    if (g.tilt_applied)
        g.fill = fill_profile(c, g.bulk_fill);
    g.wet_initial = g.tilt_applied ? g.fill.wet_fraction : c.contact;
    return g;
}

double rpm_heat_transfer(const Configuration &c) {
    const double ratio = std::pow(c.rpm / c.rpmRef, c.rpmExponent);
    return c.rpmMode == 0 ? c.href * (1 + c.rpmGain * ratio)
                          : std::min(c.hLimit, c.hStatic + (c.href - c.hStatic) * ratio);
}

BedProperties bed_properties(const Configuration &c, double melt, const Geometry &g) {
    const double f = std::clamp(melt, 0.0, 1.0), diameter = std::max(c.particle / 1000, 1e-5);
    const double contact = c.ks / (1 + c.contactR * c.ks / diameter),
                 packing = c.packing + (1 - c.packing) * f;
    const double solid = contact * (1 - f) + c.kl * f, pore = c.gasK * (1 - f) + c.kl * f;
    const double series = 1 / (packing / solid + (1 - packing) / pore),
                 parallel = packing * solid + (1 - packing) * pore;
    const double effective = series + c.contactTopology * (parallel - series);
    const double volume = g.charge_mass * ((1 - f) / (c.rhos * c.packing) + f / c.rhol);
    const double conductance = effective * std::pow(std::max(volume, 1e-9), 2.0 / 3) /
                               std::max(diameter, c.bedPathFactor * c.diameter / 1000);
    const double mixing = g.charge_mass * c.cpl * c.exchangePerRev * c.rpm / 60;
    return {effective, series,
            parallel,  conductance,
            mixing,    conductance + mixing,
            contact,   rpm_heat_transfer(c) * diameter / (6 * c.ks)};
}

Json hydraulics(const Configuration &c) {
    const double flow = c.flow / 3600;
    Json rows = Json::array();
    double straight = 0, minor = 0;
    auto segment = [&](const char *name, double outer_mm, double length, double local_k,
                       double inner_mm = 0) {
        const double outer = outer_mm / 1000, inner = inner_mm / 1000;
        const double area = pi * (outer * outer - inner * inner) / 4, dh = outer - inner,
                     velocity = flow / area;
        const double re = c.waterRho * velocity * dh / c.waterMu;
        const double factor = friction_factor(re, c.roughness / 1000 / dh, inner / outer);
        const double pressure = .5 * c.waterRho * velocity * velocity,
                     friction = factor * length / dh * pressure, local = local_k * pressure;
        straight += friction;
        minor += local;
        rows.push_back({{"name", name},
                        {"diameter", dh * 1000},
                        {"area", area},
                        {"length", length},
                        {"velocity", velocity},
                        {"re", re},
                        {"f", factor},
                        {"frictionPa", friction},
                        {"localPa", local},
                        {"totalPa", friction + local},
                        {"regime", re < 2300   ? "Laminer"
                                   : re < 4000 ? "Geçiş"
                                               : "Türbülanslı"}});
    };
    segment("Besleme hattı", c.supplyD, c.supplyL, c.supplyK);
    segment("Mil besleme kanalı", c.feedD, c.feedL, c.feedK);
    segment("Ceket, eşdeğer eksenel halka", c.diameter + 2 * c.wall + 2 * c.gap, c.length / 1000, c.jacketK,
            c.diameter + 2 * c.wall);
    segment("Mil dönüş halkası", c.returnOuter, c.shaftReturnL, c.shaftReturnK, c.returnInner);
    segment("Dönüş hattı", c.returnD, c.returnL, c.returnK);
    const double extra = (c.jointDropBar + c.equipmentDropBar) * 1e5, total = straight + minor + extra;
    return {{"rows", rows},
            {"totalPa", total},
            {"totalBar", total / 1e5},
            {"straightPa", straight},
            {"minorPa", minor},
            {"extraPa", extra},
            {"headM", total / (c.waterRho * 9.80665)},
            {"hydraulicKW", flow * total / 1000},
            {"pumpInputKW", flow * total / (1000 * c.pumpEfficiency)},
            {"estimatedOutletBar", c.pressure - total / 1e5},
            {"missingComponentData", c.jointDropBar == 0 || c.equipmentDropBar == 0}};
}

ThermalSpec thermal_spec(const Configuration &original) {
    original.validate();
    ThermalSpec s;
    s.geometry = geometry(original);
    s.c = original;
    s.c.mass = s.geometry.charge_mass;
    const auto &c = s.c;
    const auto &g = s.geometry;
    auto &m = s.mesh;
    m.axial = c.axialZones;
    m.angular = c.angularZones;
    m.cells = m.axial * m.angular;
    const int A = m.axial, P = m.angular, N = m.cells;
    auto full = fill_profile(c, .5, std::max(140, A * 14));
    m.z0 = full.slices.front().z - full.slices.front().dz / 2;
    m.z1 = full.slices.back().z + full.slices.back().dz / 2;
    m.dz = (m.z1 - m.z0) / A;
    m.weights.assign(A, 0);
    m.centers.resize(A);
    auto bin = [&](const Slice &slice) {
        return std::clamp(static_cast<int>(std::floor((slice.z - m.z0) / m.dz)), 0, A - 1);
    };
    for (const auto &slice : full.slices)
        m.weights[bin(slice)] += slice.area;
    const double total = sum(m.weights);
    for (int a = 0; a < A; ++a) {
        m.weights[a] /= total;
        m.centers[a] = m.z0 + (a + .5) * m.dz;
    }
    for (int f = 0; f <= 8; ++f) {
        const double melt = f / 8.0,
                     volume = g.charge_mass * ((1 - melt) / (c.rhos * c.packing) + melt / c.rhol);
        const auto profile = fill_profile(c, volume / g.volume, std::max(140, A * 14));
        std::vector<double> wet(N, 0);
        for (const auto &slice : profile.slices) {
            const int a = bin(slice);
            const double edge = slice.u <= -1 ? pi : slice.u >= 1 ? 0 : std::acos(slice.u);
            for (int j = 0; j < P; ++j) {
                const double lo = j * 2 * pi / P, hi = (j + 1) * 2 * pi / P;
                const double overlap =
                    std::max(0.0, std::min(hi, 2 * pi - edge) - std::max(lo, edge)) / (2 * pi / P);
                wet[a * P + j] += slice.area * overlap / (m.weights[a] * total);
            }
        }
        m.wet.push_back(std::move(wet));
    }
    s.film_coefficient = rpm_heat_transfer(c);
    for (auto *values : {&s.inner_capacity, &s.outer_capacity, &s.inner_area, &s.outer_area, &s.water_inner_g,
                         &s.water_outer_g, &s.product_g})
        values->resize(N);
    for (auto *values : {&s.water_capacity, &s.inner_angular_g, &s.outer_angular_g})
        values->resize(A);
    s.inner_axial_g.resize(A - 1);
    s.outer_axial_g.resize(A - 1);
    for (int a = 0; a < A; ++a) {
        const double weight = m.weights[a], arc = c.diameter / 2000 * 2 * pi / P;
        s.water_capacity[a] = g.water_volume * c.waterRho * c.waterCp * weight;
        s.inner_angular_g[a] = c.steelK * c.wall / 1000 * m.dz / arc;
        s.outer_angular_g[a] = c.steelK * c.shell / 1000 * m.dz / arc;
        for (int j = 0; j < P; ++j) {
            const int k = a * P + j;
            s.inner_area[k] = g.area * weight / P;
            s.outer_area[k] = g.external * weight / P;
            s.inner_capacity[k] = g.inner_mass * c.steelCp * weight / P;
            s.outer_capacity[k] = g.outer_mass * c.steelCp * weight / P;
            s.water_inner_g[k] = g.heated * weight / P / (1 / c.waterH + c.wall / 2000 / c.steelK);
            s.water_outer_g[k] = s.outer_area[k] / (1 / c.waterH + c.shell / 2000 / c.steelK);
            s.product_g[k] =
                g.heated * weight / P * c.contact / (1 / s.film_coefficient + c.wall / 2000 / c.steelK);
        }
    }
    for (int a = 0; a < A - 1; ++a) {
        s.inner_axial_g[a] = c.steelK * c.wall / 1000 * pi * c.diameter / 1000 / (P * m.dz);
        s.outer_axial_g[a] =
            c.steelK * c.shell / 1000 * pi * (c.diameter + 2 * c.wall + 2 * c.gap) / 1000 / (P * m.dz);
    }
    s.flow_capacity = c.flow / 3600 * c.waterRho * c.waterCp;
    s.rotation_rate = c.rpm * P / 60;
    const double m1 = c.mass * c.nearFraction, m2 = c.mass - m1;
    s.population = {m1, m2};
    const double gb = std::max(bed_properties(c, 0, g).total, bed_properties(c, 1, g).total),
                 cp = std::min(c.cps, c.cpl);
    const double max_t = std::max({c.tin, c.waterInitial, c.metalInitial, c.target}) + 273.15;
    const double radiation_h = 4 * c.emissivity * 5.670374419e-8 * max_t * max_t * max_t;
    s.dt = std::min({c.dt, .16 * m1 * cp / (sum(s.product_g) + gb), .16 * m2 * cp / gb});
    for (int a = 0; a < A; ++a) {
        const int first = a * P;
        const double water_g = s.flow_capacity + P * (s.water_inner_g[first] + s.water_outer_g[first]) +
                               c.extraUA * m.weights[a];
        s.dt = std::min(s.dt, .16 * s.water_capacity[a] / water_g);
        for (int j = 0; j < P; ++j) {
            const int k = a * P + j;
            const double axial_i = (a ? s.inner_axial_g[a - 1] : 0) + (a < A - 1 ? s.inner_axial_g[a] : 0);
            const double axial_o = (a ? s.outer_axial_g[a - 1] : 0) + (a < A - 1 ? s.outer_axial_g[a] : 0);
            s.dt =
                std::min({s.dt,
                          .16 * s.inner_capacity[k] /
                              (s.water_inner_g[k] + s.product_g[k] + 2 * s.inner_angular_g[a] + axial_i +
                               s.inner_capacity[k] * s.rotation_rate),
                          .16 * s.outer_capacity[k] /
                              (s.water_outer_g[k] + s.outer_area[k] * (c.externalH + radiation_h) +
                               2 * s.outer_angular_g[a] + axial_o + s.outer_capacity[k] * s.rotation_rate)});
        }
    }
    s.radial = c.radialZones;
    const int K = s.radial;
    const double r = c.particle / 2000, dr = r / K;
    s.radial_weights.resize(K);
    s.mass.resize(2 * K);
    s.radial_base.assign(2, std::vector<double>(K - 1));
    s.surface_base.resize(2);
    s.exchange_mass_flow = c.mass * c.exchangePerRev * c.rpm / 60;
    for (int j = 0; j < K; ++j)
        s.radial_weights[j] = (std::pow(j + 1, 3) - std::pow(j, 3)) / std::pow(K, 3);
    const double bed_max = std::max(bed_properties(c, 0, g).conductance, bed_properties(c, 1, g).conductance);
    const double k_max = std::max(c.ks, c.kl);
    for (int pop = 0; pop < 2; ++pop) {
        const double particles = s.population[pop] / (c.rhos * 4 * pi * r * r * r / 3);
        for (int j = 0; j < K; ++j)
            s.mass[pop * K + j] = s.population[pop] * s.radial_weights[j];
        for (int j = 0; j < K - 1; ++j)
            s.radial_base[pop][j] = particles * 4 * pi * std::pow((j + 1) * dr, 2) / dr;
        s.surface_base[pop] = particles * 4 * pi * r * r / (dr / 2);
        for (int j = 0; j < K; ++j) {
            const double conductance = (j ? s.radial_base[pop][j - 1] * k_max : 0) +
                                       (j < K - 1 ? s.radial_base[pop][j] * k_max : 0) +
                                       (j == K - 1 ? ((pop == 0 ? sum(s.product_g) : 0) + bed_max) : 0) +
                                       s.exchange_mass_flow * s.radial_weights[j] * cp;
            s.dt = std::min(s.dt, .12 * s.mass[pop * K + j] * cp / std::max(1e-20, conductance));
        }
    }
    return s;
}
} // namespace rotary
