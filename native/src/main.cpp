#include "rotary/Api.h"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <nlohmann/json.hpp>
#include <sstream>
#include <string>
#include <vector>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
// clang-format off
#include <windows.h>
#include <shellapi.h>
// clang-format on
#endif

namespace {
using Json = nlohmann::json;
Json execute(const Json &request) {
    const auto encoded = request.dump();
    const char *raw = rotary_execute_json(encoded.c_str(), nullptr, nullptr, nullptr);
    if (!raw)
        throw std::runtime_error("native backend returned an empty response");
    const std::unique_ptr<const char, decltype(&rotary_free_json)> response(raw, &rotary_free_json);
    auto envelope = Json::parse(raw);
    if (!envelope.value("ok", false))
        throw std::runtime_error(envelope.value("error", std::string("native calculation failed")));
    return envelope.at("result");
}
std::filesystem::path utf8_path(const std::string &text) {
    return std::filesystem::path(std::u8string(reinterpret_cast<const char8_t *>(text.data()), text.size()));
}
} // namespace

int main(int argc, char **argv) {
    try {
        std::vector<std::string> args;
#ifdef _WIN32
        int count = 0;
        LPWSTR *wide = CommandLineToArgvW(GetCommandLineW(), &count);
        if (!wide)
            throw std::runtime_error("cannot decode command line");
        for (int i = 1; i < count; ++i) {
            const int size = WideCharToMultiByte(CP_UTF8, 0, wide[i], -1, nullptr, 0, nullptr, nullptr);
            std::string text(size, '\0');
            WideCharToMultiByte(CP_UTF8, 0, wide[i], -1, text.data(), size, nullptr, nullptr);
            text.pop_back();
            args.push_back(std::move(text));
        }
        LocalFree(wide);
#else
        for (int i = 1; i < argc; ++i)
            args.emplace_back(argv[i]);
#endif
        std::string input, output;
        Json options = Json::object();
        std::string action = "simulate";
        for (std::size_t i = 0; i < args.size(); ++i) {
            const auto &arg = args[i];
            auto next = [&]() {
                if (i + 1 >= args.size())
                    throw std::invalid_argument("missing value after " + arg);
                return args[++i];
            };
            if (arg == "--help") {
                std::cout << "Rotary Melter C++\n  --info\n  --input scenario.json --output result.json\n  "
                             "--integrator midpoint|rk4|dopri5 --threads N --no-history\n  Without --input: "
                             "read a JSON request from stdin.\n";
                return 0;
            }
            if (arg == "--info") {
                std::cout << execute({{"action", "info"}}).dump(2) << '\n';
                return 0;
            }
            if (arg == "--input")
                input = next();
            else if (arg == "--output")
                output = next();
            else if (arg == "--integrator")
                options["integrator"] = next();
            else if (arg == "--threads")
                options["threads"] = std::stoi(next());
            else if (arg == "--no-history")
                options["noHistory"] = true;
            else
                throw std::invalid_argument("unknown argument: " + arg);
        }
        Json request;
        if (input.empty()) {
            std::cin >> request;
        } else {
            std::ifstream file(utf8_path(input));
            if (!file)
                throw std::runtime_error("cannot read input scenario");
            Json data;
            file >> data;
            request = {{"action", action}, {"configuration", data}, {"options", options}};
        }
        const auto result = execute(request);
        const auto serialized = result.dump(2);
        if (output.empty())
            std::cout << serialized << '\n';
        else {
            const auto file_path = utf8_path(output);
            if (!file_path.parent_path().empty())
                std::filesystem::create_directories(file_path.parent_path());
            std::ofstream file(file_path);
            if (!file)
                throw std::runtime_error("cannot write output");
            file << serialized << '\n';
        }
        return 0;
    } catch (const std::exception &error) {
        std::cerr << Json{{"ok", false}, {"error", error.what()}}.dump() << '\n';
        return 1;
    }
}
