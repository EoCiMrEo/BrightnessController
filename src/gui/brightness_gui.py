"""
Brightness GUI Module
Handles the graphical user interface for brightness control
Single Responsibility: User interface only
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from core.logging_config import get_component_logger
from core.display_detector import DisplayDetector
from core.brightness_controller import BrightnessController


class SettingsManager:
    """Manages application settings persistence"""
    
    def __init__(self):
        self.logger = get_component_logger('GUI.Settings')
        self.settings_file = Path.home() / ".brightness_controller_settings.json"
        self.logger.debug("Settings file: %s", self.settings_file)
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                self.logger.info("Settings loaded: %s", settings)
                return settings
        except Exception as e:
            self.logger.warning("Error loading settings: %s", e)
        
        # Return default settings
        defaults = {
            'last_brightness': 50,
            'last_display_index': 0,
            'window_geometry': None
        }
        self.logger.debug("Using default settings: %s", defaults)
        return defaults
    
    def save_settings(self, settings: Dict[str, Any]) -> None:
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            self.logger.info("Settings saved: %s", settings)
        except Exception as e:
            self.logger.error("Error saving settings: %s", e)


class StatusDisplay:
    """Manages status display and messages"""
    
    def __init__(self, status_label: ttk.Label):
        self.logger = get_component_logger('GUI.Status')
        self.status_label = status_label
        self.logger.debug("Status display initialized")
    
    def show_success(self, message: str) -> None:
        """Show success message"""
        self.logger.info("Success: %s", message)
        self.status_label.config(text=message, foreground="green")
    
    def show_error(self, message: str) -> None:
        """Show error message"""
        self.logger.warning("Error: %s", message)
        self.status_label.config(text=message, foreground="red")
    
    def show_info(self, message: str) -> None:
        """Show info message"""
        self.logger.info("Info: %s", message)
        self.status_label.config(text=message, foreground="blue")
    
    def show_working(self, message: str = "Working...") -> None:
        """Show working message"""
        self.logger.debug("Working: %s", message)
        self.status_label.config(text=message, foreground="orange")


class BrightnessGUI:
    """
    Main GUI application for brightness control
    Follows Single Responsibility Principle - only handles user interface
    Depends on DisplayDetector and BrightnessController (Dependency Inversion)
    """
    
    def __init__(self, display_detector: DisplayDetector, brightness_controller: BrightnessController):
        self.logger = get_component_logger('GUI')
        self.logger.info("Initializing BrightnessGUI")
        
        # Dependencies (injected)
        self.display_detector = display_detector
        self.brightness_controller = brightness_controller
        
        # GUI components
        self.root = None
        self.display_combo = None
        self.brightness_var = None
        self.brightness_scale = None
        self.brightness_label = None
        self.status_display = None
        
        # State
        self.current_display = None
        self.updating = False
        
        # Settings
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load_settings()
        
        # Initialize GUI
        self._setup_window()
        self._setup_gui()
        self._apply_settings()
        self._select_initial_display()
        
        self.logger.info("BrightnessGUI initialization complete")
    
    def _setup_window(self) -> None:
        """Setup main window"""
        self.logger.debug("Setting up main window")
        
        self.root = tk.Tk()
        self.root.title("Universal Brightness Controller")
        self.root.geometry("450x350")
        self.root.resizable(False, False)
        
        # Configure window properties
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Apply saved geometry if available
        if self.settings.get('window_geometry'):
            try:
                self.root.geometry(self.settings['window_geometry'])
            except Exception as e:
                self.logger.debug("Could not apply saved geometry: %s", e)
        
        self.logger.debug("Main window setup complete")
    
    def _setup_gui(self) -> None:
        """Setup GUI components"""
        self.logger.debug("Setting up GUI components")
        
        # Configure styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Universal Brightness Controller", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Display selection
        ttk.Label(main_frame, text="Select Display:", font=('Arial', 10, 'bold')).grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        
        self.display_var = tk.StringVar()
        self.display_combo = ttk.Combobox(main_frame, textvariable=self.display_var, 
                                         state="readonly", width=40)
        self.display_combo.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        self.display_combo.bind('<<ComboboxSelected>>', self._on_display_change)
        
        # Populate display combo
        self._update_display_list()
        
        # Brightness control section
        brightness_frame = ttk.LabelFrame(main_frame, text="Brightness Control", padding="10")
        brightness_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Current brightness display
        brightness_info_frame = ttk.Frame(brightness_frame)
        brightness_info_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(brightness_info_frame, text="Current Brightness:", font=('Arial', 10)).grid(
            row=0, column=0, sticky=tk.W
        )
        
        self.brightness_label = ttk.Label(brightness_info_frame, text="50%", font=('Arial', 12, 'bold'))
        self.brightness_label.grid(row=0, column=1, sticky=tk.E)
        
        # Brightness slider
        self.brightness_var = tk.IntVar()
        self.brightness_scale = ttk.Scale(brightness_frame, from_=0, to=100, 
                                         variable=self.brightness_var,
                                         orient=tk.HORIZONTAL, length=380,
                                         command=self._on_brightness_change)
        self.brightness_scale.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        
        # Quick brightness buttons
        button_frame = ttk.Frame(brightness_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10))
        
        quick_values = [0, 25, 50, 75, 100]
        for i, value in enumerate(quick_values):
            btn = ttk.Button(button_frame, text=f"{value}%", width=8,
                           command=lambda v=value: self._set_quick_brightness(v))
            btn.grid(row=0, column=i, padx=2)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, columnspan=2, pady=(0, 15))
        
        ttk.Button(control_frame, text="Refresh Displays", 
                  command=self._refresh_displays).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="Test Support", 
                  command=self._test_brightness_support).grid(row=0, column=1, padx=5)
        
        # Status display
        self.status_label = ttk.Label(main_frame, text="Ready", foreground="green")
        self.status_label.grid(row=5, column=0, columnspan=2, pady=(0, 10))
        
        self.status_display = StatusDisplay(self.status_label)
        
        # Security info
        info_text = "✓ Secure: No network access, validated inputs only"
        ttk.Label(main_frame, text=info_text, font=('Arial', 8), foreground="blue").grid(
            row=6, column=0, columnspan=2
        )
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        brightness_frame.columnconfigure(0, weight=1)
        brightness_info_frame.columnconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        self.logger.debug("GUI components setup complete")
    
    def _update_display_list(self) -> None:
        """Update the display combo box with available displays"""
        self.logger.debug("Updating display list")
        
        displays = self.display_detector.get_displays()
        display_names = [f"{d['name']} ({d['type']})" for d in displays]
        
        self.display_combo['values'] = display_names
        self.logger.info("Display list updated: %d displays", len(display_names))
        
        for i, name in enumerate(display_names):
            self.logger.debug("Display %d: %s", i, name)
    
    def _apply_settings(self) -> None:
        """Apply loaded settings to GUI"""
        self.logger.debug("Applying settings")
        
        # Set brightness slider to last value
        last_brightness = self.settings.get('last_brightness', 50)
        self.brightness_var.set(last_brightness)
        self.brightness_label.config(text=f"{last_brightness}%")
        
        self.logger.debug("Settings applied")
    
    def _select_initial_display(self) -> None:
        """Select the initial display"""
        self.logger.debug("Selecting initial display")
        
        displays = self.display_detector.get_displays()
        if not displays:
            self.logger.warning("No displays available to select")
            self.status_display.show_error("No displays detected")
            return
        
        # Try to select last used display, or first available
        last_index = self.settings.get('last_display_index', 0)
        if 0 <= last_index < len(displays):
            self.display_combo.current(last_index)
        else:
            self.display_combo.current(0)
        
        self._on_display_change()
        self.logger.info("Initial display selected")
    
    def _on_display_change(self, event=None) -> None:
        """Handle display selection change"""
        self.logger.debug("Display selection changed")
        
        selection = self.display_combo.current()
        displays = self.display_detector.get_displays()
        
        if 0 <= selection < len(displays):
            self.current_display = displays[selection]
            self.logger.info("Selected display: %s", self.current_display['name'])
            self.status_display.show_info(f"Selected: {self.current_display['name']}")
            self._update_brightness_display()
        else:
            self.logger.warning("Invalid display selection: %d", selection)
            self.status_display.show_error("Invalid display selection")
    
    def _on_brightness_change(self, value) -> None:
        """Handle brightness slider change"""
        if self.updating:
            self.logger.debug("Ignoring brightness change during update")
            return
        
        if not self.current_display:
            self.logger.warning("No display selected for brightness change")
            return
        
        try:
            brightness = int(float(value))
            self.logger.debug("Brightness slider changed to: %d", brightness)
            
            self.brightness_label.config(text=f"{brightness}%")
            self.status_display.show_working("Updating brightness...")
            
            # Update brightness in separate thread
            threading.Thread(target=self._update_brightness_async, 
                           args=(brightness,), daemon=True).start()
            
        except ValueError as e:
            self.logger.error("Invalid brightness value: %s, error: %s", value, e)
            self.status_display.show_error("Invalid brightness value")
    
    def _update_brightness_async(self, brightness: int) -> None:
        """Update brightness asynchronously"""
        self.logger.info("Updating brightness to %d for display %s", 
                        brightness, self.current_display['name'])
        
        try:
            success = self.brightness_controller.set_brightness(self.current_display, brightness)
            
            # Update GUI in main thread
            if success:
                self.root.after(0, lambda: self.status_display.show_success("Brightness updated"))
            else:
                self.root.after(0, lambda: self.status_display.show_error("Failed to update brightness"))
                
        except Exception as e:
            self.logger.error("Error updating brightness: %s", e)
            self.root.after(0, lambda: self.status_display.show_error(f"Error: {str(e)[:30]}"))
    
    def _set_quick_brightness(self, brightness: int) -> None:
        """Set brightness to a quick value"""
        self.logger.info("Setting quick brightness to %d", brightness)
        self.brightness_var.set(brightness)
        self._on_brightness_change(brightness)
    
    def _update_brightness_display(self) -> None:
        """Update the current brightness display"""
        if not self.current_display:
            self.logger.warning("No display selected for brightness display update")
            return
        
        self.logger.debug("Updating brightness display for %s", self.current_display['name'])
        
        def update_async():
            try:
                self.updating = True
                current = self.brightness_controller.get_brightness(self.current_display)
                
                if current is not None:
                    self.root.after(0, lambda: self.brightness_var.set(current))
                    self.root.after(0, lambda: self.brightness_label.config(text=f"{current}%"))
                    self.root.after(0, lambda: self.status_display.show_info(f"Current: {current}%"))
                    self.logger.debug("Updated brightness display to %d", current)
                else:
                    self.root.after(0, lambda: self.status_display.show_error("Could not read brightness"))
                    self.logger.warning("Could not get current brightness")
                    
            except Exception as e:
                self.logger.error("Error updating brightness display: %s", e)
                self.root.after(0, lambda: self.status_display.show_error("Error reading brightness"))
            finally:
                self.updating = False
        
        threading.Thread(target=update_async, daemon=True).start()
    
    def _refresh_displays(self) -> None:
        """Refresh display detection"""
        self.logger.info("Refreshing display detection")
        self.status_display.show_working("Refreshing displays...")
        
        def refresh_async():
            try:
                self.display_detector.refresh_displays()
                self.root.after(0, self._update_display_list)
                self.root.after(0, self._select_initial_display)
                self.root.after(0, lambda: self.status_display.show_success("Displays refreshed"))
            except Exception as e:
                self.logger.error("Error refreshing displays: %s", e)
                self.root.after(0, lambda: self.status_display.show_error("Refresh failed"))
        
        threading.Thread(target=refresh_async, daemon=True).start()
    
    def _test_brightness_support(self) -> None:
        """Test brightness support for current display"""
        if not self.current_display:
            self.status_display.show_error("No display selected")
            return
        
        self.logger.info("Testing brightness support for %s", self.current_display['name'])
        self.status_display.show_working("Testing support...")
        
        def test_async():
            try:
                support_info = self.brightness_controller.test_brightness_support(self.current_display)
                
                # Create results message
                results = []
                for operation, supported in support_info.items():
                    status = "✓" if supported else "✗"
                    results.append(f"{status} {operation.replace('_', ' ').title()}")
                
                result_text = "\n".join(results)
                
                self.root.after(0, lambda: messagebox.showinfo(
                    "Brightness Support Test",
                    f"Display: {self.current_display['name']}\n\n{result_text}"
                ))
                
                self.root.after(0, lambda: self.status_display.show_success("Support test complete"))
                
            except Exception as e:
                self.logger.error("Error testing brightness support: %s", e)
                self.root.after(0, lambda: self.status_display.show_error("Test failed"))
        
        threading.Thread(target=test_async, daemon=True).start()
    
    def _save_current_settings(self) -> None:
        """Save current settings"""
        try:
            settings = {
                'last_brightness': self.brightness_var.get(),
                'last_display_index': self.display_combo.current(),
                'window_geometry': self.root.geometry()
            }
            self.settings_manager.save_settings(settings)
        except Exception as e:
            self.logger.error("Error saving settings: %s", e)
    
    def _on_closing(self) -> None:
        """Handle application closing"""
        self.logger.info("Application closing")
        self._save_current_settings()
        self.root.destroy()
    
    def run(self) -> None:
        """Start the GUI main loop"""
        self.logger.info("Starting GUI main loop")
        
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("GUI interrupted by keyboard")
            self._on_closing()
        except Exception as e:
            self.logger.error("GUI main loop error: %s", e)
            raise
        
        self.logger.info("GUI main loop ended")