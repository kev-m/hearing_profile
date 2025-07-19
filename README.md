# Hearing Profiler

Hearing frequency range typically decreases as we age. Teenagers can hear higher and lower 
frequencies than their grandparents. This is a normal ageing process.

This application allows you to get a qualitative impression of your hearing range.

## Method

This application generates single frequency tones in a semi-random fashion, and uses
user-feedback to map out an approximate graph of hearing range.

## Detail Method

After a simplistic calibration process, this application splits the typical hearing range
into 10 or 15 bands. For each band, it generates 3 or 4 sinusoidal signal tones of about
1/3 to 1/2 a second, at the band centre frequency, at different intensities, for each ear 
independently.

It uses user-feedback (a button press, to indicate that they heard the tone), to build
up a hearing range sensitivity graph.

At the end, it correlates the marked and the missed signals, to output a typical 
efficiency versus frequency graph, for each ear.

The user can save the graph and the data, for future comparisons.

## Technical Details

Because the user may be using BlueTooth headphones/earphones, the application must generate
a constant audio output, to prevent the BlueTooth device from missing any part of the
audio signals.

## Installation and Setup

### Prerequisites
- Windows 10/11
- Python 3.9 or higher
- Audio output device (headphones recommended)

### Quick Start
1. **Install dependencies** (already done in your virtual environment):
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python hearing_profiler.py
   ```

### Files Overview
- `hearing_profiler.py` - Main application with GUI
- `hearing_analyser.py` - Advanced analysis and reporting
- `cli_tone_test.py` - Single-shot CLI tone generator for testing
- `config.json` - **Configuration settings (editable)**
- `CONFIG_GUIDE.md` - **Complete configuration documentation**
- `USER_GUIDE.md` - Comprehensive user documentation

## Features Implemented

### Core Functionality
✅ **Frequency Testing**: 15 logarithmically-spaced frequency bands (125 Hz - 16 kHz)  
✅ **Multi-Intensity Testing**: 4 different volume levels per frequency  
✅ **Bilateral Testing**: Independent left and right ear assessment  
✅ **Randomized Presentation**: Prevents bias and anticipation  
✅ **Continuous Audio Stream**: Bluetooth headphone compatibility  
✅ **Dual Test Modes**: Quick test (2 min) and Full test (8-10 min)  
✅ **Precomputed Audio**: Single audio stream with precise timing  
✅ **JSON Configuration**: All settings editable in `config.json`  

### User Interface
✅ **Calibration System**: Volume adjustment with smooth analog slider  
✅ **Test Mode Selection**: Choose between Quick (2 min) or Full (8-10 min) tests  
✅ **Progress Tracking**: Real-time test progress display  
✅ **Visual Results**: Matplotlib-based hearing profile graphs  
✅ **Data Management**: Save/load test results in JSON format  
✅ **Persistent Settings**: Calibration volume saved automatically  

### Advanced Analysis
✅ **Hearing Classification**: Normal to profound hearing loss categories  
✅ **Asymmetry Detection**: Left vs right ear comparison  
✅ **High-Frequency Assessment**: Age-related hearing loss detection  
✅ **Age Comparison**: Compare results to age-appropriate norms  
✅ **Detailed Reporting**: Comprehensive analysis with recommendations  

## Usage Instructions

### Basic Test Procedure
1. Connect quality headphones
2. Find a quiet environment
3. Launch the application
4. Calibrate system volume using the test tone
4. Calibrate test volume using the test tone
5. Start the hearing test
6. Click "I Heard It!" when you hear tones
7. Review your hearing profile graphs
8. Save results for future comparison

### CLI Tone Testing
For debugging or manual testing, use the single-shot CLI tool:
```bash
# Generate specific tones for testing (now with logarithmic volume scaling)
python cli_tone_test.py 1000 0.5 1.0        # Reference tone (mid intensity)
python cli_tone_test.py 4000 0.1 0.5 left   # Very quiet test (left ear)
python cli_tone_test.py 8000 0.8 0.3 right  # Loud high frequency test (right ear)
python cli_tone_test.py 1000 0.1 1.0 both 0.5  # Quiet test with 50% volume limit
```

**Important Volume Changes:** The application now uses **logarithmic volume scaling** instead of linear scaling. This means:
- Intensity 0.1 = 1.6% of max volume
- Intensity 0.3 = 4.0% of max volume  
- Intensity 0.6 = 15.8% of max volume
- Intensity 1.0 = 100% of max volume

This creates a much better range for detecting hearing thresholds and should resolve issues with "flat" hearing profiles.

### Configuration System
The application now reads all settings from `config.json`:
```json
{
  "audio": {
    "tone_duration": 0.33,     // Customize tone length
    "fade_duration": 0.01      // Prevent audio clicks
  },
  "testing": {
    "frequency_bands": 15,     // Number of test frequencies
    "intensity_levels": [0.1, 0.3, 0.6, 1.0],  // Test volume levels
    "inter_test_delay_range": [0.75, 1.25]     // Gap between tones
  },
  "calibration": {
    "saved_volume": 0.5        // Automatically saved calibration
  }
}
```

**Benefits:**
- **Edit settings** without modifying Python code
- **Persistent calibration** volume across sessions
- **Customize test parameters** for different use cases
- **Create test profiles** for quick vs. detailed assessments

See `CONFIG_GUIDE.md` for complete documentation and examples.

### Understanding Results
- **Lower thresholds = Better hearing**
- **Graph shows frequency response**
- **Compare left vs right ear performance**
- **Track changes over time**

### Professional Note
This application is for educational and personal use only. It is not a medical device and should not replace professional audiological assessment. 
Consult a healthcare provider for hearing concerns.

## Technical Implementation

### Audio Engine
- **Sample Rate**: 44.1 kHz
- **Tone Generation**: Pure sinusoidal waves with anti-click envelopes
- **Stream Management**: Continuous output for Bluetooth compatibility
- **Precision Timing**: Accurate tone duration and spacing

### Test Methodology
- **Logarithmic Frequency Spacing**: Better resolution in critical ranges
- **Multiple Measurements**: Statistical reliability through repetition
- **Threshold Detection**: Minimum audible intensity per frequency
- **Cross-Validation**: Consistency checking across intensity levels

### Data Analysis
- **Threshold Calculation**: Convert intensity responses to dB scale
- **Curve Fitting**: Smooth hearing profile generation
- **Statistical Analysis**: Confidence intervals and reliability metrics
- **Comparative Analysis**: Age norms and bilateral comparison