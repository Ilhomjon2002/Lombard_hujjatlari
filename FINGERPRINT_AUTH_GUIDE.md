# Fingerprint Authentication Implementation Guide

## Overview

This document describes the fingerprint authentication feature implemented in the Document Signature System. Users can now register their fingerprints and use them for quick, secure authentication without needing to enter their password.

## Features

### 1. **Dual Authentication Methods**
- **Password Authentication**: Traditional username/password login
- **Fingerprint Authentication**: WebAuthn/FIDO2-based biometric authentication using your device's fingerprint scanner

### 2. **Support Across Platforms**
- Windows Hello (Windows 10+)
- Touch ID (Mac)
- Fingerprint scaners on Android/iOS devices
- Other FIDO2-compatible authenticators

### 3. **User Management**
- Register fingerprint from user profile page
- Remove/disable fingerprint authentication anytime
- Store secure credential data server-side

## How It Works

### Registration Flow

1. User goes to their Profile page (`/profile/`)
2. User clicks "Register Fingerprint" button
3. Browser prompts for fingerprint (or face/PIN depending on device)
4. System stores the credential securely in the database
5. Fingerprint is now enabled for login

### Login Flow

1. User visits login page
2. User clicks on "Fingerprint" tab
3. User clicks "Authenticate with Fingerprint" button
4. Browser prompts for fingerprint
5. Server verifies the credential
6. User is logged in and redirected to dashboard

## Database Schema

### FingerprintCredential Model

```python
class FingerprintCredential(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='fingerprint_credential')
    credential_id = models.TextField(verbose_name='Credential ID', unique=True)
    credential_data = models.JSONField(verbose_name='Credential Public Key')
    sign_count = models.IntegerField(default=0, verbose_name='Sign Count')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### CustomUser Model Extensions

```python
# Added to CustomUser model
fingerprint_enabled = models.BooleanField(default=False, verbose_name='Fingerprint Authentication Enabled')
```

## API Endpoints

### Registration Endpoints

#### GET `/fingerprint/register/start/`
Initiates fingerprint registration. Returns:
```json
{
    "challenge": "base64-encoded-challenge",
    "userId": "user-uuid",
    "userName": "username",
    "displayName": "User Full Name",
    "rp": {
        "name": "Document Signature System",
        "id": "hostname"
    }
}
```

#### POST `/fingerprint/register/start/`
Completes fingerprint registration. Expects:
```json
{
    "id": "credential-id",
    "rawId": [array of integers],
    "response": {
        "clientDataJSON": [array of integers],
        "attestationObject": [array of integers]
    },
    "type": "public-key"
}
```

### Login Endpoints

#### GET `/fingerprint/login/start/`
Initiates fingerprint login. Returns:
```json
{
    "challenge": "base64-encoded-challenge",
    "timeout": 60000,
    "userVerification": "preferred",
    "rp": {
        "id": "hostname"
    }
}
```

#### POST `/fingerprint/login/start/`
Completes fingerprint login. Expects:
```json
{
    "id": "credential-id",
    "rawId": [array of integers],
    "response": {
        "authenticatorData": [array of integers],
        "clientDataJSON": [array of integers],
        "signature": [array of integers]
    }
}
```

### Other Endpoints

#### POST `/fingerprint/remove/`
Removes fingerprint authentication for the logged-in user. Requires POST request.

## Views and URL Configuration

### URLs (`/users/urls.py`)

```python
path('fingerprint/register/start/',     views.fingerprint_register_start,   name='fingerprint_register_start'),
path('fingerprint/login/start/',        views.fingerprint_login_start,      name='fingerprint_login_start'),
path('fingerprint/remove/',             views.remove_fingerprint,           name='remove_fingerprint'),
```

### Views (`/users/views.py`)

- `fingerprint_register_start()` - Handle both GET (get options) and POST (save credential)
- `fingerprint_login_start()` - Handle both GET (get options) and POST (verify credential)
- `remove_fingerprint()` - Remove fingerprint registration for a user

## Frontend Implementation

### Login Page (`/templates/users/login.html`)

- Two tabs: Password login and Fingerprint login
- JavaScript handles WebAuthn interaction
- Uses browser's Web Authentication API
- Displays status messages during the process

### Profile Page (`/templates/users/profile.html`)

- Shows fingerprint authentication status
- Register button for new users
- Remove button for users with fingerprint already registered
- JavaScript handles registration process

## Security Considerations

### What's Secure

1. **Credential Storage**: Only public key portion is stored; private key stays on device
2. **Challenge-Based Authentication**: Server generates unique challenges for each operation
3. **Credential ID Uniqueness**: Each credential has a unique ID to prevent reuse
4. **Server-Side Verification**: All credential data is verified server-side
5. **HTTPS Only in Production**: WebAuthn requires secure context (HTTPS)

### Best Practices

1. **Always use HTTPS in production** - WebAuthn requires a secure context
2. **Keep credentials secure** - Don't share access to the device
3. **Backup credentials** - Register multiple authenticators if possible
4. **Regular updates** - Keep your browser and OS up to date

## Dependencies

The implementation uses native browser WebAuthn API. No additional JavaScript libraries are required.

## Browser Compatibility

| Browser | Support | Requirements |
|---------|---------|---|
| Chrome | ✅ | 67+ |
| Firefox | ✅ | 60+ |
| Safari | ✅ | 13+ (macOS), 14+ (iOS) |
| Edge | ✅ | 18+ |
| Internet Explorer | ❌ | Not supported |

## Testing the Feature

### For Development

If your device doesn't have a fingerprint scanner:

1. **Windows**: Windows Hello with PIN option works
2. **Mac**: Touch ID or use FaceID on compatible devices
3. **Linux**: Use FIDO2 USB security keys if available
4. **Android/iOS**: Use device's biometric authentication

### Testing Checklist

- [ ] Can register fingerprint from profile page
- [ ] Can log in with fingerprint
- [ ] Can remove fingerprint authentication
- [ ] Password login still works
- [ ] Cannot register same fingerprint twice
- [ ] Cannot use unregistered fingerprint for login
- [ ] Error messages display correctly

## Troubleshooting

### "Browser does not support fingerprint authentication"

**Cause**: Your browser doesn't support WebAuthn API
**Solution**: Use a modern browser (Chrome, Firefox, Safari, or Edge)

### "Fingerprint authentication cancelled"

**Cause**: User cancelled the fingerprint prompt
**Solution**: Click the button again and try once more

### "This fingerprint is already registered"

**Cause**: Attempting to register the same credential twice
**Solution**: Use a different authenticator or remove the existing one first

### "Authentication cancelled" during login

**Cause**: User cancelled or timed out
**Solution**: Click "Authenticate with Fingerprint" and try again

## Future Enhancements

1. **Multiple Authenticators**: Allow users to register multiple fingerprints/devices
2. **Backup Codes**: Provide backup codes if authenticator is lost
3. **Attestation Verification**: Verify authenticator attestation for enhanced security
4. **Passwordless Authentication**: Make fingerprint the primary authentication method
5. **Recovery Options**: SMS or email-based backup authentication

## Contact & Support

For issues or questions about the fingerprint authentication implementation, please contact the system administrator.

---

## API Implementation Details

### Password-to-Credential-ID Mapping

The system uses a one-to-one relationship. Each user can have only one fingerprint credential registered at a time. To register a new one, the old one must be deleted first.

### Challenge Generation

Challenges are randomly generated 32-byte values, base64-encoded for transmission. Each challenge is stored in the user's session and is single-use.

### Credential Verification

During login, the server:

1. Retrieves the stored credential for the given credential ID
2. Verifies the signature using the stored public key
3. Checks the challenge matches
4. Validates the client data
5. Logs in the user if all checks pass

## Environment Variables

No additional environment variables are required. The system uses Django's default security settings.

## Performance Considerations

- Fingerprint authentication adds minimal database load (credential lookup only)
- WebAuthn operations happen client-side; server load is minimal
- Credential verification is fast (< 100ms typically)

---

**Last Updated**: February 2026
**Version**: 1.0
