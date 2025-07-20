#!/usr/bin/env python3
"""
Qualitative hearing analysis.

A Python application that generates frequency tones to map hearing range
and create a hearing sensitivity graph for each ear.
"""
# Semantic Versioning according to https://semver.org/spec/v2.0.0.html
__version__ = "0.1.2" # Patch level, to use pyproject.toml, etc.

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import sounddevice as sd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import time
import json
from datetime import datetime
import os


class HearingProfiler:

    def __init__(self):
        # Load configuration from file
        self.config = self.load_config()

        self.root = tk.Tk()
        self.root.title("Hearing Profiler")
        self.root.geometry(self.config['ui']['window_size'])

        # Audio parameters from config
        self.sample_rate = self.config['audio']['sample_rate']
        self.tone_duration = self.config['audio']['tone_duration']
        self.min_gap = self.config['testing']['inter_test_delay_range'][0]
        self.max_gap = self.config['testing']['inter_test_delay_range'][1]

        # Frequency bands (Hz) - from config
        self.frequency_bands = np.logspace(
            np.log10(self.config['testing']['min_frequency']),
            np.log10(self.config['testing']['max_frequency']),
            self.config['testing']['frequency_bands']
        )

        # Intensity levels from config
        self.intensity_levels = self.config['testing']['intensity_levels']

        # Results storage
        self.test_results = {'left': {}, 'right': {}}
        self.previous_results = []  # List of previous test results with metadata
        self.current_test = None
        self.current_ear = 'left'
        self.test_index = 0

        # Calibration volume from config (can be overridden by user)
        self.calibration_volume = self.config['calibration'].get('saved_volume',
                                                                 self.config['calibration']['default_volume'])

        # Test sequence and timing
        self.test_sequence = []
        self.test_audio_stream = None
        self.test_start_time = 0
        self.tone_events = []  # List of (start_time, end_time, test_data)

        # Test modes
        self.test_mode = 'quick'  # 'quick' or 'full'

        # Audio stream for continuous output (Bluetooth compatibility)
        self.audio_stream = None
        self.audio_buffer = np.zeros(1024)
        self.is_playing_tone = False
        self.current_tone = np.zeros(int(self.sample_rate *
                                         self.tone_duration))

        self.setup_gui()
        self.start_continuous_audio()

    def load_config(self):
        """Load configuration from config.json"""
        config_file = 'config.json'
        default_config = {
            "audio": {
                "sample_rate": 44100,
                "tone_duration": 0.33,
                "silence_duration": 0.3,
                "fade_duration": 0.01
            },
            "testing": {
                "frequency_bands": 15,
                "min_frequency": 125,
                "max_frequency": 16000,
                "intensity_levels": [0.1, 0.3, 0.6, 1.0],
                "randomize_order": True,
                "inter_test_delay_range": [0.75, 1.25]
            },
            "calibration": {
                "default_volume": 0.5,
                "calibration_frequency": 1000,
                "calibration_intensity": 0.5
            },
            "ui": {
                "window_size": "800x600",
                "show_frequency_during_test": False,
                "auto_save_results": True
            }
        }

        try:
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print(f"✓ Loaded configuration from {config_file}")

                # Merge with defaults to ensure all keys exist
                for section, values in default_config.items():
                    if section not in config:
                        config[section] = values
                    else:
                        for key, value in values.items():
                            if key not in config[section]:
                                config[section][key] = value

                return config
            else:
                print(f"⚠ Config file {config_file} not found, using defaults")
                return default_config

        except Exception as e:
            print(f"⚠ Error loading config: {e}, using defaults")
            return default_config

    def save_config(self):
        """Save current configuration back to config.json"""
        config_file = 'config.json'

        # Update the saved calibration volume
        self.config['calibration']['saved_volume'] = self.calibration_volume

        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"✓ Configuration saved to {config_file}")
        except Exception as e:
            print(f"⚠ Error saving config: {e}")

    def setup_gui(self):
        """Set up the main GUI interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="ewns")

        # Title
        title_label = ttk.Label(main_frame,
                                text="Hearing Profiler",
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Calibration section
        calibration_frame = ttk.LabelFrame(main_frame,
                                           text="Calibration",
                                           padding="10")
        calibration_frame.grid(row=1,
                               column=0,
                               columnspan=3,
                               sticky="ew",
                               pady=(0, 10))

        ttk.Label(calibration_frame,
                  text="Adjust volume to comfortable level:").grid(row=0,
                                                                   column=0,
                                                                   sticky=tk.W)

        self.volume_scale = tk.Scale(calibration_frame,
                                     from_=0.1,
                                     to=1.0,
                                     orient=tk.HORIZONTAL,
                                     length=200,
                                     resolution=0.01,
                                     digits=3)
        # Use saved calibration volume
        self.volume_scale.set(self.calibration_volume)
        self.volume_scale.grid(row=1, column=0, sticky="ew", padx=(0, 10))

        ttk.Button(calibration_frame,
                   text="Generate Softest Tone",
                   command=self.play_softest_tone).grid(row=1, column=1)

        ttk.Button(calibration_frame,
                   text="Test Calibration Tone",
                   command=self.play_calibration_tone).grid(row=2, column=1)

        # Test control section
        control_frame = ttk.LabelFrame(main_frame,
                                       text="Test Controls",
                                       padding="10")
        control_frame.grid(row=2,
                           column=0,
                           columnspan=3,
                           sticky="ew",
                           pady=(0, 10))

        # Test mode selection
        ttk.Label(control_frame, text="Test Mode:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))

        self.test_mode_var = tk.StringVar(value="quick")
        ttk.Radiobutton(control_frame, text="Quick Test (2 min)",
                        variable=self.test_mode_var, value="quick").grid(row=0, column=1, sticky=tk.W)
        ttk.Radiobutton(control_frame, text="Full Test (8-10 min)",
                        variable=self.test_mode_var, value="full").grid(row=0, column=2, sticky=tk.W)

        ttk.Button(control_frame,
                   text="Start Hearing Test",
                   command=self.start_hearing_test).grid(row=1,
                                                         column=0,
                                                         padx=(0, 10),
                                                         pady=(10, 0))

        self.heard_button = ttk.Button(control_frame,
                                       text="I Heard It!",
                                       command=self.tone_heard,
                                       state='disabled')
        self.heard_button.grid(row=1, column=1, padx=(0, 10), pady=(10, 0))

        # Status section
        status_frame = ttk.LabelFrame(main_frame,
                                      text="Test Status",
                                      padding="10")
        status_frame.grid(row=3,
                          column=0,
                          columnspan=3,
                          sticky="ew",
                          pady=(0, 10))

        self.status_label = ttk.Label(status_frame, text="Ready to start test")
        self.status_label.grid(row=0, column=0, sticky=tk.W)

        self.progress_var = tk.StringVar(value="Progress: 0%")
        self.progress_label = ttk.Label(status_frame,
                                        textvariable=self.progress_var)
        self.progress_label.grid(row=1, column=0, sticky=tk.W)

        # Results section
        results_frame = ttk.LabelFrame(main_frame,
                                       text="Results",
                                       padding="10")
        results_frame.grid(row=4,
                           column=0,
                           columnspan=3,
                           sticky="ewns",
                           pady=(0, 10))

        # Matplotlib figure for results
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(10, 4))
        self.fig.suptitle('Hearing Sensitivity Profile')

        self.canvas = FigureCanvasTkAgg(self.fig, results_frame)
        self.canvas.get_tk_widget().grid(row=0,
                                         column=0,
                                         columnspan=3,
                                         sticky="ewns")

        ttk.Button(results_frame,
                   text="Save Results",
                   command=self.save_results).grid(row=1,
                                                   column=0,
                                                   pady=(10, 0))

        ttk.Button(results_frame,
                   text="Load Previous Results",
                   command=self.load_results).grid(row=1,
                                                   column=1,
                                                   pady=(10, 0))

        ttk.Button(results_frame,
                   text="Clear Previous Results",
                   command=self.clear_previous_results).grid(row=1,
                                                             column=2,
                                                             pady=(10, 0))
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(2, weight=1)
        main_frame.rowconfigure(4, weight=1)
        results_frame.columnconfigure(2, weight=1)
        results_frame.rowconfigure(0, weight=1)
        calibration_frame.columnconfigure(0, weight=1)

    def start_continuous_audio(self):
        """Start continuous audio stream for Bluetooth compatibility"""
        self.audio_position = 0  # Track position in current tone

        def audio_callback(outdata, frames, time, status):
            if self.is_playing_tone and self.current_tone is not None and len(self.current_tone) > 0:
                # Calculate how much of the current tone to play
                end_pos = min(self.audio_position + frames,
                              len(self.current_tone))

                if end_pos > self.audio_position:
                    # Copy tone data to output
                    tone_frames = end_pos - self.audio_position
                    outdata[:tone_frames, 0] = self.current_tone[self.audio_position:end_pos] * \
                        self.calibration_volume

                    # Fill remaining frames with silence if needed
                    if tone_frames < frames:
                        outdata[tone_frames:, 0] = 0

                    self.audio_position = end_pos

                    # Check if we've reached the end of the audio
                    if self.audio_position >= len(self.current_tone):
                        self.is_playing_tone = False
                else:
                    outdata[:, 0] = 0
            else:
                # Output silence but keep stream active
                # Very quiet noise to keep stream active
                outdata[:, 0] = np.random.normal(0, 0.001, frames)
                self.audio_position = 0  # Reset position when not playing

        try:
            self.audio_stream = sd.OutputStream(samplerate=self.sample_rate,
                                                channels=1,
                                                callback=audio_callback,
                                                blocksize=1024)
            self.audio_stream.start()
        except Exception as e:
            messagebox.showerror("Audio Error",
                                 f"Could not start audio stream: {e}")

    def generate_tone(self, frequency, intensity, ear='both', duration_s=None):
        """Generate a sinusoidal tone with proper volume scaling"""
        if duration_s is None:
            duration_s = self.tone_duration
        t = np.linspace(0, duration_s,
                        int(self.sample_rate * duration_s))

        # Apply envelope to avoid clicks using config fade duration
        envelope = np.ones_like(t)
        fade_samples = int(self.config['audio']
                           ['fade_duration'] * self.sample_rate)
        if len(envelope) > 2 * fade_samples:
            envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
            envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)

        # Apply logarithmic volume scaling relative to calibration volume
        # intensity is relative (0.0-1.0), calibration_volume is absolute max
        # Minimum volume should be 1% of max (barely audible)
        min_volume_ratio = 0.01  # 1% of max volume
        max_volume = self.calibration_volume
        min_volume = max_volume * min_volume_ratio

        # Logarithmic scale: log interpolation between min and max
        if intensity <= 0:
            actual_volume = 0
        else:
            # Use logarithmic scaling: volume = min_vol * (max_vol/min_vol)^intensity
            volume_ratio = (max_volume / min_volume) ** intensity
            actual_volume = min_volume * volume_ratio

        tone = actual_volume * np.sin(2 * np.pi * frequency * t) * envelope

        return tone

    def play_softest_tone(self):
        """Play a tone using the config values, at 0.1 volume"""
        test_volume = 0.1
        # Use calibration frequency from config
        cal_freq = self.config['calibration']['calibration_frequency']
        cal_duration = 5.0  # 5 second calibration tone

        # For lowest level calibration, using the logarithmic scaling
        # This is to select the "just audible" threshold
        tone = self.generate_tone(cal_freq, test_volume, 'both', cal_duration)

        # Add fade envelope using config fade duration
        envelope = np.ones_like(tone)
        fade_samples = int(self.config['audio']
                           ['fade_duration'] * self.sample_rate)
        if len(envelope) > 2 * fade_samples:
            envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
            envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        tone = tone * envelope

        self.play_tone_async(tone)

    def play_calibration_tone(self):
        """Play a calibration tone using config values"""
        self.calibration_volume = self.volume_scale.get()

        # Save the calibration volume to config
        self.save_config()

        # Use calibration frequency from config
        cal_freq = self.config['calibration']['calibration_frequency']
        cal_duration = 1.0  # 1 second calibration tone

        # For calibration, use the raw volume directly (not the logarithmic scaling)
        # This tone should be at the selected "comfortable listening level"
        tone = self.calibration_volume * np.sin(2 * np.pi * cal_freq *
                                                np.linspace(0, cal_duration, int(self.sample_rate * cal_duration)))

        # Add fade envelope using config fade duration
        envelope = np.ones_like(tone)
        fade_samples = int(self.config['audio']
                           ['fade_duration'] * self.sample_rate)
        if len(envelope) > 2 * fade_samples:
            envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
            envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        tone = tone * envelope

        self.play_tone_async(tone)

    def play_tone_async(self, tone):
        """Play a tone asynchronously"""

        def play():
            self.current_tone = tone
            self.audio_position = 0  # Reset audio position
            self.is_playing_tone = True

            # Calculate actual tone duration based on tone length
            actual_duration = len(tone) / self.sample_rate
            time.sleep(actual_duration)

            self.is_playing_tone = False
            self.current_tone = np.zeros(
                int(self.sample_rate * self.tone_duration))
            self.audio_position = 0  # Reset position when done

        threading.Thread(target=play, daemon=True).start()

    def create_test_sequence(self, mode='quick'):
        """Create a precomputed test sequence with all tones and gaps"""
        import random

        # Determine test parameters based on mode
        if mode == 'quick':
            # Quick test: fewer frequencies and intensities
            frequencies = np.logspace(
                np.log10(250), np.log10(8000), 8)  # 8 frequencies
            intensities = [0.2, 0.6, 1.0]  # 3 intensities
        else:
            # Full test: all frequencies and intensities
            frequencies = self.frequency_bands  # 15 frequencies
            intensities = self.intensity_levels  # 4 intensities

        # Create test sequence
        test_sequence = []
        for ear in ['left', 'right']:
            for freq in frequencies:
                for intensity in intensities:
                    test_sequence.append({
                        'ear': ear,
                        'frequency': freq,
                        'intensity': intensity,
                        'heard': None
                    })

        # Shuffle the sequence
        random.shuffle(test_sequence)

        return test_sequence

    def generate_test_audio_stream(self, test_sequence):
        """Generate a single audio stream with all tones and gaps"""
        import random

        audio_data = []
        tone_events = []
        current_time = 0.0

        for i, test in enumerate(test_sequence):
            # Add gap before tone
            gap_duration = random.uniform(self.min_gap, self.max_gap)
            gap_samples = int(gap_duration * self.sample_rate)
            audio_data.extend(np.zeros(gap_samples))
            current_time += gap_duration

            # Generate and add tone
            tone_start = current_time
            tone = self.generate_tone(
                test['frequency'], test['intensity'], test['ear'])
            audio_data.extend(tone)
            current_time += len(tone) / self.sample_rate
            tone_end = current_time

            # Record tone event
            tone_events.append({
                'start_time': tone_start,
                'end_time': tone_end,
                'test_index': i,
                'test_data': test
            })

        # Add final gap
        final_gap = int(2.0 * self.sample_rate)  # 2 seconds at end
        audio_data.extend(np.zeros(final_gap))

        return np.array(audio_data), tone_events

    def start_hearing_test(self):
        """Start the hearing test sequence"""
        if not self.audio_stream or not self.audio_stream.active:
            messagebox.showerror(
                "Audio Error",
                "Audio system not ready. Please restart the application.")
            return

        # Get test mode
        self.test_mode = self.test_mode_var.get()

        # Reset results
        self.test_results = {'left': {}, 'right': {}}

        # Create test sequence
        self.test_sequence = self.create_test_sequence(self.test_mode)

        # Generate precomputed audio stream
        self.status_label.config(text="Preparing audio stream...")
        self.test_audio_stream, self.tone_events = self.generate_test_audio_stream(
            self.test_sequence)

        # Enable the heard button
        self.heard_button.config(state='normal')

        # Show test info
        test_duration = len(self.test_audio_stream) / \
            self.sample_rate / 60  # minutes
        num_tones = len(self.tone_events)

        messagebox.showinfo(
            "Test Starting",
            f"{'Quick' if self.test_mode == 'quick' else 'Full'} hearing test will now begin.\n\n"
            f"Duration: {test_duration:.1f} minutes\n"
            f"Number of tones: {num_tones}\n\n"
            f"Click 'I Heard It!' immediately when you hear a tone.\n"
            f"Tones are spaced 0.75-1.25 seconds apart.\n\n"
            f"Put on your headphones and click OK to start.")

        # Start the test
        self.start_test_playback()

    def start_test_playback(self):
        """Start playing the precomputed test audio"""
        self.test_start_time = time.time()
        self.test_index = 0
        self.current_tone = self.test_audio_stream
        self.audio_position = 0
        self.is_playing_tone = True

        self.status_label.config(text="Test in progress - Listen carefully!")
        self.progress_var.set("Progress: 0%")

        # Start progress monitoring
        self.monitor_test_progress()

    def monitor_test_progress(self):
        """Monitor test progress and update UI"""
        if not self.is_playing_tone:
            # Test finished
            self.finish_test()
            return

        # Calculate progress
        if self.test_audio_stream is not None and len(self.test_audio_stream) > 0:
            progress = (self.audio_position /
                        len(self.test_audio_stream)) * 100
            self.progress_var.set(f"Progress: {progress:.1f}%")

        # Check again in 100ms
        self.root.after(100, self.monitor_test_progress)

    def tone_heard(self):
        """Called when user indicates they heard a tone"""
        current_time = time.time() - self.test_start_time

        # Find which tone (if any) the user is responding to
        for event in self.tone_events:
            if (event['start_time'] <= current_time <= event['end_time'] + 1.0 and
                    event['test_data']['heard'] is None):

                # Mark this tone as heard
                event['test_data']['heard'] = True

                # Store result
                test = event['test_data']
                ear = test['ear']
                freq = test['frequency']
                if freq not in self.test_results[ear]:
                    self.test_results[ear][freq] = []
                self.test_results[ear][freq].append({
                    'intensity': test['intensity'],
                    'heard': True
                })
                break

    def finish_test(self):
        """Finish the test and show results"""
        # Stop audio playback
        self.is_playing_tone = False

        # Process any unheard tones
        for event in self.tone_events:
            if event['test_data']['heard'] is None:
                # Mark as not heard
                event['test_data']['heard'] = False

                # Store result
                test = event['test_data']
                ear = test['ear']
                freq = test['frequency']
                if freq not in self.test_results[ear]:
                    self.test_results[ear][freq] = []
                self.test_results[ear][freq].append({
                    'intensity': test['intensity'],
                    'heard': False
                })

        # Update UI
        self.heard_button.config(state='disabled')
        self.status_label.config(text="Test completed!")
        self.progress_var.set("Progress: 100%")

        # Refresh plot to show current results with any previous overlays
        self.analyze_and_plot_results()

        num_previous = len(self.previous_results)
        overlay_text = f"\n{num_previous} previous result(s) overlaid in red." if num_previous > 0 else ""

        messagebox.showinfo(
            "Test Complete",
            f"Hearing test completed!\n\n"
            f"Your current hearing profile is displayed in blue.{overlay_text}\n\n"
            f"You can save the results for future comparison.")

    def analyze_and_plot_results(self):
        """Analyze results and create hearing profile plots with overlaid previous results"""
        self.ax1.clear()
        self.ax2.clear()

        for i, ear in enumerate(['left', 'right']):
            ax = self.ax1 if ear == 'left' else self.ax2
            ax.set_title(f'{ear.title()} Ear')
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Hearing Threshold (dB)')
            ax.set_xscale('log')
            ax.grid(True, alpha=0.3)

            # Plot previous results first (from oldest to newest)
            for prev_idx, prev_result in enumerate(self.previous_results):
                frequencies = []
                thresholds = []

                prev_data = prev_result['results']
                if ear in prev_data:
                    for freq in sorted(prev_data[ear].keys()):
                        results = prev_data[ear][freq]

                        # Find minimum intensity that was heard
                        heard_intensities = [
                            r['intensity'] for r in results if r['heard']
                        ]

                        if heard_intensities:
                            min_heard = min(heard_intensities)
                            # Convert to approximate dB scale (relative)
                            threshold_db = -20 * np.log10(min_heard)
                        else:
                            # Not heard at any intensity
                            threshold_db = 60  # Assume significant hearing loss

                        frequencies.append(freq)
                        thresholds.append(threshold_db)

                    if frequencies:
                        # Calculate alpha (transparency) - older results are lighter
                        num_prev = len(self.previous_results)
                        alpha = 0.3 + (0.4 * (prev_idx + 1) /
                                       num_prev)  # 0.3 to 0.7

                        # Format timestamp for legend
                        timestamp = prev_result.get('timestamp', 'Unknown')
                        if timestamp != 'Unknown':
                            try:
                                dt = datetime.fromisoformat(
                                    timestamp.replace('Z', '+00:00'))
                                label = dt.strftime('%Y-%m-%d %H:%M')
                            except:
                                label = timestamp[:16]  # Fallback
                        else:
                            label = f'Previous {prev_idx + 1}'

                        ax.plot(frequencies,
                                thresholds,
                                'o-',
                                color='red',
                                alpha=alpha,
                                linewidth=1,
                                markersize=3,
                                label=label)

            # Plot current results on top (always blue and prominent)
            if self.test_results[ear]:
                frequencies = []
                thresholds = []

                for freq in sorted(self.test_results[ear].keys()):
                    results = self.test_results[ear][freq]

                    # Find minimum intensity that was heard
                    heard_intensities = [
                        r['intensity'] for r in results if r['heard']
                    ]

                    if heard_intensities:
                        min_heard = min(heard_intensities)
                        # Convert to approximate dB scale (relative)
                        threshold_db = -20 * np.log10(min_heard)
                    else:
                        # Not heard at any intensity
                        threshold_db = 60  # Assume significant hearing loss

                    frequencies.append(freq)
                    thresholds.append(threshold_db)

                if frequencies:
                    ax.plot(frequencies,
                            thresholds,
                            'o-',
                            color='blue',
                            linewidth=2,
                            markersize=6,
                            label='Current Test',
                            zorder=10)  # Ensure current test is on top

            # Set axis limits and add legend
            ax.set_xlim(100, 20000)
            ax.set_ylim(0, 70)
            ax.invert_yaxis()  # Lower dB (better hearing) at top

            # Add legend if there are multiple results
            if self.previous_results or self.test_results[ear]:
                ax.legend(loc='lower left', fontsize=8)

        self.canvas.draw()

    def save_results(self):
        """Save test results to a file"""
        if not self.test_results['left'] and not self.test_results['right']:
            messagebox.showwarning("No Results", "No test results to save.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Hearing Test Results")

        if filename:
            data = {
                'timestamp': datetime.now().isoformat(),
                'calibration_volume': self.calibration_volume,
                'frequency_bands': self.frequency_bands.tolist(),
                'intensity_levels': self.intensity_levels,
                'results': self.test_results
            }

            try:
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)
                messagebox.showinfo("Saved", f"Results saved to {filename}")
            except Exception as e:
                messagebox.showerror("Save Error",
                                     f"Could not save results: {e}")

    def load_results(self):
        """Load previous test results"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Load Hearing Test Results")

        if filename:
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)

                # Convert the string frequencies to float
                results = data['results']
                fixed_results = {'left': {}, 'right': {}}
                for ear in ['left', 'right']:
                    for freq_str, values in results[ear].items():
                        freq_float = float(freq_str)
                        fixed_results[ear][freq_float] = values

                # Add to previous results list instead of replacing current results
                previous_result = {
                    'timestamp': data.get('timestamp', 'Unknown'),
                    'calibration_volume': data.get('calibration_volume', 0.5),
                    'results': fixed_results,
                    # Just filename
                    'filename': filename.split('/')[-1].split('\\')[-1]
                }

                self.previous_results.append(previous_result)

                # Refresh the plot to show the new overlay
                self.analyze_and_plot_results()

                timestamp = data.get('timestamp', 'Unknown')
                num_loaded = len(self.previous_results)
                # messagebox.showinfo("Loaded",
                #                     f"Results added to overlay!\n\n"
                #                     f"Loaded: {timestamp}\n"
                #                     f"Total overlaid results: {num_loaded}")

            except Exception as e:
                messagebox.showerror("Load Error",
                                     f"Could not load results: {e}")

    def clear_previous_results(self):
        """Clear all previous results from the overlay"""
        if not self.previous_results:
            messagebox.showinfo("No Previous Results",
                                "No previous results to clear.")
            return

        result = messagebox.askyesno("Clear Previous Results",
                                     f"Clear {len(self.previous_results)} previous result(s) from the overlay?")
        if result:
            self.previous_results.clear()
            self.analyze_and_plot_results()
            # messagebox.showinfo(
            #     "Cleared", "Previous results cleared from overlay.")

    def run(self):
        """Start the application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()

    def on_closing(self):
        """Clean up when closing the application"""
        try:
            # Save current calibration volume
            self.calibration_volume = self.volume_scale.get()
            self.save_config()

            # Stop any ongoing tone playback
            self.is_playing_tone = False

            # Stop and close audio stream
            if self.audio_stream:
                try:
                    self.audio_stream.stop()
                    self.audio_stream.close()
                except Exception:
                    pass  # Ignore errors during cleanup

            # Close matplotlib figure
            if hasattr(self, 'fig'):
                plt.close(self.fig)

            # Destroy the root window
            if self.root:
                self.root.quit()  # Exit the mainloop
                self.root.destroy()  # Destroy the window

        except Exception:
            pass  # Ignore any cleanup errors

        # Force exit if needed
        import sys
        sys.exit(0)

def main():
    print("HearingProfiler - starting")
    app = HearingProfiler()
    app.run()
    print("HearingProfiler - done!")

if __name__ == "__main__":
    main()