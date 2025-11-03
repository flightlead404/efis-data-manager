# Custom Partition Table for ESP Portable Platform

This document describes the custom partition table used by the ESP Portable Platform to support OTA updates and multi-boot functionality.

## Partition Layout

### ESP32 Partition Table (4MB Flash)

| Name      | Type | SubType | Offset   | Size     | Description                    |
|-----------|------|---------|----------|----------|--------------------------------|
| nvs       | data | nvs     | 0x9000   | 0x6000   | Non-volatile storage           |
| phy_init  | data | phy     | 0xf000   | 0x1000   | PHY initialization data        |
| factory   | app  | factory | 0x10000  | 0x100000 | Factory firmware (1MB)         |
| ota_0     | app  | ota_0   | 0x110000 | 0x100000 | OTA slot 0 (1MB)               |
| ota_1     | app  | ota_1   | 0x210000 | 0x100000 | OTA slot 1 (1MB)               |
| storage   | data | spiffs  | 0x310000 | 0x80000  | File system storage (512KB)    |
| config    | data | nvs     | 0x390000 | 0x10000  | Configuration storage (64KB)   |
| debug     | data | spiffs  | 0x3a0000 | 0x60000  | Debug logs storage (384KB)     |

### ESP8266 Partition Table (4MB Flash)

| Name      | Type | SubType | Offset   | Size     | Description                    |
|-----------|------|---------|----------|----------|--------------------------------|
| nvs       | data | nvs     | 0x9000   | 0x6000   | Non-volatile storage           |
| phy_init  | data | phy     | 0xf000   | 0x1000   | PHY initialization data        |
| factory   | app  | factory | 0x10000  | 0x100000 | Factory firmware (1MB)         |
| ota_0     | app  | ota_0   | 0x110000 | 0x100000 | OTA slot 0 (1MB)               |
| ota_1     | app  | ota_1   | 0x210000 | 0x100000 | OTA slot 1 (1MB)               |
| storage   | data | spiffs  | 0x310000 | 0x80000  | File system storage (512KB)    |
| config    | data | nvs     | 0x390000 | 0x10000  | Configuration storage (64KB)   |
| debug     | data | spiffs  | 0x3a0000 | 0x60000  | Debug logs storage (384KB)     |

## Partition Purposes

### Application Partitions

#### factory
- **Purpose**: Contains the bootloader and initial firmware
- **Size**: 1MB (0x100000)
- **Usage**: Primary boot partition, contains the ESP Platform bootloader

#### ota_0 and ota_1
- **Purpose**: OTA update slots for firmware
- **Size**: 1MB each (0x100000)
- **Usage**: 
  - ota_0: Active firmware slot
  - ota_1: Update target slot
  - Swapped during OTA updates

### Data Partitions

#### nvs
- **Purpose**: Non-volatile storage for system settings
- **Size**: 24KB (0x6000)
- **Usage**: WiFi credentials, boot configuration, system flags

#### storage
- **Purpose**: File system for user data
- **Size**: 512KB (0x80000)
- **Usage**: Configuration files, user applications, data storage

#### config
- **Purpose**: Dedicated configuration storage
- **Size**: 64KB (0x10000)
- **Usage**: IoT and app configuration files

#### debug
- **Purpose**: Debug log storage
- **Size**: 384KB (0x60000)
- **Usage**: Debug logs, crash dumps, diagnostic data

## Arduino IDE Configuration

### ESP32 Setup
1. Open Arduino IDE
2. Go to **Tools → Partition Scheme**
3. Select **Custom Partition Scheme**
4. Set **Custom Partition CSV** to point to `hardware/partitions.csv`

### ESP8266 Setup
1. Open Arduino IDE
2. Go to **Tools → Flash Size**
3. Select **4MB (FS:2MB OTA:~1019KB)**
4. The ESP8266 will use the built-in partition scheme

## Multi-Boot Functionality

### Boot Process
1. **Bootloader** starts from factory partition
2. **Check boot flags** in NVS to determine which slot to boot
3. **Load firmware** from selected slot (factory, ota_0, or ota_1)
4. **Execute firmware** with platform initialization

### OTA Update Process
1. **Download firmware** to inactive OTA slot
2. **Verify firmware** integrity and size
3. **Set boot flags** to boot from new slot
4. **Restart device** to load new firmware

### Firmware Selection
- **Button-based selection**: Use physical buttons to select firmware
- **Web interface**: Select firmware via web interface
- **Automatic fallback**: Boot factory if OTA slots fail

## File System Usage

### Storage Partition (`/storage`)
```
/storage/
├── apps/           # User applications
├── config/         # Configuration files
│   ├── iot.json
│   └── app.json
├── splash/         # Splash screen images
└── data/           # User data
```

### Debug Partition (`/debug`)
```
/debug/
├── logs/           # Debug logs
├── crashes/        # Crash dumps
└── diagnostics/    # System diagnostics
```

## Configuration

### Partition Table Selection
The partition table is selected based on the board configuration:

- **ESP32**: Uses `hardware/partitions.csv`
- **ESP8266**: Uses built-in 4MB partition scheme

### Customization
To modify the partition layout:

1. Edit the appropriate CSV file
2. Ensure total size fits in flash memory
3. Update bootloader code if needed
4. Reflash the device with new partition table

## Troubleshooting

### Common Issues

1. **"Partition table not found"**
   - Verify CSV file path in Arduino IDE
   - Check file format and syntax

2. **"OTA update failed"**
   - Check available space in OTA slots
   - Verify firmware size fits in partition

3. **"File system mount failed"**
   - Check partition table configuration
   - Verify SPIFFS partition size

4. **"Boot loop"**
   - Check boot flags in NVS
   - Verify firmware integrity

### Debug Commands
```cpp
// Print partition information
esp_partition_iterator_t it = esp_partition_find(ESP_PARTITION_TYPE_ANY, ESP_PARTITION_SUBTYPE_ANY, NULL);
while (it != NULL) {
    const esp_partition_t* part = esp_partition_get(it);
    Serial.printf("Partition: %s, Type: %d, SubType: %d, Address: 0x%x, Size: %d\n",
                  part->label, part->type, part->subtype, part->address, part->size);
    it = esp_partition_next(it);
}
esp_partition_iterator_release(it);
```

## Security Considerations

1. **Firmware Verification**: Always verify firmware integrity before booting
2. **Secure Boot**: Consider enabling secure boot for production devices
3. **Encryption**: Sensitive data should be encrypted in storage partitions
4. **Access Control**: Implement proper access control for configuration changes

## Future Enhancements

1. **Multiple App Slots**: Support for more than 2 OTA slots
2. **Compressed Storage**: Use compression to store more data
3. **Encrypted Partitions**: Add encryption support for sensitive data
4. **Dynamic Partitioning**: Runtime partition table modification 