# Testing Checklist - Optimized Example Set

This checklist ensures all components of the optimized example set work correctly.

## Pre-Testing Setup

### Hardware Verification
- [ ] ESP32 board connected via USB
- [ ] LED connected to GPIO 2
- [ ] Button 0 connected to GPIO 0
- [ ] Button 1 connected to GPIO 27
- [ ] OLED display connected (if using Full tier examples)
- [ ] Serial monitor open at 115200 baud

### Software Verification
- [ ] Arduino IDE configured with ESP32 board support
- [ ] Optimized partition scheme selected
- [ ] All required libraries installed
- [ ] Framework files present in `framework/` directory

## Step 1: Bootloader Testing

### Compilation Test
- [ ] `boilerplate.ino` compiles without errors
- [ ] Binary size is reasonable (~700-800KB)
- [ ] No missing library errors

### Upload Test
- [ ] Bootloader uploads successfully to ESP32
- [ ] Device reboots after upload
- [ ] Serial output shows initialization messages
- [ ] Splash screens display correctly

### Basic Functionality Test
- [ ] Device creates WiFi AP with correct SSID
- [ ] Web interface accessible at device IP
- [ ] File manager shows empty filesystem
- [ ] System status page shows correct information

## Step 2: Example Compilation Testing

### Counter Example (Bare Bones)
- [ ] `counter_example.ino` compiles without errors
- [ ] Binary size is ~100-150KB
- [ ] No framework dependency errors
- [ ] Serial output shows initialization

### Sensor Example (Basic)
- [ ] `sensor_example.ino` compiles without errors
- [ ] Binary size is ~250-350KB
- [ ] LED and button functionality included
- [ ] File system operations work

### Compact IoT Example (IoT)
- [ ] `compact_iot_example.ino` compiles without errors
- [ ] Binary size is ~400-500KB
- [ ] WiFi functionality included
- [ ] Web server functionality included
- [ ] OTA functionality included

## Step 3: Filesystem Upload Testing

### Web Interface Upload
- [ ] Connect to ESP32's WiFi AP
- [ ] Access web interface at device IP
- [ ] Navigate to File Manager section
- [ ] Upload `counter_example.bin`
- [ ] Upload `sensor_example.bin`
- [ ] Upload `compact_iot_example.bin`
- [ ] Verify files appear in file list
- [ ] Check filesystem space usage

### Alternative Upload Methods
- [ ] LittleFS uploader plugin works (if used)
- [ ] Files upload to correct location
- [ ] File permissions are correct
- [ ] Files are readable by bootloader

## Step 4: Multi-Boot Functionality Testing

### Bootloader Recognition
- [ ] Bootloader detects uploaded firmware files
- [ ] File list shows correct names and sizes
- [ ] Bootloader can select different firmware
- [ ] Bootloader can boot selected firmware

### Example Selection
- [ ] Button 0 cycles through available examples
- [ ] Button 1 confirms selection
- [ ] Display shows current selection (if available)
- [ ] LED indicates selection status

### Example Execution
- [ ] Counter example boots and runs
- [ ] Sensor example boots and runs
- [ ] Compact IoT example boots and runs
- [ ] Each example shows appropriate serial output
- [ ] Each example responds to button input

## Step 5: Individual Example Testing

### Counter Example Testing
- [ ] Serial output shows counter incrementing
- [ ] Counter changes direction at limits
- [ ] System information displays periodically
- [ ] No memory leaks or crashes
- [ ] LED indicates system status

### Sensor Example Testing
- [ ] LED patterns change based on sensor value
- [ ] Button 0 triggers sensor reading
- [ ] Button 1 shows sensor status
- [ ] Data logging creates files correctly
- [ ] File system operations work
- [ ] Long press toggles logging on/off

### Compact IoT Example Testing
- [ ] WiFi connects to configured network
- [ ] Web interface accessible at device IP
- [ ] LED indicates WiFi connection status
- [ ] Button 0 cycles LED patterns
- [ ] Button 1 toggles WiFi AP mode
- [ ] OTA functionality works
- [ ] Configuration management works

## Step 6: Integration Testing

### Multi-Example Workflow
- [ ] Boot into Counter example
- [ ] Verify counter functionality
- [ ] Use buttons to select Sensor example
- [ ] Verify sensor functionality
- [ ] Use buttons to select Compact IoT example
- [ ] Verify IoT functionality
- [ ] Return to bootloader
- [ ] Verify all examples still available

### Filesystem Management
- [ ] Web interface shows all uploaded files
- [ ] File sizes are correct
- [ ] Filesystem space usage is accurate
- [ ] Can delete files if needed
- [ ] Can upload new files
- [ ] Bootloader recognizes new files

### Performance Testing
- [ ] Boot time is reasonable (<10 seconds)
- [ ] Example switching is fast (<5 seconds)
- [ ] Memory usage is stable
- [ ] No memory leaks during operation
- [ ] WiFi performance is good
- [ ] Web interface is responsive

## Step 7: Error Handling Testing

### Network Issues
- [ ] Device handles WiFi connection failures gracefully
- [ ] AP mode works when no WiFi available
- [ ] Web interface works in AP mode
- [ ] OTA updates fail gracefully

### Filesystem Issues
- [ ] Device handles corrupted files gracefully
- [ ] Device handles full filesystem gracefully
- [ ] Device handles missing files gracefully
- [ ] Bootloader shows appropriate error messages

### Hardware Issues
- [ ] Device works without display connected
- [ ] Device works without buttons connected
- [ ] Device works without LED connected
- [ ] Device handles hardware failures gracefully

## Step 8: Documentation Verification

### Code Documentation
- [ ] All examples have clear comments
- [ ] Framework functions are documented
- [ ] Configuration options are explained
- [ ] Troubleshooting information is available

### User Documentation
- [ ] README.md is up to date
- [ ] Compilation guide is accurate
- [ ] Testing checklist is complete
- [ ] Future improvements are documented

## Success Criteria

### Functional Requirements
- [ ] All examples compile and run correctly
- [ ] Multi-boot functionality works reliably
- [ ] Web interface is functional
- [ ] Filesystem operations work correctly
- [ ] WiFi and OTA functionality work

### Performance Requirements
- [ ] Total example set fits in 1.9MB filesystem
- [ ] Boot time is under 10 seconds
- [ ] Example switching is under 5 seconds
- [ ] Memory usage is stable
- [ ] No crashes during normal operation

### Quality Requirements
- [ ] Code is well-documented
- [ ] Error handling is robust
- [ ] User interface is intuitive
- [ ] System is reliable and stable

## Post-Testing Actions

### If All Tests Pass
- [ ] Document successful testing
- [ ] Create release notes
- [ ] Tag version in Git
- [ ] Plan Phase 2 (SD card support)

### If Issues Found
- [ ] Document issues in detail
- [ ] Prioritize fixes
- [ ] Implement fixes
- [ ] Re-test affected components
- [ ] Update documentation

### Optimization Opportunities
- [ ] Identify areas for size optimization
- [ ] Identify areas for performance improvement
- [ ] Plan additional examples if space permits
- [ ] Consider user feedback for improvements 