/**
 * Fingerprint Authentication with Local Scanner
 * JavaScript client for ZKTeco USB fingerprint scanner integration
 * 
 * Arxitektura: JS brauzerda agent (localhost:8001) bilan to'g'ridan-to'g'ri gaplashadi,
 * keyin natijani Django serverga (Render) yuboradi.
 */

class FingerprintScannerClient {
    constructor(options = {}) {
        this.agentUrl = options.agentUrl || 'http://127.0.0.1:8001';
        this.csrfToken = this.getCSRFToken();
        this.isCapturing = false;
        this.lastQuality = 0;
        
        console.log('FingerprintScannerClient initialized, agent:', this.agentUrl);
    }
    
    // ========================================================================
    // UTILITY METHODS
    // ========================================================================
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
               document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1] ||
               '';
    }
    
    async makeAgentRequest(endpoint, options = {}) {
        /** Agent'ga (localhost:8001) so'rov yuborish */
        const url = `${this.agentUrl}${endpoint}`;
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...(options.headers || {})
            }
        });
        const data = await response.json();
        return { status: response.status, data };
    }
    
    async makeDjangoRequest(url, options = {}) {
        /** Django serverga so'rov yuborish */
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.csrfToken,
                ...(options.headers || {})
            },
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
            statusEl.style.display = 'block';
        }
        // Also update fp-status if exists (scanner_register.html)
        const fpStatus = document.getElementById('fp-status');
        const fpStatusText = document.getElementById('fp-status-text');
        if (fpStatus && fpStatusText) {
            fpStatus.classList.remove('d-none');
            fpStatusText.textContent = message;
        }
    }
    
    setError(message) {
        console.error(message);
        const errorEl = document.getElementById('fingerprint-error');
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.style.display = 'block';
            errorEl.classList.remove('d-none');
        }
        // Also update fp-error if exists (scanner_register.html)
        const fpError = document.getElementById('fp-error');
        const fpErrorText = document.getElementById('fp-error-text');
        if (fpError && fpErrorText) {
            fpError.classList.remove('d-none');
            fpErrorText.textContent = message;
        }
        this.setStatus(message, 'error');
    }
    
    clearError() {
        const errorEl = document.getElementById('fingerprint-error');
        if (errorEl) {
            errorEl.style.display = 'none';
            errorEl.classList.add('d-none');
        }
        const fpError = document.getElementById('fp-error');
        if (fpError) fpError.classList.add('d-none');
        
        const fpStatus = document.getElementById('fp-status');
        if (fpStatus) fpStatus.classList.add('d-none');
    }
    
    // ========================================================================
    // AGENT HEALTH CHECK — to'g'ridan-to'g'ri agentga murojaat
    // ========================================================================
    
    async checkAgentHealth() {
        try {
            const { status, data } = await this.makeAgentRequest('/api/status');
            if (status === 200) {
                // Also check scanner detection
                let scannerDetected = false;
                try {
                    const detectResp = await this.makeAgentRequest('/api/scanner/detect');
                    scannerDetected = detectResp.status === 200 && 
                        (detectResp.data.detected || detectResp.data.success);
                } catch(e) {
                    console.warn('Scanner detect failed:', e);
                }
                
                return {
                    agent_running: true,
                    scanner_detected: scannerDetected,
                    agent_version: data.version || 'unknown'
                };
            }
            return { agent_running: false, scanner_detected: false };
        } catch (e) {
            console.error('Agent health check failed:', e);
            return { agent_running: false, scanner_detected: false };
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
    // FINGERPRINT REGISTRATION — agent'dan template olish, Django'ga yuborish
    // ========================================================================
    
    async startRegistration() {
        this.clearError();
        this.setStatus("Agent va skaner tekshirilmoqda...", 'info');
        
        try {
            // To'g'ridan-to'g'ri agent'ni tekshirish
            const health = await this.checkAgentHealth();
            if (!health.agent_running) {
                this.setError("Barmoq izi agenti ishlamayapti. Uni ishga tushiring.");
                return false;
            }
            
            if (!health.scanner_detected) {
                this.setError("Skaner topilmadi. USB skanerni ulang.");
                return false;
            }
            
            this.setStatus("Skaner tayyor!", 'success');
            return true;
            
        } catch (e) {
            this.setError(`Xatolik: ${e.message}`);
            return false;
        }
    }
    
    async completeRegistration(fingerPosition = 'right_index') {
        this.setStatus("Barmog'ingizni skanerga 3 marta qo'ying... Kutilmoqda...", 'info');
        
        try {
            // Step 1: Agent'da 3x capture va register qilish
            const { status: agentStatus, data: agentData } = await this.makeAgentRequest(
                '/api/fingerprint/register',
                {
                    method: 'POST',
                    body: JSON.stringify({ captures_needed: 3 })
                }
            );
            
            if (agentStatus !== 200) {
                this.setError(agentData.error || "Ro'yxatdan o'tkazish muvaffaqiyatsiz");
                return false;
            }
            
            const template = agentData.template;
            const quality = agentData.quality || 0;
            
            if (!template) {
                this.setError("Agent shablon qaytarmadi");
                return false;
            }
            
            this.setStatus("Barmoq izi olinDi! Saqlanmoqda...", 'info');
            
            // Step 2: Template'ni Django serverga yuborish
            const { status: djangoStatus, data: djangoData } = await this.makeDjangoRequest(
                '/api/auth/fingerprint/register/complete',
                {
                    method: 'POST',
                    body: JSON.stringify({
                        template: template,
                        quality: quality,
                        finger_position: fingerPosition
                    })
                }
            );
            
            if (djangoStatus !== 200) {
                this.setError(djangoData.error || "Saqlashda xatolik");
                return false;
            }
            
            this.setStatus("Barmoq izi muvaffaqiyatli ro'yxatdan o'tkazildi!", 'success');
            
            if (djangoData.redirect) {
                setTimeout(() => {
                    window.location.href = djangoData.redirect;
                }, 1500);
            }
            
            return true;
            
        } catch (e) {
            this.setError(`Xatolik: ${e.message}`);
            return false;
        }
    }
    
    // ========================================================================
    // FINGERPRINT AUTHENTICATION/LOGIN
    // Flow: Django'dan stored_template olish -> Agent'da capture+verify -> Django'ga tasdiqlash
    // ========================================================================
    
    async authenticateWithFingerprint(username) {
        this.clearError();
        this.setStatus("Autentifikatsiya tayyorlanmoqda...", 'info');
        
        try {
            // Step 1: Agent tekshirish
            const health = await this.checkAgentHealth();
            if (!health.agent_running) {
                this.setError("Barmoq izi agenti ishlamayapti.");
                return false;
            }
            
            // Step 2: Django'dan stored_template olish
            this.setStatus("Foydalanuvchi tekshirilmoqda...", 'info');
            const { status: authStatus, data: authData } = await this.makeDjangoRequest(
                '/api/auth/fingerprint/authenticate',
                {
                    method: 'POST',
                    body: JSON.stringify({ username: username.trim() })
                }
            );
            
            if (authStatus !== 200) {
                this.setError(authData.error || "Autentifikatsiya xatoligi");
                return false;
            }
            
            const storedTemplate = authData.stored_template;
            if (!storedTemplate) {
                this.setError("Saqlangan shablon topilmadi");
                return false;
            }
            
            // Step 3: Agent'da barmoq izini olish
            this.setStatus("Barmog'ingizni skanerga qo'ying...", 'info');
            const { status: captureStatus, data: captureData } = await this.makeAgentRequest(
                '/api/fingerprint/capture'
            );
            
            if (captureStatus !== 200) {
                this.setError(captureData.error || "Barmoq izini olishda xatolik");
                return false;
            }
            
            const capturedTemplate = captureData.template;
            
            // Step 4: Agent'da verify qilish
            this.setStatus("Barmoq izi tekshirilmoqda...", 'info');
            const { status: verifyStatus, data: verifyData } = await this.makeAgentRequest(
                '/api/fingerprint/verify',
                {
                    method: 'POST',
                    body: JSON.stringify({
                        stored_template: storedTemplate,
                        current_template: capturedTemplate,
                        threshold: 50
                    })
                }
            );
            
            if (verifyStatus !== 200 || !verifyData.match) {
                this.setError("Barmoq izi mos kelmadi");
                return false;
            }
            
            // Step 5: Django'ga tasdiqlash (login)
            this.setStatus("Tizimga kirilmoqda...", 'info');
            const { status: confirmStatus, data: confirmData } = await this.makeDjangoRequest(
                '/api/auth/fingerprint/auth/confirm',
                {
                    method: 'POST',
                    body: JSON.stringify({
                        username: username.trim(),
                        match: true,
                        score: verifyData.score || 0
                    })
                }
            );
            
            if (confirmStatus !== 200) {
                this.setError(confirmData.error || "Tizimga kirishda xatolik");
                return false;
            }
            
            this.setStatus("Muvaffaqiyatli kirdingiz! Yo'naltirilmoqda...", 'success');
            
            if (confirmData.redirect) {
                setTimeout(() => {
                    window.location.href = confirmData.redirect;
                }, 1000);
            }
            
            return true;
            
        } catch (e) {
            this.setError(`Xatolik: ${e.message}`);
            return false;
        }
    }
    
    // Legacy methods for backward compatibility
    async startAuthentication(username) {
        return this.authenticateWithFingerprint(username);
    }
    
    async verifyFingerprint(username) {
        // This is now handled by authenticateWithFingerprint
        return true;
    }
    
    // ========================================================================
    // FINGERPRINT VERIFICATION FOR SIGNING
    // Flow: Django'dan stored_template -> Agent capture+verify -> Django tasdiqlash
    // ========================================================================
    
    async verifyForSigning() {
        this.clearError();
        this.setStatus("Barmoq izi tekshirilmoqda...", 'info');
        
        try {
            // Step 1: Agent tekshirish
            const health = await this.checkAgentHealth();
            if (!health.agent_running) {
                this.setError("Barmoq izi agenti ishlamayapti.");
                return false;
            }
            
            // Step 2: Django'dan stored_template olish
            const { status: tplStatus, data: tplData } = await this.makeDjangoRequest(
                '/api/auth/fingerprint/verify-signing',
                {
                    method: 'POST',
                    body: JSON.stringify({ action: 'get_template' })
                }
            );
            
            if (tplStatus !== 200) {
                this.setError(tplData.error || "Shablon olishda xatolik");
                return false;
            }
            
            const storedTemplate = tplData.stored_template;
            
            // Step 3: Agent'da capture
            this.setStatus("Barmog'ingizni skanerga qo'ying...", 'info');
            const { status: captureStatus, data: captureData } = await this.makeAgentRequest(
                '/api/fingerprint/capture'
            );
            
            if (captureStatus !== 200) {
                this.setError(captureData.error || "Barmoq izini olishda xatolik");
                return false;
            }
            
            // Step 4: Agent'da verify
            this.setStatus("Tekshirilmoqda...", 'info');
            const { status: verifyStatus, data: verifyData } = await this.makeAgentRequest(
                '/api/fingerprint/verify',
                {
                    method: 'POST',
                    body: JSON.stringify({
                        stored_template: storedTemplate,
                        current_template: captureData.template,
                        threshold: 50
                    })
                }
            );
            
            if (verifyStatus !== 200 || !verifyData.match) {
                this.setError("Barmoq izi mos kelmadi");
                return false;
            }
            
            // Step 5: Django'ga tasdiqlash
            const { status: confirmStatus, data: confirmData } = await this.makeDjangoRequest(
                '/api/auth/fingerprint/verify-signing',
                {
                    method: 'POST',
                    body: JSON.stringify({
                        action: 'confirm',
                        match: true,
                        score: verifyData.score || 0
                    })
                }
            );
            
            if (confirmStatus !== 200) {
                this.setError(confirmData.error || "Tasdiqlashda xatolik");
                return false;
            }
            
            this.setStatus("Barmoq izi tasdiqlandi!", 'success');
            return true;
            
        } catch (e) {
            this.setError(`Xatolik: ${e.message}`);
            return false;
        }
    }
    
    // ========================================================================
    // FINGERPRINT REMOVAL
    // ========================================================================
    
    async removeFingerprint() {
        if (!confirm("Barmoq izi autentifikatsiyasini o'chirmoqchimisiz?")) {
            return false;
        }
        
        this.setStatus("Barmoq izi o'chirilmoqda...", 'info');
        
        try {
            const { status, data } = await this.makeDjangoRequest(
                '/api/auth/fingerprint/remove',
                { method: 'POST' }
            );
            
            if (status !== 200) {
                this.setError(data.error || "O'chirishda xatolik");
                return false;
            }
            
            this.setStatus("Barmoq izi muvaffaqiyatli o'chirildi!", 'success');
            setTimeout(() => window.location.reload(), 1500);
            return true;
            
        } catch (e) {
            this.setError(`Xatolik: ${e.message}`);
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

async function handleLoginClick() {
    const username = document.getElementById('fingerprint-username')?.value;
    
    if (!username) {
        fingerprintScanner.setError('Loginingizni kiriting');
        return;
    }
    
    const btn = document.getElementById('login-fingerprint-btn');
    btn.disabled = true;
    
    const success = await fingerprintScanner.authenticateWithFingerprint(username);
    
    if (!success) {
        btn.disabled = false;
    }
}

// Export for use in other scripts
window.FingerprintScannerClient = FingerprintScannerClient;
window.fingerprintScanner = fingerprintScanner;
