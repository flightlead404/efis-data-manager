# Arduino IDE Setup Guide for ESP Portable Platform

This guide will help you set up the Arduino IDE 2.3.6 for development with the ESP Portable Platform.

## Prerequisites

- Arduino IDE 2.3.6 or later
- ESP32 or ESP8266 board support
- Required libraries (see below)

## Step 1: Install Arduino IDE

1. Download Arduino IDE 2.3.6 from [arduino.cc](https://www.arduino.cc/en/software)
2. Install the IDE following the platform-specific instructions
3. Launch Arduino IDE

## Step 2: Add Board Support

### For ESP32 (DOIT ESP32 DevKit V1)

1. Open Arduino IDE
2. Go to **File → Preferences**
3. In **Additional Board Manager URLs**, add:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Click **OK**
5. Go to **Tools → Board → Boards Manager**
6. Search for "ESP32"
7. Install "ESP32 by Espressif Systems"
8. Select your board: **Tools → Board → ESP32 Arduino → DOIT ESP32 DevKit V1**

### For ESP8266

1. Open Arduino IDE
2. Go to **File → Preferences**
3. In **Additional Board Manager URLs**, add:
   ```
   https://arduino.esp8266.com/stable/package_esp8266com_index.json
   ```
4. Click **OK**
5. Go to **Tools → Board → Boards Manager**
6. Search for "ESP8266"
7. Install "ESP8266 by ESP8266 Community"
8. Select your board: **Tools → Board → ESP8266 Boards → NodeMCU 1.0 (ESP-12E Module)**

## Step 3: Configure Board Settings

### ESP32 Configuration

1. **Board**: DOIT ESP32 DevKit V1
2. **Upload Speed**: 921600
3. **CPU Frequency**: 240MHz (WiFi/BT)
4. **Flash Frequency**: 80MHz
5. **Flash Mode**: QIO
6. **Flash Size**: 4MB (32Mb)
7. **Partition Scheme**: Custom Partition Scheme
8. **Custom Partition CSV**: Point to `hardware/partitions.csv` in the project
9. **PSRAM**: Disabled
10. **Core Debug Level**: None
11. **Events Run On**: Core 1
12. **Arduino Runs On**: Core 1

### ESP8266 Configuration

1. **Board**: NodeMCU 1.0 (ESP-12E Module)
2. **Upload Speed**: 921600
3. **CPU Frequency**: 80 MHz
4. **Flash Frequency**: 40 MHz
5. **Flash Mode**: QIO
6. **Flash Size**: 4MB (FS:2MB OTA:~1019KB)
7. **Debug port**: Disabled
8. **Debug Level**: None
9. **Reset Method**: nodemcu
10. **Crystal Frequency**: 26 MHz
11. **Flash Voltage**: 3.3V
12. **Port**: Select your device port

## Step 4: Install Required Libraries

Go to **Tools → Manage Libraries** and install:

### Required Libraries
- **ArduinoJson** by Benoit Blanchon (version 6.x)
- **WiFiManager** by tzapu (version 2.x)
- **Adafruit GFX Library** by Adafruit
- **Adafruit SSD1351** by Adafruit (for SSD1351 displays)
- **Adafruit SSD1327** by Adafruit (for SSD1327 displays)

### Optional Libraries
- **ArduinoOTA** (included with ESP32/ESP8266)
- **SPIFFS** (included with ESP32/ESP8266)
- **LittleFS** (included with ESP32/ESP8266)

## Step 5: Configure Partition Table

### For ESP32

1. **Set Partition Scheme**: Go to **Tools → Partition Scheme → Custom Partition Scheme**
2. **Set Custom Partition CSV**: Go to **Tools → Custom Partition CSV**
3. Browse to the `hardware/partitions.csv` file in your project
4. The partition table provides:
   - **factory**: 1MB bootloader partition
   - **ota_0**: 1MB OTA slot 0
   - **ota_1**: 1MB OTA slot 1
   - **storage**: 512KB file system
   - **config**: 64KB configuration storage
   - **debug**: 384KB debug logs

### For ESP8266

1. **Set Flash Size**: Go to **Tools → Flash Size → 4MB (FS:2MB OTA:~1019KB)**
2. The ESP8266 uses a built-in partition scheme that provides:
   - **sketch**: ~1019KB application space
   - **spiffs**: ~2MB file system space
   - **ota**: ~1019KB OTA update space

## Step 6: Install ESP Platform Library

1. Copy the `framework` folder to your Arduino libraries directory:
   - **macOS**: `~/Documents/Arduino/libraries/`
   - **Windows**: `Documents\Arduino\libraries\`
   - **Linux**: `~/Arduino/libraries/`

2. Rename the folder to `ESPPlatform`

3. Restart Arduino IDE

## Step 7: Test Setup

1. Open one of the example sketches:
   - `examples/blink_example/blink_example.ino`
   - `examples/button_test/button_test.ino`
   - `examples/partition_test/partition_test.ino`

2. Select the correct board and port

3. Click **Verify** to compile the sketch

4. If compilation succeeds, click **Upload** to flash the device

## Step 8: Verify Partition Table

After uploading, you can verify the partition table is working:

1. Open the Serial Monitor (Tools → Serial Monitor)
2. Set baud rate to 115200
3. Reset the device
4. Look for partition information in the debug output

## Troubleshooting

### Common Issues

1. **"Partition table not found"**
   - Verify the CSV file path is correct
   - Check that the file exists and is readable
   - Ensure the file format is correct (no extra spaces, proper commas)

2. **"Upload failed"**
   - Check the upload speed (try 115200 if 921600 fails)
   - Verify the correct port is selected
   - Put the device in download mode (hold BOOT button while uploading)

3. **"Compilation failed"**
   - Check that all required libraries are installed
   - Verify the ESPPlatform library is in the correct location
   - Check for library version conflicts

4. **"Board not found"**
   - Ensure board support is properly installed
   - Check the board manager URLs are correct
   - Restart Arduino IDE after installing board support

### Debug Output

Enable debug output by adding these lines to your sketch:

```cpp
#define DEBUG_SERIAL_ENABLED
#define DEBUG_FILE_ENABLED
#include "ESPPlatform.h"
```

This will provide detailed debug information about:
- Partition table loading
- File system initialization
- WiFi connection
- OTA updates

## Next Steps

1. **Read the Documentation**: Check the `docs/` folder for detailed guides
2. **Try Examples**: Start with the basic examples and work your way up
3. **Customize Hardware**: Modify pin definitions in `ESPPlatform.h` for your specific hardware
4. **Create Your Own Apps**: Use the framework to build your own applications

## Support

If you encounter issues:

1. Check the debug output for error messages
2. Verify your hardware connections
3. Ensure all libraries are up to date
4. Check the partition table configuration
5. Review the documentation in the `docs/` folder 