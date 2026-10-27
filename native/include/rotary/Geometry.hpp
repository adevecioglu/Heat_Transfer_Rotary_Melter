#pragma once
#include "Configuration.hpp"
#include <vector>

namespace rotary {
inline constexpr double pi = 3.141592653589793238462643383279502884;

struct Slice {
    double z{}, radius{}, dz{}, volume{}, area{}, volume_fraction{}, wet_fraction{}, u{};
    Json to_json() const;
};

struct FillProfile {
    double plane{}, fraction{}, wet_fraction{}, quadrature_volume{};
    std::vector<Slice> slices;
    Json to_json() const;
};

struct Geometry {
    double volume{}, head_volume{}, area{}, heated{}, external{}, water_volume{};
    double inner_mass{}, outer_mass{}, liquid_volume{}, bulk_volume{}, solid_volume{};
    double max_mass{}, charge_mass{}, requested_mass{}, bulk_fill{}, liquid_fill{}, wet_initial{};
    bool feasible{}, tilt_applied{};
    FillProfile fill;
    Json to_json() const;
};

struct BedProperties {
    double conductivity{}, series{}, parallel{}, conductance{}, mixing{}, total{}, solid_contact_k{},
        particle_biot{};
    Json to_json() const;
};

FillProfile fill_profile(const Configuration &c, double fraction, int slices = 140);
Geometry geometry(const Configuration &c);
double rpm_heat_transfer(const Configuration &c);
BedProperties bed_properties(const Configuration &c, double liquid_fraction, const Geometry &geometry);
Json hydraulics(const Configuration &c);

struct Mesh {
    int axial{}, angular{}, cells{};
    double z0{}, z1{}, dz{};
    std::vector<double> weights, centers;
    std::vector<std::vector<double>> wet;
};

struct ThermalSpec {
    Configuration c;
    Geometry geometry;
    Mesh mesh;
    int radial{};
    double dt{}, film_coefficient{}, flow_capacity{}, rotation_rate{}, exchange_mass_flow{};
    std::vector<double> inner_capacity, outer_capacity, water_capacity, inner_area, outer_area;
    std::vector<double> water_inner_g, water_outer_g, product_g, inner_angular_g, outer_angular_g;
    std::vector<double> inner_axial_g, outer_axial_g, radial_weights, mass, population, surface_base;
    std::vector<std::vector<double>> radial_base;
};
ThermalSpec thermal_spec(const Configuration &c);
} // namespace rotary
