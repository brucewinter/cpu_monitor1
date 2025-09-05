# Enhanced CPU Monitor & App Restarter

A powerful Windows application for monitoring CPU usage of specific applications and automatically restarting them when CPU usage exceeds thresholds or when they crash.

## 🚀 Features

- **Real-time CPU Monitoring**: Monitor multiple applications simultaneously with accurate CPU percentage readings
- **Smart Process Detection**: Automatically detects processes by name, executable path, and running instances
- **Automatic App Restart**: Restart applications when CPU usage exceeds configurable thresholds for a specified duration
- **Auto-recovery**: Automatically restart crashed or terminated applications
- **Configurable Delays**: 
  - **Startup Delay**: Wait time before restarting apps (default: 3 seconds)
  - **Monitoring Startup Delay**: Wait time before starting monitoring to allow CPU normalization (default: 10 seconds)
  - **CPU Threshold Duration**: Time CPU must stay above threshold before restarting (default: 30 seconds)
- **Process Discovery**: Automatically find executable paths for monitored applications
- **Pause/Resume**: Pause monitoring without losing configuration
- **Comprehensive Logging**: Detailed activity log with timestamps
- **Modern UI**: Clean, dark-themed interface with intuitive controls
- **Consolidated Codebase**: Single, well-organized file with type hints and clean code structure

## 📋 Requirements

- Windows 10/11
- Python 3.7+
- Required Python packages (see `requirements.txt`)

## 🔄 Recent Changes

### Version 2.5 - Consolidated and Cleaned Codebase
- **Code Consolidation**: Merged all versions into single `cpu_monitor_main.py` file
- **Type Hints**: Added type annotations for better code readability and IDE support
- **Clean Imports**: Removed unused imports and organized import statements
- **Standardized Versioning**: Consistent version numbering across the codebase
- **Simplified Structure**: Single main file with all functionality preserved

### Version 2.4 - Increased Height & Activity Log Visibility
- **Increased Height**: Made app 20% taller (900x1152) to show more activity log
- **Better Visibility**: All UI elements including activity log are now fully visible
- **Improved Layout**: Better spacing and visibility for monitoring information
- **Enhanced GPU Filtering**: More aggressive default filtering (0.5 = 50% of raw CPU) for better Task Manager accuracy
- **Taller Interface**: Increased height to 900x800 to ensure all UI elements are visible
- **Smart Auto-Start**: Only auto-starts if there are enabled apps to monitor

### Version 2.2 - GPU Filtering & Improved CPU Accuracy
- **GPU Filtering**: Configurable factor to filter out GPU-related CPU usage
- **Improved CPU Accuracy**: More accurate CPU monitoring that better matches Task Manager
- **Configurable Filtering**: Adjustable GPU filter factor (default: 0.5 = 50% of raw CPU)
- **Taller Interface**: Increased height to 900x750 to show all UI elements

### Version 2.1 - Compact UI & Version Display
- **Compact Interface**: Reduced window size to 900x650 for better fit on smaller screens
- **Version Display**: Clear version number shown in title and UI
- **Optimized Layout**: Reduced padding and spacing for more efficient use of screen space

### Version 2.0 - Enhanced CPU Monitoring
- **CPU-Only Monitoring**: Now monitors CPU usage exclusively, excluding GPU usage
- **Time-Based Thresholds**: CPU must exceed threshold for specified duration before restart
- **Visual Status Indicators**: Clear warning states and countdown timers
- **Enhanced UI**: New threshold duration setting with helpful tooltips
- **Context Menu**: Right-click to reset threshold timers manually
- **Error Filtering**: Option to filter out Reolink app error messages from console (while app is running)

## 🛠️ Installation

### Option 1: Quick Install (Recommended)

1. **Download the repository**:
   ```bash
   git clone https://github.com/yourusername/cpu_monitor1.git
   cd cpu_monitor1
   ```

2. **Run the installer**:
   ```bash
   install.bat
   ```

3. **Launch the application**:
   ```bash
   run_cpu_monitor.bat
   ```

### Option 2: Manual Installation

1. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python cpu_monitor1.py
   ```

## 🎯 Usage

### Basic Setup

1. **Launch the application**
2. **Configure settings**:
   - Set CPU threshold percentage (default: 15%)
   - Set check interval in seconds (default: 5 seconds)
   - Set startup delays as needed
3. **Add applications to monitor**:
   - Enter application name (e.g., "reolink")
   - Click "Add App"
4. **Start monitoring**:
   - Click "Start Monitoring"
   - The app will wait for the monitoring startup delay, then begin monitoring

### Advanced Features

#### CPU Threshold Duration
- **New Feature**: CPU must stay above the threshold for a specified duration before restarting
- Prevents unnecessary restarts from temporary CPU spikes
- Configurable duration (default: 30 seconds)
- Visual indicators show warning state and countdown to restart
- Right-click context menu allows manual reset of threshold timer

#### Discover Executables
- Click "Discover Executables" to automatically find and set executable paths
- Useful for applications that aren't in the system PATH

#### Debug CPU Monitoring
- Click "Debug CPU" to test CPU monitoring in real-time
- Shows detailed process information and CPU usage

#### Auto-Start Monitoring
- **Automatic Launch**: Monitoring starts automatically when the app launches (after 2 seconds)
- **Smart Detection**: Only auto-starts if there are enabled apps to monitor
- **No Manual Start**: No need to click "Start Monitoring" - it happens automatically
- **Configurable**: Can still manually start/stop/pause monitoring as needed

#### GPU Filtering
- **GPU Filter Factor**: Configurable setting to filter out GPU-related CPU usage
- **Default Value**: 0.5 (50% of raw CPU reading) - More aggressive filtering
- **Adjustable**: Lower values = more aggressive GPU filtering, Higher values = less filtering
- **Better Accuracy**: Helps match Task Manager CPU readings more closely
- **Example**: If raw CPU shows 20%, with factor 0.5, displayed CPU will be 10%

#### Error Filtering
- **Reolink Error Filter**: Option to filter out common Reolink app error messages from console output
- **System-Level Filtering**: Intercepts stdout/stderr to catch messages before they reach the console
- **Test Button**: Use "Test Filter" button to verify filtering is working correctly
- **Note**: Filtering only works while the CPU Monitor application is running
- Reduces console clutter while maintaining full logging in the UI
- Configurable setting that can be enabled/disabled as needed

#### Right-click Context Menu
- Right-click on any monitored app for additional options:
  - Set Executable Path manually
  - Reset Threshold Timer (clears the warning state)
  - Remove application from monitoring

#### Pause/Resume Monitoring
- Use "Pause Monitoring" to temporarily stop monitoring
- Click "Resume Monitoring" to continue

## ⚙️ Configuration

### Settings File (`settings.json`)
```json
{
  "cpu_threshold": 15.0,
  "check_interval": 5.0,
  "startup_delay": 3.0,
  "monitoring_startup_delay": 10.0,
  "cpu_threshold_duration": 30.0,
  "filter_reolink_errors": true,
  "gpu_filter_factor": 0.5,
  "auto_restart_enabled": true
}
```

### Monitored Apps File (`monitored_apps.json`)
```json
[
  {
    "name": "reolink",
    "process_name": "Reolink.exe",
    "status": "Active",
    "enabled": true,
    "last_cpu": 0.0,
    "restart_count": 0,
    "executable_path": "C:\\Program Files\\Reolink\\Reolink.exe"
  }
]
```

## 🔧 Troubleshooting

### Common Issues

1. **CPU always shows 0%**:
   - Use "Debug CPU" button to test monitoring
   - Check if process names match exactly
   - Verify applications are running

2. **Buttons not working**:
   - Check console output for error messages
   - Ensure window is properly sized (1000x800 minimum)
   - Verify Python dependencies are installed

3. **Process not found**:
   - Use "Discover Executables" button
   - Check process name spelling
   - Verify application is actually running

### Debug Mode

The application includes comprehensive debugging:
- Console output for all operations
- Detailed process detection logging
- Error handling with fallback mechanisms

## 📁 File Structure

```
cpu_monitor1/
├── cpu_monitor1.py            # Main application
├── requirements.txt            # Python dependencies
├── install.bat                # Windows installer
├── run_cpu_monitor.bat        # Windows launcher
├── run_cpu_monitor.ps1        # PowerShell launcher
├── settings.json              # Application settings
├── monitored_apps.json        # Monitored applications
├── cpu_monitor.log            # Application log file
└── README.md                  # This file
```

## 🆚 Version History

### v2.0 (Enhanced)
- **Fixed**: NoneType errors in process detection
- **Added**: Monitoring startup delay for CPU normalization
- **Enhanced**: Process detection with multiple fallback strategies
- **Improved**: UI layout and visibility
- **Added**: Comprehensive debugging and logging
- **Enhanced**: Error handling and recovery

### v1.0 (Original)
- Basic CPU monitoring
- Simple app restart functionality
- Basic UI

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Python and tkinter
- Uses psutil for process monitoring
- Enhanced with modern UI design principles
- Comprehensive error handling and debugging

## 📞 Support

If you encounter any issues or have questions:
1. Check the troubleshooting section above
2. Review the console output for error messages
3. Open an issue on GitHub with detailed information

---

**Happy Monitoring! 🚀**
