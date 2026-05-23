# VPN Troubleshooting Guide

## Overview
A Virtual Private Network (VPN) creates an encrypted tunnel between your device and the corporate network. Common issues include connection failures, authentication errors, slow speeds, and disconnections.

## Common VPN Issues and Fixes

### VPN Client Will Not Connect
The most common cause is a simple software glitch. Start by fully closing the VPN client from the system tray, waiting 10 seconds, and reopening it. Then attempt to reconnect. This clears any stale connection state.

If that does not help, restart the VPN service itself. On Windows, open Services (services.msc), find the VPN service (e.g., Cisco AnyConnect, GlobalProtect, or your vendor's service), right-click, and select Restart.

### Authentication Failures
If you receive an "authentication failed" error, verify your credentials carefully. Ensure Caps Lock is off and that you are using your corporate username (not your personal email) and your current network password. VPN credentials are usually the same as your Windows login password.

If your password was recently changed, the VPN client may still be caching the old credentials. Log out of the VPN client completely, clear any saved credentials, and try again with the new password.

Multi-factor authentication (MFA) timeouts can also cause failures. Make sure you approve the MFA prompt within 30 seconds of it appearing on your phone or authenticator app.

### VPN Connects But Cannot Reach Internal Resources
This is a split-tunnel or DNS issue. Try the following steps:
1. Disconnect and reconnect the VPN to force a fresh DNS registration.
2. Flush the DNS cache: open Command Prompt as Administrator and run `ipslookup /flushdns`.
3. Try accessing resources by IP address instead of hostname to determine if it is a DNS problem.
4. Check if the VPN profile is set to tunnel all traffic or only corporate traffic — your IT policy determines this.

### Slow VPN Speed
Slow speeds through VPN are usually caused by server load or a poor base internet connection. Try:
- Switching to a different VPN server or gateway if multiple are available.
- Running a speed test without VPN to confirm your base connection is healthy.
- Closing bandwidth-heavy applications (video streaming, large downloads) while connected.

### VPN Keeps Disconnecting
Frequent disconnections usually indicate an unstable internet connection or a power-saving setting interfering with the network adapter.
- Check if your Wi-Fi signal is strong. Move closer to the router or switch to a wired Ethernet connection.
- Disable the power-saving mode for your network adapter: Device Manager → Network Adapters → right-click your adapter → Properties → Power Management → uncheck "Allow the computer to turn off this device to save power."
- Increase the VPN idle timeout setting if your client allows it.

### Reinstalling the VPN Client
If all else fails, uninstall the VPN client completely (including any leftover configuration files), restart the computer, and reinstall the latest version from the IT software portal.

## When to Escalate to Tier 2
- VPN is completely down for multiple users simultaneously
- VPN gateway or concentrator is unreachable (infrastructure issue)
- Certificate errors that persist after reinstallation
- Issues that require firewall rule changes or server-side configuration
