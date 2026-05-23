# General IT Support Guide

## Overview
This guide covers general IT support topics, best practices, and common questions that do not fall under a specific category.

## IT Support Hours and Contact Methods
The IT helpdesk is available Monday to Friday during business hours. For after-hours emergencies (critical system outages), contact the on-call engineer via the emergency line listed in your IT documentation.

This voice bot is available 24/7 for Tier 1 troubleshooting. For issues that require human assistance, use the "Live Agent" button to transfer to a helpdesk representative during business hours.

## Common First Steps for Any IT Issue
When something stops working, try these universal fixes before calling the helpdesk:
1. **Restart the application** — close it fully (check Task Manager) and reopen.
2. **Restart the computer** — a full reboot resolves more issues than any other single action. Save your work first.
3. **Check your internet connection** — many cloud-based applications fail silently when connectivity is lost.
4. **Check for Windows Updates** — pending updates can cause instability; apply them and restart.
5. **Clear browser cache** — for web-based applications, clear cookies and cache in your browser (Ctrl+Shift+Delete in most browsers).

## Remote Work Best Practices
When working from home:
- Always connect to VPN before accessing internal resources (file shares, intranet, internal applications).
- Use a wired Ethernet connection where possible for stability — Wi-Fi is less reliable for video calls and VPN.
- Keep your laptop charged and plugged in during work hours to prevent power-saving modes from interfering with connections.
- Do not install personal software or browser extensions on work devices without IT approval.

## Data and File Access Issues

### Cannot Access a Shared Drive or Network Folder
- Ensure you are connected to VPN if working remotely.
- Try navigating to the share by IP address (e.g., `\\192.168.1.50\sharename`) instead of the server name to rule out DNS issues.
- Your account permissions may not include access to that folder — contact IT or your manager to request access.

### Accidentally Deleted a File
- Check the Recycle Bin first.
- If the file was on a network share, IT may be able to restore a previous version from backup. Act quickly — backups are typically retained for 30 days.
- Right-click the folder where the file was → Properties → Previous Versions to see if Windows shadow copies are available.

## Security Best Practices
- Never share your password with anyone, including IT staff. Legitimate IT support does not need your password to help you.
- Do not click links in unexpected emails, even if they appear to come from known senders. When in doubt, call the sender directly.
- Lock your computer when stepping away (Win+L).
- Report any suspected phishing emails to the IT security team immediately.
- Do not plug unknown USB drives into work computers.

## Software Installation Requests
All software installations on corporate devices must be approved by IT. Submitting a software request:
1. Submit a request via the IT service portal with the software name, business justification, and your manager's approval.
2. IT will evaluate licensing, compatibility, and security before approving.
3. Approved software will be deployed through the software management system.

Do not attempt to install software independently — this can cause compatibility issues and may violate your company's acceptable use policy.

## Ticket Tracking
When a helpdesk ticket is created (either automatically by this bot or manually by a technician), you will receive a confirmation email with a ticket number. Use this number to:
- Track the progress of your request in the IT service portal.
- Reference the issue in follow-up calls without repeating all details.
- Escalate if SLA timelines are not being met.
