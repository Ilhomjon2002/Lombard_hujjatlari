"""
Fingerprint Authentication Local Agent
For ZKTeco USB Fingerprint Scanner (Live20R / SLK20R / ZK9500)
Uses pyzkfp SDK (ZKFP2)
"""

import os
import sys
import json
import logging
import base64
import time
from datetime import datetime
from pathlib import Path

# Third-party imports
from flask import Flask, jsonify, request
from flask_cors import CORS

# Configure logging — use exe directory when frozen, else script directory
if getattr(sys, 'frozen', False):
    LOG_DIR = Path(sys.executable).parent / "logs"
else:
    LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# SECTION 1: ZKFP2 SCANNER WRAPPER
# ============================================================================

class ZKFPScanner:
    """Wrapper for ZKTeco fingerprint scanner using pyzkfp SDK"""
    
    def __init__(self):
        self.zkfp2 = None
        self.device_handle = None
        self.is_initialized = False
        self.is_open = False
        logger.info("ZKFPScanner created")
    
    def initialize(self):
        """Initialize the ZKFP2 SDK"""
        try:
            from pyzkfp import ZKFP2
            self.zkfp2 = ZKFP2()
            self.zkfp2.Init()
            self.is_initialized = True
            logger.info("ZKFP2 SDK initialized successfully")
            return True
        except ImportError:
            logger.error("pyzkfp not installed. Install with: pip install pyzkfp")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize ZKFP2: {e}")
            return False
    
    def detect_and_open(self):
        """Detect and open the first available scanner device"""
        if not self.is_initialized:
            if not self.initialize():
                return False
        
        try:
            device_count = self.zkfp2.GetDeviceCount()
            logger.info(f"Detected {device_count} fingerprint device(s)")
            
            if device_count == 0:
                self.is_open = False
                return False
            
            # Open first device
            self.device_handle = self.zkfp2.OpenDevice(0)
            self.is_open = True
            logger.info("Fingerprint scanner opened successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error detecting/opening scanner: {e}")
            self.is_open = False
            return False
    
    def capture(self, timeout=10):
        """
        Capture a single fingerprint.
        Returns (template_bytes, quality) or (None, error_message)
        """
        if not self.is_open:
            return None, "Scanner not open"
        
        try:
            # AcquireFingerprint returns (template, width, height) or raises
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    capture_result = self.zkfp2.AcquireFingerprint()
                    if capture_result:
                        template = capture_result[0]
                        # Pythonnet may return byte[] as a tuple of ints
                        if isinstance(template, tuple):
                            template = bytes(template)
                        logger.info(f"Fingerprint captured. Type: {type(template)}, Length: {len(template) if hasattr(template, '__len__') else 'N/A'}")
                        return template, None
                except Exception:
                    pass
                time.sleep(0.2)
            
            return None, "Timeout: barmoq izi olinmadi"
            
        except Exception as e:
            logger.error(f"Capture error: {e}")
            return None, str(e)
    
    def register(self, num_captures=3):
        """
        Register a fingerprint by capturing N times and generating a registration template.
        Returns (reg_template_b64, quality) or (None, error_message)
        """
        if not self.is_open:
            return None, "Scanner not open"
        
        try:
            templates = []
            for i in range(num_captures):
                logger.info(f"Waiting for capture {i+1}/{num_captures}...")
                template, error = self.capture(timeout=15)
                if template is None:
                    return None, f"Capture {i+1} failed: {error}"
                templates.append(template)
                logger.info(f"Capture {i+1}/{num_captures} successful")
                if i < num_captures - 1:
                    time.sleep(0.5)  # brief pause between captures
            
            # Generate registration template from 3 captures using DBMerge
            reg_template, _ = self.zkfp2.DBMerge(templates[0], templates[1], templates[2])
            
            if reg_template is None:
                return None, "Shablon yaratishda xatolik (DBMerge failed)"
            
            # Convert to base64 for transport
            if isinstance(reg_template, bytes):
                template_b64 = base64.b64encode(reg_template).decode()
            else:
                template_b64 = base64.b64encode(bytes(reg_template)).decode()
            
            logger.info("Registration template generated successfully")
            return template_b64, None
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return None, str(e)
    
    def verify(self, stored_template_b64, captured_template_b64=None, threshold=50):
        """
        Verify fingerprint against stored template.
        If captured_template_b64 is None, will capture a new one.
        Returns (match, score) or (None, error_message)
        """
        if not self.is_open:
            return None, "Scanner not open"
        
        try:
            # Decode stored template
            stored_bytes = base64.b64decode(stored_template_b64)
            
            # Get current fingerprint
            if captured_template_b64:
                current_bytes = base64.b64decode(captured_template_b64)
            else:
                current_bytes, error = self.capture(timeout=10)
                if current_bytes is None:
                    return None, error
            
            # Match templates
            score = self.zkfp2.DBMatch(stored_bytes, current_bytes)
            match = score >= threshold
            
            logger.info(f"Verification result: match={match}, score={score}, threshold={threshold}")
            return {"match": match, "score": score}, None
            
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return None, str(e)
    
    def close(self):
        """Close device and terminate SDK"""
        try:
            if self.is_open and self.zkfp2:
                self.zkfp2.CloseDevice()
                self.is_open = False
            if self.is_initialized and self.zkfp2:
                self.zkfp2.Terminate()
                self.is_initialized = False
            logger.info("Scanner closed")
        except Exception as e:
            logger.error(f"Error closing scanner: {e}")
    
    def get_status(self):
        """Get scanner status"""
        return {
            "initialized": self.is_initialized,
            "connected": self.is_open,
            "device": "ZKTeco USB Scanner"
        }


# ============================================================================
# SECTION 2: FLASK REST API
# ============================================================================

app = Flask(__name__)
CORS(app)

# Global scanner instance
scanner = ZKFPScanner()


@app.route('/api/status', methods=['GET'])
def api_status():
    """Get agent status"""
    return jsonify({
        "status": "running",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "scanner": scanner.get_status()
    }), 200


@app.route('/api/scanner/detect', methods=['GET', 'POST'])
def api_detect_scanner():
    """Detect and open fingerprint scanner"""
    try:
        detected = scanner.detect_and_open()
        return jsonify({
            "detected": detected,
            "message": "Skaner topildi" if detected else "Skaner topilmadi",
            "status": scanner.get_status()
        }), 200 if detected else 404
    except Exception as e:
        logger.error(f"Scanner detection error: {e}")
        return jsonify({"detected": False, "error": str(e)}), 500


@app.route('/api/fingerprint/capture', methods=['GET'])
def api_capture():
    """Capture single fingerprint"""
    try:
        if not scanner.is_open:
            # Try to auto-detect
            scanner.detect_and_open()
        
        if not scanner.is_open:
            return jsonify({"error": "Skaner ulanmagan"}), 400
        
        template, error = scanner.capture(timeout=10)
        
        if template is None:
            return jsonify({"error": error or "Barmoq izini olishda xatolik"}), 400
        
        # Convert to base64 for transport
        if isinstance(template, bytes):
            template_b64 = base64.b64encode(template).decode()
        else:
            template_b64 = base64.b64encode(bytes(template)).decode()
        
        return jsonify({
            "status": "captured",
            "template": template_b64,
            "quality": 80  # pyzkfp doesn't expose quality directly
        }), 200
        
    except Exception as e:
        logger.error(f"Capture error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/fingerprint/register', methods=['POST'])
def api_register():
    """Register fingerprint (3x capture + generate registration template)"""
    try:
        if not scanner.is_open:
            scanner.detect_and_open()
        
        if not scanner.is_open:
            return jsonify({"error": "Skaner ulanmagan"}), 400
        
        data = request.json or {}
        num_captures = data.get('captures_needed', 3)
        
        template_b64, error = scanner.register(num_captures=num_captures)
        
        if template_b64 is None:
            return jsonify({"error": error or "Ro'yxatdan o'tkazish muvaffaqiyatsiz"}), 400
        
        return jsonify({
            "template": template_b64,
            "quality": 80,
            "status": "registered"
        }), 200
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/fingerprint/verify', methods=['POST'])
def api_verify():
    """Verify captured fingerprint against stored template"""
    try:
        if not scanner.is_open:
            scanner.detect_and_open()
        
        if not scanner.is_open:
            return jsonify({"error": "Skaner ulanmagan"}), 400
        
        data = request.json
        if not data:
            return jsonify({"error": "Ma'lumot kerak"}), 400
        
        stored_template = data.get('stored_template')
        current_template = data.get('current_template')
        threshold = data.get('threshold', 50)
        
        if not stored_template:
            return jsonify({"error": "Saqlangan shablon kerak"}), 400
        
        result, error = scanner.verify(
            stored_template_b64=stored_template,
            captured_template_b64=current_template,
            threshold=threshold
        )
        
        if result is None:
            return jsonify({"error": error}), 400
        
        return jsonify({
            "match": result["match"],
            "score": result["score"],
            "threshold": threshold
        }), 200
        
    except Exception as e:
        logger.error(f"Verify error: {e}")
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint topilmadi"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Server xatoligi"}), 500


# ============================================================================
# SECTION 3: MAIN ENTRY POINT
# ============================================================================

def run_agent():
    """Run Flask application"""
    logger.info("Starting Fingerprint Agent on http://127.0.0.1:8001")
    try:
        app.run(host='127.0.0.1', port=8001, debug=False, use_reloader=False)
    except Exception as e:
        logger.error(f"Failed to start agent: {e}")
    finally:
        scanner.close()


if __name__ == '__main__':
    try:
        logger.info("=" * 60)
        logger.info("Fingerprint Authentication Agent v2.0 (pyzkfp)")
        logger.info("=" * 60)
        
        # Initialize and detect scanner at startup
        logger.info("Initializing ZKFP2 SDK...")
        if scanner.initialize():
            logger.info("SDK initialized. Detecting scanner...")
            if scanner.detect_and_open():
                logger.info("Scanner ready!")
            else:
                logger.warning("Scanner not found. Connect USB scanner and it will auto-detect on next request.")
        else:
            logger.warning("SDK initialization failed. Make sure ZKFinger SDK is installed.")
        
        # Start Flask app
        run_agent()
        
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
        scanner.close()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        scanner.close()
        sys.exit(1)
