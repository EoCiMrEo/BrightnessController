"""
Security Manager Module
Handles all security validation and sanitization operations
Single Responsibility: Security validation only
"""

import re
from typing import List, Union
from core.logging_config import get_component_logger


class SecurityManager:
    """
    Handles security validation for all system calls
    Follows Single Responsibility Principle - only handles security
    """
    
    def __init__(self):
        self.logger = get_component_logger('Security')
        self.logger.info("SecurityManager initialized")
        
        # Define safe character patterns
        self.safe_powershell_pattern = re.compile(r'^[a-zA-Z0-9\s\-_=().,:/\\]+$')
        self.safe_brightness_range = (0, 100)
        
        self.logger.debug("Security patterns configured")
    
    def validate_brightness_value(self, value: Union[int, float, str]) -> bool:
        """
        Validate brightness value is within safe range
        
        Args:
            value: Brightness value to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        self.logger.debug("Validating brightness value: %s (type: %s)", value, type(value))
        
        try:
            numeric_value = float(value)
            is_valid = self.safe_brightness_range[0] <= numeric_value <= self.safe_brightness_range[1]
            self.logger.debug("Brightness validation result: %s (value: %f)", is_valid, numeric_value)
            return is_valid
        except (ValueError, TypeError) as e:
            self.logger.warning("Invalid brightness value type: %s, error: %s", value, e)
            return False
    
    def sanitize_powershell_command(self, cmd: List[str]) -> List[str]:
        """
        Sanitize PowerShell commands to prevent injection attacks
        
        Args:
            cmd: List of command parts
            
        Returns:
            List[str]: Sanitized command parts
        """
        self.logger.debug("Sanitizing PowerShell command: %s", cmd)
        
        safe_cmd = []
        for i, part in enumerate(cmd):
            part_str = str(part)
            
            # Check against safe pattern
            if not self.safe_powershell_pattern.match(part_str):
                self.logger.warning("Potentially unsafe command part detected: %s", part_str)
                # Remove dangerous characters
                sanitized = re.sub(r'[^a-zA-Z0-9\s\-_=().,:/\\]', '', part_str)
                self.logger.debug("Sanitized part %d: '%s' -> '%s'", i, part_str, sanitized)
                safe_cmd.append(sanitized)
            else:
                safe_cmd.append(part_str)
        
        self.logger.debug("Sanitized command: %s", safe_cmd)
        return safe_cmd
    
    def validate_wmi_namespace(self, namespace: str) -> bool:
        """
        Validate WMI namespace is safe to use
        
        Args:
            namespace: WMI namespace string
            
        Returns:
            bool: True if safe, False otherwise
        """
        safe_namespaces = [
            'root/WMI',
            'root/CIMV2',
            'root/StandardCimv2'
        ]
        
        is_safe = namespace in safe_namespaces
        self.logger.debug("WMI namespace validation: '%s' -> %s", namespace, is_safe)
        
        if not is_safe:
            self.logger.warning("Unsafe WMI namespace attempted: %s", namespace)
        
        return is_safe
    
    def validate_wmi_class(self, class_name: str) -> bool:
        """
        Validate WMI class name is safe to use
        
        Args:
            class_name: WMI class name
            
        Returns:
            bool: True if safe, False otherwise
        """
        safe_classes = [
            'WmiMonitorBrightness',
            'WmiMonitorBrightnessMethods',
            'Win32_DesktopMonitor',
            'Win32_VideoController'
        ]
        
        is_safe = class_name in safe_classes
        self.logger.debug("WMI class validation: '%s' -> %s", class_name, is_safe)
        
        if not is_safe:
            self.logger.warning("Unsafe WMI class attempted: %s", class_name)
        
        return is_safe
    
    def create_safe_wmi_command(self, namespace: str, class_name: str, method: str = None, 
                               parameters: str = None) -> List[str]:
        """
        Create a safe WMI command with validation
        
        Args:
            namespace: WMI namespace
            class_name: WMI class name
            method: Optional method name
            parameters: Optional method parameters
            
        Returns:
            List[str]: Safe PowerShell command or empty list if invalid
        """
        self.logger.debug("Creating safe WMI command: namespace=%s, class=%s, method=%s", 
                         namespace, class_name, method)
        
        # Validate inputs
        if not self.validate_wmi_namespace(namespace):
            self.logger.error("Invalid WMI namespace: %s", namespace)
            return []
        
        if not self.validate_wmi_class(class_name):
            self.logger.error("Invalid WMI class: %s", class_name)
            return []
        
        # Build command
        if method:
            if parameters:
                wmi_query = f"(Get-WmiObject -Namespace {namespace} -Class {class_name}).{method}({parameters})"
            else:
                wmi_query = f"(Get-WmiObject -Namespace {namespace} -Class {class_name}).{method}()"
        else:
            wmi_query = f"Get-WmiObject -Namespace {namespace} -Class {class_name}"
        
        cmd = ["powershell", "-Command", wmi_query]
        
        # Sanitize the command
        safe_cmd = self.sanitize_powershell_command(cmd)
        
        self.logger.info("Created safe WMI command: %s", safe_cmd)
        return safe_cmd