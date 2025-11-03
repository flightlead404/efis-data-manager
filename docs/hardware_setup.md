# ESP Portable Platform Hardware Setup

This document provides detailed instructions for assembling the ESP Portable Development Platform.

## Required Components

### Core Components
- **ESP8266 or ESP32 Development Board** (NodeMCU, Wemos D1 Mini, or similar)
- **SSD1327 or SSD1351 OLED Display** (128x64 or 128x128 resolution)
- **2x Momentary Push Button Switches** (6x6mm or similar)
- **1x Status LED** (3mm or 5mm, any color)
- **On/Off Power Switch** (SPST toggle switch)
- **Battery Pack** (3.7V LiPo, 1000mAh or larger)
- **Battery Charging Module** (TP4056 or similar)
- **Small Breadboard** (170-point or similar)
- **Enclosure** (3D printed or purchased case)

### Supporting Components
- **Resistors**: 2x 10kΩ (button pull-ups), 1x 220Ω (LED current limiting)
- **Jumper Wires** (male-to-male and male-to-female)
- **Header Pins** (for breadboard connections)
- **Mounting Hardware** (screws, standoffs)
- **USB Cable** (for programming and charging)

## Pinout Diagrams

### ESP8266 Pinout
```
┌─────────────────────────────────────┐
│                ESP8266              │
├─────────────────────────────────────┤
│                                     │
│  VIN ── 3.3V Power                  │
│  GND ── Ground                      │
│  D0  ── Status LED (via 220Ω)       │
│  D1  ── Display SCL                 │
│  D2  ── Display SDA                 │
│  D3  ── Button 1 (via 10kΩ pull-up) │
│  D4  ── Button 2 (via 10kΩ pull-up) │
│  D5  ── Available for breadboard    │
│  D6  ── Available for breadboard    │
│  D7  ── Available for breadboard    │
│  D8  ── Available for breadboard    │
│  RX  ── Available for breadboard    │
│  TX  ── Available for breadboard    │
│                                     │
└─────────────────────────────────────┘
```

### ESP32 Pinout
```
┌─────────────────────────────────────┐
│                ESP32                │
├─────────────────────────────────────┤
│                                     │
│  3V3 ── 3.3V Power                  │
│  GND ── Ground                      │
│  GPIO0 ── Button 1 (via 10kΩ pull-up)│
│  GPIO2 ── Status LED (via 220Ω)     │
│  GPIO4 ── Available for breadboard  │
│  GPIO5 ── Available for breadboard  │
│  GPIO12 ── Available for breadboard │
│  GPIO13 ── Available for breadboard │
│  GPIO14 ── Available for breadboard │
│  GPIO15 ── Available for breadboard │
│  GPIO16 ── Available for breadboard │
│  GPIO17 ── Available for breadboard │
│  GPIO18 ── Available for breadboard │
│  GPIO19 ── Available for breadboard │
│  GPIO21 ── Display SDA              │
│  GPIO22 ── Display SCL              │
│  GPIO23 ── Available for breadboard │
│  GPIO25 ── Available for breadboard │
│  GPIO26 ── Available for breadboard │
│  GPIO27 ── Available for breadboard │
│  GPIO32 ── Available for breadboard │
│  GPIO33 ── Available for breadboard │
│  GPIO34 ── Available for breadboard │
│  GPIO35 ── Available for breadboard │
│  GPIO36 ── Available for breadboard │
│  GPIO39 ── Available for breadboard │
│                                     │
└─────────────────────────────────────┘
```

## Wiring Diagrams

### Display Connection
```
Display (SSD1327/SSD1351)
┌─────────────┐
│ VCC ── 3.3V │
│ GND ── GND  │
│ SDA ── D2   │ (ESP8266) or GPIO21 (ESP32)
│ SCL ── D1   │ (ESP8266) or GPIO22 (ESP32)
└─────────────┘
```

### Button Connections
```
Button 1
┌─────────────┐
│     ┌─┐     │
│  ───│ │─── D3 (ESP8266) or GPIO0 (ESP32)
│     └─┘     │
│      │      │
│     GND     │
└─────────────┘
    10kΩ pull-up to 3.3V

Button 2
┌─────────────┐
│     ┌─┐     │
│  ───│ │─── D4 (ESP8266) or GPIO2 (ESP32)
│     └─┘     │
│      │      │
│     GND     │
└─────────────┘
    10kΩ pull-up to 3.3V
```

### LED Connection
```
Status LED
┌─────────────┐
│     ┌─┐     │
│  ───│ │─── D0 (ESP8266) or GPIO2 (ESP32)
│     └─┘     │
│      │      │
│     GND     │
└─────────────┘
    220Ω current limiting resistor
```

### Power Circuit
```
Battery (3.7V LiPo)
    │
    ├─ Charging Module (TP4056)
    │   ├─ USB Input
    │   ├─ Battery Output ── 3.3V Regulator
    │   └─ Status LEDs
    │
    └─ Power Switch ── ESP Board VIN
```

## Assembly Instructions

### Step 1: Prepare the ESP Board
1. Solder header pins to the ESP development board
2. Test the board with a basic blink sketch
3. Note the board's specific pin assignments

### Step 2: Wire the Display
1. Connect the display to the ESP board using the pinout above
2. Use male-to-female jumper wires for easy disconnection
3. Test the display with a basic graphics library example

### Step 3: Wire the Buttons
1. Connect each button with a 10kΩ pull-up resistor
2. Wire to the specified GPIO pins
3. Test button functionality with a simple input example

### Step 4: Wire the LED
1. Connect the LED with a 220Ω current limiting resistor
2. Wire to the specified GPIO pin
3. Test LED functionality

### Step 5: Set up Power Circuit
1. Connect the battery charging module
2. Wire the power switch between battery and ESP board
3. Test charging and power switching functionality

### Step 6: Mount Breadboard
1. Secure the breadboard to the enclosure
2. Connect power rails to 3.3V and GND
3. Add header pins for easy GPIO access

### Step 7: Final Assembly
1. Mount all components in the enclosure
2. Secure wiring with cable ties or clips
3. Test all functionality before closing

## Component Specifications

### Display Options
- **SSD1327**: 128x64 OLED, I2C interface, grayscale
- **SSD1351**: 128x128 OLED, SPI interface, full color
- **Alternative**: SH1106, SSD1306 (different resolutions available)

### Button Specifications
- **Type**: Momentary push button
- **Size**: 6x6mm or 12x12mm
- **Rating**: 50mA, 12V
- **Actuation force**: 160-200g

### LED Specifications
- **Type**: 3mm or 5mm LED
- **Color**: Any (red, green, blue, white)
- **Forward voltage**: 2.0-3.3V
- **Forward current**: 20mA

### Battery Specifications
- **Type**: LiPo battery
- **Voltage**: 3.7V nominal
- **Capacity**: 1000mAh minimum (larger for longer runtime)
- **Protection**: Built-in protection circuit recommended

## Troubleshooting

### Common Issues

1. **Display not working**
   - Check I2C/SPI connections
   - Verify correct address (usually 0x3C)
   - Test with known working display library

2. **Buttons not responding**
   - Check pull-up resistor connections
   - Verify GPIO pin assignments
   - Test with simple digitalRead example

3. **LED not lighting**
   - Check current limiting resistor
   - Verify GPIO pin is configured as output
   - Test with simple digitalWrite example

4. **Power issues**
   - Check battery voltage
   - Verify charging module connections
   - Test power switch functionality

### Testing Procedures

1. **Basic functionality test**
   ```cpp
   // Test each component individually
   digitalWrite(LED_PIN, HIGH);  // LED on
   digitalWrite(LED_PIN, LOW);   // LED off
   
   int button1 = digitalRead(BUTTON1_PIN);
   int button2 = digitalRead(BUTTON2_PIN);
   ```

2. **Display test**
   ```cpp
   // Test display with simple text
   display.clear();
   display.setCursor(0, 0);
   display.print("Test");
   display.display();
   ```

3. **Power consumption test**
   - Measure current draw in different states
   - Test battery runtime
   - Verify charging functionality

## Safety Considerations

1. **Electrical Safety**
   - Use appropriate wire gauge for current requirements
   - Secure all connections to prevent shorts
   - Use heat shrink or electrical tape for insulation

2. **Battery Safety**
   - Use protected LiPo batteries
   - Never overcharge or over-discharge
   - Store in fireproof container when not in use

3. **Mechanical Safety**
   - Secure all components to prevent movement
   - Use appropriate mounting hardware
   - Ensure adequate ventilation for heat dissipation

## Customization Options

### Alternative Displays
- **E-Paper displays**: Lower power consumption
- **TFT displays**: Higher resolution and color
- **LCD displays**: Lower cost option

### Additional Features
- **Real-time clock**: DS3231 or similar
- **Temperature sensor**: DHT22 or BME280
- **Accelerometer**: MPU6050 for motion detection
- **GPS module**: For location-based applications

### Enclosure Options
- **3D printed**: Custom design for your needs
- **Off-the-shelf**: Hammond or similar manufacturer
- **DIY**: Wood, acrylic, or other materials

## Resources

- [ESP8266 Pinout Reference](https://randomnerdtutorials.com/esp8266-pinout-reference-gpios/)
- [ESP32 Pinout Reference](https://randomnerdtutorials.com/esp32-pinout-reference-gpios/)
- [Adafruit Display Libraries](https://github.com/adafruit/Adafruit_SSD1327)
- [PlatformIO Documentation](https://docs.platformio.org/) 