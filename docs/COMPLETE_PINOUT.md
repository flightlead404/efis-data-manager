# Complete Pinout for DOIT ESP32 DevKit V1

## Hardware Components Overview

The DOIT ESP32 DevKit V1 is configured with the following components:

- **Button 0**: GPIO 0 (BOOT button on board)
- **Button 1**: GPIO 27 (external button)
- **External LED**: GPIO 2 (built-in LED on board)
- **SSD1351 Display**: 128x128 color OLED (SPI interface)
- **SD Card Reader**: SPI interface (shared with display)

## Pin Assignment Summary

### Input Components
| Component | Pin Name | GPIO | Function | Notes |
|-----------|----------|------|----------|-------|
| Button 0 | BUTTON0_PIN | GPIO 0 | Input (Pull-up) | BOOT button on board |
| Button 1 | BUTTON1_PIN | GPIO 27 | Input (Pull-up) | External button |

### Output Components
| Component | Pin Name | GPIO | Function | Notes |
|-----------|----------|------|----------|-------|
| External LED | LED_PIN | GPIO 2 | Output | Built-in LED on board |

### Display Interface (SSD1351)
| Component | Pin Name | GPIO | Function | Notes |
|-----------|----------|------|----------|-------|
| SSD1351 | OLED_CS | GPIO 16 | Chip Select | Display CS |
| SSD1351 | OLED_DC | GPIO 4 | Data/Command | Display DC |
| SSD1351 | OLED_RST | GPIO 5 | Reset | Display Reset |

### SPI Interface (Shared between Display and SD Card)
| Component | Pin Name | GPIO | Function | Notes |
|-----------|----------|------|----------|-------|
| SPI Bus | SPI_MOSI | GPIO 23 | Master Out Slave In | Shared between display and SD card |
| SPI Bus | SPI_MISO | GPIO 19 | Master In Slave Out | Shared between display and SD card |
| SPI Bus | SPI_SCK | GPIO 18 | Serial Clock | Shared between display and SD card |

### Device-Specific Chip Select Pins
| Component | Pin Name | GPIO | Function | Notes |
|-----------|----------|------|----------|-------|
| Display | OLED_CS | GPIO 16 | Chip Select | Display CS |
| SD Card | SD_CS | GPIO 17 | Chip Select | SD Card CS |

## Detailed Component Specifications

### Button Configuration

#### Button 0 (GPIO 0)
- **Location**: Built-in BOOT button on ESP32 board
- **Function**: Firmware selection and navigation
- **Configuration**: Internal pull-up resistor enabled
- **Behavior**: Pulls LOW when pressed
- **Usage**: Cycle through firmware options, show firmware info

#### Button 1 (GPIO 27)
- **Location**: External button connection
- **Function**: Additional control functions
- **Configuration**: Internal pull-up resistor enabled
- **Behavior**: Pulls LOW when pressed
- **Usage**: Boot selected firmware, show help screen

### LED Configuration

#### External LED (GPIO 2)
- **Location**: Built-in LED on ESP32 board
- **Function**: Status indication and debugging
- **Configuration**: Active HIGH
- **Behavior**: Write HIGH to turn on, LOW to turn off
- **Usage**: System status, error indication, debug output

### Display Configuration (SSD1351)

#### Display Interface Details
- **Display Type**: SSD1351 128x128 color OLED
- **Interface**: SPI (4-wire)
- **Resolution**: 128x128 pixels
- **Color Depth**: 16-bit RGB565
- **Power**: 3.3V operation

#### Display Pin Functions
- **CS (GPIO 16)**: Chip Select - enables communication with display
- **DC (GPIO 4)**: Data/Command - determines if data is command or pixel data
- **RST (GPIO 5)**: Reset - resets the display controller
- **MOSI (GPIO 23)**: Master Out Slave In - data from ESP32 to display
- **MISO (GPIO 19)**: Master In Slave Out - data from display to ESP32 (not used for display)
- **SCK (GPIO 18)**: Serial Clock - SPI clock signal

### SD Card Configuration

#### SD Card Interface Details
- **Card Type**: SD/SDHC cards supported
- **Format**: FAT32 required
- **Interface**: SPI (4-wire)
- **Speed**: Up to 4MHz SPI clock
- **Power**: 3.3V operation

#### SD Card Pin Functions
- **CS (GPIO 17)**: Chip Select - enables communication with SD card
- **MOSI (GPIO 23)**: Master Out Slave In - data from ESP32 to SD card (shared with display)
- **MISO (GPIO 19)**: Master In Slave Out - data from SD card to ESP32 (shared with display)
- **SCK (GPIO 18)**: Serial Clock - SPI clock signal (shared with display)

**Note**: The SPI bus pins (MOSI, MISO, SCK) are shared between the display and SD card. Each device has its own chip select pin to avoid conflicts.

## Connection Diagrams

### Button Connections

```
Button 0 (BOOT):
┌─────────┐
│  GPIO 0 ├─── ESP32 GPIO 0
│         │
│  GND    ├─── ESP32 GND
└─────────┘

Button 1 (External):
┌─────────┐
│  GPIO 27├─── ESP32 GPIO 27
│         │
│  GND    ├─── ESP32 GND
└─────────┘
```

### Display Connections

```
SSD1351 Display:
┌─────────────┐
│ CS  ──── 16 ├─── ESP32 GPIO 16 (OLED_CS)
│ DC  ──── 4  ├─── ESP32 GPIO 4
│ RST ──── 5  ├─── ESP32 GPIO 5
│ MOSI ─── 23 ├─── ESP32 GPIO 23 (SPI_MOSI - shared)
│ MISO ─── 19 ├─── ESP32 GPIO 19 (SPI_MISO - shared)
│ SCK  ─── 18 ├─── ESP32 GPIO 18 (SPI_SCK - shared)
│ VCC ──── 3.3V
│ GND ──── GND
└─────────────┘
```

### SD Card Connections

```
SD Card Reader:
┌─────────────┐
│ CS  ──── 17 ├─── ESP32 GPIO 17 (SD Card CS)
│ MOSI ─── 23 ├─── ESP32 GPIO 23 (SPI_MOSI - shared)
│ MISO ─── 19 ├─── ESP32 GPIO 19 (SPI_MISO - shared)
│ SCK  ─── 18 ├─── ESP32 GPIO 18 (SPI_SCK - shared)
│ VCC ──── 3.3V
│ GND ──── GND
└─────────────┘
```

## SPI Bus Sharing

### Shared SPI Configuration
- **MOSI (GPIO 23)**: Shared between display and SD card
- **MISO (GPIO 19)**: Shared between display and SD card
- **SCK (GPIO 18)**: Shared between display and SD card
- **CS Pins**: Separate for each device (GPIO 16 for display, GPIO 17 for SD card)

### SPI Bus Management
- Each device has its own Chip Select pin
- ESP32 can handle multiple SPI devices on the same bus
- No conflicts occur due to separate CS control
- SPI speed optimized for both devices

## Power Requirements

### Voltage Levels
- **All Components**: 3.3V operation
- **ESP32**: 3.3V power supply
- **Display**: 3.3V from ESP32
- **SD Card**: 3.3V from ESP32

### Current Requirements
- **ESP32**: ~200mA typical
- **Display**: ~50mA typical
- **SD Card**: ~100mA during operations
- **Total**: ~350mA maximum

### Power Supply Recommendations
- Use a 3.3V power supply rated for at least 500mA
- Ensure stable voltage regulation
- Consider using a separate power supply for high-current applications

## Pin Conflict Resolution

### Avoided Conflicts
- **GPIO 16**: Used for display CS, not shared with SD card
- **GPIO 17**: Used for SD card CS, separate from display
- **GPIO 0**: BOOT button, used for button input
- **GPIO 2**: Built-in LED, used for status indication

### Reserved Pins
- **GPIO 0**: BOOT button (required for programming)
- **GPIO 2**: Built-in LED
- **GPIO 6-11**: Connected to flash memory (do not use)
- **GPIO 34-39**: Input only pins (can be used for additional buttons)

## Connection Order

### Recommended Connection Sequence
1. **Display**: Connect first, test basic functionality
2. **SD Card**: Connect second, verify SPI sharing works
3. **Buttons**: Connect third, test input functionality
4. **LED**: Already built-in, test output functionality

### Testing Each Component
1. **Display Test**: Show splash screen or test pattern
2. **SD Card Test**: List files, read/write test file
3. **Button Test**: Check button press detection
4. **LED Test**: Toggle LED on/off

## Troubleshooting Guide

### Display Issues
- **No Display**: Check CS, DC, and RST connections
- **Garbled Display**: Check MOSI and SCK connections
- **Wrong Colors**: Check DC pin connection
- **Display Not Responding**: Check power supply

### SD Card Issues
- **Card Not Detected**: Check CS connection and card format (must be FAT32)
- **Read/Write Errors**: Check MOSI, MISO, and SCK connections
- **Slow Performance**: Check SPI speed settings
- **Card Corruption**: Reformat card as FAT32

### Button Issues
- **Buttons Not Working**: Ensure pull-up resistors are enabled
- **False Triggers**: Check for loose connections
- **Multiple Presses**: Check debounce settings

### SPI Conflicts
- **Devices Not Responding**: Verify CS pins are properly isolated
- **Data Corruption**: Check for crosstalk between SPI lines
- **Timing Issues**: Adjust SPI speed settings

## Configuration in Code

### Pin Definitions
```cpp
// Button pins
#define BUTTON0_PIN 0      // GPIO 0 - Button 0 (BOOT)
#define BUTTON1_PIN 27     // GPIO 27 - Button 1

// LED pin
#define LED_PIN 2          // GPIO 2 - Built-in LED

// Display pins
#define OLED_CS   16       // GPIO 16 - Display Chip Select
#define OLED_DC   4        // GPIO 4 - Display Data/Command
#define OLED_RST  5        // GPIO 5 - Display Reset

// SD card pins
#define SD_CS    17        // GPIO 17 - SD Card Chip Select
#define SD_MOSI  23        // GPIO 23 - SD Card MOSI (shared)
#define SD_MISO  19        // GPIO 19 - SD Card MISO (shared)
#define SD_SCK   18        // GPIO 18 - SD Card SCK (shared)
```

### Framework Configuration
```cpp
// Enable all components
#define ESP_PLATFORM_ENABLE_DISPLAY 1
#define ESP_PLATFORM_ENABLE_SD 1
#define ESP_PLATFORM_ENABLE_BUTTONS 1
#define ESP_PLATFORM_ENABLE_LED 1
```

## Performance Considerations

### SPI Speed Optimization
- **Display**: 10MHz SPI clock for smooth graphics
- **SD Card**: 4MHz SPI clock for reliable operation
- **Shared Bus**: Use lower speed for compatibility

### Memory Usage
- **Display Buffer**: ~32KB for 128x128 RGB565
- **SD Card Buffer**: 512 bytes for file operations
- **Button Debounce**: Minimal memory usage

### Boot Time Impact
- **Display Initialization**: ~100ms
- **SD Card Detection**: ~200ms (with retries)
- **Total Boot Time**: ~500ms typical

## Safety Considerations

### ESD Protection
- Use ESD-safe handling for all components
- Ground yourself before handling components
- Use anti-static work surface

### Power Protection
- Ensure proper voltage regulation
- Use current-limiting resistors where appropriate
- Protect against reverse polarity

### Mechanical Considerations
- Secure all connections properly
- Avoid strain on connectors
- Use appropriate wire gauge for current requirements

## Conclusion

This pinout configuration provides a complete, functional system with all components working together without conflicts. The shared SPI bus design maximizes the use of available GPIO pins while maintaining reliable operation. The configuration is optimized for the Boilerplate bootloader application with SD card priority functionality. 