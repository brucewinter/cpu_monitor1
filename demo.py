#!/usr/bin/env python3
"""
Demo script for CPU Monitor functionality
This script demonstrates the core CPU monitoring capabilities
"""

import psutil
import time
import threading
from datetime import datetime

def get_app_cpu_usage(app_name):
    """Get CPU usage for a specific application"""
    total_cpu = 0.0
    process_count = 0
    
    print(f"Scanning for processes containing '{app_name}'...")
    
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            if app_name.lower() in proc.info['name'].lower():
                proc.cpu_percent()  # First call to initialize
                time.sleep(0.1)  # Small delay for accurate reading
                cpu = proc.cpu_percent()
                total_cpu += cpu
                process_count += 1
                print(f"  Found process: {proc.info['name']} (PID: {proc.info['pid']}) - CPU: {cpu:.1f}%")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
            
    return total_cpu, process_count

def monitor_app_cpu(app_name, threshold=50.0, interval=2.0, duration=30, startup_delay=3.0):
    """Monitor CPU usage for a specific application"""
    print(f"\n=== CPU Monitoring Demo for '{app_name}' ===")
    print(f"Threshold: {threshold}% | Check Interval: {interval}s | Duration: {duration}s | Startup Delay: {startup_delay}s")
    print("=" * 80)
    
    start_time = time.time()
    check_count = 0
    
    while time.time() - start_time < duration:
        try:
            cpu_percent, process_count = get_app_cpu_usage(app_name)
            check_count += 1
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if process_count > 0:
                print(f"[{timestamp}] Check #{check_count}: {app_name} CPU usage: {cpu_percent:.1f}% ({process_count} process(es))")
                
                if cpu_percent > threshold:
                    print(f"  ⚠️  WARNING: CPU usage exceeds {threshold}% threshold!")
                    print(f"  🔄 Would restart {app_name} after {startup_delay}s delay in real application")
            else:
                print(f"[{timestamp}] Check #{check_count}: No {app_name} processes found")
                print(f"  🔄 Would auto-restart {app_name} after {startup_delay}s delay (if auto-restart enabled)")
                
        except Exception as e:
            print(f"Error during monitoring: {str(e)}")
            
        time.sleep(interval)
    
    print(f"\n=== Monitoring completed after {check_count} checks ===")

def list_running_apps():
    """List some running applications for demo purposes"""
    print("\n=== Currently Running Applications ===")
    app_count = 0
    
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            if app_count < 20:  # Limit output
                proc.cpu_percent()  # Initialize
                time.sleep(0.01)
                cpu = proc.cpu_percent()
                print(f"  {proc.info['name']:<30} (PID: {proc.info['pid']:>6}) - CPU: {cpu:>6.1f}%")
                app_count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    print(f"\nShowing {app_count} applications (truncated for demo)")

def main():
    """Main demo function"""
    print("CPU Monitor & App Restarter - Demo Script")
    print("=" * 50)
    
    # Show system info
    print(f"System: {psutil.sys.platform}")
    print(f"Python: {psutil.sys.version}")
    print(f"CPU Count: {psutil.cpu_count()}")
    print(f"Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
    
    # List some running apps
    list_running_apps()
    
    # Demo monitoring for common apps
    demo_apps = ["chrome", "explorer", "svchost"]
    
    for app in demo_apps:
        try:
            monitor_app_cpu(app, threshold=30.0, interval=3.0, duration=15, startup_delay=2.0)
        except KeyboardInterrupt:
            print(f"\nDemo interrupted for {app}")
            break
        except Exception as e:
            print(f"Error in demo for {app}: {str(e)}")
    
    print("\n=== Demo Completed ===")
    print("Run 'python cpu_monitor.py' to use the full GUI application!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\nDemo error: {str(e)}")
    
    input("\nPress Enter to exit...")
