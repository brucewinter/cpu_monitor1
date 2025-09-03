# Quick Start Guide - CPU Monitor & App Restarter

## 🚀 Get Started in 3 Steps

### 1. Install Dependencies
```bash
# Run the installer (double-click)
install.bat

# OR manually install
pip install -r requirements.txt
```

### 2. Run the Application
```bash
# Option 1: Double-click
run_cpu_monitor.bat

# Option 2: PowerShell
run_cpu_monitor.ps1

# Option 3: Command line
python cpu_monitor.py
```

### 3. Configure and Monitor
1. **Add Apps**: Type app names (e.g., "reolink", "chrome")
2. **Set Threshold**: Default is 50% CPU usage
3. **Set Interval**: How often to check (default: 5 seconds)
4. **Set Startup Delay**: How long to wait before restarting (default: 3 seconds)
5. **Enable Auto-Restart**: Automatically restart terminated apps (default: enabled)
6. **Start Monitoring**: Click "Start Monitoring"

## 🎯 Example: Monitor Reolink App

1. **Add Application**: Type "reolink" in the app name field
2. **Browse Executable** (Optional): Click "Browse" and select your Reolink .exe file
3. **Set CPU Threshold**: 50% (or your preferred limit)
4. **Set Startup Delay**: 3 seconds (or your preferred delay)
5. **Enable Auto-Restart**: Keep checked to restart if Reolink is terminated
6. **Start Monitoring**: The app will automatically restart Reolink if CPU exceeds 50% or if terminated

## ⚡ Features at a Glance

- ✅ **Real-time CPU monitoring**
- ✅ **Automatic app restart**
- ✅ **Auto-restart terminated apps**
- ✅ **Configurable startup delay**
- ✅ **Configurable thresholds**
- ✅ **Modern dark UI**
- ✅ **Process detection**
- ✅ **Activity logging**
- ✅ **Settings persistence**

## 🔧 Troubleshooting

- **"Access Denied"**: Run as Administrator
- **App not detected**: Check exact process name
- **Restart issues**: Use "Browse" to specify .exe path

## 📁 Files Created

- `settings.json` - Your preferences
- `monitored_apps.json` - Apps to monitor
- `cpu_monitor.log` - Activity history

## 🆘 Need Help?

- Check the activity log for errors
- Verify Python and dependencies are installed
- Ensure proper system permissions
- Read the full README.md for detailed information

---
**Happy Monitoring! 🎉**
