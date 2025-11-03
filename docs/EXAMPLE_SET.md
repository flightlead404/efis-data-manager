# Recommended Example Set - Optimized Partition

This document outlines the recommended set of examples that will fit within the **1.9MB LittleFS partition** after partition optimization.

## Space Constraint Analysis

**Available Space**: 1.9MB in LittleFS partition (optimized from 960KB)
**Optimization**: Single OTA partition freed up 1MB for filesystem
**Required**: 4 applications (3 examples + bootmanager)

## Recommended Example Set

### 1. Counter Example (Bare Bones Tier)
**File**: `examples/counter_example/counter_example.ino`
**Size**: ~100-150KB
**Tier**: Bare Bones
**Features**:
- Core framework only
- Basic debugging
- Simple counter logic
- Minimal resource usage

**Use Case**: Learning the framework, simple data processing, minimal applications

### 2. Sensor Example (Basic Tier)
**File**: `examples/sensor_example/sensor_example.ino`
**Size**: ~250-350KB
**Tier**: Basic
**Features**:
- Core framework
- LED management (status indicators)
- Button management (data logging triggers)
- File system (data logging)
- Sensor simulation and data logging

**Use Case**: Sensor projects, data loggers, basic control systems

### 3. Compact IoT Example (IoT Tier - Optimized)
**File**: `examples/compact_iot_example/compact_iot_example.ino`
**Size**: ~400-500KB
**Tier**: IoT (Space Optimized)
**Features**:
- Core framework
- WiFi connectivity
- Web server (basic)
- OTA updates
- Configuration management
- LED and button management
- Debug output
- **Disabled**: Display, NTP (saves ~50KB)

**Use Case**: IoT applications with space constraints, connected devices

### 4. Boot Manager Application
**File**: `boilerplate.ino` (main bootloader)
**Size**: ~700-800KB
**Tier**: Full (Application-level)
**Features**:
- Multi-boot functionality
- File system management
- Web interface for firmware selection
- Splash screens and visual feedback

**Use Case**: Framework bootloader and application selector

## Total Space Usage

| Example | Tier | Size | Cumulative |
|---------|------|------|------------|
| Counter | Bare Bones | ~150KB | 150KB |
| Sensor | Basic | ~300KB | 450KB |
| Compact IoT | IoT | ~450KB | 900KB |
| Boot Manager | Full | ~750KB | 1,650KB |

**Total**: ~1,650KB ✅ (250KB remaining)

## Partition Optimization Details

### Before Optimization
- **factory**: 1MB
- **ota_0**: 1MB  
- **ota_1**: 1MB (redundant with multi-boot)
- **littlefs**: 960KB
- **Total**: 4MB

### After Optimization
- **factory**: 1MB
- **ota_0**: 1MB (single OTA partition)
- **ota_1**: ❌ (eliminated - multi-boot provides safety)
- **littlefs**: **1.9MB** (+940KB gain!)
- **Total**: 4MB

### Benefits
- ✅ **Supports 1MB Full Tier apps** in OTA partition
- ✅ **Multi-boot safety** via filesystem firmware files
- ✅ **940KB additional space** for examples
- ✅ **Simplified partition management**

## Implementation Notes

1. **Compilation**: Each example should be compiled separately and the resulting `.bin` files placed in the filesystem
2. **Naming**: Use descriptive names like `counter_example.bin`, `sensor_example.bin`, `compact_iot_example.bin`, `boilerplate.bin`
3. **Documentation**: Each example includes detailed comments about its tier and features
4. **Testing**: All examples should be tested individually before deployment
5. **Space Monitoring**: Use the web interface to monitor filesystem usage

## Future Enhancements

### SD Card Support (Phase 2)
- **Hardware**: SD card module with SPI interface
- **Storage**: 32GB+ filesystem (virtually unlimited)
- **Features**: 
  - All tier examples with multiple variations
  - User-uploaded examples
  - Configuration files and logs
  - Backup firmware storage
  - Direct file access via computer
- **Implementation**: 
  - `SDManager` class in framework
  - Fallback to LittleFS if SD card not present
  - Enhanced web interface for SD management
  - SD card status monitoring

### Additional Examples
With 250KB remaining, potential additions:
- **Display Example** (Basic + Display) - ~200KB
- **Network Example** (WiFi only) - ~150KB
- **Configuration Example** (Config management) - ~100KB

## Benefits of This Set

- ✅ **Fits within 1.9MB constraint**
- ✅ **Demonstrates 4 different tiers** (Bare Bones, Basic, IoT, Full)
- ✅ **Shows framework progression** from minimal to full functionality
- ✅ **Leaves 250KB for future additions**
- ✅ **Covers main use cases** (learning, sensors, IoT, boot management)
- ✅ **Optimized partition layout** for maximum efficiency 