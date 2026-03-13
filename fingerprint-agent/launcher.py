import sys
import os
import threading
import time
import json
import webview

# Prevent console window flashing if --noconsole is used
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def add_dll_to_path():
    """Add the directory containing libzkfp.dll to the system path"""
    dll_dir = resource_path('')
    if dll_dir not in os.environ['PATH']:
        os.environ['PATH'] = dll_dir + os.pathsep + os.environ['PATH']
    os.chdir(dll_dir)

add_dll_to_path()

# Now import agent
import agent

def run_flask_server():
    try:
        agent.run_agent()
    except Exception as e:
        agent.logger.error(f"Server crashed: {e}")

def on_closing():
    """Called when the webview window is closed by the user"""
    agent.logger.info("Agent dasturi webview orqali yopilmoqda...")
    try:
        agent.scanner.close()
    except:
        pass
    os._exit(0)

if __name__ == '__main__':
    agent.logger.info("Initializing Agent via Webview Launcher...")
    
    # Initialize scanner
    if agent.scanner.initialize():
        agent.scanner.detect_and_open()
    
    # Start flask in daemon thread
    server_thread = threading.Thread(target=run_flask_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(1)
    
    # Read config for site URL
    site_url = 'https://lombard-hujjatlari.onrender.com'
    exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(exe_dir, 'config.json')
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            site_url = config.get('site_url', site_url)
        except Exception as e:
            agent.logger.error(f"Error reading config: {e}")
    else:
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({'site_url': site_url}, f, indent=4)
        except:
            pass

    # Enable file downloads in pywebview
    webview.settings['ALLOW_DOWNLOADS'] = True

    # Create native window embedding the website
    window = webview.create_window(
        title='UzLombard',
        url=site_url,
        width=1280,
        height=850,
        min_size=(900, 600),
        text_select=True,
        zoomable=True,
        maximized=True
    )
    
    # Handle window close
    window.events.closed += on_closing
    
    # Start webview loop (blocks until closed)
    webview.start(private_mode=False)
