cmake_minimum_required(VERSION 3.14)
project(PhotoshopPluginCore VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Allow overriding architectures via CMAKE_OSX_ARCHITECTURES
if(APPLE)
    set(CMAKE_OSX_DEPLOYMENT_TARGET "10.15" CACHE STRING "Minimum macOS version")
endif()

add_library(PluginCore SHARED
    src/PluginCore.cpp
    src/PluginCore.h
)

# Export symbols for Adobe plugin SDK
target_compile_definitions(PluginCore PRIVATE PLUGIN_EXPORTS)
set_target_properties(PluginCore PROPERTIES
    POSITION_INDEPENDENT_CODE ON
    INSTALL_NAME_DIR "@executable_path/../Frameworks"
)
