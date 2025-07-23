"""
Logging Configuration Module
Centralizes all logging setup with separate files for each component
"""

import logging
import sys
import os
from pathlib import Path
from datetime import datetime


class LoggingConfig:
    """Centralized logging configuration following Single Responsibility Principle"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def get_log_formatter(self):
        """Get standardized log formatter"""
        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
    
    def setup_component_logger(self, component_name, level=logging.DEBUG):
        """Setup logger for a specific component with its own file"""
        logger = logging.getLogger(component_name)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
            
        logger.setLevel(level)
        formatter = self.get_log_formatter()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Component-specific file handler
        component_log_file = self.log_dir / f"{component_name}_{self.session_id}.log"
        file_handler = logging.FileHandler(component_log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Master log file handler (all components)
        master_log_file = self.log_dir / f"brightness_controller_{self.session_id}.log"
        master_handler = logging.FileHandler(master_log_file)
        master_handler.setLevel(logging.DEBUG)
        master_handler.setFormatter(formatter)
        logger.addHandler(master_handler)
        
        logger.info("Logger initialized for component: %s", component_name)
        logger.info("Component log file: %s", component_log_file)
        
        return logger


# Global logging config instance
_logging_config = None


def setup_logging():
    """Setup main application logging and return main logger"""
    global _logging_config
    _logging_config = LoggingConfig()
    
    # Setup main application logger
    main_logger = _logging_config.setup_component_logger('BrightnessController.Main')
    main_logger.info("Logging system initialized")
    main_logger.info("Log directory: %s", _logging_config.log_dir.absolute())
    main_logger.info("Session ID: %s", _logging_config.session_id)
    
    return main_logger


def get_component_logger(component_name):
    """Get logger for a specific component"""
    global _logging_config
    if _logging_config is None:
        _logging_config = LoggingConfig()
    
    return _logging_config.setup_component_logger(f'BrightnessController.{component_name}')