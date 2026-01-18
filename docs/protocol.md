# Turing Smart Screen Protocol Research

## Overview
This document contains research notes and experimental findings for reverse-engineering the Turing Smart Screen serial communication protocol.

**Status:** ⚠️ PROTOCOL NOT YET IMPLEMENTED - Research phase

## Hardware Information
- **Display**: Turing Smart Screen 3.5"
- **Resolution**: 320x480 pixels
- **MCU**: WCH CH552T (8-bit E8051 core)
- **Connection**: USB-serial (appears as COM port)
- **Display Controller**: Unknown (possibly ILI9486, ST7789, or custom)

## Research Findings

### Serial Connection
- **Baud Rate**: Likely 115200 (standard for USB-serial displays)
- **Data Bits**: 8 (standard)
- **Parity**: None (standard)
- **Stop Bits**: 1 (standard)
- **Flow Control**: None (standard)

### Potential Protocol Approaches

#### Approach 1: Standard LCD Controller Commands
If the display uses a standard controller (ILI9486, ST7789), it may respond to standard commands:

**ILI9486 Commands (for reference):**
- `0x01` - Software Reset
- `0x11` - Sleep Out
- `0x29` - Display ON
- `0x2A` - Column Address Set
- `0x2B` - Row Address Set
- `0x2C` - Memory Write
- `0x3A` - Pixel Format Set

**Pixel format options:**
- RGB565: 16-bit color (5-6-5 bits for R-G-B)
- RGB888: 24-bit color (8-8-8 bits for R-G-B)

#### Approach 2: Custom Serial Protocol
Turing displays may use a custom protocol over serial. Typical structure:

```
[HEADER] [COMMAND] [LENGTH] [DATA] [CHECKSUM]
```

Common headers:
- Magic bytes (e.g., `0xFF 0xAA`)
- Device ID
- Protocol version

#### Approach 3: Image as File Transfer
Some displays accept images as binary file transfers:
- Send image metadata (width, height, format)
- Stream raw pixel data
- End-of-transmission marker

## Testing Plan

### Phase 1: Connection Test
1. ✅ Connect to COM port successfully
2. ⏳ Send test bytes and observe response
3. ⏳ Check if display responds to any input

### Phase 2: Command Discovery
Try standard commands:
1. Reset command (various formats)
2. Status query command
3. Simple pixel write command
4. Full screen fill command (solid color)

### Phase 3: Image Transmission
Once basic communication works:
1. Test small image patches
2. Test full screen updates
3. Optimize for speed

### Phase 4: Protocol Documentation
1. Document working command structure
2. Create reference implementation
3. Test on different Turing models if available

## Experimental Commands to Try

### Test 1: Standard LCD Reset
```python
# ILI9486 style software reset
self.serial.write(b'\\x01')
time.sleep(0.2)
```

### Test 2: Display Wake/Sleep
```python
# Sleep Out + Display ON
self.serial.write(b'\\x11')
time.sleep(0.1)
self.serial.write(b'\\x29')
```

### Test 3: Solid Color Fill
```python
# Set column address (full width)
self.serial.write(b'\\x2A')
self.serial.write(bytes([0, 0, 0x01, 0x3F]))  # 0 to 319

# Set row address (full height)
self.serial.write(b'\\x2B')
self.serial.write(bytes([0, 0, 0x01, 0xDF]))  # 0 to 479

# Memory write
self.serial.write(b'\\x2C')

# Write red pixels (RGB565 format)
red_pixel = b'\\xF8\\x00'  # Red in RGB565
for i in range(320 * 480):
    self.serial.write(red_pixel)
```

## External Resources

### Hardware Documentation
- [CNX Software Review](https://www.cnx-software.com/2022/04/29/turing-smart-screen-a-low-cost-3-5-inch-usb-type-c-information-display/)
- [Hackaday Article](https://hackaday.com/2023/09/11/cheap-lcd-uses-usb-serial/)

### Display Controller Datasheets
- [ST7789 Datasheet](https://www.rhydolabz.com/documents/33/ST7789.pdf)
- [Luma.LCD Python Drivers](https://luma-lcd.readthedocs.io/en/latest/python-usage.html)

### Similar Projects
Research safe, non-trojan implementations for protocol reference:
- Generic USB display projects
- Arduino LCD libraries
- Raspberry Pi display drivers

## Safety Notes
⚠️ **Important:**
- Never use or reference the compromised library
- Only use safe hardware documentation and community resources
- Test with caution to avoid potential hardware damage
- Start with read operations before attempting writes

## Next Steps

1. **Immediate**: Run scanner.py to identify the display
2. **Short-term**: Test connection with device_manager.py
3. **Testing**: Try experimental commands documented above
4. **Research**: Look for safe protocol documentation in hardware forums
5. **Implementation**: Build working protocol based on findings

## Experimental Log

### Test Session 1: [Date TBD]
**Setup:**
- Display: [Model]
- COM Port: [Port]
- Baud Rate: [Rate]

**Tests:**
- [ ] Connection established
- [ ] Device responds to input
- [ ] Display reacts to commands

**Notes:**
[Record findings here]

---

## Contributing

If you discover working commands or protocol details, please document them here. Include:
- Exact command bytes (in hex)
- Expected response
- Visual result on display
- Any timing requirements
