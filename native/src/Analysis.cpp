#include "rotary/Simulation.hpp"
#include "rotary/Thermodynamics.hpp"
#include <BS_thread_pool.hpp>
#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <future>
#include <stdexcept>

namespace rotary {
namespace {
Json summary(const Json &result) {
    const auto &last = result.at("last");
    return {{"targetReached", result.at("targetReached")},
            {"seconds", result.at("seconds")},
            {"targetHours", result["targetReached"].get<bool>() ? Json(result["seconds"].get<double>() / 3600)
                                                                : Json(nullptr)},
            {"productC", last.at("product")},
            {"coreC", last.at("coreProduct")},
            {"liquidFraction", last.at("liquidFraction")},
            {"waterInC", last.at("waterIn")},
            {"waterOutC", last.at("waterOut")},
            {"energyInKWh", result.at("energyInKWh")},
            {"lossKWh", result.at("lossKWh")},
            {"balanceRelative", result.at("balanceRelative")},
            {"dt", result.at("dt")},
            {"steps", result.at("steps")},
            {"wallSeconds", result.at("engine").at("wallSeconds")},
            {"integrator", result.at("engine").at("integrator")},
            {"c", result.at("c")},
            {"hp", result.at("hp")},
            {"meltingTime", result.at("meltingTime")},
            {"cancelled", result.at("cancelled")}};
}

Json grid_index(double coarse, double medium, double fine, double noise = 0) {
    const double d32 = coarse - medium, d21 = medium - fine;
    constexpr double ratio = 2;
    Json out = {{"available", false}, {"refinementRatio", ratio}, {"noiseFloor", noise}};
    if (!std::isfinite(coarse) || !std::isfinite(medium) || !std::isfinite(fine) || fine == 0) {
        out["reason"] = "invalid";
        return out;
    }
    if (std::min(std::abs(d32), std::abs(d21)) <= noise) {
        out["reason"] = "below_time_resolution";
        return out;
    }
    if (d32 * d21 <= 0) {
        out["reason"] = "nonmonotonic";
        return out;
    }
    const double order = std::log(std::abs(d32 / d21)) / std::log(ratio);
    if (order <= 0) {
        out["reason"] = "not_contracting";
        return out;
    }
    const double den = std::pow(ratio, order) - 1, gci_fine = 1.25 * std::abs(d21 / fine) / den,
                 gci_medium = 1.25 * std::abs(d32 / medium) / den;
    out.update({{"available", true},
                {"order", order},
                {"gciFine", gci_fine},
                {"gciMedium", gci_medium},
                {"extrapolated", fine + (fine - medium) / den},
                {"asymptoticRatio", gci_medium / (std::pow(ratio, order) * gci_fine)},
                {"reason", "conditional_estimate"},
                {"note", "Numerical convergence estimate; not experimental validation."}});
    return out;
}

Json run_cases(const Json &cases, const SimulationOptions &options, Progress progress, Cancel cancelled) {
    if (!cases.is_array() || cases.empty() || cases.size() > 256)
        throw std::invalid_argument("analysis requires 1 to 256 independent cases");
    const std::size_t threads = std::min<std::size_t>(options.threads, cases.size());
    BS::thread_pool pool(threads);
    std::vector<std::future<Json>> futures;
    std::atomic<std::size_t> completed = 0;
    for (const auto &item : cases) {
        futures.push_back(pool.submit_task([&, item] {
            Json row = {{"name", item.value("name", std::string("case"))}, {"ok", true}};
            try {
                if (cancelled && cancelled())
                    throw std::runtime_error("analysis cancelled before case start");
                auto inner = options;
                inner.no_history = true;
                inner.threads = 1;
                inner.parallel_kernel = false;
                auto result =
                    simulate(Configuration::from_json(item.at("configuration")), inner, {}, cancelled);
                row["summary"] = summary(result);
            } catch (const std::exception &error) {
                row["ok"] = false;
                row["error"] = error.what();
            }
            const auto done = ++completed;
            if (progress)
                progress({{"stage", "analysis"},
                          {"case", row["name"]},
                          {"completed", done},
                          {"total", cases.size()}});
            return row;
        }));
    }
    Json rows = Json::array();
    for (auto &future : futures)
        rows.push_back(future.get());
    return {{"cases", rows},
            {"threadsUsed", threads},
            {"parallelism", "independent cases; fixed-order result collection; serial dependent time steps"}};
}
} // namespace

Json analyse(const Json &request, Progress progress, Cancel cancelled) {
    const auto started = std::chrono::steady_clock::now();
    auto options = SimulationOptions::from_json(request.value("options", Json::object()));
    const std::string mode = request.value("analysis", std::string("convergence"));
    auto finished = [&](Json result) {
        result["analysis"] = mode;
        result["validatedExperimentally"] = false;
        result["engine"] = backend_info();
        result["wallSeconds"] =
            std::chrono::duration<double>(std::chrono::steady_clock::now() - started).count();
        result["cancelled"] = bool(cancelled && cancelled());
        return result;
    };
    Configuration base = Configuration::from_json(request.at("configuration"));
    Json cases = Json::array();
    auto add = [&](const std::string &name, const Configuration &c) {
        cases.push_back({{"name", name}, {"configuration", c.to_json()}});
    };
    if (mode == "batch")
        cases = request.at("cases");
    else if (mode == "convergence") {
        Configuration coarse = base, fine = base, radial = base;
        coarse.axialZones = std::max(2, base.axialZones / 2);
        coarse.angularZones = std::max(4, base.angularZones / 2);
        fine.axialZones *= 2;
        fine.angularZones *= 2;
        radial.radialZones *= 2;
        if (coarse.axialZones * 2 != base.axialZones || coarse.angularZones * 2 != base.angularZones)
            throw std::invalid_argument(
                "systematic convergence requires an even base grid with at least 4 axial / 8 angular cells");
        const double common = std::min(
            {thermal_spec(base).dt, thermal_spec(coarse).dt, thermal_spec(fine).dt, thermal_spec(radial).dt});
        base.dt = coarse.dt = fine.dt = radial.dt = common;
        Configuration half = base;
        half.dt = common / 2;
        add("coarse", coarse);
        add("base", base);
        add("fine", fine);
        add("half_dt", half);
        add("radial_fine", radial);
    } else if (mode == "sensitivity") {
        add("base", base);
        const double perturb = request.value("perturbation", .1);
        if (!std::isfinite(perturb) || perturb <= 0 || perturb > .5)
            throw std::invalid_argument("sensitivity perturbation must lie in (0,0.5]");
        for (const auto &field : std::vector<std::string>{"rpm", "flow", "href", "exchangePerRev"})
            for (double direction : {-1., 1.}) {
                auto values = base.to_json();
                values[field] = values[field].get<double>() * (1 + direction * perturb);
                if (field == "href")
                    values["href"] = std::max(base.hStatic, values["href"].get<double>());
                cases.push_back(
                    {{"name", field + (direction < 0 ? "_low" : "_high")}, {"configuration", values}});
            }
    } else if (mode == "rpm") {
        for (double rpm = 0; rpm <= base.rpmMax + 1e-9; rpm += base.rpmStep) {
            auto c = base;
            c.rpm = rpm;
            add("rpm_" + std::to_string(rpm), c);
        }
    } else if (mode == "sizing") {
        base.sourceMode = 0;
        base.maxHours = base.goalHours;
        auto inner = options;
        inner.no_history = true;
        double lo = .01, hi = 1000;
        base.boiler = hi;
        auto top = simulate(base, inner, {}, cancelled);
        if (!top["targetReached"].get<bool>())
            return finished({{"analysis", mode},
                             {"possible", false},
                             {"limitKW", hi},
                             {"reason", "target not reached under the specified thermal assumptions"}});
        auto result = top;
        for (int i = 0; i < 16; ++i) {
            if (cancelled && cancelled())
                throw std::runtime_error("analysis cancelled");
            const double mid = (lo + hi) / 2;
            base.boiler = mid;
            auto next = simulate(base, inner, {}, cancelled);
            if (next["targetReached"].get<bool>()) {
                hi = mid;
                result = std::move(next);
            } else
                lo = mid;
            if (progress)
                progress({{"stage", "sizing"},
                          {"iteration", i + 1},
                          {"total", 16},
                          {"lowKW", lo},
                          {"highKW", hi}});
        }
        return finished(
            {{"analysis", mode},
             {"possible", true},
             {"kw", hi},
             {"result", result},
             {"parallelism", "sequential bracket refinement; each bound depends on the preceding solve"},
             {"note", "Conditional model sizing; not an equipment purchase specification."}});
    } else
        throw std::invalid_argument("unknown analysis type");
    auto result = run_cases(cases, options, progress, cancelled);
    if (mode == "convergence") {
        const auto &rows = result["cases"];
        const bool valid = std::all_of(rows.begin(), rows.end(), [](const Json &row) {
            return row["ok"].get<bool>() && !row["summary"]["cancelled"].get<bool>();
        });
        if (valid) {
            const double c = rows[0]["summary"]["seconds"], b = rows[1]["summary"]["seconds"],
                         f = rows[2]["summary"]["seconds"];
            const bool targets = rows[0]["summary"]["targetReached"].get<bool>() &&
                                 rows[1]["summary"]["targetReached"].get<bool>() &&
                                 rows[2]["summary"]["targetReached"].get<bool>();
            result["targetGci"] = targets ? grid_index(c, b, f, base.dt * 2)
                                          : Json{{"available", false}, {"reason", "target_not_reached"}};
            result["energyGci"] =
                grid_index(rows[0]["summary"]["energyInKWh"], rows[1]["summary"]["energyInKWh"],
                           rows[2]["summary"]["energyInKWh"]);
            result["commonTimeStepSeconds"] = base.dt;
            auto target_difference = [&](int index) -> Json {
                if (!rows[1]["summary"]["targetReached"].get<bool>() ||
                    !rows[index]["summary"]["targetReached"].get<bool>())
                    return nullptr;
                const double refined = rows[index]["summary"]["seconds"];
                return 100 * std::abs(refined - b) / std::max(1e-12, refined);
            };
            result["timeDifferencePercent"] = target_difference(3);
            result["radialDifferencePercent"] = target_difference(4);
        }
    }
    if (mode == "sensitivity") {
        Json sensitivities = Json::array();
        const auto &rows = result["cases"];
        const std::vector<std::string> fields = {"rpm", "flow", "href", "exchangePerRev"};
        for (std::size_t i = 0; i < fields.size(); ++i) {
            const auto &field = fields[i];
            const auto &low = rows[1 + 2 * i];
            const auto &high = rows[2 + 2 * i];
            Json item = {{"parameter", field}, {"available", false}};
            if (!rows[0]["ok"].get<bool>() || !low["ok"].get<bool>() || !high["ok"].get<bool>())
                item["reason"] = "invalid_case";
            else {
                const auto &b = rows[0]["summary"];
                const auto &l = low["summary"];
                const auto &h = high["summary"];
                const double p0 = b["c"][field],
                             span = h["c"][field].get<double>() - l["c"][field].get<double>();
                if (span == 0 || p0 == 0)
                    item["reason"] = "zero_parameter_span";
                else if (!b["targetReached"].get<bool>() || !l["targetReached"].get<bool>() ||
                         !h["targetReached"].get<bool>())
                    item["reason"] = "target_not_reached";
                else {
                    const double t0 = b["seconds"], e0 = b["energyInKWh"];
                    if (t0 <= 0 || e0 == 0)
                        item["reason"] = "zero_response";
                    else
                        item.update(
                            {{"available", true},
                             {"timeElasticity",
                              (h["seconds"].get<double>() - l["seconds"].get<double>()) / span * p0 / t0},
                             {"energyElasticity",
                              (h["energyInKWh"].get<double>() - l["energyInKWh"].get<double>()) / span * p0 /
                                  e0},
                             {"parameterLow", l["c"][field]},
                             {"parameterHigh", h["c"][field]},
                             {"reason", "local_finite_difference"}});
                }
            }
            sensitivities.push_back(item);
        }
        result["sensitivities"] = sensitivities;
    }
    return finished(std::move(result));
}

Json execute(const Json &request, Progress progress, Cancel cancelled) {
    const std::string action = request.value("action", std::string("simulate"));
    if (action == "info")
        return backend_info();
    if (action == "water_properties")
        return water_properties(request.at("temperatureC"), request.at("pressureBarAbs"));
    if (action == "analyse")
        return analyse(request, progress, cancelled);
    const auto configuration =
        Configuration::from_json(request.contains("configuration") ? request["configuration"] : request);
    if (action == "geometry")
        return geometry(configuration).to_json();
    if (action == "hydraulics")
        return hydraulics(configuration);
    if (action != "simulate")
        throw std::invalid_argument("unknown native action");
    return simulate(configuration, SimulationOptions::from_json(request.value("options", Json::object())),
                    progress, cancelled);
}
} // namespace rotary
