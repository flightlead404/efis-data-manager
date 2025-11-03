# Getting Started with ESP Portable Platform

This guide will walk you through setting up and using your ESP Portable Development Platform from start to finish.

## Quick Start Overview

1. **Hardware Assembly** - Build the physical device
2. **Software Setup** - Install development tools
3. **Bootloader Installation** - Flash the bootloader
4. **First Test** - Verify everything works
5. **Create Your First App** - Build and upload a custom application

## Prerequisites

### Required Software
- **PlatformIO Core** - For building and uploading code
- **Arduino IDE** (optional) - Alternative development environment
- **Git** - For downloading the project

### Required Hardware
- ESP8266 or ESP32 development board
- SSD1327 or SSD1351 OLED display
- 2x momentary push buttons
- 1x status LED
- On/off power switch
- Battery pack and charging module
- Small breadboard
- Enclosure
- Supporting components (resistors, wires, etc.)

## Step 1: Hardware Assembly

### 1.1 Gather Components
First, ensure you have all the required components listed in the [Hardware Setup Guide](hardware_setup.md).

### 1.2 Follow Assembly Instructions
Refer to the detailed [Hardware Setup Guide](hardware_setup.md) for step-by-step assembly instructions.

### 1.3 Test Basic Functionality
Before proceeding, test each component individually:

```cpp
// Basic LED test
void setup() {
  pinMode(16, OUTPUT); // D0 on ESP8266, GPIO2 on ESP32
}

void loop() {
  digitalWrite(16, HIGH);
  delay(1000);
  digitalWrite(16, LOW);
  delay(1000);
}
```

## Step 2: Software Setup

### 2.1 Install PlatformIO

**Option A: PlatformIO Core (Recommended)**
```bash
# Install PlatformIO Core
pip install platformio

# Or using pipx (recommended)
pipx install platformio
```

**Option B: PlatformIO IDE**
- Download and install [PlatformIO IDE](https://platformio.org/install/ide?install=vscode)
- Install the PlatformIO extension in VS Code

### 2.2 Download the Project
```bash
# Clone the repository
git clone https://github.com/yourusername/esp-portable-platform.git
cd esp-portable-platform

# Or download and extract the ZIP file
```

### 2.3 Install Dependencies
The project will automatically install required libraries when you build for the first time.

## Step 3: Bootloader Installation

### 3.1 Build the Bootloader
```bash
# Navigate to the project directory
cd esp-portable-platform

# Build for your target board
# For ESP32:
pio run -e esp32dev -p bootloader

# For ESP8266:
pio run -e esp8266 -p bootloader
```

### 3.2 Flash the Bootloader
```bash
# Connect your ESP board via USB
# Flash for ESP32:
pio run -e esp32dev -p bootloader -t upload

# Flash for ESP8266:
pio run -e esp8266 -p bootloader -t upload
```

### 3.3 Verify Installation
1. Power on your device
2. You should see a splash screen on the display
3. The LED should light up
4. The device should create a WiFi access point

## Step 4: First Test

### 4.1 Connect to WiFi
1. Look for a WiFi network named `ESPPlatform_XXXXXX` (where XXXXXX is your device's chip ID)
2. Connect to this network with password `12345678`
3. Open a web browser and navigate to `http://192.168.4.1`

### 4.2 Test Web Interface
1. **File Manager Tab**: Should show no files initially
2. **Pinout Tab**: Should display the hardware pinout diagram
3. **Status Tab**: Should show system information
4. **Debug Tab**: Should show bootloader messages

### 4.3 Test Physical Controls
1. **Buttons**: Press both buttons to test responsiveness
2. **Display**: Should show file selection screen
3. **LED**: Should indicate current state

## Step 5: Upload Your First Application

### 5.1 Build an Example
```bash
# Build the blink example
cd examples/blink_example

# For ESP32:
pio run -e esp32dev

# For ESP8266:
pio run -e esp8266
```

### 5.2 Upload via Web Interface
1. Open the web interface at `http://192.168.4.1`
2. Go to the **File Manager** tab
3. Click **Select Files** and choose the compiled `.bin` file
4. The file should appear in the file list
5. Use the physical buttons to select and run the application

### 5.3 Verify Application
1. The LED should start blinking
2. The display should show application information
3. Debug messages should appear in the web interface

## Step 6: Create Your Own Application

### 6.1 Use the Framework
Create a new Arduino sketch that includes the framework:

```cpp
#include "ESPPlatform.h"

void setup() {
  // Initialize platform
  PlatformConfig config = {
    .deviceName = "My App",
    .apSSID = "ESPPlatform_",
    .apPassword = "12345678",
    .displayType = DISPLAY_SSD1327,
    .enableWebServer = true,
    .webServerPort = 80,
    .enableDebug = true
  };
  
  if (!Platform.begin(config)) {
    return;
  }
  
  // Your initialization code here
}

void loop() {
  Platform.update();
  
  // Your main loop code here
}
```

### 6.2 Build and Upload
```bash
# Create a new project directory
mkdir my_app
cd my_app

# Copy the framework files
cp -r ../framework/ .

# Create your sketch file
# Build and upload as before
```

## Troubleshooting

### Common Issues

**Device won't power on**
- Check battery voltage
- Verify power switch connections
- Test with USB power first

**Display not working**
- Check I2C/SPI connections
- Verify correct display type in configuration
- Test with known working display library

**WiFi not connecting**
- Check if device is in AP mode
- Verify SSID and password
- Try power cycling the device

**Web interface not accessible**
- Ensure you're connected to the device's WiFi
- Check if web server is enabled in configuration
- Try accessing via IP address directly

**Buttons not responding**
- Check pull-up resistor connections
- Verify GPIO pin assignments
- Test with simple digitalRead example

### Debugging Tips

1. **Use Serial Monitor**
   ```bash
   pio run -e esp32dev -t monitor
   ```

2. **Check Debug Messages**
   - Use the web interface debug tab
   - Monitor serial output

3. **Test Components Individually**
   - Create simple test sketches for each component
   - Verify each component works before integration

## Next Steps

### Explore Examples
- **blink_example**: Basic LED control
- **button_test**: Button input handling
- Create your own examples

### Extend Functionality
- Add sensors to the breadboard
- Create custom web interface pages
- Implement wireless communication protocols

### Customize Hardware
- Modify pin assignments for your needs
- Add additional components
- Create custom enclosures

## Advanced Features

### Custom Web Endpoints
```cpp
// Add custom web endpoints
Platform.getWebServer()->addEndpoint("/my-endpoint", "GET", []() {
  // Your custom handler
});
```

### Debug Message Integration
```cpp
// Add debug messages from your application
Platform.getWebServer()->addDebugMessage("Custom debug message");
```

### File System Operations
```cpp
// Save configuration
StaticJsonDocument<512> config;
config["setting"] = "value";
Platform.saveConfig("/config.json", config);

// Load configuration
Platform.loadConfig("/config.json", config);
```

## Support and Resources

### Documentation
- [Hardware Setup Guide](hardware_setup.md)
- [Framework API Reference](framework/ESPPlatform.h)
- [Example Applications](examples/)

### Community
- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share projects
- Wiki: Community-contributed documentation

### Tools
- [Build Script](tools/build.sh): Automated building and deployment
- [PlatformIO Configuration](platformio.ini): Build settings and dependencies

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---

**Happy Building!** 🚀

If you encounter any issues or have questions, please check the troubleshooting section or open an issue on GitHub. 