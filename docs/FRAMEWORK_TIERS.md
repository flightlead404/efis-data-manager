# ESP32 Framework Tiered System

The ESP32 boilerplate framework is designed with a modular, tiered approach that allows you to enable only the components you need for your specific application. This reduces code size, memory usage, and complexity while maintaining flexibility.

## Framework Tiers Overview

The framework is organized into four main tiers, each building upon the previous one:

### 1. Bare Bones Tier
**Example**: `examples/bare_bones_example/`

**Components Enabled**:
- Core framework only
- Basic debugging (Serial output)

**Components Disabled**:
- All hardware components (LED, Buttons, Display)
- All network components (WiFi, Web, OTA, NTP)
- All system components (Config, FileSystem)

**Expected Size**: ~100-150KB
**Use Case**: When you need just the basic framework structure without any hardware dependencies or network functionality.

**Configuration**:
```cpp
#define ESP_PLATFORM_ENABLE_CORE 1
#define ESP_PLATFORM_ENABLE_DEBUG 1
// All other components disabled
```

### 2. Basic Tier
**Example**: `examples/basic_example/`

**Components Enabled**:
- Core framework
- LED management
- Button management
- Basic debugging

**Components Disabled**:
- WiFi
- Web server
- OTA updates
- Display
- Configuration management
- File system

**Expected Size**: ~200-300KB
**Use Case**: Basic hardware interaction without network functionality. Perfect for simple sensor projects, basic control systems, or learning the framework.

**Configuration**:
```cpp
#define ESP_PLATFORM_ENABLE_CORE 1
#define ESP_PLATFORM_ENABLE_DEBUG 1
#define ESP_PLATFORM_ENABLE_BUTTONS 1
#define ESP_PLATFORM_ENABLE_LED 1
// All other components disabled
```

### 3. IoT Tier
**Example**: `examples/iot_example/`

**Components Enabled**:
- Core framework
- WiFi connectivity
- Web server with steampunk interface
- OTA updates
- Configuration management
- NTP time synchronization
- File system operations
- LED and button management
- Debug output

**Components Disabled**:
- Display (OLED screen)

**Expected Size**: ~600-700KB
**Use Case**: IoT applications requiring network connectivity, remote configuration, and over-the-air updates. Ideal for smart home devices, data loggers, and connected sensors.

**Configuration**:
```cpp
#define ESP_PLATFORM_ENABLE_CORE 1
#define ESP_PLATFORM_ENABLE_DEBUG 1
#define ESP_PLATFORM_ENABLE_FILESYSTEM 1
#define ESP_PLATFORM_ENABLE_BUTTONS 1
#define ESP_PLATFORM_ENABLE_LED 1
#define ESP_PLATFORM_ENABLE_WIFI 1
#define ESP_PLATFORM_ENABLE_WEBSERVER 1
#define ESP_PLATFORM_ENABLE_OTA 1
#define ESP_PLATFORM_ENABLE_CONFIG 1
#define ESP_PLATFORM_ENABLE_NTP 1
// Display disabled
```

### 4. Full Tier
**Example**: `examples/full_example/`

**Components Enabled**:
- ALL framework components enabled
- Core framework
- WiFi connectivity
- Web server with steampunk interface
- OTA updates
- Configuration management
- NTP time synchronization
- File system operations
- OLED display (SSD1327/SSD1351)
- LED and button management
- Debug output

**Note**: Boot manager is an application that runs on top of the framework, not a framework component itself.

**Expected Size**: ~700-800KB
**Use Case**: Full-featured applications requiring all framework capabilities including display output and network functionality. Perfect for complex IoT devices, data visualization systems, and development platforms.

**Configuration**:
```cpp
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
#define ESP_PLATFORM_ENABLE_NTP 1
// Boot manager is an application-level component
```

## Component Dependencies

The framework includes dependency checks to ensure compatibility:

```cpp
// Web server requires WiFi
#if ESP_PLATFORM_ENABLE_WEBSERVER && !ESP_PLATFORM_ENABLE_WIFI
#error "Web server requires WiFi to be enabled"
#endif

// OTA updates require WiFi
#if ESP_PLATFORM_ENABLE_OTA && !ESP_PLATFORM_ENABLE_WIFI
#error "OTA updates require WiFi to be enabled"
#endif

// NTP requires WiFi
#if ESP_PLATFORM_ENABLE_NTP && !ESP_PLATFORM_ENABLE_WIFI
#error "NTP requires WiFi to be enabled"
#endif

// Configuration management requires filesystem
#if ESP_PLATFORM_ENABLE_CONFIG && !ESP_PLATFORM_ENABLE_FILESYSTEM
#error "Configuration management requires filesystem to be enabled"
#endif
```

## Available Components

### Core Components
- **Core Framework** (`ESP_PLATFORM_ENABLE_CORE`): Essential framework functionality, always enabled
- **Debug System** (`ESP_PLATFORM_ENABLE_DEBUG`): Serial and file-based debugging

### Hardware Components
- **Display** (`ESP_PLATFORM_ENABLE_DISPLAY`): OLED display support (SSD1327/SSD1351)
- **Buttons** (`ESP_PLATFORM_ENABLE_BUTTONS`): Button management with debouncing
- **LED** (`ESP_PLATFORM_ENABLE_LED`): LED state management

### Network Components
- **WiFi** (`ESP_PLATFORM_ENABLE_WIFI`): WiFi connectivity (AP and STA modes)
- **Web Server** (`ESP_PLATFORM_ENABLE_WEBSERVER`): Web interface with steampunk theme
- **OTA** (`ESP_PLATFORM_ENABLE_OTA`): Over-the-air firmware updates
- **NTP** (`ESP_PLATFORM_ENABLE_NTP`): Network time synchronization

### System Components
- **File System** (`ESP_PLATFORM_ENABLE_FILESYSTEM`): LittleFS operations
- **Configuration** (`ESP_PLATFORM_ENABLE_CONFIG`): Configuration management

### Application-Level Components
- **Boot Manager**: Multi-boot functionality (runs on top of the framework, not a framework component)

## Choosing the Right Tier

### Start with Bare Bones if:
- You're learning the framework
- You need minimal code size
- You don't need hardware interaction
- You're building a simple data processor

### Use Basic Tier if:
- You need hardware interaction (LEDs, buttons)
- You want to learn hardware abstraction
- You're building a simple sensor project
- You don't need network connectivity

### Choose IoT Tier if:
- You need network connectivity
- You want remote configuration
- You need OTA updates
- You're building a connected device
- You don't need a display

### Go with Full Tier if:
- You need all framework capabilities
- You want display output
- You're building a complex IoT device
- You want maximum framework functionality

## Migration Between Tiers

To migrate from one tier to another:

1. **Copy the example** from your current tier to a new project
2. **Update the component defines** to enable/disable components as needed
3. **Add/remove component usage** in your code
4. **Update configuration** to match the new tier requirements
5. **Test thoroughly** to ensure all dependencies are satisfied

## Custom Tiers

You can create custom tiers by selectively enabling components:

```cpp
// Example: Display + WiFi + Web (no OTA, no NTP)
#define ESP_PLATFORM_ENABLE_CORE 1
#define ESP_PLATFORM_ENABLE_DEBUG 1
#define ESP_PLATFORM_ENABLE_FILESYSTEM 1
#define ESP_PLATFORM_ENABLE_DISPLAY 1
#define ESP_PLATFORM_ENABLE_BUTTONS 1
#define ESP_PLATFORM_ENABLE_LED 1
#define ESP_PLATFORM_ENABLE_WIFI 1
#define ESP_PLATFORM_ENABLE_WEBSERVER 1
#define ESP_PLATFORM_ENABLE_OTA 0
#define ESP_PLATFORM_ENABLE_CONFIG 0
#define ESP_PLATFORM_ENABLE_NTP 0
```

## Performance Considerations

- **Memory Usage**: Each tier adds approximately 100-200KB of code size
- **RAM Usage**: Network components require additional RAM for buffers
- **Startup Time**: More components = longer initialization time
- **Power Consumption**: WiFi and display components increase power usage

## Best Practices

1. **Start Small**: Begin with the lowest tier that meets your needs
2. **Test Incrementally**: Add components one at a time and test thoroughly
3. **Monitor Resources**: Watch memory usage as you add components
4. **Consider Dependencies**: Some components require others to function
5. **Document Your Choices**: Keep track of which components you're using and why

## Troubleshooting

### Common Issues:
- **Compilation Errors**: Check component dependencies
- **Memory Issues**: Consider moving to a lower tier
- **WiFi Problems**: Ensure WiFi component is enabled
- **Display Issues**: Verify display component and pin configuration

### Debug Tips:
- Use the debug macros to track component initialization
- Monitor heap usage with `Platform.getFreeHeap()`
- Check component status in the setup function
- Use the web interface (if enabled) to monitor system status 