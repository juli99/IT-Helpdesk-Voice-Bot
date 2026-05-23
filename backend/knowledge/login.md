# Login and Password Troubleshooting Guide

## Overview
Login and password issues are the single most common IT support request. This covers Windows login failures, Active Directory account lockouts, self-service password resets, and multi-factor authentication problems.

## Cannot Log Into Windows

### Check the Basics First
Before anything else:
- Confirm Caps Lock is off — passwords are case-sensitive.
- Confirm you are typing the correct username. The format is usually `DOMAIN\username` or just your corporate email address, depending on the login screen.
- Ensure the correct domain is selected in the login dropdown if one is present.

### Account May Be Locked
Active Directory automatically locks accounts after a set number of failed login attempts (typically 5). If you suspect your account is locked, do not keep trying — each failed attempt resets the lockout timer.

Contact your IT helpdesk or use the self-service password reset portal to unlock the account. Provide your employee ID and answer your security questions, or approve an MFA request to verify your identity.

### Password Has Expired
Corporate passwords typically expire every 60 to 90 days. If your password has expired, Windows will prompt you to change it on the login screen. Follow the prompts to set a new password that meets the complexity requirements (usually: 8+ characters, uppercase, lowercase, number, special character).

If you cannot change the password from the login screen (common on laptops not connected to the domain), contact the helpdesk to perform a remote password reset.

## Self-Service Password Reset (SSPR)
Most organisations provide a self-service portal so users can reset their passwords without calling the helpdesk.

1. Navigate to the SSPR portal (your IT department will have provided this URL).
2. Enter your corporate email or username.
3. Verify your identity using one of the configured methods: email to your personal address, SMS to your registered mobile, or authenticator app code.
4. Set a new password following the complexity rules.
5. Wait 2-3 minutes for the change to propagate across systems, then try logging in.

## Multi-Factor Authentication (MFA) Issues

### MFA App Not Sending Notifications
If the Microsoft Authenticator or similar app is not sending push notifications:
- Check that the app has notification permissions on your phone (Settings → Notifications → Authenticator).
- Ensure your phone has an internet connection.
- Open the app manually and use the one-time code (OTP) instead of waiting for a push notification.

### Lost or New Phone
If you have lost your phone or switched to a new device and cannot access your MFA codes, contact the helpdesk immediately. IT can temporarily bypass MFA or help you re-register your new device using a verification code sent to your registered backup contact.

### MFA Prompts Appearing Too Frequently
If you are being asked for MFA every time you open an app, this is usually a sign that your session tokens are not being saved. Ensure you are selecting "Keep me signed in" or "Stay signed in" when prompted, and that your browser is not in private/incognito mode.

## Remote Login and VPN Considerations
If you are working remotely, your Windows password must be changed while connected to the corporate VPN, or the local cached credentials may become out of sync with Active Directory. Always connect VPN before changing your password on a remote machine.

## When to Escalate to Tier 2
- Active Directory account requires manual unlocking and self-service is unavailable
- User's account needs to be created or deleted
- MFA device registration requires admin override
- Group policy is preventing a user from logging in
- Smart card or certificate-based authentication issues
