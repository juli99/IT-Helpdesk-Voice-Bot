# Email and Outlook Troubleshooting Guide

## Overview
Email issues are among the most common helpdesk requests. This guide covers Microsoft Outlook, Exchange, and Microsoft 365 (formerly Office 365) problems including sync failures, sending and receiving issues, and account configuration problems.

## Outlook Not Syncing or Receiving Emails

### Step 1 — Check the Connection Status
In Outlook, look at the bottom-right status bar. It should say "Connected to Microsoft Exchange" or "Connected." If it shows "Disconnected" or "Trying to connect," Outlook cannot reach the mail server.

Check your internet connection first. Open a browser and load any webpage. If the internet is working, the issue is specific to Outlook or Exchange.

### Step 2 — Sign Out and Back In
Click File → Office Account → Sign Out, then close Outlook completely. Reopen Outlook and sign in with your corporate email credentials. This refreshes the authentication token and often resolves sync issues after a password change.

### Step 3 — Clear Cached Credentials
Old or corrupted credentials in Windows Credential Manager can prevent Outlook from authenticating with Exchange.
1. Open Control Panel → Credential Manager → Windows Credentials.
2. Find any entries related to Microsoft Office, Outlook, or MicrosoftOffice and remove them.
3. Restart Outlook and enter your credentials fresh when prompted.

### Step 4 — Repair the Outlook Profile
If syncing problems persist, the Outlook profile itself may be corrupted.
1. Go to Control Panel → Mail → Show Profiles.
2. Click Add to create a new profile.
3. Set up your email account in the new profile.
4. Set Outlook to always use the new profile.
5. Open Outlook and let it re-sync your mailbox from scratch.

## Cannot Send Emails

### Outbox Stuck / Emails Stuck in Outbox
Emails stuck in the Outbox are usually caused by an oversized attachment or a corrupted item.
- Open the Outbox folder, right-click the stuck message, and delete it.
- Try sending a simple test email without attachments.
- If the issue persists, work offline (Send/Receive tab → Work Offline), delete the stuck email, go back online, and send a fresh message.

### SMTP Authentication Errors
If you receive bounce-back messages or SMTP errors, verify the outgoing server settings match IT's documented configuration (server name, port, encryption type). These vary by organisation.

## Outlook Crashes or Is Very Slow

### Disable Add-ins
Third-party add-ins are a common cause of Outlook slowness and crashes.
1. Open Outlook in safe mode: hold Ctrl while clicking the Outlook icon, or run `outlook.exe /safe` from Run (Win+R).
2. If Outlook works fine in safe mode, an add-in is the culprit.
3. Go to File → Options → Add-ins → Manage COM Add-ins and disable them one by one to find the problem.

### Compact the OST/PST File
Over time, the local mailbox data file becomes fragmented. Go to File → Account Settings → Data Files, select your data file, and click Settings → Compact Now.

## Microsoft 365 / Web Mail Access
If Outlook desktop is broken, users can always access their email via browser at https://outlook.office365.com using their corporate email address and password. This is useful as a temporary workaround while the desktop client is being repaired.

## When to Escalate to Tier 2
- Entire mailbox is missing or deleted
- Exchange server is down for multiple users
- Shared mailbox permissions need to be changed
- Distribution list changes are required
- Mail flow rules or transport rules need to be modified
