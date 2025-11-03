# Manual Compilation Guide

This guide walks you through compiling the optimized example set using Arduino IDE.

## Prerequisites

- Arduino IDE with ESP32 board support
- Required libraries installed (see README.md)
- ESP32 board connected and configured

## Arduino IDE Setup

1. **Board Selection**: `Tools` → `Board` → `ESP32 Arduino` → `DOIT ESP32 DEVKIT V1`
2. **Partition Scheme**: `Tools` → `Partition Scheme` → `ESP Portable Platform (1MB APP/1MB APP/960KB LittleFS)` **← IMPORTANT: Use the optimized partition**
3. **Upload Speed**: `Tools` → `Upload Speed` → `115200`
4. **CPU Frequency**: `Tools` → `CPU Frequency` → `240MHz (WiFi/BT)`
5. **Flash Frequency**: `Tools` → `Flash Frequency` → `80MHz`
6. **Flash Mode**: `Tools` → `Flash Mode` → `QIO`
7. **Flash Size**: `Tools` → `Flash Size` → `4MB (32Mb)`

## Step 1: Compile Main Bootloader

1. **Open**: `boilerplate.ino` in Arduino IDE
2. **Verify**: Click the checkmark (✓) to compile
3. **Note**: The compiled binary will be in the build folder
4. **Expected Size**: ~700-800KB

## Step 2: Compile Examples

### Counter Example (Bare Bones)
1. **Open**: `examples/counter_example/counter_example.ino`
2. **Compile**: Click the checkmark (✓)
3. **Expected Size**: ~100-150KB
4. **Note**: This demonstrates minimal framework usage

### Sensor Example (Basic)
1. **Open**: `examples/sensor_example/sensor_example.ino`
2. **Compile**: Click the checkmark (✓)
3. **Expected Size**: ~250-350KB
4. **Note**: This demonstrates hardware interaction and data logging

### Compact IoT Example (IoT)
1. **Open**: `examples/compact_iot_example/compact_iot_example.ino`
2. **Compile**: Click the checkmark (✓)
3. **Expected Size**: ~400-500KB
4. **Note**: This demonstrates network capabilities without display

## Step 3: Locate Compiled Binaries

After compilation, the binaries are located in:
```
/tmp/arduino_build_XXXXXX/
```

Look for files ending in `.bin`:
- `boilerplate.ino.bin` → Main bootloader
- `counter_example.ino.bin` → Counter example
- `sensor_example.ino.bin` → Sensor example
- `compact_iot_example.ino.bin` → Compact IoT example

## Step 4: Upload Bootloader

1. **Select**: `boilerplate.ino` in Arduino IDE
2. **Upload**: Click the arrow (→) to upload to ESP32
3. **Wait**: For upload to complete
4. **Verify**: Device boots and shows splash screen

## Step 5: Upload Examples to Filesystem

### Option A: Web Interface Upload
1. **Connect**: To ESP32's WiFi AP or network
2. **Open**: Web browser to device IP or mDNS name
3. **Navigate**: To File Manager section
4. **Upload**: Each `.bin` file to the filesystem
5. **Rename**: Files to descriptive names:
   - `counter_example.bin`
   - `sensor_example.bin`
   - `compact_iot_example.bin`

### Option B: LittleFS Upload
1. **Install**: ESP32 LittleFS Uploader plugin
2. **Select**: `Tools` → `ESP32 Sketch Data Upload`
3. **Place**: `.bin` files in `data/` folder
4. **Upload**: Data to filesystem

## Step 6: Test Multi-Boot Functionality

1. **Reboot**: ESP32 device
2. **Watch**: Boot sequence and splash screens
3. **Select**: Different examples via buttons or web interface
4. **Verify**: Each example runs correctly
5. **Test**: Button functionality for each example

## Expected Results

### Space Usage
| Example | Size | Cumulative |
|---------|------|------------|
| Counter | ~150KB | 150KB |
| Sensor | ~300KB | 450KB |
| Compact IoT | ~450KB | 900KB |
| Boot Manager | ~750KB | 1,650KB |
| **Total**: ~1,650KB | **Remaining**: 250KB |

### Functionality Tests
- ✅ **Counter Example**: Simple counting with serial output
- ✅ **Sensor Example**: LED patterns, button input, data logging
- ✅ **Compact IoT**: WiFi connection, web interface, OTA capability
- ✅ **Boot Manager**: Multi-boot selection, file management

## Troubleshooting

### Compilation Errors
- **Library Issues**: Ensure all required libraries are installed
- **Board Selection**: Verify ESP32 board is selected correctly
- **Partition Scheme**: Use the optimized partition scheme
- **Include Paths**: Check that `#include "framework/ESPPlatform.h"` works

### Upload Issues
- **Port Selection**: Ensure correct COM port is selected
- **Upload Speed**: Try lower upload speed if issues occur
- **Reset Button**: Hold reset button during upload if needed
- **Driver Issues**: Install ESP32 USB drivers if needed

### Runtime Issues
- **Serial Monitor**: Check serial output for error messages
- **Memory Issues**: Monitor heap usage with `Platform.getFreeHeap()`
- **WiFi Issues**: Verify WiFi credentials and network availability
- **File System**: Check filesystem space and file integrity

## Next Steps

After successful compilation and testing:

1. **Document**: Any issues or improvements needed
2. **Optimize**: Example sizes if needed
3. **Add**: Additional examples if space permits
4. **Plan**: SD card implementation for Phase 2

## File Organization

Keep compiled binaries organized:
```
compiled_examples/
├── boilerplate.bin          # Main bootloader
├── counter_example.bin      # Bare bones example
├── sensor_example.bin       # Basic tier example
└── compact_iot_example.bin  # IoT tier example
```

This organization makes it easy to upload files to the filesystem and track which examples are available. 