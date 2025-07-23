"""
Brightness Controller Module
Handles brightness control for different display types
Single Responsibility: Brightness control only
"""

import subprocess
from typing import Dict, Optional, Union
from core.logging_config import get_component_logger
from core.security_manager import SecurityManager


class WMIBrightnessController:
    """Handles WMI-based brightness control for laptop displays"""
    
    def __init__(self, security_manager: SecurityManager):
        self.logger = get_component_logger('BrightnessController.WMI')
        self.security = security_manager
        self.logger.info("WMI Brightness Controller initialized")
    
    def get_brightness(self, display: Dict) -> Optional[int]:
        """Get current brightness via WMI"""
        self.logger.debug("Getting WMI brightness for display: %s", display.get('name'))
        
        try:
            # Use security manager to create safe command
            cmd = self.security.create_safe_wmi_command(
                namespace="root/WMI",
                class_name="WmiMonitorBrightness"
            )
            
            if not cmd:
                self.logger.error("Failed to create safe WMI command for get brightness")
                return None
            
            # Modify command to select CurrentBrightness
            cmd[-1] = cmd[-1] + " | Select-Object CurrentBrightness"
            
            self.logger.debug("Executing PowerShell command: %s", ' '.join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            self.logger.debug("Get brightness return code: %d", result.returncode)
            self.logger.debug("Get brightness stdout: %s", result.stdout)
            self.logger.debug("Get brightness stderr: %s", result.stderr)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                self.logger.debug("Processing %d output lines", len(lines))
                
                for i, line in enumerate(lines):
                    self.logger.debug("Line %d: '%s'", i, line.strip())
                    line_stripped = line.strip()
                    
                    # Look for numeric values
                    if line_stripped and line_stripped.isdigit():
                        brightness = int(line_stripped)
                        self.logger.info("Current WMI brightness: %d", brightness)
                        return brightness
                    
                    # Handle formatted output like "CurrentBrightness : 50"
                    if ':' in line_stripped:
                        parts = line_stripped.split(':')
                        if len(parts) >= 2 and parts[1].strip().isdigit():
                            brightness = int(parts[1].strip())
                            self.logger.info("Current WMI brightness (formatted): %d", brightness)
                            return brightness
                
                self.logger.warning("No valid brightness value found in WMI output")
            else:
                self.logger.error("WMI get brightness failed with return code %d", result.returncode)
                if result.stderr:
                    self.logger.error("WMI error: %s", result.stderr)
                    
        except subprocess.TimeoutExpired:
            self.logger.error("WMI get brightness timed out")
        except Exception as e:
            self.logger.error("Error getting WMI brightness: %s", e)
            
        self.logger.debug("WMI get brightness returned None")
        return None
    
    def set_brightness(self, display: Dict, brightness: int) -> bool:
        """Set brightness via WMI"""
        self.logger.info("Setting WMI brightness to %d for display: %s", brightness, display.get('name'))
        
        # Validate brightness value using security manager
        if not self.security.validate_brightness_value(brightness):
            self.logger.error("Invalid brightness value: %d", brightness)
            return False
        
        try:
            # Use security manager to create safe command
            cmd = self.security.create_safe_wmi_command(
                namespace="root/WMI",
                class_name="WmiMonitorBrightnessMethods",
                method="WmiSetBrightness",
                parameters=f"1,{brightness}"
            )
            
            if not cmd:
                self.logger.error("Failed to create safe WMI command for set brightness")
                return False
            
            self.logger.debug("Executing PowerShell command: %s", ' '.join(cmd))
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            self.logger.debug("Set brightness return code: %d", result.returncode)
            self.logger.debug("Set brightness stdout: %s", result.stdout)
            self.logger.debug("Set brightness stderr: %s", result.stderr)
            
            success = result.returncode == 0
            self.logger.info("WMI set brightness to %d: %s", brightness, "SUCCESS" if success else "FAILED")
            
            if not success and result.stderr:
                self.logger.error("WMI set brightness error: %s", result.stderr)
            
            return success
            
        except subprocess.TimeoutExpired:
            self.logger.error("WMI set brightness timed out")
            return False
        except Exception as e:
            self.logger.error("Error setting WMI brightness: %s", e)
            return False


class DDCBrightnessController:
    """Handles DDC/CI-based brightness control for external monitors"""
    
    def __init__(self, security_manager: SecurityManager):
        self.logger = get_component_logger('BrightnessController.DDC')
        self.security = security_manager
        self.logger.info("DDC Brightness Controller initialized")
        self.logger.warning("DDC/CI implementation is placeholder - requires hardware-specific implementation")
    
    def get_brightness(self, display: Dict) -> Optional[int]:
        """Get brightness via DDC/CI (placeholder implementation)"""
        self.logger.debug("Getting DDC brightness for display: %s", display.get('name'))
        
        # TODO: Implement actual DDC/CI communication
        # This requires low-level Windows API calls and hardware support
        # For now, return a placeholder value
        
        placeholder_brightness = 50
        self.logger.info("DDC get brightness placeholder returning: %d", placeholder_brightness)
        return placeholder_brightness
    
    def set_brightness(self, display: Dict, brightness: int) -> bool:
        """Set brightness via DDC/CI (placeholder implementation)"""
        self.logger.info("Setting DDC brightness to %d for display: %s", brightness, display.get('name'))
        
        # Validate brightness value
        if not self.security.validate_brightness_value(brightness):
            self.logger.error("Invalid brightness value: %d", brightness)
            return False
        
        # TODO: Implement actual DDC/CI communication
        # This would involve:
        # 1. Opening handle to monitor
        # 2. Sending DDC/CI commands
        # 3. Setting VCP code 0x10 (brightness)
        
        self.logger.info("DDC set brightness placeholder returning success")
        return True


class BrightnessController:
    """
    Main brightness controller that coordinates different control methods
    Follows Single Responsibility Principle - only controls brightness
    Depends on SecurityManager (Dependency Inversion Principle)
    """
    
    def __init__(self, security_manager: SecurityManager):
        self.logger = get_component_logger('BrightnessController')
        self.logger.info("Initializing BrightnessController")
        
        self.security = security_manager
        self.wmi_controller = WMIBrightnessController(security_manager)
        self.ddc_controller = DDCBrightnessController(security_manager)
        
        # Controller mapping based on display method
        self.controllers = {
            'wmi': self.wmi_controller,
            'ddc': self.ddc_controller
        }
        
        self.logger.info("BrightnessController initialized with %d controllers", len(self.controllers))
    
    def get_brightness(self, display: Dict) -> Optional[int]:
        """
        Get current brightness for a display
        
        Args:
            display: Display information dictionary
            
        Returns:
            Optional[int]: Current brightness (0-100) or None if failed
        """
        self.logger.debug("Getting brightness for display: %s", display)
        
        if not display:
            self.logger.warning("No display provided to get_brightness")
            return None
        
        method = display.get("method", "wmi")
        self.logger.debug("Using method: %s", method)
        
        controller = self.controllers.get(method)
        if not controller:
            self.logger.error("No controller available for method: %s", method)
            return None
        
        try:
            result = controller.get_brightness(display)
            self.logger.info("Got brightness %s for display %s using method %s", 
                           result, display.get("name"), method)
            return result
        except Exception as e:
            self.logger.error("Error getting brightness: %s", e)
            return None
    
    def set_brightness(self, display: Dict, brightness: Union[int, float, str]) -> bool:
        """
        Set brightness for a display
        
        Args:
            display: Display information dictionary
            brightness: Brightness value (0-100)
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("Setting brightness to %s for display: %s", brightness, display)
        
        if not display:
            self.logger.warning("No display provided to set_brightness")
            return False
        
        # Convert and validate brightness value
        try:
            brightness_int = int(float(brightness))
        except (ValueError, TypeError) as e:
            self.logger.error("Invalid brightness value type: %s, error: %s", brightness, e)
            return False
        
        if not self.security.validate_brightness_value(brightness_int):
            self.logger.error("Invalid brightness value: %d", brightness_int)
            return False
        
        method = display.get("method", "wmi")
        self.logger.debug("Using method: %s", method)
        
        controller = self.controllers.get(method)
        if not controller:
            self.logger.error("No controller available for method: %s", method)
            return False
        
        try:
            result = controller.set_brightness(display, brightness_int)
            self.logger.info("Set brightness result: %s for display %s using method %s", 
                           result, display.get("name"), method)
            return result
        except Exception as e:
            self.logger.error("Error setting brightness: %s", e)
            return False
    
    def test_brightness_support(self, display: Dict) -> Dict[str, bool]:
        """
        Test what brightness operations are supported for a display
        
        Args:
            display: Display information dictionary
            
        Returns:
            Dict[str, bool]: Dictionary of supported operations
        """
        self.logger.debug("Testing brightness support for display: %s", display.get('name'))
        
        support_info = {
            'get_brightness': False,
            'set_brightness': False,
            'method_available': False
        }
        
        method = display.get("method", "wmi")
        controller = self.controllers.get(method)
        
        if controller:
            support_info['method_available'] = True
            
            # Test get brightness
            try:
                current = controller.get_brightness(display)
                support_info['get_brightness'] = current is not None
            except Exception as e:
                self.logger.debug("Get brightness test failed: %s", e)
            
            # Test set brightness (try to set to current value if available)
            if support_info['get_brightness']:
                try:
                    result = controller.set_brightness(display, current)
                    support_info['set_brightness'] = result
                except Exception as e:
                    self.logger.debug("Set brightness test failed: %s", e)
        
        self.logger.info("Brightness support for %s: %s", display.get('name'), support_info)
        return support_info