#include "PluginCore.h"
#include <string>

static const char* PLUGIN_VERSION = "1.0.0 (Universal)";

PluginCore::PluginCore() {}
PluginCore::~PluginCore() {}

int PluginCore::Initialize() {
    // Perform initialization specific to macOS architecture
    return 0;
}

int PluginCore::Shutdown() {
    return 0;
}

const char* PluginCore::GetVersion() {
    return PLUGIN_VERSION;
}
