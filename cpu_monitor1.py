# Enhanced CPU Monitor with Pause/Resume and Better App Management
# Version 2.3 - Auto-Start Monitoring & Enhanced GPU Filtering
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import psutil
import threading
import time
import json
import os
import subprocess
from datetime import datetime
import logging
import sys
import io

# Application version
APP_VERSION = "2.3"

class FilteredOutput:
    """Custom output filter to catch and filter Reolink error messages"""
    def __init__(self, original_stream, filter_enabled=True):
        self.original_stream = original_stream
        self.filter_enabled = filter_enabled
        
    def write(self, text):
        if self.filter_enabled and self._should_filter(text):
            # Don't write filtered messages
            return
        self.original_stream.write(text)
        
    def _should_filter(self, text):
        """Check if text should be filtered"""
        if not text.strip():
            return False
            
        # Filter out any text containing Reolink error patterns
        reolink_error_patterns = [
            "handle this channel cmd:",
            "e_bc_cmd_get_wifi_signal",
            "handle:",
            "channel:",
            "cmd param: undefined",
            "-------",
            "e_bc_cmd",
            "cmd param:",
            "undefined"
        ]
        
        text_lower = text.lower()
        for pattern in reolink_error_patterns:
            if pattern.lower() in text_lower:
                return True
        return False
        
    def flush(self):
        self.original_stream.flush()
        
    def __getattr__(self, attr):
        return getattr(self.original_stream, attr)

class CPUMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Enhanced CPU Monitor & App Restarter v{APP_VERSION}")
        self.root.geometry("900x960")  # 20% taller to show activity log
        self.root.configure(bg="#2b2b2b")
        self.root.minsize(800, 900)  # Increased minimum height

        # Configure logging
        logging.basicConfig(
            filename="cpu_monitor.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )

        # App state
        self.monitoring = False
        self.paused = False
        self.monitor_thread = None
        self.monitored_apps = []
        self.cpu_threshold = 50.0
        self.check_interval = 5.0
        self.startup_delay = 3.0
        self.monitoring_startup_delay = 10.0  # New: delay before monitoring starts
        self.auto_restart_enabled = True
        self.cpu_threshold_duration = 30.0  # New: time in seconds CPU must be above threshold before restarting
        self.filter_reolink_errors = True  # New: filter out Reolink error messages from console
        self.gpu_filter_factor = 0.5  # New: factor to filter out GPU-related CPU usage (0.5 = 50% of raw CPU, more aggressive)
        
        # Set up output filtering
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.setup_output_filtering()

        # Load saved settings
        self.load_settings()

        self.setup_ui()
        self.setup_styles()
        
    def setup_output_filtering(self):
        """Set up stdout/stderr filtering for Reolink error messages"""
        if self.filter_reolink_errors:
            sys.stdout = FilteredOutput(sys.stdout, True)
            sys.stderr = FilteredOutput(sys.stderr, True)
            if hasattr(self, 'filter_status_label'):
                self.filter_status_label.config(text="(Active)", fg="#00ff88")
        else:
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr
            if hasattr(self, 'filter_status_label'):
                self.filter_status_label.config(text="(Disabled)", fg="#ff4444")
            
    def test_output_filter(self):
        """Test the output filter by printing some test messages"""
        self.log_message("=== Testing Output Filter ===")
        
        # Test messages that should be filtered
        print("------- handle this channel cmd: E_BC_CMD_GET_WIFI_SIGNAL")
        print("handle: 1000001")
        print("channel: -1")
        print("cmd param: undefined")
        
        # Test messages that should NOT be filtered
        print("This is a normal message that should appear")
        print("CPU usage is normal")
        
        self.log_message("=== Filter Test Complete ===")
        self.log_message("Check console output above to see if filtering is working")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Title.TLabel",
                       font=("Segoe UI", 16, "bold"),
                       foreground="#ffffff",
                       background="#2b2b2b")

        style.configure("Custom.TFrame",
                       background="#3c3c3c",
                       relief="raised",
                       borderwidth=1)

    def setup_ui(self):
        # Main title
        title_frame = tk.Frame(self.root, bg="#2b2b2b")
        title_frame.pack(fill="x", padx=20, pady=10)  # Reduced padding

        title_label = tk.Label(title_frame,
                              text="Enhanced CPU Monitor & App Restarter",
                              font=("Segoe UI", 18, "bold"),  # Slightly smaller font
                              fg="#00ff88",
                              bg="#2b2b2b")
        title_label.pack()
        
        # Version display
        version_label = tk.Label(title_frame,
                                text=f"Version {APP_VERSION}",
                                font=("Segoe UI", 10),
                                fg="#888888",
                                bg="#2b2b2b")
        version_label.pack()

        # Settings frame
        settings_frame = ttk.Frame(self.root, style="Custom.TFrame")
        settings_frame.pack(fill="x", padx=20, pady=5)  # Reduced padding

        # CPU Threshold setting
        threshold_frame = tk.Frame(settings_frame, bg="#3c3c3c")
        threshold_frame.pack(fill="x", padx=20, pady=5)  # Reduced padding

        tk.Label(threshold_frame,
                text="CPU Threshold (%):",
                font=("Segoe UI", 10, "bold"),
                fg="#ffffff",
                bg="#3c3c3c").pack(side="left", padx=(0, 10))

        self.threshold_var = tk.StringVar(value=str(self.cpu_threshold))
        threshold_entry = tk.Entry(threshold_frame,
                                 textvariable=self.threshold_var,
                                 font=("Segoe UI", 10),
                                 width=10,
                                 bg="#4a4a4a",
                                 fg="#ffffff",
                                 insertbackground="#ffffff")
        threshold_entry.pack(side="left")
        
        # Help text for CPU threshold
        threshold_help_label = tk.Label(threshold_frame,
                                       text="(CPU usage only, excluding GPU)",
                                       font=("Segoe UI", 8),
                                       fg="#cccccc",
                                       bg="#3c3c3c")
        threshold_help_label.pack(side="left", padx=(10, 0))

        # Check interval setting
        interval_frame = tk.Frame(settings_frame, bg="#3c3c3c")
        interval_frame.pack(fill="x", padx=20, pady=5)  # Reduced padding

        tk.Label(interval_frame,
                text="Check Interval (seconds):",
                font=("Segoe UI", 10, "bold"),
                fg="#ffffff",
                bg="#3c3c3c").pack(side="left", padx=(0, 10))

        self.interval_var = tk.StringVar(value=str(self.check_interval))
        interval_entry = tk.Entry(interval_frame,
                                textvariable=self.interval_var,
                                font=("Segoe UI", 10),
                                width=10,
                                bg="#4a4a4a",
                                fg="#ffffff",
                                insertbackground="#ffffff")
        interval_entry.pack(side="left")

        # Startup delay setting
        startup_delay_frame = tk.Frame(settings_frame, bg="#3c3c3c")
        startup_delay_frame.pack(fill="x", padx=20, pady=5)  # Reduced padding

        tk.Label(startup_delay_frame,
                text="Startup Delay (seconds):",
                font=("Segoe UI", 10, "bold"),
                fg="#ffffff",
                bg="#3c3c3c").pack(side="left", padx=(0, 10))

        self.startup_delay_var = tk.StringVar(value=str(self.startup_delay))
        startup_delay_entry = tk.Entry(startup_delay_frame,
                                     textvariable=self.startup_delay_var,
                                     font=("Segoe UI", 10),
                                     width=10,
                                     bg="#4a4a4a",
                                     fg="#ffffff",
                                     insertbackground="#ffffff")
        startup_delay_entry.pack(side="left")

        # Monitoring startup delay setting
        monitoring_startup_delay_frame = tk.Frame(settings_frame, bg="#3c3c3c")
        monitoring_startup_delay_frame.pack(fill="x", padx=20, pady=5)  # Reduced padding

        tk.Label(monitoring_startup_delay_frame,
                text="Monitoring Startup Delay (seconds):",
                font=("Segoe UI", 10, "bold"),
                fg="#ffffff",
                bg="#3c3c3c").pack(side="left", padx=(0, 10))

        self.monitoring_startup_delay_var = tk.StringVar(value=str(self.monitoring_startup_delay))
        monitoring_startup_delay_entry = tk.Entry(monitoring_startup_delay_frame,
                                               textvariable=self.monitoring_startup_delay_var,
                                               font=("Segoe UI", 10),
                                               width=10,
                                               bg="#4a4a4a",
                                               fg="#ffffff",
                                               insertbackground="#ffffff")
        monitoring_startup_delay_entry.pack(side="left")

        # CPU Threshold Duration setting
        threshold_duration_frame = tk.Frame(settings_frame, bg="#3c3c3c")
        threshold_duration_frame.pack(fill="x", padx=20, pady=5)  # Reduced padding

        tk.Label(threshold_duration_frame,
                text="CPU Threshold Duration (seconds):",
                font=("Segoe UI", 10, "bold"),
                fg="#ffffff",
                bg="#3c3c3c").pack(side="left", padx=(0, 10))

        self.threshold_duration_var = tk.StringVar(value=str(self.cpu_threshold_duration))
        threshold_duration_entry = tk.Entry(threshold_duration_frame,
                                          textvariable=self.threshold_duration_var,
                                          font=("Segoe UI", 10),
                                          width=10,
                                          bg="#4a4a4a",
                                          fg="#ffffff",
                                          insertbackground="#ffffff")
        threshold_duration_entry.pack(side="left")
        
        # Help text for threshold duration
        help_label = tk.Label(threshold_duration_frame,
                             text="(Time CPU must stay above threshold before restart)",
                             font=("Segoe UI", 8),
                             fg="#cccccc",
                             bg="#3c3c3c")
        help_label.pack(side="left", padx=(10, 0))

        # Filter Reolink errors checkbox
        filter_errors_frame = tk.Frame(settings_frame, bg="#3c3c3c")
        filter_errors_frame.pack(fill="x", padx=20, pady=5)  # Reduced padding

        self.filter_errors_var = tk.BooleanVar(value=self.filter_reolink_errors)
        filter_errors_checkbox = tk.Checkbutton(filter_errors_frame,
                                              text="Filter Reolink error messages from console",
                                              variable=self.filter_errors_var,
                                              font=("Segoe UI", 10, "bold"),
                                              fg="#ffffff",
                                              bg="#3c3c3c",
                                              activeforeground="#ffffff",
                                              activebackground="#3c3c3c",
                                              selectcolor="#00ff88")
        filter_errors_checkbox.pack(side="left")
        
        # Help text for filter setting
        filter_help_label = tk.Label(filter_errors_frame,
                                    text="(Filters while app is running only)",
                                    font=("Segoe UI", 8),
                                    fg="#cccccc",
                                    bg="#3c3c3c")
        filter_help_label.pack(side="left", padx=(10, 0))
        
        # Test filter button
        test_filter_btn = tk.Button(filter_errors_frame,
                                   text="Test Filter",
                                   command=self.test_output_filter,
                                   font=("Segoe UI", 8),
                                   bg="#4444ff",
                                   fg="#ffffff",
                                   relief="flat",
                                   padx=10)
        test_filter_btn.pack(side="left", padx=(10, 0))
        
        # Filter status label
        self.filter_status_label = tk.Label(filter_errors_frame,
                                           text="",
                                           font=("Segoe UI", 8),
                                           fg="#00ff88",
                                           bg="#3c3c3c")
        self.filter_status_label.pack(side="left", padx=(10, 0))
        
        # GPU Filter Factor setting
        gpu_filter_frame = tk.Frame(settings_frame, bg="#3c3c3c")
        gpu_filter_frame.pack(fill="x", padx=20, pady=5)

        tk.Label(gpu_filter_frame,
                text="GPU Filter Factor:",
                font=("Segoe UI", 10, "bold"),
                fg="#ffffff",
                bg="#3c3c3c").pack(side="left", padx=(0, 10))

        self.gpu_filter_var = tk.StringVar(value=str(self.gpu_filter_factor))
        gpu_filter_entry = tk.Entry(gpu_filter_frame,
                                   textvariable=self.gpu_filter_var,
                                   font=("Segoe UI", 10),
                                   width=10,
                                   bg="#4a4a4a",
                                   fg="#ffffff",
                                   insertbackground="#ffffff")
        gpu_filter_entry.pack(side="left")
        
        # Help text for GPU filter
        gpu_filter_help_label = tk.Label(gpu_filter_frame,
                                        text="(0.5 = 50% of raw CPU, lower = more aggressive GPU filtering)",
                                        font=("Segoe UI", 8),
                                        fg="#cccccc",
                                        bg="#3c3c3c")
        gpu_filter_help_label.pack(side="left", padx=(10, 0))

        # Auto-restart checkbox
        restart_frame = tk.Frame(settings_frame, bg="#3c3c3c")
        restart_frame.pack(fill="x", padx=20, pady=5)  # Reduced padding

        self.auto_restart_var = tk.BooleanVar(value=self.auto_restart_enabled)
        restart_checkbox = tk.Checkbutton(restart_frame,
                                        text="Auto-restart terminated applications",
                                        variable=self.auto_restart_var,
                                        font=("Segoe UI", 10, "bold"),
                                        fg="#ffffff",
                                        bg="#3c3c3c",
                                        activeforeground="#ffffff",
                                        activebackground="#3c3c3c",
                                        selectcolor="#00ff88")
        restart_checkbox.pack(side="left")

        # App management frame
        app_frame = ttk.Frame(self.root, style="Custom.TFrame")
        app_frame.pack(fill="x", padx=20, pady=5)  # Reduced padding

        # Add app section
        add_app_frame = tk.Frame(app_frame, bg="#3c3c3c")
        add_app_frame.pack(fill="x", padx=20, pady=5)  # Reduced padding

        tk.Label(add_app_frame,
                text="Add Application to Monitor:",
                font=("Segoe UI", 12, "bold"),
                fg="#ffffff",
                bg="#3c3c3c").pack(anchor="w")

        app_input_frame = tk.Frame(add_app_frame, bg="#3c3c3c")
        app_input_frame.pack(fill="x", pady=5)

        self.app_name_var = tk.StringVar()
        app_name_entry = tk.Entry(app_input_frame,
                                 textvariable=self.app_name_var,
                                 font=("Segoe UI", 10),
                                 bg="#4a4a4a",
                                 fg="#ffffff",
                                 insertbackground="#ffffff")
        app_name_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        add_btn = tk.Button(app_input_frame,
                           text="Add App",
                           command=self.add_app,
                           font=("Segoe UI", 10, "bold"),
                           bg="#00ff88",
                           fg="#000000",
                           relief="flat",
                           padx=20)
        add_btn.pack(side="right")

        # Monitored apps list
        list_frame = tk.Frame(app_frame, bg="#3c3c3c")
        list_frame.pack(fill="both", expand=True, padx=20, pady=5)  # Reduced padding

        tk.Label(list_frame,
                text="Monitored Applications:",
                font=("Segoe UI", 12, "bold"),
                fg="#ffffff",
                bg="#3c3c3c").pack(anchor="w")

        # Create Treeview for apps with Enabled column
        columns = ("App Name", "Process Name", "Status", "Enabled", "Last CPU %", "Restart Count", "Threshold Status")
        self.app_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=6)

        for col in columns:
            self.app_tree.heading(col, text=col)
            if col == "Enabled":
                self.app_tree.column(col, width=80, anchor="center")
            elif col == "Last CPU %":
                self.app_tree.column(col, width=100, anchor="center")
            elif col == "Restart Count":
                self.app_tree.column(col, width=100, anchor="center")
            elif col == "Threshold Status":
                self.app_tree.column(col, width=120, anchor="center")
            else:
                self.app_tree.column(col, width=120, anchor="center")

        self.app_tree.pack(fill="both", expand=True, pady=5)

        # Bind right-click to app tree for context menu
        self.app_tree.bind("<Button-3>", self.show_app_context_menu)

        # App action buttons
        app_actions_frame = tk.Frame(list_frame, bg="#3c3c3c")
        app_actions_frame.pack(fill="x", pady=5)

        self.remove_btn = tk.Button(app_actions_frame,
                                   text="Remove Selected App",
                                   command=self.remove_app,
                                   font=("Segoe UI", 10),
                                   bg="#ff4444",
                                   fg="#ffffff",
                                   relief="flat",
                                   padx=15)
        self.remove_btn.pack(side="left", padx=(0, 10))

        self.toggle_app_btn = tk.Button(app_actions_frame,
                                       text="Toggle App Status",
                                       command=self.toggle_app_status,
                                       font=("Segoe UI", 10),
                                       bg="#4444ff",
                                       fg="#ffffff",
                                       relief="flat",
                                       padx=15)
        self.toggle_app_btn.pack(side="left")

        # Discovery button
        self.discover_btn = tk.Button(app_actions_frame,
                                     text="Discover Executables",
                                     command=self.discover_executable_paths,
                                     font=("Segoe UI", 10),
                                     bg="#44ff44",
                                     fg="#000000",
                                     relief="flat",
                                     padx=15)
        self.discover_btn.pack(side="left")

        # Debug button
        self.debug_btn = tk.Button(app_actions_frame,
                                  text="Debug CPU",
                                  command=self.debug_cpu_monitoring,
                                  font=("Segoe UI", 10),
                                  bg="#ff8844",
                                  fg="#000000",
                                  relief="flat",
                                  padx=15)
        self.debug_btn.pack(side="left")

        # Control buttons frame with Pause functionality
        control_frame = tk.Frame(self.root, bg="#444444", relief="raised", borderwidth=2)
        control_frame.pack(fill="x", padx=20, pady=10)  # Reduced padding
        
        # Debug: Add a label to make sure the control frame is visible
        debug_label = tk.Label(control_frame,
                              text="Control Panel (Start/Pause/Stop buttons below)",
                              font=("Segoe UI", 10, "bold"),
                              fg="#ffffff",
                              bg="#444444")
        debug_label.pack(pady=5)

        self.start_btn = tk.Button(control_frame,
                                  text="Start Monitoring",
                                  command=self.start_monitoring,
                                  font=("Segoe UI", 12, "bold"),
                                  bg="#00ff88",
                                  fg="#000000",
                                  relief="flat",
                                  padx=30,
                                  pady=10)
        self.start_btn.pack(side="left", padx=(0, 10))
        print("DEBUG: Start button created and packed")

        self.pause_btn = tk.Button(control_frame,
                                  text="Pause Monitoring",
                                  command=self.pause_monitoring,
                                  font=("Segoe UI", 12, "bold"),
                                  bg="#ffaa00",
                                  fg="#000000",
                                  relief="flat",
                                  padx=30,
                                  pady=10,
                                  state="disabled")
        self.pause_btn.pack(side="left", padx=(0, 10))
        print("DEBUG: Pause button created and packed")

        self.stop_btn = tk.Button(control_frame,
                                 text="Stop Monitoring",
                                 command=self.stop_monitoring,
                                 font=("Segoe UI", 12, "bold"),
                                 bg="#ff4444",
                                 fg="#ffffff",
                                 relief="flat",
                                 padx=30,
                                 pady=10,
                                 state="disabled")
        self.stop_btn.pack(side="left")
        print("DEBUG: Stop button created and packed")

        # Status frame
        status_frame = tk.Frame(self.root, bg="#2b2b2b")
        status_frame.pack(fill="x", padx=20, pady=5)  # Reduced padding

        self.status_label = tk.Label(status_frame,
                                    text="Status: Ready",
                                    font=("Segoe UI", 10),
                                    fg="#00ff88",
                                    bg="#2b2b2b")
        self.status_label.pack(anchor="w")

        # Monitoring info
        self.monitoring_info_label = tk.Label(status_frame,
                                             text="",
                                             font=("Segoe UI", 9),
                                             fg="#cccccc",
                                             bg="#2b2b2b")
        self.monitoring_info_label.pack(anchor="w")

        # Log frame
        log_frame = ttk.Frame(self.root, style="Custom.TFrame")
        log_frame.pack(fill="both", expand=True, padx=20, pady=5)  # Reduced padding

        tk.Label(log_frame,
                text="Activity Log:",
                font=("Segoe UI", 12, "bold"),
                fg="#ffffff",
                bg="#3c3c3c").pack(anchor="w", padx=20, pady=5)  # Reduced padding

        self.log_text = tk.Text(log_frame,
                                height=6,  # Reduced height
                                bg="#1e1e1e",
                                fg="#00ff88",
                                font=("Consolas", 9),
                                wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=20, pady=(0, 10))  # Reduced padding

        # Scrollbar for log
        log_scrollbar = tk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        # Load existing apps
        self.load_monitored_apps()
        
        # Update filter status
        self.setup_output_filtering()
        
        # Auto-start monitoring if apps are configured
        self.root.after(2000, self.auto_start_monitoring)  # Start after 2 seconds
        
    def auto_start_monitoring(self):
        """Automatically start monitoring if apps are configured"""
        if self.monitored_apps and any(app.get("enabled", True) for app in self.monitored_apps):
            self.log_message("Auto-starting monitoring...")
            self.start_monitoring()
        else:
            self.log_message("No apps configured for monitoring - auto-start skipped")

    def add_app(self):
        app_name = self.app_name_var.get().strip()
        if not app_name:
            messagebox.showerror("Error", "Please enter an application name")
            return

        # Check if app already exists
        for app in self.monitored_apps:
            if app["name"] == app_name:
                messagebox.showerror("Error", "Application already exists in the list")
                return

        # Add to monitored apps with enabled status
        new_app = {
            "name": app_name,
            "process_name": app_name.lower(),
            "status": "Active",
            "enabled": True,
            "last_cpu": 0.0,
            "restart_count": 0,
            "executable_path": None,
            "threshold_exceeded_time": None  # Track when CPU threshold was first exceeded
        }

        self.monitored_apps.append(new_app)
        self.update_app_tree()
        self.app_name_var.set("")
        self.save_monitored_apps()
        self.log_message(f"Added application: {app_name}")

    def remove_app(self):
        selection = self.app_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an application to remove")
            return

        item = self.app_tree.item(selection[0])
        app_name = item["values"][0]

        # Show confirmation dialog
        result = messagebox.askyesno(
            "Confirm Removal",
            f'Are you sure you want to remove "{app_name}" from monitoring?\n\nThis action cannot be undone.'
        )
        
        if result:
            # Remove from list
            self.monitored_apps = [app for app in self.monitored_apps if app["name"] != app_name]
            self.update_app_tree()
            self.save_monitored_apps()
            self.log_message(f"Removed application: {app_name}")
            messagebox.showinfo("Success", f"'{app_name}' has been removed from monitoring.")

    def toggle_app_status(self):
        selection = self.app_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an application to toggle")
            return

        item = self.app_tree.item(selection[0])
        app_name = item["values"][0]
        
        self.log_message(f"Attempting to toggle status for: {app_name}")

        # Find and toggle the app
        for app in self.monitored_apps:
            if app["name"] == app_name:
                old_status = app["enabled"]
                app["enabled"] = not app["enabled"]
                new_status = "enabled" if app["enabled"] else "disabled"
                self.log_message(f"{app_name} monitoring changed from {old_status} to {new_status}")
                self.update_app_tree()
                self.save_monitored_apps()
                break
        else:
            self.log_message(f"WARNING: Could not find app '{app_name}' in monitored apps list")

    def update_app_tree(self):
        # Clear existing items
        for item in self.app_tree.get_children():
            self.app_tree.delete(item)

        # Add current apps
        for app in self.monitored_apps:
            enabled_text = "✓" if app.get("enabled", True) else "✗"
            
            # Determine threshold status
            threshold_status = "Normal"
            if app.get("threshold_exceeded_time") is not None:
                current_time = time.time()
                elapsed_time = current_time - app["threshold_exceeded_time"]
                if elapsed_time >= self.cpu_threshold_duration:
                    threshold_status = "🚨 RESTART NOW"
                else:
                    remaining_time = self.cpu_threshold_duration - elapsed_time
                    threshold_status = f"⚠️ Warning ({remaining_time:.1f}s)"
            
            self.app_tree.insert("", "end", values=(
                app["name"],
                app["process_name"],
                app["status"],
                enabled_text,
                f"{app['last_cpu']:.1f}%",
                app["restart_count"],
                threshold_status
            ))

    def start_monitoring(self):
        try:
            self.cpu_threshold = float(self.threshold_var.get())
            self.check_interval = float(self.interval_var.get())
            self.startup_delay = float(self.startup_delay_var.get())
            self.monitoring_startup_delay = float(self.monitoring_startup_delay_var.get())
            self.cpu_threshold_duration = float(self.threshold_duration_var.get())
            self.filter_reolink_errors = self.filter_errors_var.get()
            self.gpu_filter_factor = float(self.gpu_filter_var.get())
            self.auto_restart_enabled = self.auto_restart_var.get()
            
            # Update output filtering based on new setting
            self.setup_output_filtering()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for threshold, interval, delays, and duration")
            return

        if not self.monitored_apps:
            messagebox.showwarning("Warning", "Please add at least one application to monitor")
            return

        # Check if any apps are enabled
        enabled_apps = [app for app in self.monitored_apps if app.get("enabled", True)]
        if not enabled_apps:
            messagebox.showwarning("Warning", "No applications are enabled for monitoring")
            return

        self.monitoring = True
        self.paused = False
        
        # Apply monitoring startup delay to allow CPU to normalize
        if self.monitoring_startup_delay > 0:
            self.status_label.config(text=f"Status: Starting monitoring in {self.monitoring_startup_delay}s...", fg="#ffaa00")
            self.log_message(f"Starting monitoring in {self.monitoring_startup_delay} seconds to allow CPU to normalize...")
            
            # Start monitoring thread after delay
            def delayed_start():
                time.sleep(self.monitoring_startup_delay)
                if self.monitoring:  # Check if still monitoring (not stopped)
                    self.root.after(0, self.start_monitoring_thread)
            
            threading.Thread(target=delayed_start, daemon=True).start()
        else:
            self.start_monitoring_thread()
        
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")
        self.stop_btn.config(state="normal")

    def start_monitoring_thread(self):
        """Start the actual monitoring thread"""
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.status_label.config(text="Status: Monitoring Active", fg="#00ff88")
        self.log_message("Started CPU monitoring")

    def pause_monitoring(self):
        if self.paused:
            # Resume monitoring
            self.paused = False
            self.pause_btn.config(text="Pause Monitoring", bg="#ffaa00")
            self.status_label.config(text="Status: Monitoring Active", fg="#00ff88")
            self.log_message("Resumed CPU monitoring")
        else:
            # Pause monitoring
            self.paused = True
            self.pause_btn.config(text="Resume Monitoring", bg="#00aa44")
            self.status_label.config(text="Status: Monitoring Paused", fg="#ffaa00")
            self.log_message("Paused CPU monitoring")

    def stop_monitoring(self):
        self.monitoring = False
        self.paused = False
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        self.status_label.config(text="Status: Stopped", fg="#ff4444")
        self.log_message("Stopped CPU monitoring")

    def monitor_loop(self):
        while self.monitoring:
            try:
                if not self.paused:
                    self.check_apps_cpu()
                    self.root.after(0, self.update_monitoring_info)
                time.sleep(self.check_interval)
            except Exception as e:
                self.log_message(f"Error in monitoring loop: {str(e)}")
                logging.error(f"Monitoring loop error: {str(e)}")

    def update_monitoring_info(self):
        if self.monitoring and not self.paused:
            enabled_count = len([app for app in self.monitored_apps if app.get("enabled", True)])
            total_count = len(self.monitored_apps)
            
            # Count apps in threshold warning state
            warning_count = 0
            for app in self.monitored_apps:
                if app.get("enabled", True) and app.get("threshold_exceeded_time") is not None:
                    warning_count += 1
            
            status_text = f"Monitoring {enabled_count}/{total_count} applications | "
            status_text += f"Check interval: {self.check_interval}s | "
            status_text += f"CPU threshold: {self.cpu_threshold}% | "
            status_text += f"Threshold duration: {self.cpu_threshold_duration}s"
            
            if warning_count > 0:
                status_text += f" | {warning_count} app(s) in threshold warning"
            
            self.monitoring_info_label.config(text=status_text)
        elif self.paused:
            self.monitoring_info_label.config(text="Monitoring is currently paused")
        else:
            self.monitoring_info_label.config(text="")

    def check_apps_cpu(self):
        for app in self.monitored_apps:
            # Skip disabled apps
            if not app.get("enabled", True):
                continue
                
            try:
                cpu_percent, process_count = self.get_app_cpu_usage_detailed(app["name"])
                app["last_cpu"] = cpu_percent

                # Check if application is terminated and auto-restart is enabled
                if process_count == 0 and self.auto_restart_enabled:
                    if app["status"] != "Terminated":
                        app["status"] = "Terminated"
                        self.log_message(f"DETECTED: {app["name"]} has been terminated")
                        self.restart_terminated_app(app)

                # Check if CPU exceeds threshold
                elif cpu_percent > self.cpu_threshold:
                    current_time = time.time()
                    
                    # If this is the first time exceeding threshold, record the time
                    if app.get("threshold_exceeded_time") is None:
                        app["threshold_exceeded_time"] = current_time
                        self.log_message(f"WARNING: {app["name"]} CPU usage: {cpu_percent:.1f}% (exceeds {self.cpu_threshold}%) - Starting threshold timer")
                    
                    # Check if CPU has been above threshold for the required duration
                    elif current_time - app["threshold_exceeded_time"] >= self.cpu_threshold_duration:
                        self.log_message(f"CRITICAL: {app["name"]} CPU usage: {cpu_percent:.1f}% (exceeds {self.cpu_threshold}% for {self.cpu_threshold_duration}s) - Restarting")
                        self.restart_app(app)
                        # Reset the timer after restart
                        app["threshold_exceeded_time"] = None
                    else:
                        # Still above threshold but not long enough
                        remaining_time = self.cpu_threshold_duration - (current_time - app["threshold_exceeded_time"])
                        self.log_message(f"WARNING: {app["name"]} CPU usage: {cpu_percent:.1f}% (exceeds {self.cpu_threshold}%) - {remaining_time:.1f}s remaining before restart")
                
                # If CPU is below threshold, reset the timer
                elif app.get("threshold_exceeded_time") is not None:
                    app["threshold_exceeded_time"] = None
                    self.log_message(f"INFO: {app["name"]} CPU usage normalized: {cpu_percent:.1f}% (below {self.cpu_threshold}%)")

                # Update status if app is running normally
                elif process_count > 0 and app["status"] in ["Terminated", "Restarting"]:
                    app["status"] = "Active"

            except Exception as e:
                self.log_message(f"Error checking {app['name']}: {str(e)}")
                logging.error(f"Error checking {app['name']}: {str(e)}")

        # Update UI
        self.root.after(0, self.update_app_tree)

    def get_app_cpu_usage_detailed(self, app_name):
        total_cpu = 0.0
        process_count = 0

        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "exe"]):
            try:
                # Safely get process info with null checks
                proc_name = proc.info.get("name")
                proc_exe = proc.info.get("exe")
                
                # Skip processes with no name
                if not proc_name:
                    continue
                
                proc_name_lower = proc_name.lower()
                proc_exe_lower = proc_exe.lower() if proc_exe else ""
                
                # Check if process name matches or if executable path contains the app name
                if (app_name.lower() in proc_name_lower or 
                    (proc_exe_lower and app_name.lower() in proc_exe_lower)):
                    
                    # Get CPU usage with proper initialization (CPU only, excluding GPU)
                    try:
                        # First call to initialize (returns 0.0)
                        proc.cpu_percent()
                        # Wait a bit for the next call to be accurate
                        time.sleep(0.1)
                        # Second call should give us the actual CPU usage
                        raw_cpu = proc.cpu_percent()
                        
                        # Apply CPU-only filtering to exclude GPU-related usage
                        cpu = self._filter_gpu_usage(raw_cpu, proc)
                        
                        total_cpu += cpu
                        process_count += 1
                        
                        # Log for debugging
                        if cpu > 0:
                            self.log_message(f"Process {proc_name} (PID: {proc.info['pid']}) CPU: {cpu:.1f}% (filtered from {raw_cpu:.1f}%)")
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return total_cpu, process_count
        
    def _filter_gpu_usage(self, raw_cpu, proc):
        """Filter out GPU-related CPU usage to get true CPU-only percentage"""
        try:
            # Get process CPU times to calculate more accurate CPU usage
            cpu_times = proc.cpu_times()
            
            # Calculate CPU usage based on user time (excludes system/kernel time which may include GPU)
            # This gives us a more accurate representation of actual CPU work
            if hasattr(cpu_times, 'user'):
                # Use configurable factor to filter out GPU overhead
                filtered_cpu = raw_cpu * self.gpu_filter_factor
                
                # Ensure we don't go below 0
                filtered_cpu = max(0.0, filtered_cpu)
                
                return filtered_cpu
            
            # Fallback: use raw CPU but with some filtering
            return raw_cpu * self.gpu_filter_factor
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            # If we can't get CPU times, use configurable filtering
            return raw_cpu * self.gpu_filter_factor

    def restart_app(self, app):
        try:
            app_name = app["name"]
            process_name = app.get("process_name", app_name)
            self.log_message(f"Attempting to restart {app_name}...")

            # Kill existing processes - try multiple ways to find the process
            killed_count = 0
            for proc in psutil.process_iter(["pid", "name", "exe"]):
                try:
                    # Safely get process info with null checks
                    proc_name = proc.info.get("name")
                    proc_exe = proc.info.get("exe")
                    
                    # Skip processes with no name
                    if not proc_name:
                        continue
                    
                    proc_name_lower = proc_name.lower()
                    proc_exe_lower = proc_exe.lower() if proc_exe else ""
                    
                    # Check if process name matches or if executable path contains the app name
                    if (app_name.lower() in proc_name_lower or 
                        process_name.lower() in proc_name_lower or
                        (proc_exe_lower and app_name.lower() in proc_exe_lower)):
                        
                        self.log_message(f"Found process: {proc_name} (PID: {proc.info['pid']})")
                        proc.terminate()
                        killed_count += 1
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if killed_count > 0:
                self.log_message(f"Terminated {killed_count} {app_name} process(es)")

                # Wait for processes to fully terminate, then apply startup delay
                time.sleep(2)
                self.log_message(f"Waiting {self.startup_delay} seconds before restarting {app_name}...")
                time.sleep(self.startup_delay)

                # Try to restart the application
                restart_success = False
                
                # First try executable path if available
                if app.get("executable_path") and os.path.exists(app["executable_path"]):
                    try:
                        subprocess.Popen([app["executable_path"]],
                                       creationflags=subprocess.CREATE_NEW_CONSOLE)
                        self.log_message(f"Restarted {app_name} from executable path: {app['executable_path']}")
                        restart_success = True
                    except Exception as e:
                        self.log_message(f"Failed to restart from executable path: {str(e)}")
                
                # If executable path failed, try common locations
                if not restart_success:
                    common_paths = [
                        f"C:\\Program Files\\{app_name}\\{app_name}.exe",
                        f"C:\\Program Files (x86)\\{app_name}\\{app_name}.exe",
                        f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\{app_name}\\{app_name}.exe",
                        f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Roaming\\{app_name}\\{app_name}.exe"
                    ]
                    
                    for path in common_paths:
                        if os.path.exists(path):
                            try:
                                subprocess.Popen([path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                                self.log_message(f"Restarted {app_name} from common path: {path}")
                                restart_success = True
                                # Update the executable path for future use
                                app["executable_path"] = path
                                break
                            except Exception as e:
                                self.log_message(f"Failed to restart from {path}: {str(e)}")
                
                # Last resort: try to start by name
                if not restart_success:
                    try:
                        subprocess.Popen([app_name], creationflags=subprocess.CREATE_NEW_CONSOLE)
                        self.log_message(f"Restarted {app_name} by name (last resort)")
                        restart_success = True
                    except Exception as e:
                        self.log_message(f"Failed to restart {app_name} by name: {str(e)}")

                if restart_success:
                    app["restart_count"] += 1
                    app["status"] = "Restarted"
                    
                    # Show notification
                    messagebox.showinfo("App Restarted",
                                      f"{app_name} has been restarted due to high CPU usage ({app['last_cpu']:.1f}%)")
                else:
                    app["status"] = "Restart Failed"
                    self.log_message(f"Failed to restart {app_name} - all methods exhausted")

            else:
                self.log_message(f"No {app_name} process(es) found to restart")

        except Exception as e:
            error_msg = f"Error restarting {app['name']}: {str(e)}"
            self.log_message(error_msg)
            logging.error(error_msg)

    def restart_terminated_app(self, app):
        try:
            app_name = app["name"]
            app["status"] = "Restarting"
            self.log_message(f"Auto-restarting terminated application: {app_name}")

            # Apply startup delay before restarting
            if self.startup_delay > 0:
                self.log_message(f"Waiting {self.startup_delay} seconds before restarting {app_name}...")
                time.sleep(self.startup_delay)

            # Try to restart the application using the same logic as manual restart
            restart_success = False
            
            # First try executable path if available
            if app.get("executable_path") and os.path.exists(app["executable_path"]):
                try:
                    subprocess.Popen([app["executable_path"]],
                                   creationflags=subprocess.CREATE_NEW_CONSOLE)
                    self.log_message(f"Auto-restarted {app_name} from executable path: {app['executable_path']}")
                    restart_success = True
                except Exception as e:
                    self.log_message(f"Failed to auto-restart from executable path: {str(e)}")
            
            # If executable path failed, try common locations
            if not restart_success:
                common_paths = [
                    f"C:\\Program Files\\{app_name}\\{app_name}.exe",
                    f"C:\\Program Files (x86)\\{app_name}\\{app_name}.exe",
                    f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\{app_name}\\{app_name}.exe",
                    f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Roaming\\{app_name}\\{app_name}.exe"
                ]
                
                for path in common_paths:
                    if os.path.exists(path):
                        try:
                            subprocess.Popen([path], creationflags=subprocess.CREATE_NEW_CONSOLE)
                            self.log_message(f"Auto-restarted {app_name} from common path: {path}")
                            restart_success = True
                            # Update the executable path for future use
                            app["executable_path"] = path
                            break
                        except Exception as e:
                            self.log_message(f"Failed to auto-restart from {path}: {str(e)}")
            
            # Last resort: try to start by name
            if not restart_success:
                try:
                    subprocess.Popen([app_name], creationflags=subprocess.CREATE_NEW_CONSOLE)
                    self.log_message(f"Auto-restarted {app_name} by name (last resort)")
                    restart_success = True
                except Exception as e:
                    self.log_message(f"Failed to auto-restart {app_name} by name: {str(e)}")

            if restart_success:
                app["restart_count"] += 1
                app["status"] = "Auto-Restarted"
                
                # Show notification
                messagebox.showinfo("App Auto-Restarted",
                                  f"{app_name} was terminated and has been automatically restarted")
            else:
                app["status"] = "Auto-Restart Failed"
                self.log_message(f"Failed to auto-restart {app_name} - all methods exhausted")

        except Exception as e:
            error_msg = f"Error auto-restarting {app['name']}: {str(e)}"
            self.log_message(error_msg)
            logging.error(error_msg)
            app["status"] = "Auto-Restart Failed"

    def find_executable_path(self, app_name):
        """Find the executable path for a given application name"""
        try:
            # First check if it's already in PATH
            try:
                result = subprocess.run(['where', app_name], capture_output=True, text=True, shell=True)
                if result.returncode == 0:
                    paths = result.stdout.strip().split('\n')
                    if paths:
                        return paths[0]  # Return the first found path
            except:
                pass
            
            # Check common installation directories
            common_paths = [
                f"C:\\Program Files\\{app_name}\\{app_name}.exe",
                f"C:\\Program Files (x86)\\{app_name}\\{app_name}.exe",
                f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Local\\{app_name}\\{app_name}.exe",
                f"C:\\Users\\{os.getenv('USERNAME')}\\AppData\\Roaming\\{app_name}\\{app_name}.exe",
                f"C:\\Program Files\\{app_name.capitalize()}\\{app_name.capitalize()}.exe",
                f"C:\\Program Files (x86)\\{app_name.capitalize()}\\{app_name.capitalize()}.exe"
            ]
            
            for path in common_paths:
                if os.path.exists(path):
                    return path
            
            # Try to find by searching running processes
            for proc in psutil.process_iter(["pid", "name", "exe"]):
                try:
                    proc_name = proc.info.get("name")
                    if proc_name and app_name.lower() in proc_name.lower():
                        exe_path = proc.info.get("exe")
                        if exe_path and os.path.exists(exe_path):
                            return exe_path
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return None
            
        except Exception as e:
            self.log_message(f"Error finding executable for {app_name}: {str(e)}")
            return None

    def discover_executable_paths(self):
        """Automatically discover and update executable paths for all monitored apps"""
        print("DEBUG: discover_executable_paths method called")  # Immediate console output
        self.log_message("Discovering executable paths for monitored applications...")
        
        for app in self.monitored_apps:
            if not app.get("executable_path"):
                exe_path = self.find_executable_path(app["name"])
                if exe_path:
                    app["executable_path"] = exe_path
                    self.log_message(f"Found executable for {app['name']}: {exe_path}")
                else:
                    self.log_message(f"Could not find executable for {app['name']}")
        
        # Save the updated configuration
        self.save_monitored_apps()
        self.update_app_tree()
        self.log_message("Executable discovery completed!")

    def debug_cpu_monitoring(self):
        """Debug CPU monitoring for all apps"""
        print("DEBUG: debug_cpu_monitoring method called")  # Immediate console output
        self.log_message("=== DEBUG: CPU Monitoring Test ===")
        self.log_message(f"Current settings: CPU threshold: {self.cpu_threshold}%, Duration: {self.cpu_threshold_duration}s")
        
        for app in self.monitored_apps:
            if app.get("enabled", True):
                self.log_message(f"Testing CPU monitoring for: {app['name']}")
                cpu_percent, process_count = self.get_app_cpu_usage_detailed(app["name"])
                self.log_message(f"  Found {process_count} processes, Total CPU: {cpu_percent:.1f}%")
                
                # Update the app's CPU value for display
                app["last_cpu"] = cpu_percent
                
                # Check if we can find the process by name
                found_by_name = False
                for proc in psutil.process_iter(["pid", "name"]):
                    try:
                        proc_name = proc.info.get("name")
                        if proc_name and app["name"].lower() in proc_name.lower():
                            found_by_name = True
                            self.log_message(f"  Found by name: {proc_name} (PID: {proc.info['pid']})")
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                if not found_by_name:
                    self.log_message(f"  WARNING: Could not find process by name '{app['name']}'")
                
                # Check if we can find the process by process_name
                if app.get("process_name"):
                    found_by_process_name = False
                    for proc in psutil.process_iter(["pid", "name"]):
                        try:
                            proc_name = proc.info.get("name")
                            if proc_name and app["process_name"].lower() in proc_name.lower():
                                found_by_process_name = True
                                self.log_message(f"  Found by process_name: {proc_name} (PID: {proc.info['pid']})")
                                break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    
                    if not found_by_process_name:
                        self.log_message(f"  WARNING: Could not find process by process_name '{app['process_name']}'")
        
        # Update the display
        self.update_app_tree()
        self.log_message("=== DEBUG: CPU Monitoring Test Complete ===")

    def set_executable_path(self, app_name, executable_path):
        """Manually set the executable path for a specific application"""
        for app in self.monitored_apps:
            if app["name"] == app_name:
                if os.path.exists(executable_path):
                    app["executable_path"] = executable_path
                    self.log_message(f"Set executable path for {app_name}: {executable_path}")
                    self.save_monitored_apps()
                    self.update_app_tree()
                    return True
                else:
                    self.log_message(f"Executable path does not exist: {executable_path}")
                    return False
        return False

    def show_app_context_menu(self, event):
        """Show context menu for app tree items"""
        selection = self.app_tree.selection()
        if not selection:
            return
        
        # Get the selected app
        item = self.app_tree.item(selection[0])
        app_name = item["values"][0]
        
        # Create context menu
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label=f"Set Executable Path for {app_name}", 
                               command=lambda: self.prompt_executable_path(app_name))
        context_menu.add_command(label=f"Reset Threshold Timer for {app_name}", 
                               command=lambda: self.reset_threshold_timer(app_name))
        context_menu.add_separator()
        context_menu.add_command(label=f"Remove {app_name}", 
                               command=lambda: self.remove_app_by_name(app_name))
        
        # Show context menu at cursor position
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def prompt_executable_path(self, app_name):
        """Prompt user to enter executable path for an app"""
        executable_path = filedialog.askopenfilename(
            title=f"Select executable for {app_name}",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        
        if executable_path:
            self.set_executable_path(app_name, executable_path)

    def reset_threshold_timer(self, app_name):
        """Reset the threshold timer for a specific application"""
        for app in self.monitored_apps:
            if app["name"] == app_name:
                if app.get("threshold_exceeded_time") is not None:
                    app["threshold_exceeded_time"] = None
                    self.log_message(f"Reset threshold timer for {app_name}")
                    self.update_app_tree()
                    self.save_monitored_apps()
                else:
                    self.log_message(f"No active threshold timer for {app_name}")
                break

    def remove_app_by_name(self, app_name):
        """Remove app by name (for context menu)"""
        # Show confirmation dialog
        result = messagebox.askyesno(
            "Confirm Removal",
            f'Are you sure you want to remove "{app_name}" from monitoring?\n\nThis action cannot be undone.'
        )
        
        if result:
            # Remove from list
            self.monitored_apps = [app for app in self.monitored_apps if app["name"] != app_name]
            self.update_app_tree()
            self.save_monitored_apps()
            self.log_message(f"Removed application: {app_name}")

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Also print to console for debugging, but filter out Reolink error messages if enabled
        if self.filter_reolink_errors and self._is_reolink_error(message):
            # Don't print to console, but still log to the UI
            pass
        else:
            print(f"LOG: {log_entry.strip()}")
        
        # Update log in main thread with error handling
        try:
            self.root.after(0, lambda: self.update_log(log_entry))
        except Exception as e:
            print(f"Error in log_message: {e}")
            # Fallback: try to update log directly
            try:
                self.update_log(log_entry)
            except Exception as e2:
                print(f"Fallback log update also failed: {e2}")

    def _is_reolink_error(self, message):
        """Check if a message is a Reolink error that should be filtered from console output"""
        # Filter out common Reolink error patterns
        reolink_error_patterns = [
            "handle this channel cmd:",
            "E_BC_CMD_GET_WIFI_SIGNAL",
            "handle:",
            "channel:",
            "cmd param: undefined",
            "-------",  # Filter out separator lines
            "e_bc_cmd",  # Filter out other Reolink command errors
            "cmd param:",
            "undefined"
        ]
        
        message_lower = message.lower()
        for pattern in reolink_error_patterns:
            if pattern.lower() in message_lower:
                return True
        return False

    def update_log(self, log_entry):
        try:
            if hasattr(self, 'log_text') and self.log_text:
                self.log_text.insert(tk.END, log_entry)
                self.log_text.see(tk.END)  # Auto-scroll to bottom
            else:
                print(f"WARNING: log_text not available, message: {log_entry.strip()}")
        except Exception as e:
            print(f"Error in update_log: {e}")
            print(f"Failed to log: {log_entry.strip()}")

    def save_settings(self):
        settings = {
            "cpu_threshold": self.cpu_threshold,
            "check_interval": self.check_interval,
            "startup_delay": self.startup_delay,
            "monitoring_startup_delay": self.monitoring_startup_delay,
            "cpu_threshold_duration": self.cpu_threshold_duration,
            "filter_reolink_errors": self.filter_reolink_errors,
            "gpu_filter_factor": self.gpu_filter_factor,
            "auto_restart_enabled": self.auto_restart_enabled
        }

        try:
            with open("settings.json", "w") as f:
                json.dump(settings, f)
        except Exception as e:
            logging.error(f"Error saving settings: {str(e)}")

    def load_settings(self):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r") as f:
                    settings = json.load(f)
                    self.cpu_threshold = settings.get("cpu_threshold", 50.0)
                    self.check_interval = settings.get("check_interval", 5.0)
                    self.startup_delay = settings.get("startup_delay", 3.0)
                    self.monitoring_startup_delay = settings.get("monitoring_startup_delay", 10.0)
                    self.cpu_threshold_duration = settings.get("cpu_threshold_duration", 30.0)
                    self.filter_reolink_errors = settings.get("filter_reolink_errors", True)
                    self.gpu_filter_factor = settings.get("gpu_filter_factor", 0.5)
                    self.auto_restart_enabled = settings.get("auto_restart_enabled", True)
        except Exception as e:
            logging.error(f"Error loading settings: {str(e)}")

    def save_monitored_apps(self):
        try:
            with open("monitored_apps.json", "w") as f:
                json.dump(self.monitored_apps, f)
        except Exception as e:
            logging.error(f"Error saving monitored apps: {str(e)}")

    def load_monitored_apps(self):
        try:
            if os.path.exists("monitored_apps.json"):
                with open("monitored_apps.json", "r") as f:
                    self.monitored_apps = json.load(f)
                    # Ensure all apps have the required fields
                    for app in self.monitored_apps:
                        if "enabled" not in app:
                            app["enabled"] = True
                        if "threshold_exceeded_time" not in app:
                            app["threshold_exceeded_time"] = None
                    self.update_app_tree()
        except Exception as e:
            logging.error(f"Error loading monitored apps: {str(e)}")

    def on_closing(self):
        if self.monitoring:
            self.stop_monitoring()
        self.save_settings()
        self.save_monitored_apps()
        
        # Restore original stdout/stderr
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
        self.root.destroy()

def main():
    root = tk.Tk()
    app = CPUMonitorApp(root)

    # Set closing protocol
    root.protocol("WM_DELETE_WINDOW", app.on_closing)

    # Center window on screen with fixed size
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - 450  # Center 900x960 window
    y = (root.winfo_screenheight() // 2) - 480
    root.geometry(f"900x960+{x}+{y}")

    root.mainloop()

if __name__ == "__main__":
    main()
