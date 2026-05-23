# Network Connectivity Troubleshooting Guide

## Overview
Network issues range from complete loss of internet access to slow speeds, intermittent dropouts, and problems reaching specific internal resources. This guide covers both wired (Ethernet) and wireless (Wi-Fi) connectivity for individual workstations.

## No Internet Access

### Step 1 — Restart the Network Stack
The fastest first step is to release and renew your IP address. Open Command Prompt as Administrator and run:
```
ipconfig /release
ipconfig /flushdns
ipconfig /renew
```
Then try browsing again. This forces the computer to request a fresh IP address from the DHCP server.

### Step 2 — Restart the Router/Modem
If you are on a home network or a small office setup, power-cycle the router and modem:
1. Unplug both devices from power.
2. Wait 30 seconds.
3. Plug the modem back in first and wait for it to fully connect (solid lights, 1-2 minutes).
4. Then plug the router back in and wait another minute.
5. Test your connection.

On a corporate LAN, you cannot restart the router — contact the helpdesk if the entire network segment is down.

### Step 3 — Check the Physical Connection (Wired)
If using Ethernet:
- Check that the cable is firmly seated in both the computer's network port and the wall jack or switch port.
- Look for the link light on the network port — it should be solid or blinking green.
- Try swapping the cable with a known-good one.
- Try a different switch port or wall jack if available.

### Step 4 — Wireless Troubleshooting (Wi-Fi)
- Disconnect from the wireless network and reconnect: click the Wi-Fi icon → click your network name → Disconnect → reconnect and re-enter the password if needed.
- Forget the network and rejoin: Windows Settings → Network & Internet → Wi-Fi → Manage Known Networks → Find your network → Forget → reconnect from scratch.
- Check signal strength — if the signal is low, move closer to the access point.
- Try switching between the 2.4 GHz and 5 GHz bands if both are available. 5 GHz is faster but shorter range; 2.4 GHz has better range.

## Slow Internet or High Latency

### Identify the Source of Slowness
Run a speed test at speedtest.net or fast.com to get a baseline. Compare results to your expected connection speed.

If speeds are significantly below expected:
- Close bandwidth-heavy background applications (Windows Update, OneDrive sync, Teams video, Dropbox).
- Check how many devices are on the network — congestion from many active users causes slowness.
- If on Wi-Fi, interference from neighbouring networks or physical obstacles can reduce throughput.

### Network Adapter Settings
For wired connections, ensure the network adapter is set to the correct speed and duplex:
Device Manager → Network Adapters → right-click your adapter → Properties → Advanced → Speed & Duplex → set to Auto Negotiation.

## Cannot Reach Specific Internal Servers or Websites
If general internet works but specific internal addresses do not:
- Flush the DNS cache: `ipconfig /flushdns`
- Try the IP address directly to rule out DNS failure
- Check if a VPN connection is required to access internal resources
- Verify the server name with your IT team — internal server addresses sometimes change

## Windows Network Diagnostics
Windows has a built-in troubleshooter that can detect and automatically fix common problems:
Right-click the network icon in the system tray → Troubleshoot problems.
The tool will run diagnostics and attempt automatic fixes. Note what it finds even if it cannot fix the issue — the diagnostic message is useful for the helpdesk.

## When to Escalate to Tier 2
- Entire floor, office, or building has no network access
- Switch or access point appears to be offline
- DHCP server is not handing out IP addresses
- Network changes, VLAN configuration, or firewall rule changes are required
- Core infrastructure (routers, switches, WAN links) is suspect
