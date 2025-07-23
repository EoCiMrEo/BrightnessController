"""
System Checker Module
Validates system requirements and compatibility
Single Responsibility: System validation only
"""

import sys
import subprocess
import platform
from tkinter import messagebox
from typing import Dict, List, Tuple
from core.logging_config import get_component_logger


class SystemChecker:
    """
    Handles system requirements validation
    Follows Single Responsibility Principle - only checks system compatibility
    """
    
    def __init__(self):
        self.logger = get_component_logger('SystemChecker')
        self.logger.info("SystemChecker initialized")
        
        self.requirements = {
            'platform': 'win32',
            'python_version': (3, 6),
            'powershell': True,
            'tkinter': True
        }
        
        self.logger.debug("System requirements: %s", self.requirements)
    
    def check_platform(self) -> Tuple[bool, str]:
        """Check if running on supported platform"""
        self.logger.debug("Checking platform compatibility")
        
        current_platform = sys.platform
        required_platform = self.requirements['platform']
        
        is_compatible = current_platform == required_platform
        
        message = f"Platform: {current_platform}"
        if not is_compatible:
            message = f"Unsupported platform: {current_platform}, requires: {required_platform}"
            self.logger.error(message)
        else:
            self.logger.info("Platform check passed: %s", current_platform)
        
        return is_compatible, message
    
    def check_python_version(self) -> Tuple[bool, str]:
        """Check if Python version meets requirements"""
        self.logger.debug("Checking Python version")
        
        current_version = sys.version_info[:2]
        required_version = self.requirements['python_version']
        
        is_compatible = current_version >= required_version
        
        current_str = f"{current_version[0]}.{current_version[1]}"
        required_str = f"{required_version[0]}.{required_version[1]}"
        
        message = f"Python version: {current_str}"
        if not is_compatible:
            message = f"Python {current_str} not supported, requires: {required_str}+"
            self.logger.error(message)
        else:
            self.logger.info("Python version check passed: %s", current_str)
        
        return is_compatible, message
    
    def check_powershell(self) -> Tuple[bool, str]:
        """Check if PowerShell is available and accessible"""
        self.logger.debug("Checking PowerShell availability")
        
        try:
            self.logger.debug("Testing PowerShell with simple command")
            result = subprocess.run(
                ["powershell", "-Command", "echo 'test'"], 
                capture_output=True, 
                text=True,
                timeout=5
            )
            
            self.logger.debug("PowerShell test result: code=%d, stdout='%s', stderr='%s'", 
                             result.returncode, result.stdout.strip(), result.stderr.strip())
            
            is_available = result.returncode == 0 and 'test' in result.stdout
            
            if is_available:
                self.logger.info("PowerShell check passed")
                return True, "PowerShell: Available"
            else:
                error_msg = f"PowerShell test failed: code={result.returncode}, stderr='{result.stderr}'"
                self.logger.error(error_msg)
                return False, "PowerShell: Not accessible"
                
        except subprocess.TimeoutExpired:
            error_msg = "PowerShell test timed out"
            self.logger.error(error_msg)
            return False, "PowerShell: Timeout"
        except FileNotFoundError:
            error_msg = "PowerShell executable not found"
            self.logger.error(error_msg)
            return False, "PowerShell: Not found"
        except Exception as e:
            error_msg = f"PowerShell test error: {e}"
            self.logger.error(error_msg)
            return False, f"PowerShell: Error - {e}"
    
    def check_tkinter(self) -> Tuple[bool, str]:
        """Check if Tkinter is available"""
        self.logger.debug("Checking Tkinter availability")
        
        try:
            import tkinter as tk
            
            # Try to create a hidden test window
            test_root = tk.Tk()
            test_root.withdraw()  # Hide the window
            test_root.destroy()
            
            self.logger.info("Tkinter check passed")
            return True, "Tkinter: Available"
            
        except ImportError as e:
            error_msg = f"Tkinter import failed: {e}"
            self.logger.error(error_msg)
            return False, f"Tkinter: Import error - {e}"
        except Exception as e:
            error_msg = f"Tkinter test failed: {e}"
            self.logger.error(error_msg)
            return False, f"Tkinter: Error - {e}"
    
    def check_wmi_support(self) -> Tuple[bool, str]:
        """Check if WMI brightness support is available"""
        self.logger.debug("Checking WMI brightness support")
        
        try:
            self.logger.debug("Testing WMI brightness query")
            result = subprocess.run([
                "powershell", "-Command",
                "Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness -ErrorAction SilentlyContinue | Measure-Object | Select-Object Count"
            ], capture_output=True, text=True, timeout=10)
            
            self.logger.debug("WMI test result: code=%d, stdout='%s'", result.returncode, result.stdout)
            
            if result.returncode == 0:
                # Look for count information
                if 'Count' in result.stdout:
                    self.logger.info("WMI brightness support detected")
                    return True, "WMI Brightness: Supported"
                else:
                    self.logger.warning("WMI accessible but no brightness support found")
                    return False, "WMI Brightness: No devices found"
            else:
                self.logger.warning("WMI brightness query failed")
                return False, "WMI Brightness: Query failed"
                
        except subprocess.TimeoutExpired:
            self.logger.warning("WMI brightness test timed out")
            return False, "WMI Brightness: Timeout"
        except Exception as e:
            self.logger.warning("WMI brightness test error: %s", e)
            return False, f"WMI Brightness: Error - {e}"
    
    def get_system_info(self) -> Dict[str, str]:
        """Get detailed system information"""
        self.logger.debug("Gathering system information")
        
        info = {
            'platform': sys.platform,
            'python_version': sys.version,
            'architecture': platform.architecture()[0],
            'machine': platform.machine(),
            'processor': platform.processor(),
            'windows_version': '',
        }
        
        try:
            if sys.platform == 'win32':
                info['windows_version'] = platform.version()
        except Exception as e:
            self.logger.debug("Could not get Windows version: %s", e)
        
        self.logger.info("System info gathered: %s", {k: v[:50] + '...' if len(str(v)) > 50 else v for k, v in info.items()})
        return info
    
    def check_all_requirements(self) -> bool:
        """
        Check all system requirements
        
        Returns:
            bool: True if all requirements are met
        """
        self.logger.info("Starting comprehensive system requirements check")
        
        checks = [
            ("Platform", self.check_platform),
            ("Python Version", self.check_python_version),
            ("PowerShell", self.check_powershell),
            ("Tkinter", self.check_tkinter),
        ]
        
        results = []
        all_passed = True
        
        for check_name, check_func in checks:
            self.logger.debug("Running check: %s", check_name)
            try:
                passed, message = check_func()
                results.append((check_name, passed, message))
                
                if passed:
                    self.logger.info("✓ %s: %s", check_name, message)
                else:
                    self.logger.error("✗ %s: %s", check_name, message)
                    all_passed = False
                    
            except Exception as e:
                error_msg = f"Check failed with exception: {e}"
                self.logger.error("✗ %s: %s", check_name, error_msg)
                results.append((check_name, False, error_msg))
                all_passed = False
        
        # Optional checks (don't fail if these don't pass)
        self.logger.debug("Running optional checks")
        wmi_passed, wmi_message = self.check_wmi_support()
        results.append(("WMI Brightness (Optional)", wmi_passed, wmi_message))
        
        if wmi_passed:
            self.logger.info("✓ WMI Brightness: %s", wmi_message)
        else:
            self.logger.warning("! WMI Brightness: %s", wmi_message)
        
        # Show results
        if all_passed:
            self.logger.info("All required system checks passed!")
        else:
            self.logger.error("Some system checks failed!")
            
            # Show error dialog for failed requirements
            failed_checks = [f"• {name}: {msg}" for name, passed, msg in results if not passed and "Optional" not in name]
            if failed_checks:
                error_message = "System requirements not met:\n\n" + "\n".join(failed_checks)
                error_message += "\n\nPlease install missing components and try again."
                messagebox.showerror("System Requirements Error", error_message)
        
        # Log system info
        system_info = self.get_system_info()
        self.logger.info("System Information:")
        for key, value in system_info.items():
            self.logger.info("  %s: %s", key, value)
        
        return all_passed