# Makefile to build universal binary for macOS

SRC_DIR = src
BIN_DIR = bin
PLUGIN_NAME = ps_plugin

all: universal

build_x86_64:
	@echo "Building for x86_64..."
	# Your build command for x86_64, e.g.:
	# clang -arch x86_64 -dynamiclib -o $(BIN_DIR)/$(PLUGIN_NAME)_x86_64.dylib $(SRC_DIR)/plugin.c

build_arm64:
	@echo "Building for arm64..."
	# clang -arch arm64 -dynamiclib -o $(BIN_DIR)/$(PLUGIN_NAME)_arm64.dylib $(SRC_DIR)/plugin.c

universal: build_x86_64 build_arm64
	@echo "Creating universal binary..."
	lipo -create $(BIN_DIR)/$(PLUGIN_NAME)_x86_64.dylib $(BIN_DIR)/$(PLUGIN_NAME)_arm64.dylib -output $(BIN_DIR)/$(PLUGIN_NAME).dylib
	@echo "Universal binary created at $(BIN_DIR)/$(PLUGIN_NAME).dylib"

clean:
	rm -f $(BIN_DIR)/*.dylib

.PHONY: all build_x86_64 build_arm64 universal clean
