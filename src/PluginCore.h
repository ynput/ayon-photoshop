#ifndef PLUGINCORE_H
#define PLUGINCORE_H

#ifdef _WIN32
#define PLUGIN_EXPORT __declspec(dllexport)
#else
#define PLUGIN_EXPORT __attribute__((visibility("default")))
#endif

class PluginCore {
public:
    PLUGIN_EXPORT PluginCore();
    PLUGIN_EXPORT ~PluginCore();
    PLUGIN_EXPORT int Initialize();
    PLUGIN_EXPORT int Shutdown();
    PLUGIN_EXPORT const char* GetVersion();
};

#endif // PLUGINCORE_H
