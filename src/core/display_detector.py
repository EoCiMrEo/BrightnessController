"""
Display Detector Module
Detects and categorizes available displays
Single Responsibility: Display detection only
"""

import subprocess
import ctypes
import ctypes.wintypes
from ctypes import wintypes, windll
from typing import List, Dict, Optional
from core.logging_config import get_component_logger


class DisplayInfo:
    """Data class for display information"""
    
    def __init__(self, name: str, display_type: str, method: str, **kwargs):
        self.name = name
        self.type = display_type
        self.method = method
        self.properties = kwargs
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for compatibility"""
        result = {
            'name': self.name,
            'type': self.type,
            'method': self.method
        }
        result.update(self.properties)
        return result
    
    def __str__(self):
        return f"Display({self.name}, {self.type}, {self.method})"


class WMIDisplayDetector:
    """Detects laptop/internal displays via WMI"""
    
    def __init__(self):
        self.logger = get_component_logger('DisplayDetector.WMI')
        self.logger.debug("WMI Display Detector initialized")
    
    def detect_displays(self) -> List[DisplayInfo]:
        """Detect WMI-compatible displays"""
        self.logger.info("Starting WMI display detection")
        displays = []
        
        # Try to detect brightness methods first
        brightness_displays = self._detect_brightness_methods()
        displays.extend(brightness_displays)
        
        # Try to detect brightness current values
        current_displays = self._detect_current_brightness()
        
        # Merge results (avoid duplicates)
        for current_display in current_displays:
            if not any(d.name == current_display.name for d in displays):
                displays.append(current_display)
        
        self.logger.info("WMI detection complete: %d displays found", len(displays))
        return displays
    
    def _detect_brightness_methods(self) -> List[DisplayInfo]:
        """Detect displays that support brightness methods"""
        self.logger.debug("Detecting WMI brightness methods")
        displays = []
        
        try:
            # Fixed PowerShell command (added missing space)
            cmd = [
                "powershell", "-Command",
                "Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods | Select-Object InstanceName"
            ]
            
            self.logger.debug("Executing PowerShell command: %s", ' '.join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            self.logger.debug("PowerShell return code: %d", result.returncode)
            self.logger.debug("PowerShell stdout: %s", result.stdout[:500])
            self.logger.debug("PowerShell stderr: %s", result.stderr[:500])
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                self.logger.debug("Processing %d output lines", len(lines))
                
                # Skip header lines
                data_lines = [line for line in lines[2:] if line.strip() and not line.startswith('-')]
                
                for i, line in enumerate(data_lines):
                    self.logger.debug("Processing line %d: '%s'", i, line.strip())
                    if line.strip():
                        display_info = DisplayInfo(
                            name=f"Laptop Display {i + 1}",
                            display_type="internal",
                            method="wmi",
                            instance=line.strip(),
                            supports_brightness_methods=True
                        )
                        displays.append(display_info)
                        self.logger.info("Added WMI brightness method display: %s", display_info)
            else:
                self.logger.warning("WMI brightness methods query failed or returned no results")
                
        except subprocess.TimeoutExpired:
            self.logger.error("WMI brightness methods query timed out after 10 seconds")
        except subprocess.SubprocessError as e:
            self.logger.error("WMI brightness methods subprocess error: %s", e)
        except Exception as e:
            self.logger.error("Unexpected error in WMI brightness methods detection: %s", e)
        
        self.logger.debug("WMI brightness methods detection complete: %d displays", len(displays))
        return displays
    
    def _detect_current_brightness(self) -> List[DisplayInfo]:
        """Detect displays with current brightness values"""
        self.logger.debug("Detecting WMI current brightness")
        displays = []
        
        try:
            # Fixed PowerShell command (added missing space)
            cmd = [
                "powershell", "-Command",
                "Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness | Select-Object InstanceName, CurrentBrightness"
            ]
            
            self.logger.debug("Executing PowerShell command: %s", ' '.join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            self.logger.debug("PowerShell return code: %d", result.returncode)
            self.logger.debug("PowerShell stdout: %s", result.stdout[:500])
            self.logger.debug("PowerShell stderr: %s", result.stderr[:500])
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                self.logger.debug("Processing %d output lines", len(lines))
                
                # Skip header lines and process data
                data_lines = [line for line in lines[2:] if line.strip() and not line.startswith('-')]
                
                for i, line in enumerate(data_lines):
                    self.logger.debug("Processing line %d: '%s'", i, line.strip())
                    if line.strip():
                        display_info = DisplayInfo(
                            name=f"Laptop Display {i + 1}",
                            display_type="internal",
                            method="wmi",
                            instance=line.strip(),
                            supports_current_brightness=True
                        )
                        displays.append(display_info)
                        self.logger.info("Added WMI current brightness display: %s", display_info)
            else:
                self.logger.warning("WMI current brightness query failed or returned no results")
                
        except subprocess.TimeoutExpired:
            self.logger.error("WMI current brightness query timed out after 10 seconds")
        except subprocess.SubprocessError as e:
            self.logger.error("WMI current brightness subprocess error: %s", e)
        except Exception as e:
            self.logger.error("Unexpected error in WMI current brightness detection: %s", e)
        
        self.logger.debug("WMI current brightness detection complete: %d displays", len(displays))
        return displays


class DDCDisplayDetector:
    """Detects external displays via DDC/CI"""
    
    def __init__(self):
        self.logger = get_component_logger('DisplayDetector.DDC')
        self.logger.debug("DDC Display Detector initialized")
    
    def detect_displays(self) -> List[DisplayInfo]:
        """Detect DDC/CI compatible displays"""
        self.logger.info("Starting DDC display detection")
        displays = []
        
        def enum_display_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
            try:
                self.logger.debug("Found monitor handle: %s", hMonitor)
                
                display_info = DisplayInfo(
                    name=f"External Monitor {len(displays) + 1}",
                    display_type="external",
                    method="ddc",
                    handle=hMonitor,
                    rect_info=lprcMonitor.contents if lprcMonitor else None
                )
                
                displays.append(display_info)
                self.logger.info("Added DDC display: %s", display_info)
                
            except Exception as e:
                self.logger.error("Error processing monitor handle %s: %s", hMonitor, e)
            return True
        
        try:
            self.logger.debug("Setting up monitor enumeration callback")
            MONITORENUMPROC = ctypes.WINFUNCTYPE(
                ctypes.c_bool, 
                wintypes.HMONITOR, 
                wintypes.HDC, 
                ctypes.POINTER(wintypes.RECT), 
                wintypes.LPARAM
            )
            enum_proc = MONITORENUMPROC(enum_display_proc)
            
            self.logger.debug("Starting monitor enumeration")
            result = windll.user32.EnumDisplayMonitors(None, None, enum_proc, 0)
            self.logger.debug("Monitor enumeration result: %s", result)
            
        except Exception as e:
            self.logger.error("Error during monitor enumeration: %s", e)
        
        self.logger.info("DDC detection complete: %d displays found", len(displays))
        return displays


class DisplayDetector:
    """
    Main display detector that coordinates different detection methods
    Follows Single Responsibility Principle - only detects displays
    """
    
    def __init__(self):
        self.logger = get_component_logger('DisplayDetector')
        self.logger.info("Initializing DisplayDetector")
        
        self.wmi_detector = WMIDisplayDetector()
        self.ddc_detector = DDCDisplayDetector()
        
        self.displays = []
        self.detect_displays()
        
        self.logger.info("DisplayDetector initialized with %d displays", len(self.displays))
    
    def detect_displays(self) -> None:
        """Detect all available displays using all methods"""
        self.logger.info("Starting comprehensive display detection")
        self.displays = []
        
        # Method 1: WMI for laptop displays
        self.logger.debug("Detecting WMI displays (laptop/internal)")
        wmi_displays = self.wmi_detector.detect_displays()
        self.displays.extend(wmi_displays)
        self.logger.info("Found %d WMI displays", len(wmi_displays))
        
        # Method 2: DDC/CI for external displays
        self.logger.debug("Detecting DDC displays (external)")
        ddc_displays = self.ddc_detector.detect_displays()
        self.displays.extend(ddc_displays)
        self.logger.info("Found %d DDC displays", len(ddc_displays))
        
        # Fallback if no displays detected
        if not self.displays:
            self.logger.warning("No displays detected, using fallback")
            fallback_display = DisplayInfo(
                name="Primary Display",
                display_type="unknown",
                method="wmi",
                is_fallback=True
            )
            self.displays.append(fallback_display)
        
        # Log all detected displays
        self.logger.info("Total displays detected: %d", len(self.displays))
        for i, display in enumerate(self.displays):
            self.logger.info("Display %d: %s", i, display)
    
    def get_displays(self) -> List[Dict]:
        """Get list of displays as dictionaries for compatibility"""
        return [display.to_dict() for display in self.displays]
    
    def get_display_by_index(self, index: int) -> Optional[Dict]:
        """Get display by index as dictionary"""
        if 0 <= index < len(self.displays):
            return self.displays[index].to_dict()
        return None
    
    def refresh_displays(self) -> None:
        """Refresh display detection"""
        self.logger.info("Refreshing display detection")
        self.detect_displays()