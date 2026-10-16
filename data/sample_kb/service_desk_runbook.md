# NovaRetail IT Service Desk Runbook
**FICTIONAL DEMO DOCUMENT — Not real company policy**
Version 2.1 | Last updated: October 2025 | IT Operations

---

## Ticket Priority Levels

| Priority | Label | Definition | Target Response | Target Resolution |
|---|---|---|---|---|
| P1 | Critical | Company-wide outage or critical security incident affecting all users or business operations | 15 minutes | 4 hours |
| P2 | High | Major team or department blocked with no available workaround | 1 hour | 8 hours |
| P3 | Medium | Individual user blocked or significantly degraded service with limited workaround | 4 hours | 2 business days |
| P4 | Low | Standard service request, information request, or low-impact issue | 1 business day | 5 business days |

---

## Escalation Procedures

### When to Escalate to P1
Escalate to P1 immediately when:
- More than 20% of the company cannot access email, VPN, or critical business systems.
- A confirmed ransomware or data breach incident is detected.
- The primary data center or cloud provider reports a confirmed outage affecting production systems.

**P1 Escalation path:** IT Service Desk → IT Operations Manager → CTO → Executive Leadership.

Notify the IT Operations Manager at `it-ops-manager@novaretail.com` and call the emergency IT line at ext. 4911.

### When NOT to Escalate Immediately
- A single user cannot access email after a password change. Guide through self-service reset first.
- A software installation fails. Walk through troubleshooting checklist before escalating.
- A laptop is running slowly. Perform initial software diagnostics before requesting hardware replacement.

---

## Email Troubleshooting Runbook

### Initial Assessment
1. Ask: Is the issue affecting **one user or multiple users**?
2. If multiple users, check the Microsoft 365 Service Health dashboard at `status.office.com` and the internal status page at `status.novaretail.internal`. If a service incident is confirmed, open a P1 or P2 ticket, communicate to affected teams, and monitor the vendor's status page.
3. If one user, proceed with individual troubleshooting.

### Single User Cannot Send or Receive Email
1. Confirm internet connectivity: can the user browse to external websites?
2. Confirm VPN connection if the user is remote.
3. Ask the user to sign out of Outlook and sign back in.
4. Check mailbox quota: IT admin console → Exchange admin center → verify mailbox size.
5. If quota is exceeded, archive old email or request a quota increase (P4 ticket).
6. Test the web version at `outlook.office.com` — if web works but desktop does not, the issue is the local client.
7. Re-install Outlook from the Software Portal if the local client is corrupted.
8. If none of the above resolves the issue, escalate with full diagnostics to the Exchange operations team.

---

## Laptop Performance Troubleshooting

### Step 1 — Software Diagnostics
1. Check **CPU and memory usage** via Task Manager (Ctrl + Shift + Esc). Identify processes consuming high resources.
2. Check **free disk space**: at least 15% of total disk should be free. Open Disk Cleanup if below threshold.
3. Review **startup applications**: Task Manager → Startup tab. Disable non-essential startup programs.
4. Run **Windows Update**: Settings → Update & Security → Check for Updates. Install all pending updates including optional driver updates.
5. Check **endpoint security scan status**: confirm the NovaRetail security agent is active and not flagging a malware issue.
6. Restart the device and retest.

### Step 2 — Hardware Diagnostics
If software remediation does not resolve the performance issue:
1. Run the built-in hardware diagnostic tool: hold **Fn + Power** at startup (model-dependent).
2. Check for storage health using the IT-approved disk health tool available in the Software Portal.
3. Check event logs for hardware-related critical errors: Event Viewer → Windows Logs → System.

### Step 3 — Escalation
Escalate to hardware repair/replacement (P2 or P3 depending on severity) when:
- Hardware diagnostics report failure.
- The laptop experiences repeated unexpected shutdowns after software remediation.
- The device is more than 4 years old and performance cannot be improved with software changes.

**Do not disable or remove endpoint security agents as a troubleshooting shortcut.**

---

## New Employee IT Onboarding Checklist

When a new employee joins NovaRetail, the IT Service Desk should complete the following within the first business day:

- [ ] Create the user account in Active Directory / Microsoft 365.
- [ ] Provision a company email address: `firstname.lastname@novaretail.com`.
- [ ] Assign the employee to the appropriate security groups and distribution lists.
- [ ] Issue a managed laptop from device inventory and configure it with the standard image.
- [ ] Enrol the device in the company MDM system (Microsoft Intune).
- [ ] Set up MFA using the NovaRetail Authenticator app.
- [ ] Grant access to the Software Portal and relevant business applications.
- [ ] Send the employee a **Welcome to IT Services** email with links to the IT handbook and self-service portal.
- [ ] Schedule a 30-minute IT orientation session.

---

## Remote Work IT Support

### Recommended Home Network Setup
- Use a secure Wi-Fi network (WPA3 preferred, WPA2 minimum). Avoid public Wi-Fi without VPN.
- Ensure your home router firmware is up to date.
- Connect to the NovaRetail VPN before accessing any company internal resources.

### Common Remote Work Issues

| Issue | First step |
|---|---|
| VPN not connecting | Check internet connection; try a different VPN gateway |
| Outlook not syncing | Confirm VPN is connected; sign out and back in |
| Teams calls poor quality | Close other applications; try wired connection instead of Wi-Fi |
| Cannot access internal sites | Confirm VPN is active; check if site requires special access permissions |
| Printer not recognized | Remote printing is not supported through VPN; use local device printing only |

---

## Security Incident Response

### Suspected Phishing
1. Do not click any links or open attachments.
2. Forward the email as an attachment to `phishing@novaretail.com`.
3. Delete the original email.
4. If you already clicked a link or opened an attachment, immediately call IT Security at ext. 4911 — do not wait.

### Suspected Malware or Ransomware
1. **Immediately disconnect the device from all networks** — unplug ethernet and disable Wi-Fi.
2. Do not power off the device (preserve forensic evidence).
3. Call IT Security at ext. 4911 immediately.
4. Do not attempt to clean the device yourself.

### Credential Compromise
If you believe your password or MFA credentials have been compromised:
1. Immediately reset your password at `identity.novaretail.internal`.
2. Review your MFA registered devices and remove any unfamiliar devices.
3. Report to IT Security: `security@novaretail.com` or ext. 4911.
4. IT Security will review your account for suspicious activity.
