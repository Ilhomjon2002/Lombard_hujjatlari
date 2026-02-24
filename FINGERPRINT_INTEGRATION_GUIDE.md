# Integration Guide - Adding Fingerprint Scanner to Templates

## Overview

This guide shows how to integrate the fingerprint scanner authentication UI into your existing Django templates. The fingerprint scanner provides an alternative authentication method alongside WebAuthn fingerprint authentication.

---

## 1. Modify Login Template (login.html)

### Add Scanner Tab to Login Page

**File**: `templates/users/login.html`

Add a new tab for scanner-based login:

```html
<!-- Inside your login card, modify or add tabbed interface -->

<div class="card-header">
    <ul class="nav nav-tabs card-header-tabs" role="tablist">
        <li class="nav-item">
            <a class="nav-link active" id="password-tab" data-bs-toggle="tab" href="#password-panel" role="tab">
                <i class="fas fa-key"></i> Password Login
            </a>
        </li>
        <li class="nav-item">
            <a class="nav-link" id="webauthn-tab" data-bs-toggle="tab" href="#webauthn-panel" role="tab">
                <i class="fas fa-id-card"></i> WebAuthn Device
            </a>
        </li>
        <li class="nav-item">
            <a class="nav-link" id="scanner-tab" data-bs-toggle="tab" href="#scanner-panel" role="tab">
                <i class="fas fa-fingerprint"></i> Fingerprint Scanner
            </a>
        </li>
    </ul>
</div>

<div class="tab-content">
    <!-- Password Tab (existing) -->
    <div class="tab-pane fade show active" id="password-panel" role="tabpanel">
        <div class="card-body">
            {% include "users/login_password_form.html" %}
        </div>
    </div>
    
    <!-- WebAuthn Tab (existing) -->
    <div class="tab-pane fade" id="webauthn-panel" role="tabpanel">
        <div class="card-body">
            {% include "users/login_webauthn_form.html" %}
        </div>
    </div>
    
    <!-- Scanner Tab (NEW) -->
    <div class="tab-pane fade" id="scanner-panel" role="tabpanel">
        <div class="card-body">
            {% include "users/login_scanner_form.html" %}
        </div>
    </div>
</div>
```

### Create Scanner Login Form Include

**File**: `templates/users/login_scanner_form.html`

```html
{% load static %}

<!-- Fingerprint Scanner Login Form -->
<form id="scanner-login-form">
    {% csrf_token %}
    
    <!-- Error Messages -->
    <div id="fingerprint-error" class="alert alert-danger d-none" role="alert" style="margin-bottom: 15px;">
        <i class="fas fa-exclamation-circle"></i>
        <span id="error-text"></span>
    </div>
    
    <!-- Status Messages -->
    <div id="fingerprint-status" class="alert d-none" role="alert" style="margin-bottom: 15px;">
        <i class="fas fa-info-circle"></i>
        <span id="status-text"></span>
    </div>
    
    <!-- Username Field -->
    <div class="mb-3">
        <label for="fingerprint-username" class="form-label">
            <i class="fas fa-user"></i> Username
        </label>
        <input 
            type="text" 
            class="form-control" 
            id="fingerprint-username"
            name="username"
            placeholder="Enter your username"
            required
            autocomplete="off"
        >
        <small class="text-muted d-block mt-2">
            Enter your username, then place your finger on the scanner
        </small>
    </div>
    
    <!-- Separator -->
    <hr class="my-3">
    
    <!-- Login Button -->
    <button 
        type="button" 
        class="btn btn-primary w-100 mb-2"
        id="login-fingerprint-btn"
        onclick="handleLoginClick()"
    >
        <i class="fas fa-fingerprint"></i> Login with Fingerprint
    </button>
    
    <!-- Help Text -->
    <div class="alert alert-info" role="alert" style="margin-top: 15px; font-size: 13px;">
        <strong>First time?</strong> <a href="{% url 'profile' %}">Register your fingerprint in profile settings</a>
    </div>
</form>

<!-- Include JavaScript Client -->
<script src="{% static 'js/fingerprint-scanner.js' %}" defer></script>

<style>
    .fingerprint-status {
        display: none;
        padding: 12px;
        border-radius: 5px;
        animation: slideIn 0.3s ease-in-out;
    }
    
    .fingerprint-status.status-info {
        background-color: #e7f3ff;
        color: #0066cc;
        border: 1px solid #b3d9ff;
        display: block !important;
    }
    
    .fingerprint-status.status-success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
        display: block !important;
    }
    
    .fingerprint-status.status-error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
        display: block !important;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    #fingerprint-error {
        display: none;
    }
    
    #fingerprint-error:not(.d-none) {
        display: block !important;
    }
</style>
```

---

## 2. Modify Profile Template (profile.html)

### Add Scanner Section

**File**: `templates/users/profile.html`

Add the scanner section to the profile page:

```html
{% extends "base.html" %}
{% load static %}

{% block content %}

<!-- Existing profile content -->
<div class="container mt-5">
    <div class="row">
        <div class="col-md-8">
            <!-- User Info Card -->
            <div class="card mb-4">
                <!-- ... existing content ... -->
            </div>
            
            <!-- WebAuthn Fingerprint Section (if existing) -->
            <div class="card mb-4">
                <!-- ... existing WebAuthn section ... -->
            </div>
            
            <!-- NEW: Scanner Fingerprint Section -->
            {% include "users/scanner_section.html" %}
            
            <!-- Other profile sections -->
            <!-- ... -->
        </div>
        
        <div class="col-md-4">
            <!-- Sidebar if needed -->
        </div>
    </div>
</div>

<script src="{% static 'js/fingerprint-scanner.js' %}" defer></script>

{% endblock %}
```

---

## 3. Update Links in Navigation

### Add Scanner Link to Navigation Menu

**File**: `templates/layouts/sidebar.html` or `templates/layouts/header.html`

```html
<!-- Authentication Methods Section -->
<div class="list-group list-group-flush">
    <a href="{% url 'profile' %}" class="list-group-item list-group-item-action">
        <i class="fas fa-user"></i> Profile
    </a>
    <a href="{% url 'profile' %}#fingerprint-scanner" class="list-group-item list-group-item-action">
        <i class="fas fa-fingerprint"></i> Fingerprint Scanner
    </a>
    <a href="{% url 'profile' %}#webauthn" class="list-group-item list-group-item-action">
        <i class="fas fa-id-card"></i> WebAuthn Devices
    </a>
</div>
```

---

## 4. Add URL Routes (Already Done)

If not already added to `users/urls.py`, add these routes:

```python
# users/urls.py

urlpatterns = [
    # ... existing patterns ...
    
    # Scanner-based fingerprint authentication (USB ZKTeco)
    path('api/auth/scanner/status',                     views.scanner_status,                   name='scanner_status'),
    path('api/auth/fingerprint/register/start',        views.fingerprint_register_start_scanner, name='fingerprint_register_start_scanner'),
    path('api/auth/fingerprint/capture',               views.fingerprint_capture,              name='fingerprint_capture'),
    path('api/auth/fingerprint/register/complete',     views.fingerprint_register_complete_scanner, name='fingerprint_register_complete_scanner'),
    path('api/auth/fingerprint/authenticate',          views.fingerprint_authenticate_scanner, name='fingerprint_authenticate_scanner'),
    path('api/auth/fingerprint/verify',                views.fingerprint_verify_scanner,       name='fingerprint_verify_scanner'),
    path('api/auth/fingerprint/remove',                views.fingerprint_remove_scanner,       name='fingerprint_remove_scanner'),
    
    # ... rest of patterns ...
]
```

---

## 5. Static Files Setup

### Verify Static Files Configuration

**File**: `config/settings.py`

```python
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# During development
if DEBUG:
    STATICFILES_DIRS = [
        os.path.join(BASE_DIR, 'static'),
    ]

# Collect static files before production deployment
# python manage.py collectstatic
```

### Ensure JavaScript File Exists

File: `static/js/fingerprint-scanner.js` (should be created already)

Check that file contains the `FingerprintScannerClient` class and is properly formatted.

---

## 6. Database Setup

### Apply Migrations

```bash
# Apply all migrations including fingerprint scanner
python manage.py migrate

# Check status
python manage.py migrate users --list

# Should show:
# [X] 0001_initial
# [X] 0002_...
# [X] 0003_...
# [X] 0004_scanner_fingerprint_template
```

---

## 7. Test Integration

### Testing Checklist

- [ ] Login page loads with three tabs (Password, WebAuthn, Scanner)
- [ ] Clicking Scanner tab loads scanner login form
- [ ] Profile page shows scanner section
- [ ] JavaScript console shows no errors
- [ ] `fingerprintScanner` object exists in JavaScript console
- [ ] Agent running at `http://127.0.0.1:8001`
- [ ] Scanner detection shows correct status

### Test Commands

```bash
# Test static files are served
curl http://localhost:8000/static/js/fingerprint-scanner.js

# Test API endpoints
curl http://localhost:8000/api/auth/scanner/status

# Test Django
python manage.py test users
```

---

## 8. Troubleshooting Integration

### JavaScript Not Loading

**Problem**: `fingerprintScanner is not defined` error

**Solution**:
```html
<!-- Make sure script is included at end of template -->
<script src="{% static 'js/fingerprint-scanner.js' %}" defer></script>
```

### Styles Not Applied

**Problem**: Scanner section looks unstyled

**Solution**:
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check Bootstrap CSS is loaded
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0/dist/css/bootstrap.min.css" rel="stylesheet">
```

### Icons Not Showing

**Problem**: FontAwesome icons not displaying

**Solution**:
```html
<!-- Add to template head -->
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
```

---

## 9. Optional Enhancements

### Add Quick Link to Registration

In existing profile/authentication section:

```html
{% if not user.scanner_fingerprint_template %}
    <div class="alert alert-info alert-dismissible fade show" role="alert">
        <strong>New Feature:</strong> Enable fingerprint authentication!
        <a href="{% url 'scanner_register' %}" class="alert-link">Register now</a>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
{% endif %}
```

### Add Widget to Dashboard

In `templates/users/employee_dashboard.html`:

```html
<!-- Authentication Status Widget -->
<div class="card mb-3">
    <div class="card-body">
        <h6 class="card-title">
            <i class="fas fa-shield-alt"></i> Security Status
        </h6>
        <div class="list-unstyled">
            <div>
                <span class="badge bg-success">Password</span> Set
            </div>
            {% if user.fingerprint_credential %}
            <div>
                <span class="badge bg-success">WebAuthn</span> Registered
            </div>
            {% endif %}
            {% if user.scanner_fingerprint_template.is_registered %}
            <div>
                <span class="badge bg-success">Fingerprint Scanner</span> Registered
            </div>
            {% endif %}
        </div>
    </div>
</div>
```

---

## 10. Production Deployment

### Pre-Deployment Checklist

- [ ] All migrations applied: `python manage.py migrate`
- [ ] Static files collected: `python manage.py collectstatic`
- [ ] Agent service running on production Windows server
- [ ] HTTPS enabled for Django application
- [ ] CSRF protection enabled
- [ ] Django debug mode disabled: `DEBUG = False`
- [ ] Allowed hosts configured: `ALLOWED_HOSTS = ['youromain.com']`
- [ ] Secret key is strong and environment-specific
- [ ] Database backed up before deployment

### Deployment Steps

```bash
# 1. Pull latest code
git pull origin main

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run migrations
python manage.py migrate

# 4. Collect static files
python manage.py collectstatic --noinput

# 5. Restart web server
# (Apache/Nginx reload command specific to your setup)

# 6. Restart Django application
# (Gunicorn/uWSGI restart command)

# 7. Verify agent is running
sc query "Fingerprint Local Agent" | findstr STATE:

# 8. Test login page loads
curl https://yourdomain.com/users/
```

---

## Summary of Files Modified/Created

| File | Type | Purpose |
|------|------|---------|
| `static/js/fingerprint-scanner.js` | NEW | JavaScript client library |
| `templates/users/scanner_login.html` | NEW | Scanner login page |
| `templates/users/scanner_register.html` | NEW | Scanner registration page |
| `templates/users/login_scanner_form.html` | NEW | Scanner login form include |
| `templates/users/scanner_section.html` | NEW | Profile scanner management include |
| `users/urls.py` | MODIFIED | Added 7 scanner API routes |
| `users/views.py` | MODIFIED | Added 8 scanner view functions |
| `users/models.py` | MODIFIED | Added ScannerFingerprintTemplate model |
| `users/migrations/0004_*.py` | NEW | Database migration for scanner table |

---

## Support Resources

- Setup Guide: [FINGERPRINT_SETUP_GUIDE.md](FINGERPRINT_SETUP_GUIDE.md)
- Testing Guide: [FINGERPRINT_TESTING_GUIDE.md](FINGERPRINT_TESTING_GUIDE.md)
- Local Agent: [fingerprint-agent/agent.py](fingerprint-agent/agent.py)
- Architecture Plan: [LOCAL_AGENT_PLAN.md](LOCAL_AGENT_PLAN.md)

---

**Integration Guide Version**: 1.0
**Last Updated**: January 2024
**Target Django Version**: 6.0+
**Bootstrap Version**: 5.0+
**JavaScript Framework**: Vanilla JS (no dependencies)
