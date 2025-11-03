# SD Card Priority Implementation

## Overview

The Boilerplate bootloader has been enhanced with SD card priority functionality, allowing firmware binaries to be stored and loaded from SD cards while keeping other resources (splash screens, web interface files) in the internal filesystem. This provides significantly more storage capacity for firmware files while maintaining system reliability.

## Key Features

### 1. **Enhanced SD Card Detection**
- **Retry Mechanism**: 3-attempt initialization with delays between retries
- **Health Check System**: Comprehensive card validation including:
  - Card type verification
  - Card size validation
  - Root directory access test
  - Read/write/delete test file operations
- **Dynamic Status Monitoring**: Continuous availability checking that detects card removal

### 2. **BootManager SD Card Priority**
- **Priority Scanning**: SD card is checked first for firmware files, internal filesystem is fallback
- **Dual Filesystem Support**: Can read firmware from either SD card or internal storage
- **Smart File Operations**: All file operations (read, write, delete) work with the appropriate filesystem
- **Status Reporting**: Clear indication of which filesystem is being used

### 3. **Web Interface Updates**
- **SD Card Priority**: File listing, upload, download, and delete operations prioritize SD card when available
- **Fallback Support**: Automatically falls back to internal filesystem when SD card is not available
- **Status Indicators**: Web interface shows which filesystem is being used

### 4. **Boilerplate Bootloader Integration**
- **SD Status Display**: File selection screen shows SD card availability status
- **BootManager Integration**: Uses the enhanced BootManager for firmware selection
- **Clear User Feedback**: Users can see whether firmware is loaded from SD card or internal storage

## Implementation Details

### SD Card Detection Without Card Detect Pin

Since the SD card reader doesn't implement a card detect pin, the system uses a robust detection mechanism:

1. **Initialization Retry**: Attempts SD card initialization up to 3 times with delays
2. **Health Check Validation**: Performs comprehensive tests to verify card functionality
3. **Continuous Monitoring**: Regularly checks card availability during operation

### Health Check Process

The `performCardHealthCheck()` method performs these tests:

1. **Card Type Check**: Verifies the card is recognized and has a valid type
2. **Card Size Check**: Ensures the card reports a valid size
3. **Root Directory Access**: Tests ability to open and read the root directory
4. **Read/Write Test**: Creates, writes, reads, and deletes a test file
5. **Content Verification**: Ensures written and read content match

### Priority System

The system implements a clear priority hierarchy:

1. **SD Card Available**: All firmware operations use SD card
2. **SD Card Unavailable**: Falls back to internal filesystem
3. **Mixed Resources**: Splash screens and web files remain in internal storage

## Configuration

### Enable SD Card Support

In your `config.h` file:

```cpp
#define ESP_PLATFORM_ENABLE_SD 1
```

### Pin Configuration

The SD card uses these pins (shared with display):

- **SD_CS**: GPIO 17 (separate from display CS)
- **SD_MOSI**: GPIO 23 (shared with display)
- **SD_MISO**: GPIO 19 (shared with display)
- **SD_SCK**: GPIO 18 (shared with display)

## Usage Examples

### Basic SD Card Check

```cpp
if (Platform.isSDCardAvailable()) {
    Serial.println("SD card is available!");
    
    if (Platform.getSDCard()->isInitialized()) {
        Serial.println("SD card is properly initialized");
    }
} else {
    Serial.println("SD card not available");
}
```

### File Operations with Priority

```cpp
// Write file (will use SD card if available, internal filesystem otherwise)
Platform.writeSDFile("/test.txt", "Hello World");

// Read file (will read from appropriate filesystem)
String content = Platform.readSDFile("/test.txt");

// List files (will list from appropriate filesystem)
String fileList = Platform.listSDFiles("/");
```

### BootManager Integration

```cpp
BootManager* bootManager = Platform.getBootManager();

// Check SD card status
if (bootManager->isSDCardAvailable()) {
    Serial.println("Firmware loaded from SD card");
} else {
    Serial.println("Firmware loaded from internal filesystem");
}

// Get firmware count
uint8_t firmwareCount = bootManager->getFirmwareCount();
Serial.printf("Found %d firmware files\n", firmwareCount);
```

## Error Handling

### Common Error Messages

- **"Failed to initialize SD card after all retries"**: Check card format (must be FAT32)
- **"No SD card detected"**: Check physical connections and card insertion
- **"SD card health check failed"**: Card may be corrupted or incompatible
- **"Write test failed"**: Card may be write-protected or full

### Troubleshooting Steps

1. **Check Card Format**: Ensure card is formatted as FAT32
2. **Verify Connections**: Check all SPI connections
3. **Test Card Health**: Use the health check function
4. **Check Power**: Ensure adequate power supply
5. **Try Different Card**: Test with a known good card

## Performance Considerations

### SPI Sharing

- Display and SD card share the same SPI bus
- Each has separate CS pins to avoid conflicts
- SPI speed is optimized for both devices

### Memory Usage

- SD card operations use minimal RAM
- File operations are buffered efficiently
- Health checks use temporary files that are cleaned up

### Boot Time Impact

- SD card detection adds minimal boot time
- Health checks are performed only during initialization
- Fallback to internal filesystem is immediate

## API Reference

### SDCardManager Methods

```cpp
// Initialization
bool begin();
bool isAvailable();
bool isInitialized();

// File Operations
bool fileExists(const String& filename);
size_t getFileSize(const String& filename);
String readFile(const String& filename);
bool writeFile(const String& filename, const String& content);
bool appendFile(const String& filename, const String& content);
bool deleteFile(const String& filename);

// Directory Operations
String listFiles(const String& path = "/");
bool createDirectory(const String& path);
bool removeDirectory(const String& path);

// Card Information
String getCardInfo();
size_t getFreeSpace();
size_t getTotalSpace();

// Health and Validation
bool performCardHealthCheck();
bool validateFormat();
String getLastError();
```

### BootManager Methods

```cpp
// SD Card Status
bool isSDCardAvailable();

// Firmware Management
void scanFirmwareFiles();
uint8_t getFirmwareCount();
String getFirmwareName(uint8_t index);
size_t getFirmwareSize(uint8_t index);
bool bootSelectedFirmware();
```

## Best Practices

### Card Selection

- Use Class 10 or higher SD cards for best performance
- Ensure cards are formatted as FAT32
- Avoid using cards larger than 32GB for compatibility
- Use high-quality cards from reputable manufacturers

### File Organization

- Store firmware files in the root directory
- Use descriptive filenames for easy identification
- Keep splash screens and web files in internal storage
- Regularly clean up unused firmware files

### Error Recovery

- Implement graceful fallback when SD card is unavailable
- Provide clear error messages to users
- Log errors for debugging purposes
- Consider implementing automatic retry mechanisms

## Future Enhancements

### Planned Features

- **Hot-swapping**: Detect card insertion/removal during operation
- **Multiple Card Support**: Support for multiple SD cards
- **Compression**: Compress firmware files to save space
- **Encryption**: Encrypt sensitive firmware files
- **Backup System**: Automatic backup of firmware to internal storage

### Performance Optimizations

- **Caching**: Cache frequently accessed file information
- **Parallel Operations**: Perform multiple operations simultaneously
- **Compression**: Compress firmware files for faster transfer
- **Deduplication**: Avoid storing duplicate firmware files

## Conclusion

The SD card priority implementation provides a robust, flexible solution for expanding firmware storage capacity while maintaining system reliability. The automatic fallback mechanism ensures the system continues to function even when the SD card is unavailable, making it suitable for production environments where reliability is critical. 