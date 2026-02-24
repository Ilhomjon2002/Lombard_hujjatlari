"""
Windows Service Installation Script
Creates a Windows service for Fingerprint Authentication Agent
"""

import os
import sys
import logging
from pathlib import Path

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
except ImportError:
    print("ERROR: pywin32 not installed")
    print("Please install it with: pip install pywin32")
    sys.exit(1)

# Configure logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "service.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FingerprintAgentService(win32serviceutil.ServiceFramework):
    """Windows Service for Fingerprint Authentication Agent"""
    
    _svc_name_ = "FingerprintAgent"
    _svc_display_name_ = "Fingerprint Authentication Agent"
    _svc_description_ = "Local agent for fingerprint authentication with ZKTeco USB scanners"
    
    def __init__(self, *args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_alive = True
        self.agent_process = None
    
    def SvcStop(self):
        """Stop the service"""
        logger.info("Service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False
    
    def SvcDoRun(self):
        """Run the service"""
        try:
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, '')
            )
            logger.info("Fingerprint Authentication Agent service started")
            
            # Run the agent
            import subprocess
            agent_script = Path(__file__).parent / "agent.py"
            python_exe = sys.executable
            
            self.agent_process = subprocess.Popen(
                [python_exe, str(agent_script)],
                cwd=str(Path(__file__).parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            logger.info(f"Agent process started with PID: {self.agent_process.pid}")
            
            # Wait until service is stopped
            while self.is_alive:
                win32event.WaitForMultipleObjects(
                    (self.hWaitStop,), False, 10000
                )
            
        except Exception as e:
            logger.error(f"Service error: {e}")
            servicemanager.LogErrorMsg(f"Error in service: {e}")
        
        finally:
            # Stop the agent process
            if self.agent_process:
                try:
                    self.agent_process.terminate()
                    self.agent_process.wait(timeout=5)
                except:
                    self.agent_process.kill()
            
            logger.info("Fingerprint Authentication Agent service stopped")


def install_service():
    """Install the Windows service"""
    try:
        logger.info("Installing Fingerprint Authentication Agent service...")
        
        # Get the path to Python executable (venv ichidagi python.exe bo'lsa ham ishlaydi)
        python_path = sys.executable
        # __file__ bu install_service.py fayli, shuning uchun agent.py ni ishlatish uchun to'g'ri yo'lni hisoblang
        # Agar agent.py shu papkada bo'lsa:
        script_path = os.path.join(os.path.dirname(__file__), "agent.py")
        win32serviceutil.InstallService(
            pythonClassString = "agent.FingerprintAgentService",   # ← agent.py fayl nomi.agent ichidagi class
            serviceName       = FingerprintAgentService._svc_name_,
            displayName       = FingerprintAgentService._svc_display_name_,
            startType         = win32service.SERVICE_AUTO_START,
            # description       = "...",   # ba'zi versiyalarda xato beradi, olib tashlang
        )
        # Install the service – pythonClassString ni STRING qilib bering!
        # win32serviceutil.InstallService(
        #     pythonClassString = "__main__.FingerprintAgentService",  # ← TO'G'RI – string!
        #     # yoki agar FingerprintAgentService class agent.py da bo'lsa:
        #     # pythonClassString = "agent.FingerprintAgentService"
            
        #     serviceName = FingerprintAgentService._svc_name_,
        #     displayName = FingerprintAgentService._svc_display_name_,
        #     startType = win32service.SERVICE_AUTO_START,   # ixtiyoriy, qo'shish mumkin
        #     # exePath va rawArgs ni qo'shmang – ular bu versiyada kerak emas va xato berishi mumkin
        #     # serviceDescription ni ham qo'shmang (agar eski pywin32 bo'lsa)
        # )
        
        logger.info("Service installed successfully")
        print("✓ Fingerprint Authentication Agent service installed successfully")
        print(f"  Service name: {FingerprintAgentService._svc_name_}")
        print("\n  To start the service, run:")
        print(f"    net start {FingerprintAgentService._svc_name_}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to install service: {e}")
        print(f"✗ Error installing service: {e}")
        return False

def remove_service():
    """Remove the Windows service"""
    try:
        logger.info("Removing Fingerprint Authentication Agent service...")
        
        # Stop the service first
        try:
            win32serviceutil.StopService(FingerprintAgentService._svc_name_)
            logger.info("Service stopped")
        except:
            pass
        
        # Remove the service
        win32serviceutil.RemoveService(FingerprintAgentService._svc_name_)
        
        logger.info("Service removed successfully")
        print("✓ Fingerprint Authentication Agent service removed successfully")
        
        return True
    except Exception as e:
        logger.error(f"Failed to remove service: {e}")
        print(f"✗ Error removing service: {e}")
        return False


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'install':
            sys.exit(0 if install_service() else 1)
        elif sys.argv[1] == 'remove':
            sys.exit(0 if remove_service() else 1)
    
    # If running as service
    win32serviceutil.HandleCommandLine(FingerprintAgentService)
