# Escalation Policy and Tier 2 Support Guide

## Overview
Not all IT issues can be resolved remotely by Tier 1 support. This guide explains when and how issues are escalated to Tier 2 (specialist on-site technicians or system administrators).

## Tier 1 vs Tier 2 Support

### Tier 1 — Remote Helpdesk (This Bot)
Tier 1 support handles common, repeatable issues that can be resolved remotely through guided troubleshooting:
- Single-user login problems and password resets
- Outlook and email sync issues for individual users
- VPN connectivity for individual devices
- Basic software crashes and reinstallation
- Peripheral device troubleshooting (printers, keyboards, mice)
- Network connectivity for a single workstation

### Tier 2 — Specialist Support
Tier 2 involves on-site technicians, system administrators, or application specialists. Issues escalated here include:
- Infrastructure failures affecting multiple users (switches, servers, domain controllers)
- Active Directory administration (account creation, group policy, domain joins)
- Physical hardware replacement or diagnosis
- Enterprise application support (ERP, CRM, line-of-business systems)
- Server administration, SQL databases, and application servers
- Security incidents (suspected malware, data breach, ransomware)
- Network infrastructure changes (firewall rules, VLANs, routing)

## How Escalation Works
When a Tier 1 agent escalates your issue, a ticket is automatically created containing:
- Your name and contact information
- A transcript of the troubleshooting steps already attempted
- The error messages or symptoms reported
- The priority level assigned based on business impact

You will receive a ticket number by email. A Tier 2 technician will contact you within the service level agreement (SLA) timeframe:
- **Low priority**: Next business day
- **Medium priority**: Within 4 hours
- **High priority**: Within 1 hour
- **Critical** (production system down): Immediate response

## Severity Classification

### Critical — Immediate Escalation
These situations bypass Tier 1 and go directly to Tier 2 or the on-call engineer:
- Production server or database completely down
- Entire office or multiple floors have no network access
- Ransomware or active security breach detected
- VPN gateway unreachable for all remote users
- Active Directory / domain controller offline

### High Priority
- More than 5 users affected by the same issue
- Business-critical application (ERP, CRM, finance system) not accessible
- Email system down for a department

### Medium Priority
- Single user unable to work due to a technical issue
- Printer affecting a shared team
- Application not functioning but workaround exists

## What Happens After Escalation
A ticket is created automatically when this bot escalates your issue. You do not need to call or email separately. However, if the issue is critical, please also call the emergency IT hotline directly — the number is posted in your office or included in your IT onboarding documents.

The assigned technician will review the troubleshooting history in your ticket, so you will not need to repeat steps that have already been tried.
