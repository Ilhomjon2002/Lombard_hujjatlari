# Fingerprint Scanner Authentication - Setup & Deployment Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Prerequisites](#prerequisites)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)
6. [Security Considerations](#security-considerations)

---

## System Overview

The fingerprint scanner authentication system consists of two components:

### 1. Local Agent (Windows Service)
- **Location**: `fingerprint-agent/` directory
- **Technology**: Python Flask REST API
- **Purpose**: Communicates with ZKTeco USB fingerprint scanner
- **Runs on**: Background Windows service (localhost:8001)

### 2. Django Web Application
- **Location**: Main Django project
- **Technology**: Django 6.0+, REST endpoints
- **Purpose**: User authentication, fingerprint registration/verification
- **Database**: Stores encrypted fingerprint templates

---

## Prerequisites

### System Requirements
- **OS**: Windows 10/11 (64-bit recommended)
- **Python**: 3.10 or higher
- **Hardware**: USB Fingerprint Scanner (ZKTeco or compatible)
  - Vendor ID: `0x16c0`
  - Product ID: `0x0802`

### Software Requirements
```
- Django 6.0.1
- Python 3.10+
- USB drivers for ZKTeco scanner
- Administrator access to Windows
```

### Network Requirements
- Fingerprint agent runs on `http://127.0.0.1:8001` (localhost only)
- Django application communicates internally (no external exposure)
- No firewall rules needed (local machine communication only)

---

## Installation Steps

### Step 1: Prepare Virtual Environment

```bash
# Create virtual environment for agent
cd fingerprint-agent
python -m venv venv

# Activate virtual environment
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Install USB Driver for ZKTeco Scanner

1. **Download WinUSB Driver**
   - Download from: https://github.com/pbatard/libwdi/releases
   - Extract `WinUSB_x64.exe` or `WinUSB_x86.exe`

2. **Install Driver**
   ```bash
   # Connect USB scanner to computer
   # Run as Administrator
   zadig.exe
   
   # In Zadig:
   # - Select ZKTeco device from dropdown
   # - Choose "WinUSB" from driver list
   # - Click "Install Driver"
   ```

3. **Verify Driver Installation**
   ```bash
   # Check if scanner is detected
   python -c "import usb.core; devices = usb.core.find(idVendor=0x16c0); print('Scanner found!' if devices else 'Not found')"
   ```

### Step 3: Install Windows Service

```bash
cd fingerprint-agent

# Run installer as Administrator
install.bat

# Follow menu prompts:
# - Select option "1. Install Service"
# - Wait for installation to complete
# - Select option "2. Start Service" to start it

# Verify service is running
# Open Services (services.msc)
# Look for "Fingerprint Local Agent" service
# Status should show "Running"
```

### Step 4: Configure Django Application

1. **Database Migration**
   ```bash
   # In main Django project directory
   python manage.py migrate
   
   # This creates the ScannerFingerprintTemplate table
   ```

2. **Update Django Settings** (config/settings.py)
   ```python
   # Add to INSTALLED_APPS (if not present)
   INSTALLED_APPS = [
       ...
       'users',
       ...
   ]
   
   # Fingerprint settings
   FINGERPRINT_AGENT_URL = 'http://127.0.0.1:8001'
   FINGERPRINT_AGENT_TIMEOUT = 15
   ```

3. **Update URL Configuration** (already done in urls.py)
   - Scanner endpoints are at `/api/auth/fingerprint/*`

### Step 5: Test Installation

```bash
# Test agent health
python -c "import requests; r = requests.get('http://127.0.0.1:8001/api/status'); print(r.json())"

# Expected output: {"status": "ok", "version": "1.0"}

# Test scanner detection
python -c "import requests; r = requests.post('http://127.0.0.1:8001/api/scanner/detect'); print(r.json())"

# Expected output: {"detected": True, "device": "ZKTeco USB"}
```

---

## Configuration

### Fingerprint Agent Configuration

The agent reads environment variables for configuration:

```bash
# Optional - Set custom port (default: 8001)
set FINGERPRINT_AGENT_PORT=8001

# Optional - Set logging level
set FINGERPRINT_LOG_LEVEL=INFO

# Optional - Set agent timeout
set FINGERPRINT_TIMEOUT=15
```

### Django Configuration

Update `config/settings.py` for production:

```python
# Fingerprint scanner settings
FINGERPRINT_AGENT_URL = 'http://127.0.0.1:8001'  # Must be localhost
FINGERPRINT_AGENT_TIMEOUT = 15  # seconds
FINGERPRINT_QUALITY_THRESHOLD = 50  # 0-100 scale
FINGERPRINT_SIMILARITY_THRESHOLD = 90  # 0-100 scale

# Encryption key for template storage (use strong SECRET_KEY)
# Templates are encrypted with Django's SECRET_KEY
SECURE_SECRET_KEY = True
```

### Security Configuration

```python
# In config/settings.py
SECURE_SSL_REDIRECT = True  # In production
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CSRF protection enabled by default
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
```

---

## Troubleshooting

### Issue: "Agent not running" Error

**Symptoms**: Login page shows "Fingerprint agent is not running"

**Solutions**:
1. Check service status
   ```bash
   # Open Services (services.msc)
   # Look for "Fingerprint Local Agent"
   # If stopped, right-click and select "Start"
   ```

2. Check logs
   ```bash
   # View agent logs
   type fingerprint-agent\logs\agent.log
   
   # View Windows Service logs
   # Event Viewer > Windows Logs > Application
   ```

3. Restart service
   ```bash
   net stop "Fingerprint Local Agent"
   net start "Fingerprint Local Agent"
   ```

### Issue: "Fingerprint scanner not detected" Error

**Symptoms**: Scanner is connected but not detected

**Solutions**:
1. Verify physical connection
   - Check USB cable is firmly connected
   - Try different USB port (avoid USB 3.0 hubs)

2. Check driver installation
   ```bash
   # Device Manager
   # Look for ZKTeco device
   # Should show "ZKTeco" not with warnings/errors
   ```

3. Reinstall USB driver
   ```bash
   # Remove device from Device Manager
   # Unplug scanner
   # Run zadig.exe again
   # Plug scanner back in
   # Install driver as described in Step 2
   ```

### Issue: "Fingerprint quality too low" Error

**Symptoms**: Scan captured but quality below 50%

**Solutions**:
1. Clean finger surface
   - Wash and dry finger completely
   - Avoid excessive lotion/oil

2. Clean scanner surface
   - Wipe scanner with lint-free cloth
   - Remove dust particles

3. Adjust scan position
   - Place finger flat on scanner
   - Press firmly but gently
   - Center finger on scanner window

4. Adjust quality threshold (if needed)
   ```python
   # In config/settings.py (only if necessary)
   FINGERPRINT_QUALITY_THRESHOLD = 40  # Lower threshold (default: 50)
   ```

### Issue: "Fingerprint does not match" Error

**Symptoms**: Registration successful, but login fails

**Solutions**:
1. Ensure same finger used
   - Re-register fingerprint with same finger
   - Don't use different fingers

2. Try multiple times
   - Authentication has 3 attempts typically
   - Quality may vary between scans

3. Re-register fingerprint
   - Remove old fingerprint from profile
   - Register new fingerprint with fresh scan

### Issue: Windows Service Won't Start

**Symptoms**: Service installation failed or won't start

**Solutions**:
1. Run as Administrator
   ```bash
   # Right-click Command Prompt
   # Select "Run as Administrator"
   # Then run install.bat
   ```

2. Check for existing installation
   ```bash
   # In Command Prompt (as Admin)
   sc query "Fingerprint Local Agent"
   
   # If exists, uninstall first
   net stop "Fingerprint Local Agent"
   sc delete "Fingerprint Local Agent"
   ```

3. View error logs
   ```bash
   # Check Windows Event Viewer
   # Event Viewer > Windows Logs > System
   # Look for errors related to "Fingerprint Local Agent"
   ```

---

## Security Considerations

### Template Storage Security

- **Encryption**: Fingerprint templates encrypted with AES-256 (Fernet)
- **Key**: Derived from Django's `SECRET_KEY`
- **Storage**: Binary field in database
- **Access**: Only accessible to authenticated users

```python
# Template encryption example
from cryptography.fernet import Fernet
from django.conf import settings

encryption_key = settings.SECRET_KEY.encode()[:32]
cipher = Fernet(encryption_key)
encrypted_template = cipher.encrypt(template_data.encode())
```

### Network Security

- **Agent Port**: Runs on localhost (127.0.0.1:8001) only
- **Not Exposed**: No external network access
- **HTTPS**: Django app uses HTTPS in production
- **CSRF**: Protected with Django CSRF tokens

### Authentication Security

- **Quality Threshold**: Minimum 50% quality ensures genuine prints
- **Similarity Threshold**: 90% match threshold reduces false positives
- **Timeout Protection**: 15-second capture timeout prevents hangs
- **Rate Limiting**: Consider adding rate limiting for failed attempts

### Recommendations

1. **Keep SECRET_KEY Secret**
   - Never commit SECRET_KEY to version control
   - Use environment variable: `SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')`

2. **Regular Backups**
   - Backup database containing encrypted templates
   - Store backups securely

3. **Service Account**
   - Run Windows service under limited-privilege account
   - Not as Local System/Administrator

4. **Monitoring**
   - Log failed authentication attempts
   - Monitor agent service health
   - Set up alerts for service crashes

5. **USB Device Management**
   - Disable USB for unauthorized users if needed
   - Use USB port restrictions via Group Policy (enterprise)

---

## API Endpoints Reference

### Scanner Status
```
GET /api/auth/scanner/status
Response: {"agent_running": true, "scanner_detected": true, "device": "ZKTeco USB"}
```

### Start Registration
```
POST /api/auth/fingerprint/register/start
Auth: Required
Response: {"message": "Registration started", "status": "ready"}
```

### Capture Fingerprint
```
GET /api/auth/fingerprint/capture
Auth: Required
Response: {"captured": true, "quality": 85, "template": "..."}
```

### Complete Registration
```
POST /api/auth/fingerprint/register/complete
Auth: Required
Body: {"finger_position": "right_index", "template": "..."}
Response: {"message": "Fingerprint registered", "redirect": "/users/profile/"}
```

### Start Authentication
```
POST /api/auth/fingerprint/authenticate
Body: {"username": "user@example.com"}
Response: {"message": "Ready to capture", "status": "ready"}
```

### Verify & Login
```
POST /api/auth/fingerprint/verify
Body: {"username": "user@example.com"}
Response: {"message": "Authenticated", "redirect": "/users/dashboard/"}
```

### Remove Fingerprint
```
POST /api/auth/fingerprint/remove
Auth: Required
Response: {"message": "Fingerprint removed", "status": "success"}
```

---

## Support & Maintenance

### Regular Maintenance Tasks

- **Weekly**: Check service is running (`services.msc`)
- **Monthly**: Review failed authentication logs
- **Quarterly**: Update Python packages (`pip install --upgrade -r requirements.txt`)
- **Annually**: Review database backups and security settings

### Getting Help

1. Check logs in `fingerprint-agent/logs/agent.log`
2. Review Windows Event Viewer for system errors
3. Test connectivity: `http://127.0.0.1:8001/api/status`
4. Verify USB connection and driver installation

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-19 | Initial release - ZKTeco USB support |
| 1.1 | 2024-02-15 | Added quality threshold configuration |
| 1.2 | 2024-03-20 | Improved encryption and security |

---

**Last Updated**: January 2024
**Maintained By**: Development Team
**Support Email**: support@example.com
