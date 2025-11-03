# Modular Framework Configuration

The ESP32 boilerplate framework now supports modular compilation, allowing you to enable only the components you need for your specific project. This significantly reduces code size and memory usage.

## Overview

The framework is divided into independent components that can be enabled or disabled using preprocessor defines. This allows you to:

- **Reduce code size** from 866KB to 200-300KB for simple projects
- **Minimize memory usage** by excluding unused libraries
- **Speed up compilation** by processing only needed components
- **Create specialized builds** for different project requirements

## Available Components

| Component | Define | Description | Dependencies | Size Impact |
|-----------|--------|-------------|--------------|-------------|
| Core | `ESP_PLATFORM_ENABLE_CORE` | Essential framework functionality | None | ~50KB |
| Debug | `ESP_PLATFORM_ENABLE_DEBUG` | Serial and file debugging | None | ~20KB |
| Filesystem | `ESP_PLATFORM_ENABLE_FILESYSTEM` | LittleFS operations | None | ~30KB |
| Display | `ESP_PLATFORM_ENABLE_DISPLAY` | OLED screen support | SPI, Wire | ~80KB |
| Buttons | `ESP_PLATFORM_ENABLE_BUTTONS` | Button input handling | None | ~40KB |
| LED | `ESP_PLATFORM_ENABLE_LED` | LED control | None | ~20KB |
| WiFi | `ESP_PLATFORM_ENABLE_WIFI` | WiFi connectivity | WiFi libraries | ~150KB |
| Web Server | `ESP_PLATFORM_ENABLE_WEBSERVER` | HTTP web server | WiFi, JSON | ~100KB |
| OTA | `ESP_PLATFORM_ENABLE_OTA` | Over-the-air updates | WiFi | ~50KB |
| Config | `ESP_PLATFORM_ENABLE_CONFIG` | Configuration management | Filesystem, JSON | ~60KB |
| Boot Manager | `ESP_PLATFORM_ENABLE_BOOTMANAGER` | Multi-boot functionality | Filesystem | ~40KB |
| NTP | `ESP_PLATFORM_ENABLE_NTP` | Network time sync | WiFi | ~30KB |

## Usage Examples

### Minimal Example (LED + Buttons Only)

```cpp
// Disable all components except essentials
#define ESP_PLATFORM_ENABLE_WIFI 0
#define ESP_PLATFORM_ENABLE_WEBSERVER 0
#define ESP_PLATFORM_ENABLE_OTA 0
#define ESP_PLATFORM_ENABLE_DISPLAY 0
#define ESP_PLATFORM_ENABLE_CONFIG 0
#define ESP_PLATFORM_ENABLE_BOOTMANAGER 0
#define ESP_PLATFORM_ENABLE_NTP 0
#define ESP_PLATFORM_ENABLE_FILESYSTEM 0

// Enable only what you need
#define ESP_PLATFORM_ENABLE_CORE 1
#define ESP_PLATFORM_ENABLE_DEBUG 1
#define ESP_PLATFORM_ENABLE_BUTTONS 1
#define ESP_PLATFORM_ENABLE_LED 1

#include "framework/ESPPlatform.h"
```

**Expected size**: ~200-300KB

### IoT Example (WiFi + Web + OTA)

```cpp
// Enable IoT features
#define ESP_PLATFORM_ENABLE_WIFI 1
#define ESP_PLATFORM_ENABLE_WEBSERVER 1
#define ESP_PLATFORM_ENABLE_OTA 1
#define ESP_PLATFORM_ENABLE_CONFIG 1
#define ESP_PLATFORM_ENABLE_FILESYSTEM 1

// Disable unused components
#define ESP_PLATFORM_ENABLE_DISPLAY 0
#define ESP_PLATFORM_ENABLE_BOOTMANAGER 0
#define ESP_PLATFORM_ENABLE_NTP 0

// Keep core components
#define ESP_PLATFORM_ENABLE_CORE 1
#define ESP_PLATFORM_ENABLE_DEBUG 1
#define ESP_PLATFORM_ENABLE_BUTTONS 1
#define ESP_PLATFORM_ENABLE_LED 1

#include "framework/ESPPlatform.h"
```

**Expected size**: ~500-600KB

### Full Featured Example (Everything Enabled)

```cpp
// Enable all components (default behavior)
#define ESP_PLATFORM_ENABLE_CORE 1
#define ESP_PLATFORM_ENABLE_DEBUG 1
#define ESP_PLATFORM_ENABLE_FILESYSTEM 1
#define ESP_PLATFORM_ENABLE_DISPLAY 1
#define ESP_PLATFORM_ENABLE_BUTTONS 1
#define ESP_PLATFORM_ENABLE_LED 1
#define ESP_PLATFORM_ENABLE_WIFI 1
#define ESP_PLATFORM_ENABLE_WEBSERVER 1
#define ESP_PLATFORM_ENABLE_OTA 1
#define ESP_PLATFORM_ENABLE_CONFIG 1
#define ESP_PLATFORM_ENABLE_BOOTMANAGER 1
#define ESP_PLATFORM_ENABLE_NTP 1

#include "framework/ESPPlatform.h"
```

**Expected size**: ~866KB (current full framework)

## Configuration Patterns

### Pattern 1: Minimal Hardware Control
```cpp
// For simple hardware control projects
#define ESP_PLATFORM_ENABLE_CORE 1
#define ESP_PLATFORM_ENABLE_DEBUG 1
#define ESP_PLATFORM_ENABLE_BUTTONS 1
#define ESP_PLATFORM_ENABLE_LED 1
// All others disabled
```

### Pattern 2: IoT Sensor Node
```cpp
// For sensor data collection and transmission
#define ESP_PLATFORM_ENABLE_CORE 1
#define ESP_PLATFORM_ENABLE_DEBUG 1
#define ESP_PLATFORM_ENABLE_WIFI 1
#define ESP_PLATFORM_ENABLE_CONFIG 1
#define ESP_PLATFORM_ENABLE_FILESYSTEM 1
// All others disabled
```

### Pattern 3: Web-Controlled Device
```cpp
// For web-controlled projects
#define ESP_PLATFORM_ENABLE_CORE 1
#define ESP_PLATFORM_ENABLE_DEBUG 1
#define ESP_PLATFORM_ENABLE_WIFI 1
#define ESP_PLATFORM_ENABLE_WEBSERVER 1
#define ESP_PLATFORM_ENABLE_CONFIG 1
#define ESP_PLATFORM_ENABLE_FILESYSTEM 1
#define ESP_PLATFORM_ENABLE_BUTTONS 1
#define ESP_PLATFORM_ENABLE_LED 1
// All others disabled
```

### Pattern 4: Display-Based Interface
```cpp
// For projects with OLED displays
#define ESP_PLATFORM_ENABLE_CORE 1
#define ESP_PLATFORM_ENABLE_DEBUG 1
#define ESP_PLATFORM_ENABLE_DISPLAY 1
#define ESP_PLATFORM_ENABLE_BUTTONS 1
#define ESP_PLATFORM_ENABLE_LED 1
// All others disabled
```

## Dependency Management

The framework automatically checks dependencies and will generate compilation errors if you try to enable a component without its required dependencies:

- **Web Server** requires **WiFi**
- **OTA** requires **WiFi**
- **NTP** requires **WiFi**
- **Config** requires **Filesystem**
- **Boot Manager** requires **Filesystem**

## Size Optimization Tips

### 1. Disable Debug in Production
```cpp
#define ESP_PLATFORM_ENABLE_DEBUG 0  // Saves ~20KB
```

### 2. Use Minimal Components for Simple Projects
```cpp
// For basic LED blinking
#define ESP_PLATFORM_ENABLE_CORE 1
#define ESP_PLATFORM_ENABLE_LED 1
// Everything else disabled
```

### 3. Choose Components Based on Requirements
- **Need WiFi?** Enable only WiFi, not necessarily web server
- **Need configuration?** Enable filesystem + config, not necessarily WiFi
- **Need display?** Enable display, not necessarily buttons

### 4. Consider Alternative Libraries
For very simple projects, consider using Arduino's built-in libraries instead of the framework:

```cpp
// Instead of framework LED management
#define ESP_PLATFORM_ENABLE_LED 0
// Use Arduino's digitalWrite() directly
```

## Compilation Verification

After configuring your components, verify the compilation:

```bash
arduino-cli compile --fqbn esp32:esp32:esp32s3 .
```

Check the output for:
- **Sketch uses X bytes** - This shows your actual code size
- **No dependency errors** - Ensures all required components are enabled
- **Expected size reduction** - Compare with full framework size

## Migration Guide

### From Full Framework to Modular

1. **Identify required components** for your project
2. **Add component defines** before including the framework
3. **Test compilation** to ensure dependencies are met
4. **Verify functionality** - disabled components won't be available
5. **Optimize further** by disabling unused components

### Example Migration

**Before (Full Framework):**
```cpp
#include "framework/ESPPlatform.h"
// Uses all components, ~866KB
```

**After (Modular):**
```cpp
// Disable unused components
#define ESP_PLATFORM_ENABLE_WIFI 0
#define ESP_PLATFORM_ENABLE_WEBSERVER 0
#define ESP_PLATFORM_ENABLE_OTA 0
#define ESP_PLATFORM_ENABLE_DISPLAY 0
#define ESP_PLATFORM_ENABLE_CONFIG 0
#define ESP_PLATFORM_ENABLE_BOOTMANAGER 0
#define ESP_PLATFORM_ENABLE_NTP 0
#define ESP_PLATFORM_ENABLE_FILESYSTEM 0

#include "framework/ESPPlatform.h"
// Uses only core + LED + buttons + debug, ~200-300KB
```

## Future Enhancements

### SD Card Support
When you add SD card support, you can create additional patterns:

```cpp
// Future SD card pattern
#define ESP_PLATFORM_ENABLE_SD 1
#define ESP_PLATFORM_ENABLE_FILESYSTEM 1
#define ESP_PLATFORM_ENABLE_BOOTMANAGER 1
// Multiple sketches can be stored on SD card
```

### Custom Components
You can extend the framework with custom components:

```cpp
#define ESP_PLATFORM_ENABLE_CUSTOM_SENSOR 1
#define ESP_PLATFORM_ENABLE_CUSTOM_ACTUATOR 1
```

This modular approach gives you maximum flexibility while maintaining the power of the full framework when needed. 