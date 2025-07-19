#!/usr/bin/env python3
"""
Hearing Profiler - CLI Tone Generator (Single-Shot)

A command-line tool to generate a single tone with parameters specified on the command line.
This uses the same logarithmic tone generation algorithm as the main application.

Usage:
    python cli_tone_test.py <frequency> <intensity> <duration> [ear] [max_volume]
    
Examples:
    python cli_tone_test.py 1000 0.5 1.0        # 1000Hz, mid intensity, 1 second, both ears
    python cli_tone_test.py 4000 0.1 0.5 left   # 4000Hz, very quiet, 0.5 sec, left ear only
    python cli_tone_test.py 8000 0.8 0.3 right 0.5  # 8000Hz, loud, 0.3 sec, right ear, 50% max volume
"""

import numpy as np
import sounddevice as sd
import sys
import argparse

class ToneGenerator:
    def __init__(self):
        self.sample_rate = 44100
    
    def generate_tone(self, frequency, intensity, duration, max_volume=1.0):
        """Generate a sinusoidal tone with logarithmic volume scaling (same algorithm as main app)"""
        t = np.linspace(0, duration, int(self.sample_rate * duration))
        
        # Apply envelope to avoid clicks (same as main app)
        envelope = np.ones_like(t)
        fade_samples = int(0.01 * self.sample_rate)  # 10ms fade
        if len(envelope) > 2 * fade_samples:
            envelope[:fade_samples] = np.linspace(0, 1, fade_samples)
            envelope[-fade_samples:] = np.linspace(1, 0, fade_samples)
        
        # Apply logarithmic volume scaling relative to max volume
        # intensity is relative (0.0-1.0), max_volume is absolute maximum
        # Minimum volume should be 1% of max (barely audible)
        min_volume_ratio = 0.01  # 1% of max volume
        min_volume = max_volume * min_volume_ratio
        
        # Logarithmic scale: log interpolation between min and max
        if intensity <= 0:
            actual_volume = 0
        else:
            # Use logarithmic scaling: volume = min_vol * (max_vol/min_vol)^intensity
            volume_ratio = (max_volume / min_volume) ** intensity
            actual_volume = min_volume * volume_ratio
        
        # Generate sine wave with logarithmic volume scaling
        tone = actual_volume * np.sin(2 * np.pi * frequency * t) * envelope
        
        return tone
    
    def play_tone(self, frequency, intensity, duration, ear='both', max_volume=1.0):
        """Play a tone with specified parameters using direct playback"""
        
        # Generate tone with logarithmic scaling
        tone_data = self.generate_tone(frequency, intensity, duration, max_volume)
        
        # Create stereo output based on ear selection
        if ear == 'left':
            # Left channel has tone, right channel is silent
            stereo_data = np.column_stack([tone_data, np.zeros_like(tone_data)])
        elif ear == 'right':
            # Right channel has tone, left channel is silent
            stereo_data = np.column_stack([np.zeros_like(tone_data), tone_data])
        else:  # both
            # Both channels have the tone
            stereo_data = np.column_stack([tone_data, tone_data])
        
        # Calculate actual volume for display
        min_volume_ratio = 0.01
        min_volume = max_volume * min_volume_ratio
        if intensity <= 0:
            actual_volume = 0
        else:
            volume_ratio = (max_volume / min_volume) ** intensity
            actual_volume = min_volume * volume_ratio
        
        # Play the tone using sounddevice (blocking call)
        print(f"🔊 Playing: {frequency} Hz, Intensity: {intensity:.2f} → Volume: {actual_volume:.4f}, Duration: {duration}s, Ear: {ear}")
        print(f"   Max Volume: {max_volume:.2f}, Range: {min_volume:.4f} to {max_volume:.2f}")
        
        try:
            sd.play(stereo_data, samplerate=self.sample_rate)
            sd.wait()  # Wait until the tone finishes playing
            print("✓ Tone completed")
        except Exception as e:
            print(f"✗ Audio error: {e}")
            sys.exit(1)

def show_usage():
    """Show usage information"""
    print("""
🎵 Hearing Profiler - CLI Tone Generator (Single-Shot) 🎵

Usage:
    python cli_tone_test.py <frequency> <intensity> <duration> [ear] [max_volume]

Parameters:
    frequency   - Frequency in Hz (20-20000)
    intensity   - Intensity level (0.0-1.0, logarithmic scale)
    duration    - Duration in seconds (0.1-10.0)
    ear         - Which ear: 'left', 'right', or 'both' (optional, default: both)
    max_volume  - Maximum volume level (0.0-1.0, optional, default: 1.0)

Examples:
    python cli_tone_test.py 1000 0.5 1.0        # Reference tone (1000Hz, mid intensity, 1 sec)
    python cli_tone_test.py 4000 0.1 0.5 left   # Very quiet test (left ear)
    python cli_tone_test.py 8000 0.8 0.3 right  # Loud high frequency test (right ear)
    python cli_tone_test.py 16000 1.0 0.5 both 0.5  # Max intensity with 50% volume limit

Logarithmic Intensity Scale (matches main app):
    0.0  - Silent
    0.1  - Very quiet (1% of max volume)
    0.3  - Quiet (about 10% of max volume)
    0.5  - Medium (about 32% of max volume)
    0.8  - Loud (about 80% of max volume)
    1.0  - Maximum (100% of max volume)

Note: The actual volume is calculated logarithmically from 1% to 100% of max_volume.

Frequency Reference:
    125 Hz    - Very low bass
    1000 Hz   - Reference frequency (calibration tone)
    4000 Hz   - High frequency (where age-related loss often starts)
    8000 Hz   - Very high frequency
    16000 Hz  - Highest test frequency
""")

def validate_parameters(frequency, intensity, duration, ear, max_volume):
    """Validate input parameters"""
    errors = []
    
    if frequency < 20 or frequency > 20000:
        errors.append(f"Frequency {frequency} Hz is out of range (20-20000 Hz)")
    
    if intensity < 0.0 or intensity > 1.0:
        errors.append(f"Intensity {intensity} is out of range (0.0-1.0)")
    
    if duration < 0.1 or duration > 10.0:
        errors.append(f"Duration {duration} seconds is out of range (0.1-10.0 seconds)")
    
    if ear not in ['left', 'right', 'both']:
        errors.append(f"Ear '{ear}' is invalid (must be 'left', 'right', or 'both')")
    
    if max_volume < 0.0 or max_volume > 1.0:
        errors.append(f"Max volume {max_volume} is out of range (0.0-1.0)")
    
    return errors

def main():
    parser = argparse.ArgumentParser(
        description='Generate a single tone using logarithmic volume scaling (same as hearing profiler)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 1000 0.5 1.0        # 1000Hz, mid intensity, 1 second, both ears
  %(prog)s 4000 0.1 0.5 left   # 4000Hz, very quiet intensity, 0.5 sec, left ear only
  %(prog)s 8000 0.8 0.3 right 0.5  # 8000Hz, loud intensity, 0.3 sec, right ear, 50%% max volume
"""
    )
    
    parser.add_argument('frequency', type=float, help='Frequency in Hz (20-20000)')
    parser.add_argument('intensity', type=float, help='Intensity level (0.0-1.0, logarithmic scale)')
    parser.add_argument('duration', type=float, help='Duration in seconds (0.1-10.0)')
    parser.add_argument('ear', nargs='?', default='both', 
                       help='Which ear: left, right, or both (default: both)')
    parser.add_argument('max_volume', nargs='?', type=float, default=1.0,
                       help='Maximum volume level (0.0-1.0, default: 1.0)')
    
    # If no arguments provided, show usage
    if len(sys.argv) == 1:
        show_usage()
        return
    
    try:
        args = parser.parse_args()
    except SystemExit:
        return
    
    # Validate parameters
    errors = validate_parameters(args.frequency, args.intensity, args.duration, args.ear, args.max_volume)
    if errors:
        print("✗ Parameter errors:")
        for error in errors:
            print(f"  - {error}")
        print("\nUse --help for usage information")
        return
    
    # Generate and play tone
    try:
        generator = ToneGenerator()
        generator.play_tone(args.frequency, args.intensity, args.duration, args.ear, args.max_volume)
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
