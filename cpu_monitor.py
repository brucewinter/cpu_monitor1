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

class CPUMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CPU Monitor & App Restarter")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # Configure logging
        logging.basicConfig(
            filename='cpu_monitor.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # App state
        self.monitoring = False
        self.monitor_thread = None
        self.monitored_apps = []
        self.cpu_threshold = 50.0
        self.check_interval = 5.0  # seconds
        self.startup_delay = 3.0  # seconds to wait before restarting apps
        self.auto_restart_enabled = True  # enable automatic restart of terminated apps
        
        # Load saved settings
        self.load_settings()
        
        self.setup_ui()
        self.setup_styles()
        
    def setup_styles(self):
        """Configure modern styling for the application"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 16, 'bold'),
                       foreground='#ffffff',
                       background='#2b2b2b')
        
        style.configure('Header.TLabel',
                       font=('Segoe UI', 12, 'bold'),
                       foreground='#00ff88',
                       background='#2b2b2b')
        
        style.configure('Info.TLabel',
                       font=('Segoe UI', 10),
                       foreground='#cccccc',
                       background='#2b2b2b')
        
        style.configure('Custom.TFrame',
                       background='#3c3c3c',
                       relief='raised',
                       borderwidth=1)
        
        style.configure('Custom.TButton',
                       font=('Segoe UI', 10, 'bold'),
                       padding=10)
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main title
        title_frame = tk.Frame(self.root, bg='#2b2b2b')
        title_frame.pack(fill='x', padx=20, pady=20)
        
        title_label = tk.Label(title_frame, 
                              text="CPU Monitor & App Restarter",
                              font=('Segoe UI', 20, 'bold'),
                              fg='#00ff88',
                              bg='#2b2b2b')
        title_label.pack()
        
        # Settings frame
        settings_frame = ttk.Frame(self.root, style='Custom.TFrame')
        settings_frame.pack(fill='x', padx=20, pady=10)
        
        # CPU Threshold setting
        threshold_frame = tk.Frame(settings_frame, bg='#3c3c3c')
        threshold_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(threshold_frame, 
                text="CPU Threshold (%):",
                font=('Segoe UI', 10, 'bold'),
                fg='#ffffff',
                bg='#3c3c3c').pack(side='left', padx=(0, 10))
        
        self.threshold_var = tk.StringVar(value=str(self.cpu_threshold))
        threshold_entry = tk.Entry(threshold_frame, 
                                 textvariable=self.threshold_var,
                                 font=('Segoe UI', 10),
                                 width=10,
                                 bg='#4a4a4a',
                                 fg='#ffffff',
                                 insertbackground='#ffffff')
        threshold_entry.pack(side='left')
        
        # Check interval setting
        interval_frame = tk.Frame(settings_frame, bg='#3c3c3c')
        interval_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(interval_frame, 
                text="Check Interval (seconds):",
                font=('Segoe UI', 10, 'bold'),
                fg='#ffffff',
                bg='#3c3c3c').pack(side='left', padx=(0, 10))
        
        self.interval_var = tk.StringVar(value=str(self.check_interval))
        interval_entry = tk.Entry(interval_frame, 
                                textvariable=self.interval_var,
                                font=('Segoe UI', 10),
                                width=10,
                                bg='#4a4a4a',
                                fg='#ffffff',
                                insertbackground='#ffffff')
        interval_entry.pack(side='left')
        
        # Startup delay setting
        delay_frame = tk.Frame(settings_frame, bg='#3c3c3c')
        delay_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(delay_frame, 
                text="Startup Delay (seconds):",
                font=('Segoe UI', 10, 'bold'),
                fg='#ffffff',
                bg='#3c3c3c').pack(side='left', padx=(0, 10))
        
        self.delay_var = tk.StringVar(value=str(self.startup_delay))
        delay_entry = tk.Entry(delay_frame, 
                              textvariable=self.delay_var,
                              font=('Segoe UI', 10),
                              width=10,
                              bg='#4a4a4a',
                              fg='#ffffff',
                              insertbackground='#ffffff')
        delay_entry.pack(side='left')
        
        # Auto-restart checkbox
        restart_frame = tk.Frame(settings_frame, bg='#3c3c3c')
        restart_frame.pack(fill='x', padx=20, pady=10)
        
        self.auto_restart_var = tk.BooleanVar(value=self.auto_restart_enabled)
        restart_checkbox = tk.Checkbutton(restart_frame,
                                        text="Auto-restart terminated applications",
                                        variable=self.auto_restart_var,
                                        font=('Segoe UI', 10, 'bold'),
                                        fg='#ffffff',
                                        bg='#3c3c3c',
                                        activeforeground='#ffffff',
                                        activebackground='#3c3c3c',
                                        selectcolor='#00ff88')
        restart_checkbox.pack(side='left')
        
        # App management frame
        app_frame = ttk.Frame(self.root, style='Custom.TFrame')
        app_frame.pack(fill='x', padx=20, pady=10)
        
        # Add app section
        add_app_frame = tk.Frame(app_frame, bg='#3c3c3c')
        add_app_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(add_app_frame, 
                text="Add Application to Monitor:",
                font=('Segoe UI', 12, 'bold'),
                fg='#ffffff',
                bg='#3c3c3c').pack(anchor='w')
        
        app_input_frame = tk.Frame(add_app_frame, bg='#3c3c3c')
        app_input_frame.pack(fill='x', pady=5)
        
        self.app_name_var = tk.StringVar()
        app_name_entry = tk.Entry(app_input_frame, 
                                 textvariable=self.app_name_var,
                                 font=('Segoe UI', 10),
                                 bg='#4a4a4a',
                                 fg='#ffffff',
                                 insertbackground='#ffffff')
        app_name_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        add_btn = tk.Button(app_input_frame,
                           text="Add App",
                           command=self.add_app,
                           font=('Segoe UI', 10, 'bold'),
                           bg='#00ff88',
                           fg='#000000',
                           relief='flat',
                           padx=20)
        add_btn.pack(side='right')
        
        # Browse button for executable
        browse_btn = tk.Button(app_input_frame,
                              text="Browse",
                              command=self.browse_executable,
                              font=('Segoe UI', 10),
                              bg='#4a4a4a',
                              fg='#ffffff',
                              relief='flat',
                              padx=15)
        browse_btn.pack(side='right', padx=(0, 10))
        
        # Monitored apps list
        list_frame = tk.Frame(app_frame, bg='#3c3c3c')
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        tk.Label(list_frame, 
                text="Monitored Applications:",
                font=('Segoe UI', 12, 'bold'),
                fg='#ffffff',
                bg='#3c3c3c').pack(anchor='w')
        
        # Create Treeview for apps
        columns = ('App Name', 'Process Name', 'Status', 'Last CPU %', 'Restart Count')
        self.app_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=6)
        
        for col in columns:
            self.app_tree.heading(col, text=col)
            self.app_tree.column(col, width=120, anchor='center')
        
        self.app_tree.pack(fill='both', expand=True, pady=5)
        
        # Remove app button
        remove_btn = tk.Button(list_frame,
                              text="Remove Selected App",
                              command=self.remove_app,
                              font=('Segoe UI', 10),
                              bg='#ff4444',
                              fg='#ffffff',
                              relief='flat',
                              padx=15)
        remove_btn.pack(pady=5)
        
        # Control buttons frame
        control_frame = tk.Frame(self.root, bg='#2b2b2b')
        control_frame.pack(fill='x', padx=20, pady=20)
        
        self.start_btn = tk.Button(control_frame,
                                  text="Start Monitoring",
                                  command=self.start_monitoring,
                                  font=('Segoe UI', 12, 'bold'),
                                  bg='#00ff88',
                                  fg='#000000',
                                  relief='flat',
                                  padx=30,
                                  pady=10)
        self.start_btn.pack(side='left', padx=(0, 10))
        
        self.stop_btn = tk.Button(control_frame,
                                 text="Stop Monitoring",
                                 command=self.stop_monitoring,
                                 font=('Segoe UI', 12, 'bold'),
                                 bg='#ff4444',
                                 fg='#ffffff',
                                 relief='flat',
                                 padx=30,
                                 pady=10,
                                 state='disabled')
        self.stop_btn.pack(side='left')`n`n        # Add pause button`n        self.pause_btn = tk.Button(control_frame,`n                                  text="Pause Monitoring",`n                                  command=self.pause_monitoring,`n                                  font=('Segoe UI', 12, 'bold'),`n                                  bg='#ffaa00',`n                                  fg='#000000',`n                                  relief='flat',`n                                  padx=30,`n                                  pady=10,`n                                  state='disabled')`n        self.pause_btn.pack(side='left', padx=(0, 10))
        
        # Status frame
        status_frame = tk.Frame(self.root, bg='#2b2b2b')
        status_frame.pack(fill='x', padx=20, pady=10)
        
        self.status_label = tk.Label(status_frame,
                                    text="Status: Ready",
                                    font=('Segoe UI', 10),
                                    fg='#00ff88',
                                    bg='#2b2b2b')
        self.status_label.pack(anchor='w')
        
        # Log frame
        log_frame = ttk.Frame(self.root, style='Custom.TFrame')
        log_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        tk.Label(log_frame, 
                text="Activity Log:",
                font=('Segoe UI', 12, 'bold'),
                fg='#ffffff',
                bg='#3c3c3c').pack(anchor='w', padx=20, pady=10)
        
        self.log_text = tk.Text(log_frame,
                                height=8,
                                bg='#1e1e1e',
                                fg='#00ff88',
                                font=('Consolas', 9),
                                wrap='word')
        self.log_text.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Scrollbar for log
        log_scrollbar = tk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        log_scrollbar.pack(side='right', fill='y')
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        # Load existing apps
        self.load_monitored_apps()
        
    def add_app(self):
        """Add a new application to monitor"""
        app_name = self.app_name_var.get().strip()
        if not app_name:
            messagebox.showerror("Error", "Please enter an application name")
            return
            
        # Check if app already exists
        for app in self.monitored_apps:
            if app['name'] == app_name:
                messagebox.showerror("Error", "Application already exists in the list")
                return
        
        # Add to monitored apps
        new_app = {
            'name': app_name,
            'process_name': app_name.lower(),
            'status': 'Active',
            'last_cpu': 0.0,
            'restart_count': 0,
            'executable_path': None
        }
        
        self.monitored_apps.append(new_app)
        self.update_app_tree()
        self.app_name_var.set("")
        self.save_monitored_apps()
        self.log_message(f"Added application: {app_name}")
        
    def browse_executable(self):
        """Browse for executable file"""
        file_path = filedialog.askopenfilename(
            title="Select Application Executable",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if file_path:
            app_name = os.path.splitext(os.path.basename(file_path))[0]
            self.app_name_var.set(app_name)
            
    def remove_app(self):
        """Remove selected application from monitoring"""
        selection = self.app_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an application to remove")
            return
            
        item = self.app_tree.item(selection[0])
        app_name = item['values'][0]
        
        # Remove from list
        self.monitored_apps = [app for app in self.monitored_apps if app['name'] != app_name]
        self.update_app_tree()
        self.save_monitored_apps()
        self.log_message(f"Removed application: {app_name}")
        
    def update_app_tree(self):
        """Update the applications treeview"""
        # Clear existing items
        for item in self.app_tree.get_children():
            self.app_tree.delete(item)
            
        # Add current apps
        for app in self.monitored_apps:
            self.app_tree.insert('', 'end', values=(
                app['name'],
                app['process_name'],
                app['status'],
                f"{app['last_cpu']:.1f}%",
                app['restart_count']
            ))
            
    def start_monitoring(self):
        try:
            self.cpu_threshold = float(self.threshold_var.get())
            self.check_interval = float(self.interval_var.get())
            self.startup_delay = float(self.delay_var.get())
            self.auto_restart_enabled = self.auto_restart_var.get()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for threshold, interval, and startup delay")
            return
            
        if not self.monitored_apps:
            messagebox.showwarning("Warning", "Please add at least one application to monitor")
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.start_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.status_label.config(text="Status: Monitoring Active", fg='#00ff88')
        self.log_message("Started CPU monitoring")
        
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.monitoring = False
        self.start_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        self.status_label.config(text="Status: Stopped", fg='#ff4444')
        self.log_message("Stopped CPU monitoring")
        
    def monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                self.check_apps_cpu()
                time.sleep(self.check_interval)
            except Exception as e:
                self.log_message(f"Error in monitoring loop: {str(e)}")
                logging.error(f"Monitoring loop error: {str(e)}")
                
    def check_apps_cpu(self):
        """Check CPU usage for all monitored applications"""
        for app in self.monitored_apps:
            try:
                cpu_percent, process_count = self.get_app_cpu_usage_detailed(app['name'])
                app['last_cpu'] = cpu_percent
                
                # Check if application is terminated and auto-restart is enabled
                if process_count == 0 and self.auto_restart_enabled:
                    if app['status'] != 'Terminated':
                        app['status'] = 'Terminated'
                        self.log_message(f"DETECTED: {app['name']} has been terminated")
                        self.restart_terminated_app(app)
                    
                # Check if CPU exceeds threshold
                elif cpu_percent > self.cpu_threshold:
                    self.log_message(f"WARNING: {app['name']} CPU usage: {cpu_percent:.1f}% (exceeds {self.cpu_threshold}%)")
                    self.restart_app(app)
                    
                # Update status if app is running normally
                elif process_count > 0 and app['status'] in ['Terminated', 'Restarting']:
                    app['status'] = 'Active'
                    
            except Exception as e:
                self.log_message(f"Error checking {app['name']}: {str(e)}")
                logging.error(f"Error checking {app['name']}: {str(e)}")
                
        # Update UI
        self.root.after(0, self.update_app_tree)
        
    def get_app_cpu_usage(self, app_name):
        """Get CPU usage for a specific application (legacy method for compatibility)"""
        cpu_usage, _ = self.get_app_cpu_usage_detailed(app_name)
        return cpu_usage
        
    def get_app_cpu_usage_detailed(self, app_name):
        """Get CPU usage and process count for a specific application"""
        total_cpu = 0.0
        process_count = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                if app_name.lower() in proc.info['name'].lower():
                    proc.cpu_percent()  # First call to initialize
                    time.sleep(0.1)  # Small delay for accurate reading
                    cpu = proc.cpu_percent()
                    total_cpu += cpu
                    process_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
                
        return total_cpu, process_count
        
    def restart_app(self, app):
        """Restart the specified application"""
        try:
            app_name = app['name']
            self.log_message(f"Attempting to restart {app_name}...")
            
            # Kill existing processes
            killed_count = 0
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if app_name.lower() in proc.info['name'].lower():
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
                if app.get('executable_path') and os.path.exists(app['executable_path']):
                    subprocess.Popen([app['executable_path']], 
                                   creationflags=subprocess.CREATE_NEW_CONSOLE)
                    self.log_message(f"Restarted {app_name} from executable path")
                else:
                    # Try to start by name
                    subprocess.Popen([app_name], 
                                   creationflags=subprocess.CREATE_NEW_CONSOLE)
                    self.log_message(f"Restarted {app_name} by name")
                    
                app['restart_count'] += 1
                app['status'] = 'Restarted'
                
                # Show notification
                messagebox.showinfo("App Restarted", 
                                  f"{app_name} has been restarted due to high CPU usage ({app['last_cpu']:.1f}%)")
                                  
            else:
                self.log_message(f"No {app_name} processes found to restart")
                
        except Exception as e:
            error_msg = f"Error restarting {app['name']}: {str(e)}"
            self.log_message(error_msg)
            logging.error(error_msg)
            
    def restart_terminated_app(self, app):
        """Restart an application that has been terminated"""
        try:
            app_name = app['name']
            app['status'] = 'Restarting'
            self.log_message(f"Auto-restarting terminated application: {app_name}")
            
            # Apply startup delay before restarting
            if self.startup_delay > 0:
                self.log_message(f"Waiting {self.startup_delay} seconds before restarting {app_name}...")
                time.sleep(self.startup_delay)
            
            # Try to restart the application
            if app.get('executable_path') and os.path.exists(app['executable_path']):
                subprocess.Popen([app['executable_path']], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
                self.log_message(f"Auto-restarted {app_name} from executable path")
            else:
                # Try to start by name
                subprocess.Popen([app_name], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
                self.log_message(f"Auto-restarted {app_name} by name")
                
            app['restart_count'] += 1
            app['status'] = 'Auto-Restarted'
            
            # Show notification
            messagebox.showinfo("App Auto-Restarted", 
                              f"{app_name} was terminated and has been automatically restarted")
                              
        except Exception as e:
            error_msg = f"Error auto-restarting {app['name']}: {str(e)}"
            self.log_message(error_msg)
            logging.error(error_msg)
            app['status'] = 'Restart Failed'
            
    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Update log in main thread
        self.root.after(0, lambda: self.update_log(log_entry))
        
    def update_log(self, log_entry):
        """Update the log text widget"""
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Limit log size
        if int(self.log_text.index('end-1c').split('.')[0]) > 1000:
            self.log_text.delete('1.0', '100.0')
            
    def save_settings(self):
        """Save application settings"""
        settings = {
            'cpu_threshold': self.cpu_threshold,
            'check_interval': self.check_interval,
            'startup_delay': self.startup_delay,
            'auto_restart_enabled': self.auto_restart_enabled
        }
        
        try:
            with open('settings.json', 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            logging.error(f"Error saving settings: {str(e)}")
            
    def load_settings(self):
        """Load application settings"""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
                    self.cpu_threshold = settings.get('cpu_threshold', 50.0)
                    self.check_interval = settings.get('check_interval', 5.0)
                    self.startup_delay = settings.get('startup_delay', 3.0)
                    self.auto_restart_enabled = settings.get('auto_restart_enabled', True)
        except Exception as e:
            logging.error(f"Error loading settings: {str(e)}")
            
    def save_monitored_apps(self):
        """Save monitored applications list"""
        try:
            with open('monitored_apps.json', 'w') as f:
                json.dump(self.monitored_apps, f)
        except Exception as e:
            logging.error(f"Error saving monitored apps: {str(e)}")
            
    def load_monitored_apps(self):
        """Load monitored applications list"""
        try:
            if os.path.exists('monitored_apps.json'):
                with open('monitored_apps.json', 'r') as f:
                    self.monitored_apps = json.load(f)
                    self.update_app_tree()
        except Exception as e:
            logging.error(f"Error loading monitored apps: {str(e)}")
            
    def on_closing(self):
        """Handle application closing"""
        if self.monitoring:
            self.stop_monitoring()
        self.save_settings()
        self.save_monitored_apps()
        self.root.destroy()

def main():
    root = tk.Tk()
    app = CPUMonitorApp(root)
    
    # Set closing protocol
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()

