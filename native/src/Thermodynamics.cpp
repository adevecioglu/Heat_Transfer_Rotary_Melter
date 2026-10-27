#include "rotary/Thermodynamics.hpp"
#include <IF97.h>
#include <algorithm>
#include <boost/math/tools/toms748_solve.hpp>
#include <cmath>
#include <stdexcept>

namespace rotary {
double enthalpy(const Configuration &c, double t) {
    const double apparent = (c.cps + c.cpl) / 2 + c.latent / (c.liquidus - c.solidus);
    const double solid = c.cps * c.solidus;
    const double liquid = solid + apparent * (c.liquidus - c.solidus);
    if (t <= c.solidus)
        return c.cps * t;
    if (t < c.liquidus)
        return solid + apparent * (t - c.solidus);
    return liquid + c.cpl * (t - c.liquidus);
}

double temperature(const Configuration &c, double h) {
    const double apparent = (c.cps + c.cpl) / 2 + c.latent / (c.liquidus - c.solidus);
    const double solid = c.cps * c.solidus;
    const double liquid = solid + apparent * (c.liquidus - c.solidus);
    if (h <= solid)
        return h / c.cps;
    if (h < liquid)
        return c.solidus + (h - solid) / apparent;
    return c.liquidus + (h - liquid) / c.cpl;
}

double liquid_fraction(const Configuration &c, double t) {
    return std::clamp((t - c.solidus) / (c.liquidus - c.solidus), 0.0, 1.0);
}

double saturation_pressure_bar(double t) {
    const double kelvin = t + 273.15;
    if (kelvin < 273.16 || kelvin > IF97::get_Tcrit())
        throw std::invalid_argument("temperature outside the IAPWS saturation-pressure domain");
    return IF97::psat97(kelvin) / 1e5;
}

Json water_properties(double t, double pressure_bar) {
    const double kelvin = t + 273.15, pressure_pa = pressure_bar * 1e5;
    if (kelvin < 273.16 || kelvin >= IF97::get_Tcrit())
        throw std::invalid_argument("water reference temperature is outside the liquid range");
    if (pressure_pa <= IF97::psat97(kelvin))
        throw std::invalid_argument("water pressure must exceed saturation pressure for liquid properties");
    return {{"temperatureC", t},
            {"pressureBarAbs", pressure_bar},
            {"densityKgM3", IF97::rhomass_Tp(kelvin, pressure_pa)},
            {"specificHeatJKgK", IF97::cpmass_Tp(kelvin, pressure_pa)},
            {"dynamicViscosityPaS", IF97::visc_Tp(kelvin, pressure_pa)},
            {"saturationPressureBar", IF97::psat97(kelvin) / 1e5},
            {"source", "CoolProp/IF97 v2.2.1; IAPWS-IF97"}};
}

ExteriorFlux exterior_flux(const Configuration &c, double area, double metal) {
    constexpr double sigma = 5.670374419e-8;
    auto flux = [&](double surface) {
        const double tk = surface + 273.15, ak = c.ambient + 273.15;
        return ExteriorFlux{surface, c.externalH * area * (surface - c.ambient),
                            c.emissivity * sigma * area * (tk * tk * tk * tk - ak * ak * ak * ak)};
    };
    if (c.insulation <= 0 || metal == c.ambient)
        return flux(metal);
    const double conductance = c.insulationK * area / (c.insulation / 1000);
    auto balance = [&](double surface) {
        const auto q = flux(surface);
        return conductance * (metal - surface) - q.convection - q.radiation;
    };
    const double lo = std::min(metal, c.ambient), hi = std::max(metal, c.ambient);
    std::uintmax_t iterations = 64;
    const auto bracket = boost::math::tools::toms748_solve(
        balance, lo, hi, [](double a, double b) { return std::abs(a - b) < 1e-11; }, iterations);
    return flux((bracket.first + bracket.second) / 2);
}
} // namespace rotary
