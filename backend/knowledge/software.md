# Software and Application Troubleshooting Guide

## Overview
Software issues include applications that crash, freeze, fail to open, produce errors, or behave unexpectedly. This guide covers general application troubleshooting that applies to most software, as well as specific guidance for common corporate applications.

## Application Crashes or Will Not Open

### Step 1 — Force Close and Restart
Sometimes an application process gets stuck even after the window closes. Open Task Manager (Ctrl+Shift+Esc), find the application in the Processes tab, right-click it, and select End Task. Then relaunch the application cleanly.

### Step 2 — Restart the Computer
Many application problems — especially after a Windows update or a long uptime — are resolved by a fresh reboot. Save any open work in other applications and restart. A full shutdown and startup (not hibernate) clears memory, resets drivers, and applies any pending patches.

### Step 3 — Run as Administrator
Some applications require elevated privileges to function correctly. Right-click the application shortcut and select "Run as administrator." If this resolves the issue, discuss with IT whether permanent elevation is appropriate for your role.

### Step 4 — Check for and Apply Updates
Outdated software often has bugs that were fixed in newer versions. Look for an "Update" or "Check for Updates" option within the application's Help or Settings menu. Alternatively, check the IT software portal for the latest approved version.

### Step 5 — Clear Application Cache and Temp Files
Corrupted cache files can cause crashes and unexpected behaviour.
- Close the application.
- Press Win+R, type `%temp%`, and press Enter. Delete the contents of this folder (skip files that are in use).
- Also clear the application's own cache folder if accessible (usually in AppData).
- Relaunch the application.

## Application Error Messages

### "Missing DLL" or "Side-by-Side Configuration" Errors
These errors indicate missing system components. Try reinstalling the Microsoft Visual C++ Redistributable packages (available from Microsoft's website) or the .NET Framework version required by the application.

### Licence or Activation Errors
If an application reports it is unlicensed or activation has failed:
- Check that you are connected to the corporate network or VPN, as many licence servers are internal.
- Sign out and back into the application using your corporate credentials.
- Contact IT to verify your licence assignment in the software management system.

## Microsoft Office Applications

### Word, Excel, PowerPoint Crashing
Office applications crash most often due to corrupt add-ins or a corrupt Office installation. Start the affected Office application in safe mode by holding Ctrl while clicking its icon. If it works in safe mode, an add-in is the culprit — go to File → Options → Add-ins and disable them.

If safe mode does not help, run an Office repair: Control Panel → Programs → Microsoft Office → Change → Quick Repair. If Quick Repair fails, run Online Repair (requires internet access, takes longer but is more thorough).

### OneDrive Sync Issues
If OneDrive shows sync errors or a red X icon:
1. Click the OneDrive cloud icon in the system tray.
2. Click Help & Settings → Settings → Account → Unlink this PC.
3. Sign back in and let OneDrive re-sync.
If specific files refuse to sync, check for invalid characters in file names (colons, asterisks, angle brackets) or file paths that are too long (over 400 characters total).

## Uninstalling and Reinstalling Applications
If the above steps do not resolve the issue, a clean reinstall is the next step:
1. Uninstall via Control Panel → Programs → Uninstall a program.
2. Restart the computer.
3. Reinstall from the IT software portal or approved source.
4. Apply any available updates after installation.

## When to Escalate to Tier 2
- Application is part of a complex enterprise deployment (ERP, CRM, line-of-business apps)
- The issue affects multiple users on the same system or network share
- Reinstallation fails or requires admin credentials not available to the user
- Licensing issues that require reassignment in the licence management system
- Application needs to be newly deployed or removed from multiple machines
