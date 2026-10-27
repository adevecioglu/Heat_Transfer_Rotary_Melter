#pragma once
#include <nlohmann/json.hpp>
#include <string>

namespace rotary {
using Json = nlohmann::json;

// SI conversions occur explicitly in geometry/thermal code; field names match V11 JSON.
struct Configuration {
    double diameter = 600;
    double length = 800;
    double headDepth = 150;
    int heads = 1;
    double wall = 5;
    double shell = 3;
    double gap = 15;
    double coverage = 1;
    double contact = 1;
    double angle = 45;
    double packing = 0.64;
    double freeboard = 0.2;
    double mass = 180;
    double rhos = 893;
    double rhol = 782;
    double cps = 2100;
    double cpl = 2490;
    double latent = 189000;
    double ks = 0.21;
    double kl = 0.17;
    double solidus = 58;
    double liquidus = 62;
    double initial = 25;
    double target = 75;
    double particle = 15;
    double steelK = 16.2;
    double steelRho = 8000;
    double steelCp = 500;
    double tin = 110;
    double flow = 10;
    double waterInitial = 25;
    double metalInitial = 25;
    double waterRho = 950;
    double waterCp = 4220;
    double waterH = 1500;
    double loopL = 20;
    double pressure = 4;
    double boiler = 30;
    double efficiency = 0.95;
    int sourceMode = 1;
    double ambient = 25;
    double externalH = 8;
    double emissivity = 0.2;
    double insulation = 0;
    double insulationK = 0.045;
    double extraUA = 0;
    double rpm = 10;
    double href = 100;
    double rpmRef = 10;
    double rpmGain = 0;
    double rpmExponent = 0.5;
    int rpmMode = 1;
    double hStatic = 40;
    double hLimit = 300;
    double rpmMax = 30;
    double rpmStep = 5;
    double maxHours = 24;
    double dt = 1;
    double goalHours = 2;
    int chargeMode = 1;
    double targetFill = 0.5;
    int tiltModel = 1;
    int bedModel = 1;
    double nearFraction = 0.35;
    double exchangePerRev = 0.02;
    double contactTopology = 0.25;
    double contactR = 0.002;
    double gasK = 0.028;
    double bedPathFactor = 0.25;
    double waterMu = 0.00026;
    double roughness = 0.0015;
    double supplyD = 32;
    double supplyL = 3;
    double supplyK = 3;
    double returnD = 32;
    double returnL = 3;
    double returnK = 3;
    double feedD = 20;
    double feedL = 1.2;
    double feedK = 2;
    double returnOuter = 40;
    double returnInner = 25;
    double shaftReturnL = 1.2;
    double shaftReturnK = 2;
    double jacketK = 2;
    double jointDropBar = 0;
    double equipmentDropBar = 0;
    double pumpEfficiency = 0.6;
    int thermalModel = 1;
    int axialZones = 16;
    int angularZones = 16;
    int rotationDirection = -1;
    int radialZones = 24;

    static Configuration from_json(const Json &envelope);
    Json to_json() const;
    void validate() const;
};
} // namespace rotary
