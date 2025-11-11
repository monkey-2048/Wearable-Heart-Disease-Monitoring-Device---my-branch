import numpy as np
import matplotlib.pyplot as plt
from matplotlib.offsetbox import AnchoredText
from scipy import signal
import pandas as pd
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, Scale, HORIZONTAL, StringVar, ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os
import re
from matplotlib.animation import FuncAnimation

class ECGLiveFilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ECG Signal Processor with Live Display")
        self.root.geometry("1000x850")
        
        # Create the user interface
        self.create_widgets()
        
        # Signal data
        self.time = None
        self.signal_raw = None
        self.signal_filtered = None
        self.signal_original = None  # Keep a copy of the original signal
        self.sampling_rate = 500  # Hardcoded sampling rate (Hz)
        
        # Variables for live display
        self.animation = None
        self.is_playing = False
        self.current_index = 0
        self.display_width = 10  # Number of seconds to display on screen
        self.animation_speed = 1.0  # Default display speed
        self.filter_count = 0  # Number of times the filter has been applied
        self.y_scale = 1.0  # Y-axis scale

        # vars to show features
        self.feature_vars = {
            "HR": tk.StringVar(value="—"),
            "Oldpeak": tk.StringVar(value="—"),
            "ST_Slope": tk.StringVar(value="—"),
            "n_beats": tk.StringVar(value="—"),
        }

        # right-side panel (or put it under the plot; adjust grid/pack as you like)
        self.feature_frame = ttk.Labelframe(self.root, text="ECG Features")
        self.feature_frame.pack(side="right", fill="y", padx=8, pady=8)

        def add_row(parent, label, var):
            row = ttk.Frame(parent)
            ttk.Label(row, text=label, width=12).pack(side="left")
            ttk.Label(row, textvariable=var, width=18).pack(side="left")
            row.pack(anchor="w", padx=6, pady=2)

        add_row(self.feature_frame, "HR (bpm)", self.feature_vars["HR"])
        add_row(self.feature_frame, "Oldpeak (mV)", self.feature_vars["Oldpeak"])
        add_row(self.feature_frame, "ST_Slope",     self.feature_vars["ST_Slope"])
        add_row(self.feature_frame, "#Beats",       self.feature_vars["n_beats"])
        
    def create_widgets(self):
        # Button frame
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)
        
        # Load file button
        load_btn = tk.Button(btn_frame, text="Load ECG File", command=self.load_file, width=15, height=2)
        load_btn.grid(row=0, column=0, padx=10)
        
        # Process signal button
        self.process_btn = tk.Button(btn_frame, text="Process Signal", command=self.process_signal, width=15, height=2)
        self.process_btn.grid(row=0, column=1, padx=10)
        
        # Display filter application count
        self.filter_count_var = StringVar()
        bigfont = tkfont.Font(size=12)
        filter_count_label = tk.Label(btn_frame, textvariable=self.filter_count_var, width=20, font=bigfont)
        filter_count_label.grid(row=0, column=2, padx=10)
        
        # Reset filter button
        reset_filter_btn = tk.Button(btn_frame, text="Reset Filter", command=self.reset_filter, width=15, height=2)
        reset_filter_btn.grid(row=0, column=3, padx=10)
        
        # Start/Stop live display button
        self.play_btn = tk.Button(btn_frame, text="Start Live Display", command=self.toggle_live_display, width=15, height=2)
        self.play_btn.grid(row=1, column=0, padx=10, pady=5)
        
        # Save filtered signal button
        save_btn = tk.Button(btn_frame, text="Save Filtered Signal", command=self.save_filtered_signal, width=15, height=2)
        save_btn.grid(row=1, column=1, padx=10, pady=5)
        
        # Settings frame
        settings_frame = tk.Frame(self.root)
        settings_frame.pack(pady=5)
        
        # Display speed settings
        speed_frame = tk.Frame(settings_frame)
        speed_frame.grid(row=0, column=0, padx=20)
        
        tk.Label(speed_frame, text="Display Speed:").pack(side=tk.LEFT)
        self.speed_scale = Scale(speed_frame, from_=0.1, to=5.0, resolution=0.1, 
                                orient=HORIZONTAL, length=150, command=self.update_speed)
        self.speed_scale.set(1.0)
        self.speed_scale.pack(side=tk.LEFT)
        
        # Additional settings frame
        settings_frame2 = tk.Frame(self.root)
        settings_frame2.pack(pady=5)
        
        # Display window size settings
        width_frame = tk.Frame(settings_frame2)
        width_frame.grid(row=0, column=0, padx=20)
        
        tk.Label(width_frame, text="Window Width (Seconds):").pack(side=tk.LEFT)
        self.width_scale = Scale(width_frame, from_=2, to=30, resolution=1, 
                                orient=HORIZONTAL, length=150, command=self.update_display_width)
        self.width_scale.set(10)
        self.width_scale.pack(side=tk.LEFT)
        
        # Y-axis scale settings
        yscale_frame = tk.Frame(settings_frame2)
        yscale_frame.grid(row=0, column=1, padx=20)
        
        tk.Label(yscale_frame, text="Y Scale:").pack(side=tk.LEFT)
        self.yscale_scale = Scale(yscale_frame, from_=0.1, to=10.0, resolution=0.1, 
                                 orient=HORIZONTAL, length=150, command=self.update_y_scale)
        self.yscale_scale.set(1.0)
        self.yscale_scale.pack(side=tk.LEFT)
        
        # Frame for displaying plots
        self.plot_frame = tk.Frame(self.root)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create figure
        self.fig = Figure(figsize=(8, 8), dpi=100)
        
        # Add subplots
        self.ax1 = self.fig.add_subplot(211)
        self.ax2 = self.fig.add_subplot(212)
        
        # Set subplot titles
        self.ax1.set_title("Original ECG Signal")
        self.ax2.set_title("ECG Signal After Noise Removal")
        
        # Initialize plot lines
        self.line_raw, = self.ax1.plot([], [], 'b-')
        self.line_filtered, = self.ax2.plot([], [], 'r-')
        
        # Add figure to user interface
        self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Add status information
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to load ECG file")
        status_label = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Progress indicator
        progress_frame = tk.Frame(self.root)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(progress_frame, text="Progress:").pack(side=tk.LEFT)
        self.progress_var = tk.DoubleVar()
        self.progress_scale = Scale(progress_frame, variable=self.progress_var, from_=0, to=100, 
                                  orient=HORIZONTAL, length=850, command=self.seek_position)
        self.progress_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)

    
    def update_speed(self, val):
        self.animation_speed = float(val)
        
    def update_display_width(self, val):
        self.display_width = int(val)
        # Reset horizontal axis limits
        if self.signal_raw is not None:
            self.update_axes_limits()

    def update_y_scale(self, val):
        self.y_scale = float(val)
        
        
        # Update plot
        self.update_axes_limits()
        self.update_display()
    
    def update_axes_limits(self):
        # Update axis limits based on current position
        if self.time is not None and len(self.time) > 0:
            start_idx = max(0, self.current_index - int(self.display_width * self.sampling_rate))
            end_idx = min(len(self.time), self.current_index + int(0.1 * self.sampling_rate))
            
            # Ensure there is enough data
            if end_idx > start_idx:
                start_time = self.time[start_idx]
                end_time = start_time + self.display_width
                
                self.ax1.set_xlim(start_time, end_time)
                self.ax2.set_xlim(start_time, end_time)
                
                # Update vertical axis limits based on Y scale
                if self.signal_raw is not None and len(self.signal_raw) > 0:
                    data_slice = self.signal_raw[max(0, start_idx):min(len(self.signal_raw), end_idx+1)]
                    if len(data_slice) > 0:
                        center = (np.max(data_slice) + np.min(data_slice)) / 2
                        range_val = (np.max(data_slice) - np.min(data_slice)) / 2
                        min_val = center - (range_val / self.y_scale)
                        max_val = center + (range_val / self.y_scale)
                        self.ax1.set_ylim(min_val, max_val)
                
                if self.signal_filtered is not None and len(self.signal_filtered) > 0:
                    data_slice = self.signal_filtered[max(0, start_idx):min(len(self.signal_filtered), end_idx+1)]
                    if len(data_slice) > 0:
                        center = (np.max(data_slice) + np.min(data_slice)) / 2
                        range_val = (np.max(data_slice) - np.min(data_slice)) / 2
                        min_val = center - (range_val / self.y_scale)
                        max_val = center + (range_val / self.y_scale)
                        self.ax2.set_ylim(min_val, max_val)
    
    def seek_position(self, val):
        if not self.is_playing and self.signal_raw is not None:
            # Convert percentage to index
            pos = int(float(val) / 100 * len(self.signal_raw))
            self.current_index = pos
            self.update_display()
    
    def toggle_live_display(self):
        if self.signal_raw is None:
            messagebox.showwarning("Warning", "Please load an ECG file first")
            return
            
        if self.is_playing:
            # Stop display
            self.is_playing = False
            if self.animation:
                self.animation.event_source.stop()
            self.play_btn.config(text="Start Live Display")
            self.status_var.set("Live display stopped")
        else:
            # Start display
            self.is_playing = True
            self.play_btn.config(text="Stop Live Display")
            self.status_var.set("Live display in progress...")
            
            # Reset index if reached the end
            if self.current_index >= len(self.signal_raw) - 1:
                self.current_index = 0
                
            # Start animation
            self.start_animation()
            
    def start_animation(self):
        # Stop any previous animation
        if self.animation:
            self.animation.event_source.stop()
            
        # Initialize plot axes
        self.update_axes_limits()
        
        # Start new animation
        self.animation = FuncAnimation(
            self.fig, self.update_animation, interval=50, 
            blit=False, cache_frame_data=False
        )
        self.canvas.draw()
    
    def update_animation(self, frame):
        if not self.is_playing:
            return
            
        # Calculate number of points to advance based on speed
        step = int(self.sampling_rate * 0.05 * self.animation_speed)  # 0.05 seconds * speed factor
        
        # Update index
        self.current_index += step
        
        # Check if index has reached the end of data
        if self.current_index >= len(self.signal_raw):
            self.current_index = 0
            
        # Update progress bar
        progress_percent = (self.current_index / len(self.signal_raw)) * 100
        self.progress_var.set(progress_percent)
            
        self.update_display()
        
    def update_display(self):
        # Update axis limits
        self.update_axes_limits()
        
        # Update line data
        visible_start = max(0, self.current_index - int(self.display_width * self.sampling_rate))
        visible_end = self.current_index
        
        if visible_start < visible_end:
            self.line_raw.set_data(self.time[visible_start:visible_end], self.signal_raw[visible_start:visible_end])
            
            if self.signal_filtered is not None:
                self.line_filtered.set_data(self.time[visible_start:visible_end], self.signal_filtered[visible_start:visible_end])
        
        # Update plot
        self.canvas.draw_idle()

    def load_first_channel_from_wfdb_dat(self, dat_path: str):
        """
        Read the first channel from a WFDB .dat file, using the companion .hea header.
        Returns: sig_mV (np.ndarray shape [N,]), fs (float), lead_name (str)
        """
        base, _ = os.path.splitext(dat_path)
        hea_path = base + ".hea"

        # Defaults if .hea not found (fallback)
        n_sig = None
        nsamp = None
        fs = None
        gains = None
        baselines = None
        lead_names = None
        fmt = None

        if os.path.exists(hea_path):
            with open(hea_path, "r") as f:
                lines = [ln.strip() for ln in f if ln.strip()]

            # First line: "<record> <n_sig> <fs> <nsamp>"
            m = re.split(r"\s+", lines[0])
            # e.g., ['00001_hr','12','500','5000']
            n_sig = int(m[1])
            fs = float(m[2])
            nsamp = int(m[3])

            gains = []
            baselines = []
            lead_names = []
            fmts = []

            # Following lines: one per channel
            for ln in lines[1:1+n_sig]:
                # Example:
                # 00001_hr.dat 16 1000.0(0)/mV 16 0 -115 13047 0 I
                parts = re.split(r"\s+", ln)
                fmts.append(int(parts[1]))                            # 16
                gain_field = parts[2]                                 # "1000.0(0)/mV"
                g = float(gain_field.split("(")[0])                   # 1000.0
                b = int(gain_field.split("(")[1].split(")")[0])       # 0
                gains.append(g)
                baselines.append(b)
                lead_names.append(parts[-1])

            # Assure all fmts identical and equal to 16
            if not all(x == 16 for x in fmts):
                raise ValueError(f"Unsupported WFDB format(s): {fmts} (expect all 16).")
            fmt = 16
        else:
            # Fallback if no header: assume 12 channels, int16 LE, unknown fs
            fmt = 16
            n_sig = 12
            fs = None
            gains = [1.0]*n_sig
            baselines = [0]*n_sig
            lead_names = [f"ch{i+1}" for i in range(n_sig)]

        # Map WFDB format 16 -> little-endian int16
        if fmt == 16:
            dtype = "<i2"
        else:
            raise ValueError(f"Unsupported WFDB format: {fmt}")

        raw = np.fromfile(dat_path, dtype=dtype)

        if nsamp is None:
            if raw.size % n_sig != 0:
                raise ValueError(f"Raw length {raw.size} not divisible by n_sig={n_sig}")
            nsamp = raw.size // n_sig

        data_adc = raw.reshape(nsamp, n_sig)

        # First channel only (index 0)
        ch0_adc = data_adc[:, 0].astype(np.int32)
        ch0 = (ch0_adc - baselines[0]) / float(gains[0])   # -> mV

        return ch0
    
    def load_file(self):
        # Stop live display
        if self.is_playing:
            self.toggle_live_display()
            
        # Open file selection dialog
        file_path = filedialog.askopenfilename(
            title="Select ECG File",
            filetypes=[
                ("All Supported Files", "*.txt *.csv *.xlsx *.xls *.dat"),
                ("Text Files", "*.txt"),
                ("CSV Files", "*.csv"),
                ("Excel Files", "*.xlsx *.xls"),
                ("DAT Files", "*.dat")
            ]
        )
        
        if not file_path:
            return
            
        try:
            # Determine file type and process it
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.txt' or file_ext == '.dat':
                # Read text or DAT file
                self.signal_raw = self.load_first_channel_from_wfdb_dat(file_path)
            elif file_ext == '.csv':
                # Read CSV file
                df = pd.read_csv(file_path)
                self.signal_raw = df.iloc[:, 0].values  # Assume signal is in the first column
            elif file_ext == '.xlsx' or file_ext == '.xls':
                # Read Excel file
                df = pd.read_excel(file_path)
                self.signal_raw = df.iloc[:, 0].values  # Assume signal is in the first column
            
            # Save a copy of the original signal
            self.signal_original = self.signal_raw.copy()
            
            # Create time axis
            self.time = np.arange(0, len(self.signal_raw)) / self.sampling_rate
            
            # Initialize plot
            self.current_index = 0
            self.signal_filtered = None
            self.filter_count = 0
            
            # Prepare plots
            self.ax1.clear()
            self.ax2.clear()
            
            
            self.ax1.set_title("Original ECG Signal")
            self.ax1.set_xlabel("Time (Seconds)")
            self.ax1.set_ylabel("Voltage")
            self.ax1.grid(True)
            
            self.ax2.set_title("ECG Signal After Noise Removal")
            self.ax2.set_xlabel("Time (Seconds)")
            self.ax2.set_ylabel("Voltage")
            self.ax2.grid(True)
            
            # Reinitialize plot lines
            self.line_raw, = self.ax1.plot([], [], 'b-')
            self.line_filtered, = self.ax2.plot([], [], 'r-')
            
            # Update only the top plot (before applying filter)
            visible_start = 0
            visible_end = min(int(self.display_width * self.sampling_rate), len(self.signal_raw))
            self.line_raw.set_data(self.time[visible_start:visible_end], self.signal_raw[visible_start:visible_end])
            
            # Update axis limits
            self.update_axes_limits()
            
            self.fig.tight_layout()
            self.canvas.draw()
            
            # Update progress bar
            self.progress_var.set(0)
            
            self.status_var.set(f"File loaded: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error Reading File", str(e))
    
    def update_feature_panel(self, feats: dict):
        def fmt(v, fstr):
            return fstr.format(v) if v is not None else "—"

        self.feature_vars["HR"].set(   fmt(feats.get("HR"),    "{:.1f}"))
        self.feature_vars["Oldpeak"].set( fmt(feats.get("Oldpeak"),  "{:.3f}"))
        self.feature_vars["ST_Slope"].set(fmt(feats.get("ST_Slope"), "{:.1f} mV/s"))
        self.feature_vars["n_beats"].set( str(feats.get("n_beats") or "—") )

    def _set_feature_box(self, feats):
        def fmt(v, f): return (f.format(v) if v is not None else "—")
        text = (
            f"HR: {fmt(feats.get('HR'),    '{:.1f}')} bpm\n"
            f"Oldpeak: {fmt(feats.get('Oldpeak'),'{:.3f}')} mV\n"
            f"ST_Slope: {fmt(feats.get('ST_Slope'),'{:.1f}')} mV/s\n"
            f"#Beats: {feats.get('n_beats') or '—'}"
        )
        self.filter_count_var.set(text)
        self.canvas.draw_idle()

    def process_signal(self):
        if self.signal_raw is None:
            messagebox.showwarning("Warning", "Please load an ECG file first")
            return
        
        try:
            # Ensure the appropriate signal is used for processing
            if self.signal_filtered is None:
                # First processing
                signal_to_process = self.signal_raw
            else:
                # Subsequent processing
                signal_to_process = self.signal_filtered
            
            # Remove baseline wander using a high-pass filter
            b, a = signal.butter(4, 0.5/(self.sampling_rate/2), 'high')
            filtered_signal = signal.filtfilt(b, a, signal_to_process)
            
            # Remove 50 Hz AC noise using a notch filter
            notch_freq = 50  # Can be adjusted to 60 Hz for regions with 60 Hz powerline frequency
            b, a = signal.iirnotch(notch_freq, 30, self.sampling_rate)
            filtered_signal = signal.filtfilt(b, a, filtered_signal)
            
            # Add a low-pass filter to remove high-frequency noise
            b, a = signal.butter(4, 40/(self.sampling_rate/2), 'low')
            filtered_signal = signal.filtfilt(b, a, filtered_signal)
            
            # Update the processed signal
            self.signal_filtered = filtered_signal

            # Calculate features from data
            features = self.compute_ecg_features(self.signal_filtered, self.sampling_rate)
            self.update_feature_panel(features)
            self.status_var.set(
                f"Processed. HR={features['HR']:.1f} bpm, "
                f"Oldpeak={features['Oldpeak']:.3f} mV, "
                f"ST_Slope={features['ST_Slope']:.1f} mV/s, "
            )
            # Optionally store for later use
            self.features_ = features

            # Update plot if in stopped mode
            if not self.is_playing:
                self.update_display()
            
        except Exception as e:
            messagebox.showerror("Error in Processing", str(e))

        # 在 process_signal() 計算特徵後呼叫：
        features = self.compute_ecg_features(self.signal_filtered, self.sampling_rate)
        self.update_feature_panel(features)     
        self._set_feature_box(features)
    
    def reset_filter(self):
        """Reset the filter and use the original signal"""
        if self.signal_original is None:
            return
            
        self.signal_raw = self.signal_original.copy()
        self.signal_filtered = None
        self.filter_count = 0
        
        # Update plot
        self.update_display()
        self.status_var.set("Filter reset")
    
    def save_filtered_signal(self):
        if self.signal_filtered is None:
            messagebox.showwarning("Warning", "Please process the signal first")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Filtered Signal",
            defaultextension=".csv",
            filetypes=[
                ("CSV File", "*.csv"),
                ("Text File", "*.txt"),
                ("Excel File", "*.xlsx")
            ]
        )
        
        if not file_path:
            return
            
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            # Create a DataFrame containing time, original signal, and filtered signal
            df = pd.DataFrame({
                'time': self.time,
                'original_signal': self.signal_original,
                'filtered_signal': self.signal_filtered
            })
            
            if file_ext == '.csv':
                df.to_csv(file_path, index=False)
            elif file_ext == '.txt':
                df.to_csv(file_path, sep='\t', index=False)
            elif file_ext == '.xlsx':
                df.to_excel(file_path, index=False)
            
            self.status_var.set(f"Filtered signal saved to: {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Error Saving File", str(e))

    def robust_r_peaks(self, sig_mV, fs):
        """
        Pan-Tompkins style R-peak detection with adaptive thresholds.
        Input:  sig_mV (1-D, in mV), fs (Hz)
        Return: peaks (np.ndarray of sample indices)
        """
        # 1) Bandpass to enhance QRS (wider than before to keep morphology)
        bp = signal.butter(2, [5/(fs/2), 20/(fs/2)], btype='bandpass')
        x = signal.filtfilt(*bp, sig_mV)

        # 2) Derivative -> Square -> Moving Window Integration (~150 ms)
        dx = np.diff(x, prepend=x[0])
        sq = dx * dx
        win = max(1, int(0.15 * fs))
        mwi = np.convolve(sq, np.ones(win)/win, mode="same")

        # 3) Robust normalization & adaptive thresholds
        med = np.median(mwi)
        mad = np.median(np.abs(mwi - med)) + 1e-12  # robust scale
        z = (mwi - med) / mad

        # Refractory period 250–300 ms
        refractory = int(0.28 * fs)

        # Height/prominence from robust stats (tuneable)
        height = 3.0     # in z-units
        prom   = 1.5     # in z-units

        peaks_mwi, _ = signal.find_peaks(
            z,
            distance=refractory,
            height=height,
            prominence=prom
        )

        if peaks_mwi.size == 0:
            return peaks_mwi

        # 4) Refine: for each candidate, snap to the closest *true* maximum
        # on the band-passed signal within ±80 ms around the MWI peak.
        refine_win = int(0.08 * fs)
        refined = []
        for p in peaks_mwi:
            lo = max(0, p - refine_win)
            hi = min(len(x), p + refine_win + 1)
            # Use absolute to be polarity-agnostic; take the argmax on |x|
            local = np.abs(x[lo:hi])
            if local.size == 0:
                continue
            refined.append(lo + int(np.argmax(local)))
        refined = np.array(sorted(set(refined)), dtype=int)

        # 5) Optional: merge peaks closer than refractory by keeping the higher one
        if refined.size > 1:
            keep = [refined[0]]
            for idx in refined[1:]:
                if idx - keep[-1] < refractory:
                    # keep the one with larger |x|
                    keep[-1] = keep[-1] if abs(x[keep[-1]]) >= abs(x[idx]) else idx
                else:
                    keep.append(idx)
            refined = np.array(keep, dtype=int)

        return refined

    def compute_ecg_features(self, sig, fs):
        """
        Compute MaxHR, Oldpeak (signed), OldpeakAbs (magnitude), ST_Slope, ST_Label,
        and a coarse RestingECG label. 'sig' must be in mV.
        Returns a dict; keys match the feature panel.
        """

        # 1) QRS enhancement & R-peak detection
        b, a = signal.butter(2, [5/(fs/2), 15/(fs/2)], btype='bandpass')
        qrs_enh = signal.filtfilt(b, a, sig)

        peaks = self.robust_r_peaks(sig, fs)

        # 2) Instantaneous HR from RR intervals
        rr = np.diff(peaks) / fs
        hr_inst = 60.0 / rr if rr.size else np.array([])
        max_hr = float(np.max(hr_inst)) if hr_inst.size else None

        # 3) ST metrics per beat (baseline referenced)
        st_vals, slopes = [], []
        for r in peaks:
            pre_start = r - int(0.20*fs)   # PR baseline window: -200 ms
            pre_end   = r - int(0.12*fs)   # to -120 ms
            j        = r + int(0.04*fs)    # J point ~ +40 ms
            st_start = r + int(0.06*fs)    # ST eval window: +60 ms
            st_end   = r + int(0.08*fs)    # to +80 ms

            if pre_start < 0 or st_end >= len(sig):
                continue

            baseline = float(np.median(sig[pre_start:pre_end]))
            # (A) ST offset (signed): + elevation, - depression
            st_val = float(np.mean(sig[st_start:st_end]) - baseline)
            st_vals.append(st_val)

            # (B) ST slope: linear fit on baseline-referenced segment (J -> J+80 ms)
            j_end = min(j + int(0.08*fs), len(sig))
            x = np.arange(j, j_end) / fs
            y = sig[j:j_end] - baseline
            if x.size >= 3:
                k, _ = np.polyfit(x, y, 1)  # mV/s
                slopes.append(float(k))

        # Aggregate
        oldpeak_signed = float(np.median(st_vals)) if st_vals else None
        oldpeak_mag    = float(np.median(np.abs(st_vals))) if st_vals else None
        st_slope       = float(np.median(slopes)) if slopes else None

        # Optional 3-class label from slope
        if st_slope is None:
            st_label = None
        else:
            thr = 0.5  # mV/s (tune 0.3~1.0 as needed)
            st_label = "Up" if st_slope > thr else ("Down" if st_slope < -thr else "Flat")

        # Coarse RestingECG
        resting_ecg = None
        if oldpeak_mag is not None:
            resting_ecg = "ST" if oldpeak_mag >= 0.10 else "Normal"

        if max_hr > 160:
            beats_count = int(int(peaks.size)/2)
        else:
            beats_count = int(peaks.size)


        max_hr = 60/(10-(peaks[0]/500)) * beats_count

        return {
            "HR": max_hr,
            "Oldpeak": oldpeak_signed,   # signed
            "OldpeakAbs": oldpeak_mag,   # magnitude
            "ST_Slope": st_slope,
            "ST_Label": st_label,
            "RestingECG": resting_ecg,
            "n_beats": beats_count,
        }


def main():
    root = tk.Tk()
    app = ECGLiveFilterApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
