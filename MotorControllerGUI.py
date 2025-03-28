import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import serial
import serial.tools.list_ports
import threading

class MotorControlApp:
    def __init__(self, master):
        self.master = master
        master.title("Motor Control Interface")
        master.geometry("1000x700")
        master.configure(bg='#2c3e50')
        # Serial connection variables
        self.ser = None
        self.is_connected = False
        # Motor states (these are default values)
        self.motor1_rpm = 1
        self.motor2_rpm = 1
        self.motor3_rpm = 1
        # Motor speed difference (default 5 RPM)
        self.motor_speed_diff = 5
        # Key press states
        self.key_pressed = False
        self.current_command = None
        # Styling
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TLabel', foreground='white', background='#2c3e50', font=('Arial', 12))
        self.style.configure('TButton', font=('Arial', 10))
        # UI Components
        self.create_ui()
        # Bind keyboard events
        master.bind('<KeyPress>', self.on_key_press)
        master.bind('<KeyRelease>', self.on_key_release)

    def create_ui(self):
        # Main frame
        main_frame = tk.Frame(self.master, bg='#2c3e50')
        main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # Top Section with Connection and Motor Controls
        top_frame = tk.Frame(main_frame, bg='#2c3e50')
        top_frame.pack(fill=tk.X)

        # Serial Connection Frame
        connection_frame = tk.Frame(top_frame, bg='#34495e', borderwidth=2, relief=tk.RAISED)
        connection_frame.pack(fill=tk.X, pady=10)

        # Port Selection Dropdown
        self.port_var = tk.StringVar()
        self.port_dropdown = ttk.Combobox(connection_frame, textvariable=self.port_var, width=30)
        self.port_dropdown['values'] = [port.device for port in serial.tools.list_ports.comports()]
        self.port_dropdown.pack(side=tk.LEFT, padx=10, pady=5)

        # Connect/Disconnect Buttons
        self.connect_btn = ttk.Button(connection_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.pack(side=tk.LEFT, padx=10, pady=5)

        # Logs and Controls
        lower_frame = tk.Frame(main_frame, bg='#2c3e50')
        lower_frame.pack(fill=tk.BOTH, expand=True)

        # Left Column - Motor Controls and Sent Commands
        left_column = tk.Frame(lower_frame, bg='#2c3e50')
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # Motor Controls Frame
        controls_frame = tk.Frame(left_column, bg='#34495e', borderwidth=2, relief=tk.RAISED)
        controls_frame.pack(fill=tk.X, pady=10)

        # Motor 1 & 2 Control Section
        ttk.Label(controls_frame, text="Motors 1 & 2 Control", style='TLabel').pack(pady=5)
        self.motor12_speed_label = ttk.Label(controls_frame, text=f"Speed: {self.motor1_rpm} RPM", style='TLabel')
        self.motor12_speed_label.pack(pady=5)

        # Motor Speed Difference Input (1 rpm - 10 rpm)
        diff_frame = tk.Frame(controls_frame, bg='#34495e')
        diff_frame.pack(pady=5)
        ttk.Label(diff_frame, text="Motor Speed Difference (1-10 RPM):", style='TLabel').pack(side=tk.LEFT)
        self.speed_diff_var = tk.IntVar(value=self.motor_speed_diff)
        self.speed_diff_entry = ttk.Entry(diff_frame, textvariable=self.speed_diff_var, width=5)
        self.speed_diff_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(diff_frame, text="Set", command=self.update_speed_difference).pack(side=tk.LEFT)

        # Motor 3 Control Section
        ttk.Label(controls_frame, text="Motor 3 Control", style='TLabel').pack(pady=5)
        self.motor3_speed_label = ttk.Label(controls_frame, text=f"Speed: {self.motor3_rpm} RPM", style='TLabel')
        self.motor3_speed_label.pack(pady=5)

        # Sent Commands Log
        sent_frame = tk.Frame(left_column, bg='#34495e', borderwidth=2, relief=tk.RAISED)
        sent_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        ttk.Label(sent_frame, text="Sent Commands", style='TLabel').pack(pady=5)
        self.sent_log_text = scrolledtext.ScrolledText(sent_frame, wrap=tk.WORD, width=40, height=15,
                                                       bg='#2c3e50', fg='white',
                                                       insertbackground='white')
        self.sent_log_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Arduino Data
        right_column = tk.Frame(lower_frame, bg='#2c3e50')
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        # Arduino Data Log
        arduino_frame = tk.Frame(right_column, bg='#34495e', borderwidth=2, relief=tk.RAISED)
        arduino_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        ttk.Label(arduino_frame, text="Arduino Data", style='TLabel').pack(pady=5)
        self.arduino_log_text = scrolledtext.ScrolledText(arduino_frame, wrap=tk.WORD, width=40, height=15,
                                                          bg='#2c3e50', fg='white',
                                                          insertbackground='white')
        self.arduino_log_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Instructions for user
        instructions = """
        Controls:
        Arrow Keys: Motor 1 & 2 Direction
        W/S: Motor 3 Direction
        +/-: Increase/Decrease Speed
        D/A: Differential Motor Control
        """
        ttk.Label(main_frame, text=instructions, style='TLabel', justify=tk.LEFT).pack(pady=10)

    def update_speed_difference(self):
        try:
            new_diff = int(self.speed_diff_var.get())
            if 1 <= new_diff <= 10:
                self.motor_speed_diff = new_diff
                self.log_sent_message(f"Motor speed difference set to {new_diff} RPM")
            else:
                messagebox.showerror("Invalid Input", "Speed difference must be between 1 and 10 RPM.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid integer.")

    def toggle_connection(self):
        if not self.is_connected:
            # Connect
            port = self.port_var.get()
            if not port:
                messagebox.showerror("Error", "Please select a port")
                return
            try:
                self.ser = serial.Serial(port, 115200, timeout=1)
                self.is_connected = True
                self.connect_btn.config(text="Disconnect")
                self.log_sent_message("Connected to " + port)
                # Start a thread to read serial data
                self.serial_thread = threading.Thread(target=self.read_serial_data, daemon=True)
                self.serial_thread.start()
            except Exception as e:
                messagebox.showerror("Connection Error", str(e))
        else:
            # Disconnect
            if self.ser:
                self.ser.close()
            self.ser = None
            self.is_connected = False
            self.connect_btn.config(text="Connect")
            self.log_sent_message("Disconnected from serial port")

    def read_serial_data(self):
        while self.is_connected and self.ser:
            try:
                if self.ser.in_waiting:
                    data = self.ser.readline().decode('utf-8').strip()
                    if data:
                        self.log_arduino_message(data)
            except Exception as e:
                self.log_sent_message(f"Serial read error: {e}")
                break

    def send_motor_command(self, m1_rpm, m1_dir, m2_rpm, m2_dir, m3_rpm, m3_dir):
        if self.ser and self.is_connected:
            command = f"{m1_rpm} {m1_dir} {m2_rpm} {m2_dir} {m3_rpm} {m3_dir}\n"
            try:
                self.ser.write(command.encode())
                # log message
                log_message = (f"M1: {m1_rpm} RPM, Dir: {'CW' if m1_dir == 0 else 'CCW'} | "
                               f"M2: {m2_rpm} RPM, Dir: {'CW' if m2_dir == 0 else 'CCW'} | "
                               f"M3: {m3_rpm} RPM, Dir: {'CW' if m3_dir == 0 else 'CCW'}")
                self.log_sent_message(log_message)
            except Exception as e:
                self.log_sent_message(f"Send error: {e}")

    def log_sent_message(self, message):
        self.sent_log_text.insert(tk.END, message + "\n")
        self.sent_log_text.see(tk.END)

    def log_arduino_message(self, message):
        self.arduino_log_text.insert(tk.END, message + "\n")
        self.arduino_log_text.see(tk.END)

    def on_key_press(self, event):
        if not self.is_connected or self.key_pressed:
            return
        key = event.keysym.lower()
        self.key_pressed = True
        # Motor 1 & 2 Control
        if key == 'up':
            self.current_command = lambda: self.send_motor_command(self.motor1_rpm, 0, self.motor2_rpm, 1, 0, 0)
            self.motor12_speed_label.config(text=f"Speed: {self.motor1_rpm} RPM (Opposite)")
        elif key == 'down':
            self.current_command = lambda: self.send_motor_command(self.motor1_rpm, 1, self.motor2_rpm, 0, 0, 0)
            self.motor12_speed_label.config(text=f"Speed: {self.motor1_rpm} RPM (Opposite)")
        # Left/Right Same Direction
        elif key == 'left':
            self.current_command = lambda: self.send_motor_command(self.motor1_rpm, 0, self.motor2_rpm, 0, 0, 0)
            self.motor12_speed_label.config(text=f"Speed: {self.motor1_rpm} RPM (Same CW)")
        elif key == 'right':
            self.current_command = lambda: self.send_motor_command(self.motor1_rpm, 1, self.motor2_rpm, 1, 0, 0)
            self.motor12_speed_label.config(text=f"Speed: {self.motor1_rpm} RPM (Same CCW)")
        # Differential Control
        elif key == 'd':
            self.current_command = lambda: self.send_motor_command(self.motor1_rpm, 0, self.motor1_rpm + self.motor_speed_diff, 0, 0, 0)
            self.motor12_speed_label.config(text=f"Speed: {self.motor1_rpm} & {self.motor1_rpm+self.motor_speed_diff} RPM")
        elif key == 'a':
            self.current_command = lambda: self.send_motor_command(self.motor1_rpm, 1, self.motor1_rpm + self.motor_speed_diff, 1, 0, 0)
            self.motor12_speed_label.config(text=f"Speed: {self.motor1_rpm} & {self.motor1_rpm+self.motor_speed_diff} RPM")
        # Motor 3 Control
        elif key == 'w':
            self.current_command = lambda: self.send_motor_command(0, 0, 0, 0, self.motor3_rpm, 0)
            self.motor3_speed_label.config(text=f"Speed: {self.motor3_rpm} RPM (CW)")
        elif key == 's':
            self.current_command = lambda: self.send_motor_command(0, 0, 0, 0, self.motor3_rpm, 1)
            self.motor3_speed_label.config(text=f"Speed: {self.motor3_rpm} RPM (CCW)")
        # Speed Control
        elif key == 'plus' or key == 'equal':
            # Increase speed for Motors 1 & 2
            self.motor1_rpm = min(30, self.motor1_rpm + 1)
            self.motor2_rpm = self.motor1_rpm
            self.motor12_speed_label.config(text=f"Speed: {self.motor1_rpm} RPM")
        elif key == 'minus':
            # Decrease speed for Motors 1 & 2
            self.motor1_rpm = max(0, self.motor1_rpm - 1)
            self.motor2_rpm = self.motor1_rpm
            self.motor12_speed_label.config(text=f"Speed: {self.motor1_rpm} RPM")
        elif key == 'bracketright':  # use ']' for Motor 3 speed increase
            self.motor3_rpm = min(30, self.motor3_rpm + 1)
            self.motor3_speed_label.config(text=f"Speed: {self.motor3_rpm} RPM")
        elif key == 'bracketleft':  # use '[' for Motor 3 speed decrease
            self.motor3_rpm = max(0, self.motor3_rpm - 1)
            self.motor3_speed_label.config(text=f"Speed: {self.motor3_rpm} RPM")
        # Start sending commands
        if self.current_command:
            self.send_continuous_commands()

    def send_continuous_commands(self):
        if self.key_pressed and self.current_command:
            self.current_command()
            self.master.after(100, self.send_continuous_commands)  # Send commands every 100ms

    def on_key_release(self, event):
        # Stop all motors when keys are released
        if self.is_connected:
            self.key_pressed = False
            self.current_command = None
            self.send_motor_command(0, 0, 0, 0, 0, 0)
            self.motor12_speed_label.config(text="Speed: 0 RPM")
            self.motor3_speed_label.config(text="Speed: 0 RPM")

def main():
    root = tk.Tk()
    app = MotorControlApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()