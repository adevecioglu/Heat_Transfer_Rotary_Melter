#pragma once
#include "Configuration.hpp"

namespace rotary {
double enthalpy(const Configuration &c, double temperature);
double temperature(const Configuration &c, double specific_enthalpy);
double liquid_fraction(const Configuration &c, double temperature);
double saturation_pressure_bar(double temperature_c);
Json water_properties(double temperature_c, double pressure_bar);

struct ExteriorFlux {
    double surface{}, convection{}, radiation{};
};
ExteriorFlux exterior_flux(const Configuration &c, double area, double metal_temperature);
} // namespace rotary
