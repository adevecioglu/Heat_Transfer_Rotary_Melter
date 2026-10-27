#include "rotary/Configuration.hpp"
#include <cmath>
#include <limits>
#include <stdexcept>
#include <type_traits>

namespace rotary {
Configuration Configuration::from_json(const Json &envelope) {
    const Json &input = envelope.contains("inputs") ? envelope.at("inputs") : envelope;
    if (!input.is_object())
        throw std::invalid_argument("inputs must be a JSON object");
    Configuration result;
    auto read = [&](const char *key, auto &target) {
        if (!input.contains(key))
            return;
        if (!input[key].is_number())
            throw std::invalid_argument(std::string(key) + ": expected a number");
        const double value = input[key].get<double>();
        if (!std::isfinite(value))
            throw std::invalid_argument(std::string(key) + ": expected a finite number");
        using T = std::remove_reference_t<decltype(target)>;
        if constexpr (std::is_integral_v<T>) {
            if (std::trunc(value) != value || value < std::numeric_limits<int>::min() ||
                value > std::numeric_limits<int>::max())
                throw std::invalid_argument(std::string(key) + ": expected an integer");
        }
        target = static_cast<T>(value);
    };
    read("diameter", result.diameter);
    read("length", result.length);
    read("headDepth", result.headDepth);
    read("heads", result.heads);
    read("wall", result.wall);
    read("shell", result.shell);
    read("gap", result.gap);
    read("coverage", result.coverage);
    read("contact", result.contact);
    read("angle", result.angle);
    read("packing", result.packing);
    read("freeboard", result.freeboard);
    read("mass", result.mass);
    read("rhos", result.rhos);
    read("rhol", result.rhol);
    read("cps", result.cps);
    read("cpl", result.cpl);
    read("latent", result.latent);
    read("ks", result.ks);
    read("kl", result.kl);
    read("solidus", result.solidus);
    read("liquidus", result.liquidus);
    read("initial", result.initial);
    read("target", result.target);
    read("particle", result.particle);
    read("steelK", result.steelK);
    read("steelRho", result.steelRho);
    read("steelCp", result.steelCp);
    read("tin", result.tin);
    read("flow", result.flow);
    read("waterInitial", result.waterInitial);
    read("metalInitial", result.metalInitial);
    read("waterRho", result.waterRho);
    read("waterCp", result.waterCp);
    read("waterH", result.waterH);
    read("loopL", result.loopL);
    read("pressure", result.pressure);
    read("boiler", result.boiler);
    read("efficiency", result.efficiency);
    read("sourceMode", result.sourceMode);
    read("ambient", result.ambient);
    read("externalH", result.externalH);
    read("emissivity", result.emissivity);
    read("insulation", result.insulation);
    read("insulationK", result.insulationK);
    read("extraUA", result.extraUA);
    read("rpm", result.rpm);
    read("href", result.href);
    read("rpmRef", result.rpmRef);
    read("rpmGain", result.rpmGain);
    read("rpmExponent", result.rpmExponent);
    read("rpmMode", result.rpmMode);
    read("hStatic", result.hStatic);
    read("hLimit", result.hLimit);
    read("rpmMax", result.rpmMax);
    read("rpmStep", result.rpmStep);
    read("maxHours", result.maxHours);
    read("dt", result.dt);
    read("goalHours", result.goalHours);
    read("chargeMode", result.chargeMode);
    read("targetFill", result.targetFill);
    read("tiltModel", result.tiltModel);
    read("bedModel", result.bedModel);
    read("nearFraction", result.nearFraction);
    read("exchangePerRev", result.exchangePerRev);
    read("contactTopology", result.contactTopology);
    read("contactR", result.contactR);
    read("gasK", result.gasK);
    read("bedPathFactor", result.bedPathFactor);
    read("waterMu", result.waterMu);
    read("roughness", result.roughness);
    read("supplyD", result.supplyD);
    read("supplyL", result.supplyL);
    read("supplyK", result.supplyK);
    read("returnD", result.returnD);
    read("returnL", result.returnL);
    read("returnK", result.returnK);
    read("feedD", result.feedD);
    read("feedL", result.feedL);
    read("feedK", result.feedK);
    read("returnOuter", result.returnOuter);
    read("returnInner", result.returnInner);
    read("shaftReturnL", result.shaftReturnL);
    read("shaftReturnK", result.shaftReturnK);
    read("jacketK", result.jacketK);
    read("jointDropBar", result.jointDropBar);
    read("equipmentDropBar", result.equipmentDropBar);
    read("pumpEfficiency", result.pumpEfficiency);
    read("thermalModel", result.thermalModel);
    read("axialZones", result.axialZones);
    read("angularZones", result.angularZones);
    read("rotationDirection", result.rotationDirection);
    read("radialZones", result.radialZones);
    if (!input.contains("rpmMode"))
        result.rpmMode = 0;
    // The current V11 migration selects the regional, inclined, two-population model.
    result.thermalModel = result.bedModel = result.tiltModel = 1;
    result.validate();
    return result;
}

Json Configuration::to_json() const {
    return Json{{"diameter", diameter},
                {"length", length},
                {"headDepth", headDepth},
                {"heads", heads},
                {"wall", wall},
                {"shell", shell},
                {"gap", gap},
                {"coverage", coverage},
                {"contact", contact},
                {"angle", angle},
                {"packing", packing},
                {"freeboard", freeboard},
                {"mass", mass},
                {"rhos", rhos},
                {"rhol", rhol},
                {"cps", cps},
                {"cpl", cpl},
                {"latent", latent},
                {"ks", ks},
                {"kl", kl},
                {"solidus", solidus},
                {"liquidus", liquidus},
                {"initial", initial},
                {"target", target},
                {"particle", particle},
                {"steelK", steelK},
                {"steelRho", steelRho},
                {"steelCp", steelCp},
                {"tin", tin},
                {"flow", flow},
                {"waterInitial", waterInitial},
                {"metalInitial", metalInitial},
                {"waterRho", waterRho},
                {"waterCp", waterCp},
                {"waterH", waterH},
                {"loopL", loopL},
                {"pressure", pressure},
                {"boiler", boiler},
                {"efficiency", efficiency},
                {"sourceMode", sourceMode},
                {"ambient", ambient},
                {"externalH", externalH},
                {"emissivity", emissivity},
                {"insulation", insulation},
                {"insulationK", insulationK},
                {"extraUA", extraUA},
                {"rpm", rpm},
                {"href", href},
                {"rpmRef", rpmRef},
                {"rpmGain", rpmGain},
                {"rpmExponent", rpmExponent},
                {"rpmMode", rpmMode},
                {"hStatic", hStatic},
                {"hLimit", hLimit},
                {"rpmMax", rpmMax},
                {"rpmStep", rpmStep},
                {"maxHours", maxHours},
                {"dt", dt},
                {"goalHours", goalHours},
                {"chargeMode", chargeMode},
                {"targetFill", targetFill},
                {"tiltModel", tiltModel},
                {"bedModel", bedModel},
                {"nearFraction", nearFraction},
                {"exchangePerRev", exchangePerRev},
                {"contactTopology", contactTopology},
                {"contactR", contactR},
                {"gasK", gasK},
                {"bedPathFactor", bedPathFactor},
                {"waterMu", waterMu},
                {"roughness", roughness},
                {"supplyD", supplyD},
                {"supplyL", supplyL},
                {"supplyK", supplyK},
                {"returnD", returnD},
                {"returnL", returnL},
                {"returnK", returnK},
                {"feedD", feedD},
                {"feedL", feedL},
                {"feedK", feedK},
                {"returnOuter", returnOuter},
                {"returnInner", returnInner},
                {"shaftReturnL", shaftReturnL},
                {"shaftReturnK", shaftReturnK},
                {"jacketK", jacketK},
                {"jointDropBar", jointDropBar},
                {"equipmentDropBar", equipmentDropBar},
                {"pumpEfficiency", pumpEfficiency},
                {"thermalModel", thermalModel},
                {"axialZones", axialZones},
                {"angularZones", angularZones},
                {"rotationDirection", rotationDirection},
                {"radialZones", radialZones}};
}

void Configuration::validate() const {
    auto positive = [](double v, const char *name) {
        if (!(v > 0) || !std::isfinite(v))
            throw std::invalid_argument(std::string(name) + ": must be finite and positive");
    };
    auto nonnegative = [](double v, const char *name) {
        if (!(v >= 0) || !std::isfinite(v))
            throw std::invalid_argument(std::string(name) + ": must be finite and nonnegative");
    };
    positive(diameter, "diameter");
    positive(length, "length");
    positive(wall, "wall");
    positive(shell, "shell");
    positive(gap, "gap");
    positive(mass, "mass");
    positive(rhos, "rhos");
    positive(rhol, "rhol");
    positive(cps, "cps");
    positive(cpl, "cpl");
    positive(ks, "ks");
    positive(kl, "kl");
    positive(steelK, "steelK");
    positive(steelRho, "steelRho");
    positive(steelCp, "steelCp");
    positive(flow, "flow");
    positive(waterRho, "waterRho");
    positive(waterCp, "waterCp");
    positive(waterH, "waterH");
    positive(pressure, "pressure");
    positive(boiler, "boiler");
    positive(insulationK, "insulationK");
    positive(href, "href");
    positive(rpmRef, "rpmRef");
    positive(maxHours, "maxHours");
    positive(dt, "dt");
    positive(goalHours, "goalHours");
    positive(waterMu, "waterMu");
    positive(supplyD, "supplyD");
    positive(returnD, "returnD");
    positive(feedD, "feedD");
    positive(returnOuter, "returnOuter");
    positive(returnInner, "returnInner");
    positive(gasK, "gasK");
    positive(bedPathFactor, "bedPathFactor");
    positive(particle, "particle");
    positive(hStatic, "hStatic");
    positive(hLimit, "hLimit");
    positive(rpmMax, "rpmMax");
    positive(rpmStep, "rpmStep");
    nonnegative(headDepth, "headDepth");
    nonnegative(latent, "latent");
    nonnegative(loopL, "loopL");
    nonnegative(externalH, "externalH");
    nonnegative(extraUA, "extraUA");
    nonnegative(insulation, "insulation");
    nonnegative(rpm, "rpm");
    nonnegative(rpmGain, "rpmGain");
    nonnegative(supplyL, "supplyL");
    nonnegative(returnL, "returnL");
    nonnegative(feedL, "feedL");
    nonnegative(shaftReturnL, "shaftReturnL");
    nonnegative(supplyK, "supplyK");
    nonnegative(returnK, "returnK");
    nonnegative(feedK, "feedK");
    nonnegative(shaftReturnK, "shaftReturnK");
    nonnegative(jacketK, "jacketK");
    nonnegative(jointDropBar, "jointDropBar");
    nonnegative(equipmentDropBar, "equipmentDropBar");
    nonnegative(roughness, "roughness");
    nonnegative(exchangePerRev, "exchangePerRev");
    nonnegative(contactR, "contactR");
    auto fraction = [&](double value, const char *key, bool include_zero = false) {
        if ((!include_zero && value <= 0) || value < 0 || value > 1 || !std::isfinite(value))
            throw std::invalid_argument(std::string(key) + ": outside the permitted fraction range");
    };
    fraction(coverage, "coverage");
    fraction(contact, "contact");
    fraction(packing, "packing");
    fraction(efficiency, "efficiency");
    fraction(pumpEfficiency, "pumpEfficiency");
    fraction(freeboard, "freeboard", true);
    fraction(emissivity, "emissivity", true);
    fraction(contactTopology, "contactTopology", true);
    if (freeboard >= 1 || targetFill <= 0 || targetFill >= 1 || nearFraction <= 0 || nearFraction >= 1)
        throw std::invalid_argument("freeboard, targetFill or nearFraction is outside its range");
    if (heads < 0 || heads > 2 || headDepth > diameter / 2 || (heads && headDepth <= 0))
        throw std::invalid_argument("invalid spherical-head geometry");
    if (liquidus <= solidus || target <= initial)
        throw std::invalid_argument("invalid phase or heating temperature range");
    for (double t : {initial, target, ambient, tin, waterInitial, metalInitial, solidus, liquidus})
        if (!std::isfinite(t) || t <= -273.15)
            throw std::invalid_argument("temperature must be finite and above absolute zero");
    if (tin < .01 || tin >= 373.946)
        throw std::invalid_argument("inlet water temperature is outside the liquid-water correlation domain");
    if (angle < 0 || angle > 90 || rpmExponent < 0 || rpmExponent > 2)
        throw std::invalid_argument("invalid inclination or RPM exponent");
    if (rpmMode < 0 || rpmMode > 1 || sourceMode < 0 || sourceMode > 1 || chargeMode < 0 || chargeMode > 1)
        throw std::invalid_argument("invalid model mode");
    if (rpmMode == 1 && (href < hStatic || hLimit < href || rpmExponent <= 0))
        throw std::invalid_argument("RPM sensitivity coefficients are inconsistent");
    if (returnOuter <= returnInner)
        throw std::invalid_argument("return annulus outer diameter must exceed its inner diameter");
    if (axialZones < 2 || angularZones < 4 || radialZones < 2 ||
        (rotationDirection != -1 && rotationDirection != 1))
        throw std::invalid_argument("invalid mesh or rotation direction");
    const auto cells = static_cast<std::size_t>(axialZones) * static_cast<std::size_t>(angularZones);
    if (cells > 2000000 || radialZones > 100000)
        throw std::invalid_argument(
            "mesh exceeds the safe allocation budget; reduce resolution or use a distributed solver");
}
} // namespace rotary
