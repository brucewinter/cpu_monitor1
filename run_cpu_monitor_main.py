#!/usr/bin/env python3
"""
CPU Monitor Launcher Script
Launches the consolidated CPU Monitor application
"""

if __name__ == "__main__":
    try:
        from cpu_monitor1 import main
        main()
    except ImportError as e:
        print(f"Error importing cpu_monitor_main: {e}")
        print("Please ensure cpu_monitor1.py is in the same directory")
        input("Press Enter to exit...")
    except Exception as e:
        print(f"Error starting CPU Monitor: {e}")
        input("Press Enter to exit...")
