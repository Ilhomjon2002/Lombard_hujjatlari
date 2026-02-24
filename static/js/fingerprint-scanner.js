/**
 * Fingerprint Authentication with Local Scanner
 * JavaScript client for ZKTeco USB fingerprint scanner integration
 */

class FingerprintScannerClient {
    constructor(options = {}) {
        this.agentUrl = options.agentUrl || 'http://127.0.0.1:8001';
        this.csrfToken = this.getCSRFToken();
        this.isCapturing = false;
        this.lastQuality = 0;
        
        console.log('FingerprintScannerClient initialized');
    }
    
    // ========================================================================
    // UTILITY METHODS
    // ========================================================================
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] ||
               '';
    }
    
    async makeRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken
            }
        };
        
        const response = await fetch(url, {
            ...defaultOptions,
            ...options
        });
        
        const data = await response.json();
        return { status: response.status, data };
    }
    
    setStatus(message, type = 'info') {
        console.log(`[${type}] ${message}`);
        const statusEl = document.getElementById('fingerprint-status');
        if (statusEl) {
            statusEl.textContent = message;
            statusEl.className = `fingerprint-status status-${type}`;
        }
    }
    
    setError(message) {
        console.error(message);
        const errorEl = document.getElementById('fingerprint-error');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
        }
        this.setStatus(message, 'error');
    }
    
    clearError() {
        const errorEl = document.getElementById('fingerprint-error');
        if (errorEl) {
            errorEl.style.display = 'none';
        }
    }
    
    // ========================================================================
    // AGENT HEALTH CHECK
    // ========================================================================
    
    async checkAgentHealth() {
        try {
            const response = await fetch('/api/auth/scanner/status');
            const data = await response.json();
            return data;
        } catch (e) {
            console.error('Agent health check failed:', e);
            return { agent_running: false };
        }
    }
    
    async waitForScanner(timeout = 10000) {
        const startTime = Date.now();
        while (Date.now() - startTime < timeout) {
            const health = await this.checkAgentHealth();
            if (health.scanner_detected) {
                return true;
            }
            await new Promise(r => setTimeout(r, 500));
        }
        return false;
    }
    
    // ========================================================================
    // FINGERPRINT REGISTRATION
    // ========================================================================
    
    async startRegistration() {
        this.clearError();
        this.setStatus('Checking fingerprint scanner...', 'info');
        
        try {
            // Check agent and scanner
            const health = await this.checkAgentHealth();
            if (!health.agent_running) {
                this.setError('Fingerprint agent is not running. Please start it first.');
                return false;
            }
            
            if (!health.scanner_detected) {
                this.setError('Fingerprint scanner not detected. Please connect the USB scanner.');
                return false;
            }
            
            // Start registration
            const { status, data } = await this.makeRequest(
                '/api/auth/fingerprint/register/start',
                { method: 'POST' }
            );
            
            if (status !== 200) {
                this.setError(data.error || 'Failed to start registration');
                return false;
            }
            
            return true;
            
        } catch (e) {
            this.setError(`Registration error: ${e.message}`);
            return false;
        }
    }
    
    async captureFingerprint(attempt = 1) {
        this.isCapturing = true;
        this.setStatus(`Capturing fingerprint (Attempt ${attempt})... Place your finger on the scanner.`, 'info');
        
        try {
            const { status, data } = await this.makeRequest(
                '/api/auth/fingerprint/capture',
                { method: 'GET' }
            );
            
            if (status !== 200) {
                this.setError(data.error || 'Fingerprint capture failed');
                return false;
            }
            
            this.lastQuality = data.quality;
            this.setStatus(`Fingerprint captured successfully (Quality: ${data.quality}%)`, 'success');
            
            return true;
            
        } catch (e) {
            this.setError(`Capture error: ${e.message}`);
            return false;
        } finally {
            this.isCapturing = false;
        }
    }
    
    async completeRegistration(fingerPosition = 'right_index') {
        this.setStatus('Saving fingerprint...', 'info');
        
        try {
            const { status, data } = await this.makeRequest(
                '/api/auth/fingerprint/register/complete',
                {
                    method: 'POST',
                    body: JSON.stringify({ finger_position: fingerPosition })
                }
            );
            
            if (status !== 200) {
                this.setError(data.error || 'Failed to save fingerprint');
                return false;
            }
            
            this.setStatus('Fingerprint registered successfully!', 'success');
            
            if (data.redirect) {
                setTimeout(() => {
                    window.location.href = data.redirect;
                }, 1500);
            }
            
            return true;
            
        } catch (e) {
            this.setError(`Registration completion error: ${e.message}`);
            return false;
        }
    }
    
    // ========================================================================
    // FINGERPRINT AUTHENTICATION/LOGIN
    // ========================================================================
    
    async startAuthentication(username) {
        this.clearError();
        this.setStatus('Preparing fingerprint authentication...', 'info');
        
        try {
            const { status, data } = await this.makeRequest(
                '/api/auth/fingerprint/authenticate',
                {
                    method: 'POST',
                    body: JSON.stringify({ username: username.trim() })
                }
            );
            
            if (status !== 200) {
                this.setError(data.error || 'Authentication initialization failed');
                return false;
            }
            
            this.setStatus(data.message, 'info');
            return true;
            
        } catch (e) {
            this.setError(`Authentication error: ${e.message}`);
            return false;
        }
    }
    
    async verifyFingerprint(username, attempt = 1) {
        this.isCapturing = true;
        this.setStatus(`Verifying fingerprint (Attempt ${attempt})... Place your finger on the scanner.`, 'info');
        
        try {
            const { status, data } = await this.makeRequest(
                '/api/auth/fingerprint/verify',
                {
                    method: 'POST',
                    body: JSON.stringify({ username: username.trim() })
                }
            );
            
            if (status === 200) {
                this.setStatus('Authentication successful! Redirecting...', 'success');
                
                if (data.redirect) {
                    setTimeout(() => {
                        window.location.href = data.redirect;
                    }, 1500);
                }
                
                return true;
            } else {
                this.setError(data.error || 'Fingerprint verification failed');
                return false;
            }
            
        } catch (e) {
            this.setError(`Verification error: ${e.message}`);
            return false;
        } finally {
            this.isCapturing = false;
        }
    }
    
    // ========================================================================
    // FINGERPRINT REMOVAL
    // ========================================================================
    
    async removeFingerprint() {
        if (!confirm('Are you sure you want to remove fingerprint authentication?')) {
            return false;
        }
        
        this.setStatus('Removing fingerprint...', 'info');
        
        try {
            const { status, data } = await this.makeRequest(
                '/api/auth/fingerprint/remove',
                { method: 'POST' }
            );
            
            if (status !== 200) {
                this.setError(data.error || 'Failed to remove fingerprint');
                return false;
            }
            
            this.setStatus('Fingerprint removed successfully!', 'success');
            setTimeout(() => window.location.reload(), 1500);
            return true;
            
        } catch (e) {
            this.setError(`Removal error: ${e.message}`);
            return false;
        }
    }
}

// ============================================================================
// GLOBAL INSTANCE
// ============================================================================

const fingerprintScanner = new FingerprintScannerClient();

// ============================================================================
// UI EVENT HANDLERS
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize fingerprint buttons
    const registerBtn = document.getElementById('register-fingerprint-btn');
    if (registerBtn) {
        registerBtn.addEventListener('click', handleRegisterClick);
    }
    
    const captureBtn = document.getElementById('capture-fingerprint-btn');
    if (captureBtn) {
        captureBtn.addEventListener('click', handleCaptureClick);
    }
    
    const completeBtn = document.getElementById('complete-fingerprint-btn');
    if (completeBtn) {
        completeBtn.addEventListener('click', handleCompleteClick);
    }
    
    const loginFingerprintBtn = document.getElementById('login-fingerprint-btn');
    if (loginFingerprintBtn) {
        loginFingerprintBtn.addEventListener('click', handleLoginClick);
    }
    
    const removeFingerprintBtn = document.getElementById('remove-fingerprint-btn');
    if (removeFingerprintBtn) {
        removeFingerprintBtn.addEventListener('click', () => {
            fingerprintScanner.removeFingerprint();
        });
    }
});

async function handleRegisterClick() {
    const btn = document.getElementById('register-fingerprint-btn');
    btn.disabled = true;
    
    const success = await fingerprintScanner.startRegistration();
    
    if (success) {
        // Move to capture phase
        setTimeout(() => {
            handleCaptureClick();
        }, 500);
    } else {
        btn.disabled = false;
    }
}

async function handleCaptureClick() {
    const btn = document.getElementById('capture-fingerprint-btn');
    btn.disabled = true;
    
    const success = await fingerprintScanner.captureFingerprint();
    
    if (success) {
        // Show complete button
        const completeBtn = document.getElementById('complete-fingerprint-btn');
        if (completeBtn) {
            completeBtn.style.display = 'block';
        }
    } else {
        btn.disabled = false;
    }
}

async function handleCompleteClick() {
    const fingerPosition = document.getElementById('finger-position')?.value || 'right_index';
    const btn = document.getElementById('complete-fingerprint-btn');
    btn.disabled = true;
    
    const success = await fingerprintScanner.completeRegistration(fingerPosition);
    
    if (!success) {
        btn.disabled = false;
    }
}

async function handleLoginClick() {
    const username = document.getElementById('fingerprint-username')?.value;
    
    if (!username) {
        fingerprintScanner.setError('Please enter your username');
        return;
    }
    
    const btn = document.getElementById('login-fingerprint-btn');
    btn.disabled = true;
    
    const prepared = await fingerprintScanner.startAuthentication(username);
    
    if (prepared) {
        setTimeout(() => {
            handleVerifyClick(username);
        }, 500);
    } else {
        btn.disabled = false;
    }
}

async function handleVerifyClick(username) {
    const success = await fingerprintScanner.verifyFingerprint(username);
    
    if (!success) {
        const btn = document.getElementById('login-fingerprint-btn');
        btn.disabled = false;
    }
}

// Export for use in other scripts
window.FingerprintScannerClient = FingerprintScannerClient;
window.fingerprintScanner = fingerprintScanner;
