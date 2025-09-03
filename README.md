# Enhanced CPU Monitor & App Restarter

A powerful Windows application for monitoring CPU usage of specific applications and automatically restarting them when CPU usage exceeds thresholds or when they crash.

## 🚀 Features

- **Real-time CPU Monitoring**: Monitor multiple applications simultaneously with accurate CPU percentage readings
- **Smart Process Detection**: Automatically detects processes by name, executable path, and running instances
- **Automatic App Restart**: Restart applications when CPU usage exceeds configurable thresholds
- **Auto-recovery**: Automatically restart crashed or terminated applications
- **Configurable Delays**: 
  - **Startup Delay**: Wait time before restarting apps (default: 3 seconds)
  - **Monitoring Startup Delay**: Wait time before starting monitoring to allow CPU normalization (default: 10 seconds)
- **Process Discovery**: Automatically find executable paths for monitored applications
- **Pause/Resume**: Pause monitoring without losing configuration
- **Comprehensive Logging**: Detailed activity log with timestamps
- **Modern UI**: Clean, dark-themed interface with intuitive controls

## 📋 Requirements

- Windows 10/11
- Python 3.7+
- Required Python packages (see `requirements.txt`)

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
   python cpu_monitor_enhanced.py
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

#### Discover Executables
- Click "Discover Executables" to automatically find and set executable paths
- Useful for applications that aren't in the system PATH

#### Debug CPU Monitoring
- Click "Debug CPU" to test CPU monitoring in real-time
- Shows detailed process information and CPU usage

#### Right-click Context Menu
- Right-click on any monitored app for additional options:
  - Set Executable Path manually
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
├── cpu_monitor_enhanced.py    # Main application
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
