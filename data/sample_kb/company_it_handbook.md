# NovaRetail Internal IT Support Handbook
**FICTIONAL DEMO DOCUMENT — Not real company policy**
Version 3.2 | Last updated: October 2025 | IT Department

---

## VPN Access

Employees working outside the office must use the company VPN before accessing any internal systems, including email, file servers, HR systems, and business applications.

### Installing the VPN Client
1. Open the **NovaRetail Software Portal** at `software.novaretail.internal` from any managed company device.
2. Search for **NovaSecure VPN Client** (version 6.x or later).
3. Click **Install** and follow the on-screen prompts. Administrator approval is not required for this application.
4. After installation, launch **NovaSecure VPN** from your Start menu or Applications folder.

### Connecting to the VPN
1. Sign in with your company email address (e.g. `firstname.lastname@novaretail.com`) and your current company password.
2. Complete Multi-Factor Authentication (MFA) using the NovaRetail Authenticator app or a registered hardware security key.
3. Select the **corporate gateway closest to your location** from the dropdown list.
4. Click **Connect**. A green shield icon in the system tray confirms an active VPN session.

### VPN Troubleshooting
- **Connection refused or timeout**: Confirm that your home internet is working. Try a different gateway location.
- **MFA prompt not appearing**: Ensure the NovaRetail Authenticator app is installed and your device is registered. Re-open the VPN client.
- **"Authentication failed" error**: Your company password may have expired. Use the self-service identity portal at `identity.novaretail.internal` to reset it, or contact the IT Service Desk.
- **Slow VPN speed**: Try the closest gateway. Avoid using VPN for personal internet browsing — route only company traffic through the VPN if split-tunnel mode is available.
- **VPN disconnects repeatedly**: Update the NovaSecure VPN Client from the Software Portal. Restart your device.

**Do not disable endpoint security software, Windows Defender, or firewall settings to make the VPN work.** If the problem persists after following these steps, open an IT ticket and attach a screenshot of the error message.

---

## Password Reset Policy

### Password Requirements
Company passwords must meet all of the following criteria:
- Minimum **14 characters** in length.
- Must include at least one uppercase letter, one lowercase letter, one number, and one special character.
- Must not match any of the last **12 passwords**.
- Must not contain your name, username, or common dictionary words.
- Passwords expire every **90 days**. You will receive a reminder 14 days before expiry.

### Self-Service Password Reset
1. Go to `identity.novaretail.internal` from any device with internet access.
2. Click **Forgot Password** or **Reset My Password**.
3. Enter your company email address and complete identity verification using your registered MFA method.
4. Choose a new password that meets all requirements above.
5. Sign in to all devices and applications using your new password.

### Account Lockout
After **five consecutive failed login attempts**, your account will be temporarily locked for 15 minutes. After the lockout period, you can attempt to sign in again or use self-service password reset.

If self-service recovery fails or your account is permanently locked, contact the IT Service Desk. Provide your employee ID for identity verification.

**Employees must never share passwords with anyone — including IT support personnel.** The IT Service Desk will never ask for your password.

---

## Multi-Factor Authentication (MFA)

MFA is mandatory for:
- Company email (Outlook / Microsoft 365)
- VPN access
- Cloud administration portals
- HR and payroll systems
- Any application marked as "MFA Required" in the Software Portal

### Approved MFA Methods
1. **NovaRetail Authenticator App** (preferred) — available on iOS and Android from the company device enrolment portal.
2. **Registered hardware security key** (FIDO2/WebAuthn) — contact the IT Service Desk for issuance.
3. **SMS one-time passcode** — only available as a recovery method when explicitly enabled by IT. Not recommended as the primary method due to SIM-swap risk.

### MFA Security Rules
- **Never share your MFA code with anyone**, including IT support, managers, or senior leadership. A legitimate IT support interaction will never require your MFA code.
- If someone asks for your MFA code, this is a social engineering or phishing attempt. Report it immediately to `security@novaretail.com`.
- If you lose access to your MFA device, contact the IT Service Desk immediately with your employee ID and manager's name.

---

## Software Installation Policy

### Approved Business Software
Employees should install all business software exclusively from the **NovaRetail Software Portal** (`software.novaretail.internal`). Approved applications include Microsoft 365, Zoom, Slack, and department-specific tools.

### Requesting New Software
1. Identify the software and its business justification.
2. Obtain written approval from your direct manager.
3. Submit a software request ticket via the IT portal: `helpdesk.novaretail.internal`.
4. IT Security will review the request within 5 business days.
5. If approved, IT will add the software to the portal or deploy it to your device.

### Restrictions
- **Administrator access is not granted** simply to install unapproved applications.
- Personal software (games, personal cloud sync, etc.) must not be installed on company devices.
- Do not use browser extensions not approved by IT — they may capture credentials or company data.

### Troubleshooting Software Installation Failures
1. Check that you are connected to the company VPN (required for portal access from home).
2. Confirm the software is listed in the Software Portal — it may require a specific version.
3. Check available disk space (at least 10 GB free recommended).
4. Try running the installer as the current logged-in user, not as Administrator.
5. Restart your device and retry.
6. If the installation still fails, open a ticket with the exact error message and the application name and version.

---

## Microsoft Teams Troubleshooting

### Teams Not Starting or Crashing
1. Fully quit Teams: right-click the taskbar icon → Quit.
2. Clear the Teams cache: press **Win + R**, type `%appdata%\Microsoft\Teams`, and delete the contents (not the folder itself).
3. Restart Teams.

### Teams Not Working After an Update
1. Sign out of Teams and close it completely.
2. Open **Windows Update** and ensure all pending updates are installed.
3. Uninstall Teams from **Settings → Apps**, then reinstall from the Software Portal.
4. If the issue persists, check the Microsoft 365 Service Health dashboard at `status.office.com`.

### Audio/Video Issues in Teams Calls
1. Go to **Teams Settings → Devices** and confirm the correct microphone, speaker, and camera are selected.
2. Test audio using the **Make a test call** option.
3. Ensure your headset or webcam driver is up to date via Device Manager.

### Teams Showing "You're Missing Out" or Login Loop
Your account may need re-authentication. Sign out completely, clear the credentials from **Windows Credential Manager**, and sign back in.

---

## Lost or Stolen Laptop

**Immediately** report a lost or stolen company laptop to:
1. **IT Service Desk** — ext. 4357 or `helpdesk@novaretail.com`.
2. **Your direct manager**.
3. **Corporate Security** — ext. 4911 or `security@novaretail.com`.

Provide:
- Device asset tag number (found on a sticker on the bottom of the laptop).
- Last known location and date/time the device was last seen.
- Whether the device was encrypted (all NovaRetail devices should be — confirm with IT).
- Whether you were connected to the company VPN when the device was last used.

IT will initiate a **remote device lock and wipe** procedure within one hour of the report. Do not attempt to recover the device yourself.

---

## Email Setup and Troubleshooting

### Accessing Company Email
Company email is hosted on **Microsoft 365 Outlook**. Access via:
- Outlook desktop application (installed from the Software Portal).
- Web browser: `outlook.office.com` — sign in with your company email and MFA.
- Mobile: install Outlook from the Apple App Store or Google Play; sign in with company email.

### Cannot Send or Receive Email
1. Check your internet connection and, if working from home, your VPN connection.
2. Confirm the Microsoft 365 service is not experiencing an outage at `status.office.com`.
3. Sign out of Outlook and sign back in.
4. Check whether your mailbox quota is near the 50 GB limit: **File → Info → Mailbox Settings**.
5. If the issue affects multiple users in your team, escalate immediately — do not ask every user to reinstall software.

### Phishing and Suspicious Emails
- Do not click links or open attachments in unexpected emails.
- Forward suspicious emails as an attachment to `phishing@novaretail.com`.
- Report to IT Security if you believe you have clicked a malicious link.
