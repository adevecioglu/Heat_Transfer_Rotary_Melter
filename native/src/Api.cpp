#include "rotary/Api.h"
#include "rotary/Simulation.hpp"
#include <cstring>
#include <exception>
#include <string>

extern "C" {
const char *rotary_execute_json(const char *request, rotary_progress_callback progress,
                                rotary_cancel_callback cancel, void *context) {
    std::string response;
    try {
        if (!request)
            throw std::invalid_argument("request is null");
        auto event = [&](const rotary::Json &data) {
            if (progress) {
                const auto text = data.dump();
                progress(text.c_str(), context);
            }
        };
        auto stopped = [&]() { return cancel && cancel(context) != 0; };
        response = rotary::Json{{"ok", true},
                                {"result", rotary::execute(rotary::Json::parse(request), event, stopped)}}
                       .dump();
    } catch (const std::exception &error) {
        response = rotary::Json{{"ok", false}, {"error", error.what()}}.dump();
    } catch (...) {
        response = R"({"ok":false,"error":"unhandled native exception"})";
    }
    auto *memory = new char[response.size() + 1];
    std::memcpy(memory, response.c_str(), response.size() + 1);
    return memory;
}
void rotary_free_json(const char *memory) {
    delete[] memory;
}
unsigned rotary_abi_version(void) {
    return 1;
}
}
