# Fingerprint Scanner Authentication - Testing & Validation Guide

## Pre-Deployment Testing Checklist

### ✓ Environment Setup Tests

- [ ] Python 3.10+ installed
  ```bash
  python --version
  ```

- [ ] Virtual environment created
  ```bash
  cd fingerprint-agent
  python -m venv venv
  venv\Scripts\activate.bat
  ```

- [ ] Dependencies installed
  ```bash
  pip install -r requirements.txt
  ```

- [ ] USB driver installed for ZKTeco scanner
  - [ ] Device shows in Device Manager as "ZKTeco"
  - [ ] No warning/error icons

- [ ] Django environment configured
  ```bash
  cd ..
  python manage.py check
  # Should show "System check identified no issues"
  ```

- [ ] Database migrated
  ```bash
  python manage.py migrate
  # Should show "Operations to perform: 1"
  ```

### ✓ Service Installation Tests

- [ ] Run installer as Administrator
  ```bash
  cd fingerprint-agent
  install.bat
  ```

- [ ] Service installed successfully
  ```bash
  sc query "Fingerprint Local Agent"
  # Should show STATE: stopped or running
  ```

- [ ] Service starts without errors
  ```bash
  net start "Fingerprint Local Agent"
  net stop "Fingerprint Local Agent"
  ```

- [ ] Service appears in Services.msc window

### ✓ Agent API Tests

- [ ] Agent starts on port 8001
  ```bash
  netstat -ano | findstr :8001
  # Should show LISTENING
  ```

- [ ] Health check endpoint works
  ```bash
  curl http://127.0.0.1:8001/api/status
  # Response: {"status": "ok"}
  ```

- [ ] Scanner detection works
  ```bash
  curl -X POST http://127.0.0.1:8001/api/scanner/detect
  # Response: {"detected": true, "device": "ZKTeco USB"}
  ```

### ✓ Registration Flow Tests

- [ ] Start registration endpoint
  ```python
  import requests
  r = requests.post('http://localhost:8000/api/auth/fingerprint/register/start')
  print(r.json())
  # Should return success status
  ```

- [ ] Capture endpoint returns template
  ```python
  r = requests.get('http://localhost:8000/api/auth/fingerprint/capture')
  print(r.json())
  # Should return template with quality score > 50
  ```

- [ ] Complete registration saves to database
  ```python
  # Check database
  from users.models import ScannerFingerprintTemplate
  t = ScannerFingerprintTemplate.objects.first()
  print(f"Quality: {t.quality_score}")
  print(f"Registered: {t.is_registered}")
  ```

### ✓ Authentication Flow Tests

- [ ] Authentication endpoint accepts username
  ```python
  r = requests.post('http://localhost:8000/api/auth/fingerprint/authenticate',
                    json={'username': 'testuser'})
  print(r.json())
  # Should return ready status
  ```

- [ ] Verify endpoint authenticates user
  ```python
  r = requests.post('http://localhost:8000/api/auth/fingerprint/verify',
                    json={'username': 'testuser'})
  print(r.json())
  # Should return success with redirect or template mismatch
  ```

- [ ] Fingerprint removal works
  ```python
  r = requests.post('http://localhost:8000/api/auth/fingerprint/remove')
  print(r.json())
  # Should return success
  # Check database: is_registered should be False
  ```

### ✓ UI/Frontend Tests

- [ ] Scanner login page loads
  - [ ] Navigate to `/users/scanner_login/`
  - [ ] Page displays username field
  - [ ] Scanner status message appears
  - [ ] Login button enabled

- [ ] Scanner registration page works
  - [ ] Navigate to user profile
  - [ ] "Register Fingerprint Now" button visible
  - [ ] Click button → registration page loads
  - [ ] Step indicators visible and update correctly

- [ ] JavaScript client works
  - [ ] Open browser console (F12)
  - [ ] Check: `fingerprintScanner` object exists
  - [ ] Check: `FingerprintScannerClient` class available
  - [ ] No console errors

### ✓ Error Handling Tests

- [ ] Agent down gracefully
  - [ ] Stop agent: `net stop "Fingerprint Local Agent"`
  - [ ] Try login: Should show "Agent not running" error
  - [ ] Page doesn't crash
  - [ ] Restart agent: `net start "Fingerprint Local Agent"`

- [ ] Scanner disconnected handling
  - [ ] Unplug USB scanner
  - [ ] Try capture: Should show "Scanner not detected" error
  - [ ] Replug scanner: Should work again

- [ ] Low quality fingerprint handling
  - [ ] Clean scanner and retry scan
  - [ ] If quality < 50%: Should show quality error
  - [ ] Can retry capture

- [ ] Fingerprint mismatch handling
  - [ ] Use different finger for verification
  - [ ] Should show "Does not match" error
  - [ ] Allows retry attempts

### ✓ Security Tests

- [ ] CSRF tokens verified
  - [ ] View page source
  - [ ] Compare csrfmiddlewaretoken in form

- [ ] Authentication required
  - [ ] Try accessing registration without login
  - [ ] Should redirect to login page

- [ ] Encrypted template storage
  ```python
  from users.models import ScannerFingerprintTemplate
  t = ScannerFingerprintTemplate.objects.first()
  template_bytes = t.template_data
  # Should be encrypted binary, not readable text
  print(type(template_bytes), len(template_bytes))
  ```

---

## Manual End-to-End Testing

### Test Scenario 1: Complete Registration & Login

**Preconditions**: 
- Agent running
- Scanner connected
- User logged into Django Admin
- User has no existing fingerprint

**Steps**:
1. Navigate to `/users/profile/`
2. Scroll to "Fingerprint Scanner Authentication" section
3. Click "Register Fingerprint Now"
4. See "Step 1: Preparation" with instructions
5. Click "Start Registration"
6. Review preparation instructions
7. Click "Capture Fingerprint"
8. See "Place your finger on scanner" status
9. Place finger on physical scanner
10. Wait for capture (should show quality %)
11. Quality > 50%: Move to Step 3
12. Select finger position from dropdown
13. Click "Save Fingerprint"
14. See success message and redirect to profile
15. Verify "Fingerprint Registered" section shows

**Verify**:
- Fingerprint section shows "Registered" status
- Registered date/time displayed
- Quality score shown
- Finger position correct
- Verification count = 0 (not used yet)

**Logout and Test Login**:
1. Logout from application
2. Navigate to `/users/scanner_login/`
3. Enter username
4. Click "Login with Fingerprint"
5. Place finger on scanner
6. See success message
7. Redirect to dashboard
8. Verify logged in as correct user

---

### Test Scenario 2: Fingerprint Removal & Re-registration

**Preconditions**:
- User has registered fingerprint
- Logged in as that user

**Steps**:
1. Navigate to profile
2. Click "Remove Fingerprint" button
3. Confirm removal dialog
4. See success message
5. Verify "No Fingerprint Registered" section shows
6. Run Scenario 1 again (register new fingerprint)

**Verify**:
- Old template deleted from database
- New template saved successfully
- Can login with new fingerprint

---

### Test Scenario 3: Error Recovery

**Test Agent Restart**:
1. Agent running, fingerprint registered
2. Stop agent: `net stop "Fingerprint Local Agent"`
3. Try scanner login
4. See "Agent not running" error
5. Restart agent: `net start "Fingerprint Local Agent"`
6. Try again - should work

**Test Low Quality**:
1. Dirty scanner surface
2. Try to capture fingerprint
3. See quality < 50%
4. See error message "Quality too low"
5. Click retry
6. Clean scanner
7. Capture again - should succeed

**Test Mismatch**:
1. Register with finger A
2. Logout
3. Login but place finger B on scanner
4. See error "Does not match"
5. Try again with finger A - should work

---

## Performance Testing

### Load Test: Concurrent Registrations

```python
import concurrent.futures
import requests

def register_fingerprint(user_id):
    # Simulate registration
    r = requests.post(f'http://localhost:8000/api/auth/fingerprint/register/complete',
                      json={'user_id': user_id, 'template': 'xxx'})
    return r.status_code == 200

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    results = executor.map(register_fingerprint, range(1, 6))
    passed = sum(results)
    print(f"Passed: {passed}/5")
```

**Expected**: All registrations succeed without timeouts

### Response Time Test

```python
import time
import requests

start = time.time()
r = requests.get('http://127.0.0.1:8001/api/status')
duration = (time.time() - start) * 1000
print(f"Agent response time: {duration:.2f}ms")
# Expected: < 100ms
```

---

## Browser Compatibility Testing

| Browser | Windows 10 | Windows 11 | Notes |
|---------|-----------|-----------|-------|
| Chrome | ✓ | ✓ | Recommended |
| Firefox | ✓ | ✓ | Works fine |
| Edge | ✓ | ✓ | Native Windows |
| IE 11 | ✗ | N/A | Not supported |

---

## Database Testing

### Verify Schema

```bash
python manage.py sqlmigrate users 0004
# Should show CREATE TABLE scanner_fingerprint_template with all fields
```

### Test Model Operations

```python
from users.models import CustomUser, ScannerFingerprintTemplate
from django.utils import timezone

# Create test template
user = CustomUser.objects.first()
template = ScannerFingerprintTemplate.objects.create(
    user=user,
    template_data=b'encrypted_template_here',
    quality_score=85,
    finger_position='right_index',
    is_registered=True
)

# Update
template.verification_count = 5
template.last_verified = timezone.now()
template.save()

# Retrieve
retrieved = ScannerFingerprintTemplate.objects.get(user=user)
print(f"Quality: {retrieved.quality_score}")

# Delete
template.delete()
print("Test completed successfully")
```

---

## Deployment Validation Checklist

Before deploying to production:

- [ ] All tests passed
- [ ] No console errors in browser
- [ ] Agent logs are clean (no warnings/errors)
- [ ] Database backups created
- [ ] SECRET_KEY is strong and secure
- [ ] HTTPS enabled in production
- [ ] CSRF tokens functioning
- [ ] Rate limiting configured (optional)
- [ ] Monitoring/alerting set up
- [ ] Documentation reviewed
- [ ] Team trained on system
- [ ] Rollback plan documented

---

## Post-Deployment Monitoring

### Daily Checks
- [ ] Agent service running
- [ ] No failed authentication attempts spike
- [ ] Database size normal

### Weekly Checks
- [ ] Review agent logs for errors
- [ ] Check Windows Event Viewer
- [ ] Verify database backups

### Monthly Checks
- [ ] User feedback on fingerprint reliability
- [ ] Authentication success rate analysis
- [ ] Performance metrics

---

## Test Report Template

```
Date: YYYY-MM-DD
Tester: [Name]
System: [OS Version]
Python: [Version]
Django: [Version]

Test Results:
- Environment Setup: PASS/FAIL
- Service Installation: PASS/FAIL
- Agent API: PASS/FAIL
- Registration Flow: PASS/FAIL
- Authentication Flow: PASS/FAIL
- UI/Frontend: PASS/FAIL
- Error Handling: PASS/FAIL
- Security: PASS/FAIL
- End-to-End: PASS/FAIL
- Performance: PASS/FAIL

Issues Found:
1. [Issue]
2. [Issue]

Recommendations:
1. [Recommendation]
2. [Recommendation]

Sign-off: _______________
```

---

**Test Guide Version**: 1.0
**Last Updated**: January 2024
