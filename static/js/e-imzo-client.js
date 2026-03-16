/**
 * JS library for E-IMZO operations
 * Connects with local E-IMZO proxy (127.0.0.1:64443 or similar)
 */
const EIMZOClient = (function() {
    let ws = null;
    let wsFallbackPorts = [64443, 64443];
    let wsCurrentPort = null;
    let domain = '127.0.0.1';
    
    // Default implementation wrapped into Promise based API
    // Connect to WebSocket
    function connect() {
        return new Promise((resolve, reject) => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                resolve(ws);
                return;
            }
            
            let portIndex = 0;
            
            function tryConnect() {
                if (portIndex >= wsFallbackPorts.length) {
                    reject(new Error("Cannot connect to E-IMZO WebSocket"));
                    return;
                }
                
                const port = wsFallbackPorts[portIndex];
                const url = `wss://${domain}:${port}/service/cryptapi`;
                
                try {
                    ws = new WebSocket(url);
                    
                    ws.onopen = function() {
                        wsCurrentPort = port;
                        resolve(ws);
                    };
                    
                    ws.onerror = function() {
                        portIndex++;
                        tryConnect();
                    };
                } catch (e) {
                    portIndex++;
                    tryConnect();
                }
            }
            
            tryConnect();
        });
    }

    // Send command to WS
    function sendCommand(command, params = {}) {
        return new Promise((resolve, reject) => {
            connect().then((socket) => {
                const nonce = Date.now().toString() + Math.random().toString().substring(2);
                
                const messageHandler = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        if (data.plugin === command || data.reason) {
                            socket.removeEventListener('message', messageHandler);
                            if (data.success) {
                                resolve(data);
                            } else {
                                reject(new Error(data.reason || "Unknown error"));
                            }
                        }
                    } catch (e) {
                        // Ignore parse errors from other messages
                    }
                };
                
                socket.addEventListener('message', messageHandler);
                
                // Add timeout
                setTimeout(() => {
                    socket.removeEventListener('message', messageHandler);
                    reject(new Error("Timeout waiting for E-IMZO response"));
                }, 10000); // 10s timeout
                
                socket.send(JSON.stringify({
                    plugin: command,
                    ...params
                }));
            }).catch(reject);
        });
    }

    // Public API
    return {
        ping: function() {
            // Check if service is alive
            return connect();
        },
        
        listAllUserKeys: async function() {
            // E-IMZO command to get certificates (pfx)
            const res = await sendCommand("pfx", { name: "list_all_certificates" });
            if (res && res.certificates) {
                // Filter only valid ones, or return all
                return res.certificates;
            }
            return [];
        },
        
        extractKeyInfo: function(certObj) {
            // Normally cert string has `CN=..., SN=..., TIN=..., UID=...`
            let name = "Noma'lum";
            let pinfl = "";
            let inn = "";
            
            if (certObj && certObj.alias) {
               name = certObj.alias;
            }

            if (certObj && certObj.vo) {
                const subject = certObj.vo.subjectName || "";
                
                // Parse SUBJECT
                const parts = subject.split(',');
                parts.forEach(part => {
                    const kv = part.split('=');
                    if (kv.length >= 2) {
                        const k = kv[0].trim();
                        const v = kv[1].trim();
                        
                        if (k === 'CN') name = v;
                        if (k === 'UID' || k === 'PINFL' || k === '1.2.860.3.16.1.2') pinfl = v;
                        if (k === 'tin' || k === 'TIN' || k === '1.2.860.3.16.1.1') inn = v;
                    }
                });
            }
            
            return { name, pinfl, inn };
        },

        createPkcs7: async function(certSerialNumber, textToSign) {
            // 1. Get auth UI (if EImzo needs to prompt pin inside its own window) 
            // NOTE: Usually in modern E-IMZO you just send create_pkcs7 and it handles the PIN modal
            const res = await sendCommand("pfx", {
                name: "create_pkcs7",
                serial_number: certSerialNumber,
                text: btoa(unescape(encodeURIComponent(textToSign))) // Base64 encode the string
            });
            
            if (res && res.pkcs7_64) {
                return res.pkcs7_64;
            }
            
            throw new Error("Failed to create PKCS7");
        }
    };
})();
