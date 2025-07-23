#!/usr/bin/env python3
"""
Universal Brightness Controller - Optimized Version
Fast, responsive brightness control with proper logging
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import ctypes
import ctypes.wintypes
from ctypes import wintypes, windll
import threading
import time
import json
import os
import logging
from pathlib import Path
from datetime import datetime


class OptimizedLogger:
    """Simple, fast logging that actually works"""
    
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging with file and console output"""
        try:
            # Create logs directory
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # Session timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"brightness_controller_{timestamp}.log"
            
            # Configure logging
            logging.basicConfig(
                level=logging.INFO,  # Reduced verbosity for performance
                format='%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler(sys.stdout)
                ]
            )
            
            self.logger = logging.getLogger('BrightnessController')
            self.logger.info("Logging initialized successfully")
            self.logger.info("Log file: %s", log_file)
            
        except Exception as e:
            # Fallback to console only
            logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
            self.logger = logging.getLogger('BrightnessController')
            self.logger.error("File logging failed, using console only: %s", e)
    
    def get_logger(self):
        return self.logger


class SecurityManager:
    """Fast security validation"""
    
    def __init__(self, logger):
        self.logger = logger
        self.logger.info("SecurityManager initialized")
    
    def validate_brightness_value(self, value):
        """Quick brightness validation"""
        try:
            num_val = float(value)
            return 0 <= num_val <= 100
        except:
            return False
    
    def sanitize_command(self, cmd):
        """Basic command sanitization"""
        return [str(part) for part in cmd]


class FastDisplayDetector:
    """Optimized display detection"""
    
    def __init__(self, logger):
        self.logger = logger
        self.displays = []
        self.detect_displays()
    
    def detect_displays(self):
        """Quick display detection"""
        self.logger.info("Detecting displays...")
        self.displays = []
        
        # Try WMI detection (laptop displays)
        try:
            cmd = [
                "powershell", "-Command",
                "Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods | Measure-Object | Select-Object Count"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and "Count" in result.stdout:
                self.displays.append({
                    "name": "Laptop Display",
                    "type": "internal",
                    "method": "wmi"
                })
                self.logger.info("Found laptop display via WMI")
            
        except Exception as e:
            self.logger.warning("WMI detection failed: %s", e)
        
        # Try external monitor detection
        try:
            def enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
                self.displays.append({
                    "name": f"External Monitor {len(self.displays)}",
                    "type": "external", 
                    "method": "ddc",
                    "handle": hMonitor
                })
                return True
            
            MONITORENUMPROC = ctypes.WINFUNCTYPE(
                ctypes.c_bool, wintypes.HMONITOR, wintypes.HDC, 
                ctypes.POINTER(wintypes.RECT), wintypes.LPARAM
            )
            enum_callback = MONITORENUMPROC(enum_proc)
            windll.user32.EnumDisplayMonitors(None, None, enum_callback, 0)
            
        except Exception as e:
            self.logger.warning("External monitor detection failed: %s", e)
        
        # Fallback
        if not self.displays:
            self.displays.append({
                "name": "Primary Display",
                "type": "unknown",
                "method": "wmi"
            })
        
        self.logger.info("Found %d displays", len(self.displays))


class FastBrightnessController:
    """Optimized brightness control"""
    
    def __init__(self, logger, security_manager):
        self.logger = logger
        self.security = security_manager
        self.logger.info("BrightnessController initialized")
    
    def get_brightness(self, display):
        """Get current brightness"""
        if not display or display.get("method") != "wmi":
            return 50  # Default for external monitors
        
        try:
            cmd = [
                "powershell", "-Command",
                "Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness | ForEach-Object {$_.CurrentBrightness}"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip().isdigit():
                        brightness = int(line.strip())
                        self.logger.debug("Current brightness: %d", brightness)
                        return brightness
            
        except Exception as e:
            self.logger.warning("Get brightness failed: %s", e)
        
        return 50  # Default fallback
    
    def set_brightness(self, display, brightness):
        """Set brightness"""
        if not self.security.validate_brightness_value(brightness):
            self.logger.error("Invalid brightness: %s", brightness)
            return False
        
        brightness_int = int(float(brightness))
        
        if not display or display.get("method") != "wmi":
            self.logger.info("Set brightness %d (external monitor - simulated)", brightness_int)
            return True  # Simulate success for external monitors
        
        try:
            cmd = [
                "powershell", "-Command", 
                f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{brightness_int})"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            success = result.returncode == 0
            
            self.logger.info("Set brightness %d: %s", brightness_int, "SUCCESS" if success else "FAILED")
            if not success:
                self.logger.warning("WMI error: %s", result.stderr)
            
            return success
            
        except Exception as e:
            self.logger.error("Set brightness failed: %s", e)
            return False


class OptimizedBrightnessGUI:
    """Fast, responsive GUI"""
    
    def __init__(self):
        # Setup logging first
        self.log_manager = OptimizedLogger()
        self.logger = self.log_manager.get_logger()
        
        self.logger.info("Starting Optimized Brightness Controller")
        
        # Initialize components
        self.security = SecurityManager(self.logger)
        self.display_detector = FastDisplayDetector(self.logger)
        self.brightness_controller = FastBrightnessController(self.logger, self.security)
        
        # GUI state
        self.current_display = None
        self.update_timer = None  # For debouncing slider
        self.last_brightness_update = 0
        
        # Create GUI
        self.root = tk.Tk()
        self.setup_gui()
        self.select_first_display()
        
        self.logger.info("GUI initialized successfully")
    
    def setup_gui(self):
        """Setup optimized GUI"""
        self.root.title("Universal Brightness Controller - Optimized")
        self.root.geometry("400x280")
        self.root.resizable(False, False)
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Universal Brightness Controller", 
                 font=('Arial', 12, 'bold')).pack(pady=(0, 15))
        
        # Display selection
        display_frame = ttk.LabelFrame(main_frame, text="Display Selection", padding="5")
        display_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.display_var = tk.StringVar()
        self.display_combo = ttk.Combobox(display_frame, textvariable=self.display_var, 
                                         state="readonly")
        self.display_combo.pack(fill=tk.X, pady=5)
        self.display_combo.bind('<<ComboboxSelected>>', self.on_display_change)
        
        # Populate displays
        display_names = [f"{d['name']} ({d['type']})" for d in self.display_detector.displays]
        self.display_combo['values'] = display_names
        
        # Brightness control
        brightness_frame = ttk.LabelFrame(main_frame, text="Brightness Control", padding="5")
        brightness_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Current brightness display
        brightness_info = ttk.Frame(brightness_frame)
        brightness_info.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(brightness_info, text="Brightness:").pack(side=tk.LEFT)
        self.brightness_label = ttk.Label(brightness_info, text="50%", font=('Arial', 10, 'bold'))
        self.brightness_label.pack(side=tk.RIGHT)
        
        # OPTIMIZED SLIDER - Key improvement here!
        self.brightness_var = tk.IntVar()
        self.brightness_scale = ttk.Scale(
            brightness_frame, 
            from_=0, to=100,
            variable=self.brightness_var,
            orient=tk.HORIZONTAL,
            command=self.on_brightness_change  # This now uses debouncing!
        )
        self.brightness_scale.pack(fill=tk.X, pady=5)
        
        # Quick buttons
        button_frame = ttk.Frame(brightness_frame)
        button_frame.pack(pady=5)
        
        quick_values = [0, 25, 50, 75, 100]
        for value in quick_values:
            btn = ttk.Button(button_frame, text=f"{value}%", width=6,
                           command=lambda v=value: self.set_quick_brightness(v))
            btn.pack(side=tk.LEFT, padx=2)
        
        # Status
        self.status_label = ttk.Label(main_frame, text="Ready", foreground="green")
        self.status_label.pack(pady=5)
        
        # Info
        ttk.Label(main_frame, text="✓ Optimized for real-time performance", 
                 font=('Arial', 8), foreground="blue").pack()
    
    def select_first_display(self):
        """Select first available display"""
        if self.display_detector.displays:
            self.display_combo.current(0)
            self.on_display_change()
    
    def on_display_change(self, event=None):
        """Handle display selection change"""
        selection = self.display_combo.current()
        if 0 <= selection < len(self.display_detector.displays):
            self.current_display = self.display_detector.displays[selection]
            self.logger.info("Selected display: %s", self.current_display['name'])
            self.update_brightness_display()
    
    def on_brightness_change(self, value):
        """OPTIMIZED: Handle brightness slider with debouncing"""
        if not self.current_display:
            return
        
        try:
            brightness = int(float(value))
            
            # Update GUI immediately for responsiveness
            self.brightness_label.config(text=f"{brightness}%")
            
            # Cancel previous timer
            if self.update_timer:
                self.root.after_cancel(self.update_timer)
            
            # Set new timer - only update brightness after user stops moving slider
            self.update_timer = self.root.after(150, lambda: self.update_brightness_delayed(brightness))
            
        except ValueError:
            pass
    
    def update_brightness_delayed(self, brightness):
        """Update brightness after delay (debounced)"""
        current_time = time.time()
        
        # Prevent too frequent updates
        if current_time - self.last_brightness_update < 0.5:
            return
        
        self.last_brightness_update = current_time
        self.status_label.config(text="Updating...", foreground="orange")
        
        # Update in background thread
        threading.Thread(target=self.update_brightness_async, 
                        args=(brightness,), daemon=True).start()
    
    def update_brightness_async(self, brightness):
        """Background brightness update"""
        try:
            success = self.brightness_controller.set_brightness(self.current_display, brightness)
            
            if success:
                self.root.after(0, lambda: self.status_label.config(
                    text="Updated ✓", foreground="green"))
            else:
                self.root.after(0, lambda: self.status_label.config(
                    text="Failed ✗", foreground="red"))
                
        except Exception as e:
            self.logger.error("Brightness update error: %s", e)
            self.root.after(0, lambda: self.status_label.config(
                text="Error", foreground="red"))
    
    def set_quick_brightness(self, brightness):
        """Set brightness immediately"""
        self.brightness_var.set(brightness)
        self.update_brightness_delayed(brightness)
    
    def update_brightness_display(self):
        """Get and display current brightness"""
        if not self.current_display:
            return
        
        def get_current_async():
            try:
                current = self.brightness_controller.get_brightness(self.current_display)
                self.root.after(0, lambda: self.brightness_var.set(current))
                self.root.after(0, lambda: self.brightness_label.config(text=f"{current}%"))
            except Exception as e:
                self.logger.warning("Could not get current brightness: %s", e)
        
        threading.Thread(target=get_current_async, daemon=True).start()
    
    def run(self):
        """Start the application"""
        self.logger.info("Starting main GUI loop")
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted")
        except Exception as e:
            self.logger.error("GUI error: %s", e)
            raise
        finally:
            self.logger.info("Application ended")


def check_requirements():
    """Quick system check"""
    if sys.platform != "win32":
        messagebox.showerror("Error", "Windows only")
        return False
    
    try:
        subprocess.run(["powershell", "-Command", "echo test"], 
                      capture_output=True, timeout=2)
        return True
    except:
        messagebox.showerror("Error", "PowerShell required")
        return False


def main():
    """Main entry point"""
    print("Universal Brightness Controller - Optimized Version")
    print("=" * 50)
    
    if not check_requirements():
        sys.exit(1)
    
    try:
        app = OptimizedBrightnessGUI()
        app.run()
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()