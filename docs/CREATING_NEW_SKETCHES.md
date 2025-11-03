# Creating New Sketches with ESP32 Boilerplate Framework

This guide explains how to create new Arduino sketches using the ESP32 Boilerplate Framework, which provides a comprehensive set of tools for ESP32 development including WiFi management, OTA updates, web interfaces, and hardware abstraction.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Structure](#project-structure)
3. [Creating a New Sketch](#creating-a-new-sketch)
4. [Framework Components](#framework-components)
5. [Basic Sketch Template](#basic-sketch-template)
6. [Configuration Management](#configuration-management)
7. [Hardware Integration](#hardware-integration)
8. [Web Interface](#web-interface)
9. [OTA Updates](#ota-updates)
10. [Testing and Deployment](#testing-and-deployment)
11. [Troubleshooting](#troubleshooting)

## Prerequisites

Before creating a new sketch, ensure you have:

- **Arduino IDE 2.0+** or **arduino-cli**
- **ESP32 Board Package** (version 2.0.11 recommended)
- **Required Libraries**:
  - ArduinoJson (7.4.1)
  - WiFiManager (2.0.17)
  - Adafruit GFX Library (1.12.1)
  - Adafruit BusIO (1.17.1)
  - Adafruit SSD1327 (1.0.4) - for grayscale OLED
  - Adafruit SSD1351 (1.3.2) - for color OLED

## Project Structure

The framework follows this structure:

```
your_project/
├── your_sketch.ino          # Main sketch file
├── framework/               # Framework files (copy from boilerplate)
│   ├── ESPPlatform.h       # Main framework header
│   ├── ESPPlatform.cpp     # Main framework implementation
│   ├── Display.cpp         # Display manager
│   ├── ButtonManager.cpp   # Button manager
│   ├── LEDManager.cpp      # LED manager
│   ├── WiFiManagerWrapper.cpp
│   ├── WebServerManager.cpp
│   ├── OTAManager.cpp
│   ├── ConfigManager.cpp
│   ├── WebInterface.cpp
│   └── BootManager.cpp
├── data/                   # LittleFS data files
│   ├── iot_config.json    # IoT configuration
│   └── app_config.json    # Application configuration
└── README.md              # Project documentation
```

## Creating a New Sketch

### Step 1: Create Project Directory

```bash
mkdir my_esp32_project
cd my_esp32_project
```

### Step 2: Copy Framework Files

Copy the framework directory from the boilerplate project:

```bash
cp -r /path/to/boilerplate/framework .
```

### Step 3: Create Main Sketch File

Create your main sketch file (e.g., `my_sketch.ino`):

```cpp
/*
 * My ESP32 Project
 * Description of what your project does
 * 
 * Hardware:
 * - LED: GPIO 2
 * - Button 0: GPIO 0
 * - Button 1: GPIO 27
 * - Display: SSD1327 (128x64) or SSD1351 (128x128)
 * 
 * Features:
 * - WiFi connectivity
 * - Web interface
 * - OTA updates
 * - Configuration management
 */

#include "framework/ESPPlatform.h"

// Global variables
bool systemRunning = false;
unsigned long lastUpdate = 0;

// Button callback function
void onButtonEvent(ButtonPressType pressType, const ButtonInfo& button) {
  if (pressType == BUTTON_PRESS_SHORT) {
    if (button.pin == 0) {  // Button 0
      // Handle button 0 press
      systemRunning = !systemRunning;
      
      // Update LED
      if (systemRunning) {
        Platform.getLED()->setState(LED_BLINK_SLOW);
      } else {
        Platform.getLED()->setState(LED_OFF);
      }
      
      // Update display
      Platform.getDisplay()->clear();
      Platform.getDisplay()->setCursor(0, 0);
      Platform.getDisplay()->print("System: ");
      Platform.getDisplay()->print(systemRunning ? "ON" : "OFF");
      Platform.getDisplay()->display();
      
    } else if (button.pin == 27) {  // Button 1
      // Handle button 1 press
      Platform.getDisplay()->clear();
      Platform.getDisplay()->setCursor(0, 0);
      Platform.getDisplay()->print("Button 1 Pressed!");
      Platform.getDisplay()->display();
      delay(1000);
    }
  }
}

void setup() {
  // Initialize platform with configuration files
  if (!Platform.begin()) {
    Serial.println("Failed to initialize platform");
    return;
  }
  
  // Set button callbacks
  Platform.getButtons()->setButton0Callback(onButtonEvent);
  Platform.getButtons()->setButton1Callback(onButtonEvent);
  
  // Initialize your application
  systemRunning = false;
  
  // Show startup message
  Platform.getDisplay()->clear();
  Platform.getDisplay()->setCursor(0, 0);
  Platform.getDisplay()->print("My ESP32 Project");
  Platform.getDisplay()->setCursor(0, 16);
  Platform.getDisplay()->print("B0: Toggle System");
  Platform.getDisplay()->setCursor(0, 32);
  Platform.getDisplay()->print("B1: Test Button");
  Platform.getDisplay()->display();
  
  delay(3000);
  
  Serial.println("My ESP32 Project initialized");
}

void loop() {
  // Update platform components
  Platform.update();
  
  // Your application logic
  if (systemRunning) {
    // Do something when system is running
    if (millis() - lastUpdate >= 1000) {
      lastUpdate = millis();
      
      // Update display with status
      Platform.getDisplay()->clear();
      Platform.getDisplay()->setCursor(0, 0);
      Platform.getDisplay()->print("Uptime: " + String(millis() / 1000) + "s");
      Platform.getDisplay()->setCursor(0, 16);
      Platform.getDisplay()->print("System: RUNNING");
      Platform.getDisplay()->setCursor(0, 32);
      Platform.getDisplay()->print("Free Heap: " + Platform.getFreeHeap() + "B");
      Platform.getDisplay()->display();
    }
  }
  
  // Small delay to prevent excessive CPU usage
  delay(10);
}
```

## Framework Components

### Platform Management

The main `ESPPlatform` class provides access to all framework components:

```cpp
// Access framework components
Display* display = Platform.getDisplay();
ButtonManager* buttons = Platform.getButtons();
LEDManager* led = Platform.getLED();
WiFiManagerWrapper* wifi = Platform.getWiFi();
WebServerManager* webServer = Platform.getWebServer();
OTAManager* ota = Platform.getOTA();
ConfigManager* config = Platform.getConfig();
BootManager* bootManager = Platform.getBootManager();
```

### Display Management

```cpp
// Basic display operations
Platform.getDisplay()->clear();
Platform.getDisplay()->setCursor(0, 0);
Platform.getDisplay()->print("Hello World");
Platform.getDisplay()->display();

// Text formatting
Platform.getDisplay()->setTextSize(2);
Platform.getDisplay()->setTextColor(WHITE);
Platform.getDisplay()->println("Large Text");

// Graphics
Platform.getDisplay()->drawRect(0, 0, 64, 32, WHITE);
Platform.getDisplay()->fillCircle(32, 16, 8, WHITE);
```

### Button Management

```cpp
// Set button callbacks
Platform.getButtons()->setButton0Callback(onButtonEvent);
Platform.getButtons()->setButton1Callback(onButtonEvent);

// Check button states
if (Platform.getButtons()->isButton0Pressed()) {
  // Button 0 was just pressed
}

if (Platform.getButtons()->isButton1LongPress()) {
  // Button 1 long press detected
}
```

### LED Management

```cpp
// Set LED states
Platform.getLED()->setState(LED_OFF);
Platform.getLED()->setState(LED_ON);
Platform.getLED()->setState(LED_BLINK_SLOW);
Platform.getLED()->setState(LED_BLINK_FAST);

// Custom blink rate
Platform.getLED()->setBlinkRate(500, 500); // 500ms on, 500ms off
```

### WiFi Management

```cpp
// Check WiFi status
if (Platform.getWiFi()->isConnected()) {
  String ip = Platform.getWiFi()->getLocalIP();
  int rssi = Platform.getWiFi()->getRSSI();
}

// Connect to WiFi
Platform.getWiFi()->connectToWiFi("MyNetwork", "password");
```

## Configuration Management

### IoT Configuration

The framework uses JSON-based configuration files stored in LittleFS:

```cpp
// Load IoT configuration
IoTConfig config = Platform.getIoTConfig();
String deviceName = config.deviceName;
String wifiSSID = config.wifi.ssid;

// Update configuration
config.deviceName = "MyDevice";
Platform.updateIoTConfig(config);
```

### Application Configuration

For application-specific settings, use the ConfigManager:

```cpp
// Note: Template methods are currently being fixed
// For now, use direct JSON access:

// Load app config
AppConfig appConfig = Platform.getAppConfig();
if (appConfig.isValid) {
  // Access JSON data
  int value = appConfig.config["myKey"] | 0;
}

// Save app config
appConfig.config["myKey"] = 42;
Platform.updateAppConfig(appConfig);
```

## Hardware Integration

### Pin Definitions

The framework uses these default pins:

- **LED**: GPIO 2
- **Button 0**: GPIO 0 (pulls low when pressed)
- **Button 1**: GPIO 27
- **Display**: SPI interface
  - CS: GPIO 5
  - DC: GPIO 4
  - RST: GPIO 16
  - MOSI: GPIO 23
  - SCK: GPIO 18

### Custom Pin Configuration

To use different pins, modify the configuration:

```cpp
// In setup(), before Platform.begin():
PlatformConfig config;
config.deviceName = "MyDevice";
// Add custom pin configuration here
Platform.begin(config);
```

## Web Interface

The framework provides a built-in web interface accessible at `http://[device-ip]`:

- **Status Page**: System information and status
- **File Manager**: Upload/download files
- **Configuration**: WiFi and system settings
- **OTA Updates**: Firmware update interface

### Custom Web Endpoints

Add custom web endpoints:

```cpp
// In setup():
Platform.getWebServer()->addEndpoint("/api/status", []() {
  // Handle GET /api/status
  String status = "{\"running\":" + String(systemRunning) + "}";
  Platform.getWebServer()->server->send(200, "application/json", status);
});
```

## OTA Updates

The framework supports Over-The-Air updates:

1. **Via Web Interface**: Upload `.bin` files through the web interface
2. **Via Arduino IDE**: Use "Upload via Network" feature
3. **Via arduino-cli**: Use `arduino-cli upload --port network`

### OTA Configuration

```cpp
// Check OTA status
if (Platform.getOTA()->getState() == OTA_STATE_UPDATING) {
  int progress = Platform.getOTA()->getProgress();
  // Show progress on display
}
```

## Testing and Deployment

### Local Testing

1. **Compile**: Use Arduino IDE or arduino-cli
2. **Upload**: Connect via USB and upload sketch
3. **Test**: Verify all components work correctly

### Network Deployment

1. **Configure WiFi**: Use the web interface or WiFiManager portal
2. **Upload Files**: Use the web interface to upload data files
3. **OTA Updates**: Use network upload for future updates

### Compilation Commands

```bash
# Using arduino-cli
arduino-cli compile --fqbn esp32:esp32:esp32s3 .

# Upload sketch
arduino-cli upload --fqbn esp32:esp32:esp32s3 --port /dev/ttyUSB0 .

# Upload LittleFS
arduino-cli upload --fqbn esp32:esp32:esp32s3 --port /dev/ttyUSB0 --input-dir data .
```

## Troubleshooting

### Common Issues

1. **Compilation Errors**:
   - Ensure all required libraries are installed
   - Check library versions match requirements
   - Verify framework files are copied correctly

2. **Runtime Errors**:
   - Check serial monitor for error messages
   - Verify hardware connections
   - Check configuration files

3. **WiFi Issues**:
   - Use WiFiManager portal for configuration
   - Check network credentials
   - Verify signal strength

4. **Display Issues**:
   - Check SPI connections
   - Verify display type configuration
   - Test with basic display functions

### Debug Information

The framework provides debug output via Serial:

```cpp
// Enable debug output
Serial.begin(115200);
// Framework will output debug information automatically
```

### Getting Help

1. Check the example sketches in the boilerplate project
2. Review the framework header files for available methods
3. Use the web interface for system diagnostics
4. Check the serial monitor for detailed error messages

## Next Steps

1. **Customize**: Modify the basic template for your specific needs
2. **Add Features**: Integrate sensors, actuators, or other hardware
3. **Optimize**: Fine-tune performance and memory usage
4. **Deploy**: Use OTA updates for production deployment

For more advanced usage, refer to the individual component documentation and example sketches provided with the framework. 