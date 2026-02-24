# Fingerprint Authentication Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Device & Browser                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Biometric Hardware (Fingerprint Scanner / Touch ID)     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ▲                                      │
│                           │ User scans fingerprint               │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  WebAuthn API (navigator.credentials)                   │  │
│  │  - Login credentials.get()                              │  │
│  │  - Register credentials.create()                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ▲                                      │
│                           │ HTTP/JSON                           │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Frontend JavaScript                                    │  │
│  │  ├─ registerFingerprint()                              │  │
│  │  └─ fingerprintLoginBtn listener                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           ▲
                           │ HTTPS/JSON
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Django Backend Server                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  URLs (users/urls.py)                                   │  │
│  │  ├─ /fingerprint/register/start/ [GET/POST]            │  │
│  │  ├─ /fingerprint/login/start/ [GET/POST]               │  │
│  │  └─ /fingerprint/remove/ [POST]                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ▲                                      │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Views (users/views.py)                                 │  │
│  │  ├─ fingerprint_register_start()                        │  │
│  │  │  └─ Generates challenge                             │  │
│  │  │  └─ Saves fingerprint credential                    │  │
│  │  │                                                     │  │
│  │  ├─ fingerprint_login_start()                          │  │
│  │  │  └─ Generates login challenge                       │  │
│  │  │  └─ Verifies credential                            │  │
│  │  │  └─ Authenticates user                             │  │
│  │  │                                                     │  │
│  │  └─ remove_fingerprint()                               │  │
│  │     └─ Deletes fingerprint credential                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ▲                                      │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Models (users/models.py)                               │  │
│  │  ├─ CustomUser                                          │  │
│  │  │  └─ fingerprint_enabled: Boolean                    │  │
│  │  │                                                     │  │
│  │  └─ FingerprintCredential (One-to-One)                │  │
│  │     ├─ user: ForeignKey                               │  │
│  │     ├─ credential_id: TextField                       │  │
│  │     ├─ credential_data: JSONField                     │  │
│  │     ├─ sign_count: Integer                            │  │
│  │     ├─ created_at: DateTime                           │  │
│  │     └─ updated_at: DateTime                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ▲                                      │
│                           │                                      │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Database (SQLite / PostgreSQL)                         │  │
│  │  ├─ users_customuser                                   │  │
│  │  └─ users_fingerprintcredential                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Registration Flow

```
User                    Browser              Server
 │                        │                    │
 │ 1. Click Register      │                    │
 │   Fingerprint          │                    │
 ├──────────────────────→ │                    │
 │                        │ 2. GET /register/  │
 │                        │         start/     │
 │                        ├───────────────────→│
 │                        │                    │
 │                        │ 3. Return options  │
 │                        │    + challenge     │
 │                        │←───────────────────┤
 │                        │                    │
 │ 4. Scan fingerprint    │                    │
 │                        │                    │
 │← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│                    │
 │ (WebAuthn API)         │                    │
 │ generates credential   │                    │
 │                        │                    │
 │ 5. Send credential    │                    │
 ├──────────────────────→ │                    │
 │                        │ 6. POST credential │
 │                        ├───────────────────→│
 │                        │                    │
 │                        │ 7. Verify & Save  │
 │                        │    credential DB  │
 │                        │                    │
 │                        │ 8. Success response│
 │                        │←───────────────────┤
 │ 9. Success "Reload"    │                    │
 │←──────────────────────│                    │
 │                        │                    │
 ✓ Fingerprint registered
```

## Login Flow

```
User                    Browser              Server
 │                        │                    │
 │ 1. Click Fingerprint   │                    │
 │    Auth button         │                    │
 ├──────────────────────→ │                    │
 │                        │ 2. GET /login/     │
 │                        │       start/       │
 │                        ├───────────────────→│
 │                        │                    │
 │                        │ 3. Return options  │
 │                        │    + challenge     │
 │                        │←───────────────────┤
 │                        │                    │
 │ 4. Scan fingerprint    │                    │
 │                        │                    │
 │← ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│                    │
 │ (WebAuthn API)         │                    │
 │ retrieves credential   │                    │
 │                        │                    │
 │ 5. Send credential     │                    │
 │    + proof             │                    │
 ├──────────────────────→ │                    │
 │                        │ 6. POST credential │
 │                        ├───────────────────→│
 │                        │                    │
 │                        │ 7. Verify signature│
 │                        │    Check challenge │
 │                        │    Authenticate   │
 │                        │                    │
 │                        │ 8. Success response│
 │                        │←───────────────────┤
 │ 9. Redirect to         │                    │
 │    dashboard           │                    │
 │←──────────────────────│                    │
 │                        │                    │
 ✓ Logged in successfully
```

## Data Flow

### Registration Request
```json
{
  "id": "credential_id_from_device",
  "rawId": [byte array],
  "response": {
    "clientDataJSON": [byte array],
    "attestationObject": [byte array]
  },
  "type": "public-key"
}
```

### Login Request
```json
{
  "id": "known_credential_id",
  "rawId": [byte array],
  "response": {
    "authenticatorData": [byte array],
    "clientDataJSON": [byte array],
    "signature": [byte array]
  }
}
```

### Server Response (Success)
```json
{
  "success": true,
  "message": "Fingerprint registered successfully",
  "redirect": "/dashboard/"
}
```

### Server Response (Error)
```json
{
  "error": "This fingerprint is already registered",
  "code": 400
}
```

## State Transitions

### User States
```
┌─────────────┐
│ No Account  │
└──────┬──────┘
       │ Register
       ▼
┌──────────────────────────┐
│ Account Created          │
│ (Password only)          │
└──────┬───────────────────┘
       │ Register Fingerprint
       ▼
┌──────────────────────────┐
│ Account with Fingerprint │
│ (Both methods available) │
└──────┬───────────────────┘
       │ Remove Fingerprint
       ▼
┌──────────────────────────┐
│ Account (Password only)  │
│ (Back to step 2)         │
└──────────────────────────┘
```

### Session States
```
┌─────────────┐
│ Logged Out  │
└──────┬──────┘
       │ Authenticate (Password or Fingerprint)
       ▼
┌──────────────────────────┐
│ Authenticated            │
│ Session Created          │
└──────┬───────────────────┘
       │ Logout or Session Timeout
       ▼
┌─────────────┐
│ Logged Out  │
└─────────────┘
```

## Security Considerations

### Key Points
```
Device Side:
├─ Private Key
│  └─ Never leaves device
│  └─ Never transmitted
│  └─ Used only for signing
│
├─ Public Key
│  └─ Sent to server once (registration)
│  └─ Stored in database
│
└─ Credential ID
   └─ Identifies the credential
   └─ Sent with each authentication

Server Side:
├─ Public Key Storage
│  └─ Secure database
│  └─ Never exposed to JavaScript
│
├─ Challenge Verification
│  └─ Each operation uses unique challenge
│  └─ Single-use challenges
│
├─ Signature Verification
│  └─ Cryptographic signature check
│  └─ Guarantees authenticity
│
└─ Sign Count
   └─ Prevents credential cloning
   └─ Must increase on each use
```

## Threat Mitigation

```
Threat                          Mitigation
──────────────────────────────────────────────────
Password compromise            ✓ No password needed
Network eavesdropping          ✓ HTTPS + challenge-response
Credential replay              ✓ One-time challenges
Phishing attacks               ✓ Origin verification
Credential cloning             ✓ Sign count tracking
Man-in-the-middle              ✓ Cryptographic verification
Malware on device              ✓ Hardware isolation
Database breach                ✓ Only public key stored
```

## Performance Metrics

```
Operation              Time (approx)  Network Calls
─────────────────────────────────────────────────
Registration          2-5 seconds    2 (GET + POST)
Login                 2-5 seconds    2 (GET + POST)
Removal              < 1 second     1 (POST)

Database Lookups:
├─ Registration: Check existing, create new
├─ Login: Fetch credential, verify
└─ Removal: Delete credential

Average Response Time: < 100ms
Credential Verification: < 50ms
```

---

This architecture diagram shows how each component of the fingerprint authentication system works together to provide secure, convenient biometric authentication.
