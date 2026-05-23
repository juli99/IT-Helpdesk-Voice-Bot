# Hardware Troubleshooting Guide

## Overview
Hardware issues cover physical devices including computers, monitors, keyboards, mice, printers, headsets, USB peripherals, and other office equipment. Many hardware problems can be resolved by checking connections, updating drivers, or restarting the device.

## Computer Will Not Power On

### Check Power Supply
- Verify the power cable is firmly connected to both the computer and the wall outlet.
- Try a different power outlet to rule out a dead socket.
- For laptops: check that the charger is properly seated and the charging indicator light is on. Try a different charger if available.
- For desktops: check the power switch on the rear of the tower (if present) is set to ON.

### Perform a Hard Reset
For laptops: disconnect the power adapter, remove the battery (if removable), hold the power button for 30 seconds, then reconnect power and try again. This discharges residual electricity from capacitors.

For desktops: hold the power button for 10 seconds to force it off, then press it once to start.

## Monitor or Display Issues

### No Display / Black Screen
- Check the cable connecting the monitor to the computer (HDMI, DisplayPort, or VGA) at both ends.
- Try pressing Win+P and cycling through display modes (PC screen only, Extend, Duplicate, Second screen only).
- If the computer powers on (you can hear it) but the screen stays black, connect to a different monitor or use a laptop's built-in display to rule out a faulty monitor.

### Display is Blurry or Wrong Resolution
Right-click the desktop → Display Settings → Resolution. Set it to the recommended resolution (usually the highest available option marked "Recommended"). Also check the scaling setting — 100% or 125% is standard for most monitors.

## Keyboard and Mouse Issues

### Keyboard or Mouse Not Responding
- For wired peripherals: disconnect the USB cable and plug it into a different USB port. Avoid USB hubs if possible — plug directly into the computer.
- For wireless peripherals: check the batteries, ensure the USB receiver is plugged in, and press the pairing button if the device has one.
- Restart the computer with the device connected to allow drivers to reload.

### Keys Sticking or Wrong Characters Appearing
Check that the keyboard language and layout is set correctly: Settings → Time & Language → Language → your language → Options → verify the keyboard layout. An accidentally switched keyboard layout is a common culprit when keys produce unexpected characters.

## Printer Issues

### Printer Offline or Not Printing
1. Open the print queue (Settings → Devices → Printers & Scanners → click your printer → Open Queue).
2. Cancel all pending jobs.
3. Right-click the printer → See what's printing → Printer menu → uncheck "Use Printer Offline."
4. Restart the Print Spooler service: open Services (services.msc), find Print Spooler, and restart it.
5. Try printing a test page (right-click the printer in Devices → Properties → Print Test Page).

### Printer Showing as "Unavailable" on Network
For network printers: verify your computer is on the correct network (wired vs. Wi-Fi can matter), and try removing and re-adding the printer using its IP address. Contact IT for the printer's IP if you do not have it.

## USB and Peripheral Devices

### Device Not Recognised
- Try a different USB port, preferably USB 3.0 (blue port) for higher-powered devices.
- Try the device on another computer to determine whether the device itself or the computer's USB port is faulty.
- Check Device Manager for yellow warning triangles, which indicate driver problems. Right-click the device → Update Driver → Search automatically for drivers.

## When to Escalate to Tier 2
- Computer will not power on and basic resets have not helped — may require physical inspection
- Suspected hard drive failure (clicking sounds, data not accessible, SMART errors)
- Monitor or laptop screen is physically damaged
- Memory (RAM) failure — repeated blue screen errors with memory-related error codes
- Motherboard or internal component replacement is required
- Warranty claim or hardware procurement is needed
