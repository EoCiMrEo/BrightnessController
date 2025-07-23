@echo off

rem Assume you are in the project's root folder
rem The `mkdir` command will create the full directory path `src\brightness_controller`
rem inside your current folder

mkdir src\brightness_controller\core
mkdir src\brightness_controller\utils
mkdir src\brightness_controller\gui
mkdir src\brightness_controller\logs

rem Create empty files with relative paths
type nul > src\brightness_controller\brightness_controller.py
type nul > src\brightness_controller\core\logging_config.py
type nul > src\brightness_controller\core\security_manager.py
type nul > src\brightness_controller\core\display_detector.py
type nul > src\brightness_controller\core\brightness_controller.py
type nul > src\brightness_controller\utils\system_checker.py
type nul > src\brightness_controller\gui\brightness_gui.py

rem Create log files with relative paths
type nul > src\brightness_controller\logs\BrightnessController.Main_20250723_143022.log
type nul > src\brightness_controller\logs\BrightnessController.Security_20250723_143022.log
type nul > src\brightness_controller\logs\BrightnessController.DisplayDetector_20250723_143022.log
type nul > src\brightness_controller\logs\BrightnessController.BrightnessController_20250723_143022.log
type nul > src\brightness_controller\logs\BrightnessController.GUI_20250723_143022.log
type nul > src\brightness_controller\logs\brightness_controller_20250723_143022.log

Your code is pretty great ! Thank you so much ! I haven't tested yet, I have given you a permission to access the project folder BrightnessController, please help me to insert all the codes you write into each files accordingly. All the files and folder inside brightness_controller folder have already move to /src folder so all the folder structure store in /src folder please go there you will see all the files and folder that you need.