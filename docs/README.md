# ESP32 Boilerplate Documentation

This directory contains comprehensive documentation for the ESP32 Boilerplate project.

## Core Documentation

### [Framework Tiers](FRAMEWORK_TIERS.md)
Detailed explanation of the tiered framework architecture, including size estimates and use cases for each tier.

### [Modular Framework](MODULAR_FRAMEWORK.md)
Architecture overview of the modular framework design and component system.

### [Complete Pinout](COMPLETE_PINOUT.md)
Comprehensive pinout guide for DOIT ESP32 DevKit V1 with all components including buttons, LED, display, and SD card.

### [SD Card Priority](SD_CARD_PRIORITY.md)
Implementation details for the SD card priority system, including detection, health checks, and API reference.

## Setup and Configuration

### [Arduino IDE Setup](ARDUINO_IDE_SETUP.md)
Step-by-step guide for configuring Arduino IDE for ESP32 development.

### [Hardware Setup](hardware_setup.md)
Hardware assembly instructions and component specifications.

### [Getting Started](getting_started.md)
Quick start guide for new users.

## Development Guides

### [Creating New Sketches](CREATING_NEW_SKETCHES.md)
Guide for creating new applications using the framework.

### [Compilation Guide](COMPILATION_GUIDE.md)
Manual compilation instructions and troubleshooting.

### [Testing Checklist](TESTING_CHECKLIST.md)
Comprehensive testing procedures for framework components.

## Deployment and Examples

### [Example Set](EXAMPLE_SET.md)
Overview of all available examples and their purposes.

### [Deployment Summary](DEPLOYMENT_SUMMARY.md)
Deployment procedures and best practices.

### [Partition Table](PARTITION_TABLE.md)
ESP32 partition scheme configuration and optimization.

## Advanced Topics

### [Future Improvements](FUTURE_IMPROVEMENTS.md)
Planned enhancements and roadmap for the framework.

## Quick Reference

### Framework Components
- **Core**: Essential functionality (always enabled)
- **Display**: OLED display support (SSD1327/SSD1351)
- **Buttons**: Button management with debouncing
- **LED**: LED state management
- **WiFi**: WiFi connectivity (AP and STA modes)
- **Web Server**: Web interface with steampunk theme
- **OTA**: Over-the-air firmware updates
- **NTP**: Network time synchronization
- **File System**: LittleFS operations
- **SD Card**: SD card file operations with priority system
- **Configuration**: Configuration management
- **Boot Manager**: Multi-boot functionality (application-level)

### Pin Assignments (DOIT ESP32 DevKit V1)
- **Button 0**: GPIO 0 (BOOT button)
- **Button 1**: GPIO 27 (external)
- **LED**: GPIO 2 (built-in)
- **Display CS**: GPIO 16
- **Display DC**: GPIO 4
- **Display RST**: GPIO 5
- **SD Card CS**: GPIO 17
- **SPI Shared**: GPIO 23 (MOSI), GPIO 19 (MISO), GPIO 18 (SCK)

### Framework Tiers
- **Bare Bones**: ~100-150KB - Core framework only
- **Basic**: ~200-300KB - Hardware interaction
- **IoT**: ~600-700KB - Network capabilities
- **Full**: ~700-800KB - Complete functionality

## Contributing

When adding new documentation:
1. Use clear, descriptive filenames
2. Include code examples where appropriate
3. Update this index file
4. Follow the existing documentation style
5. Include troubleshooting sections for complex topics

## Support

For issues and questions:
1. Check the relevant documentation first
2. Review the examples for implementation patterns
3. Check the testing checklist for common issues
4. Review the troubleshooting sections in each guide 