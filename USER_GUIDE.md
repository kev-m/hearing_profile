# Hearing Profiler - User Guide

## Quick Start

1. **Run the application**:
   - Double-click `run_hearing_profiler.bat`
   - Or run: `python hearing_profiler.py`

2. **Setup your environment**:
   - Connect good quality headphones or earphones
   - Find a quiet room

3. **Calibration Lowest**:
   - Click "Generate Softest Tone" to hear a 1000 Hz reference tone
   - Adjust your computer system volume until you can just hear the tone (almost too soft to hear)

3. **Calibration Comfort**:
   - Use the volume slider to set a comfortable listening level
   - Click "Test Calibration Tone" to hear a 1000 Hz reference tone
   - Adjust until the tone is clearly audible but not loud

4. **Take the test**:
   - Click "Start Hearing Test"
   - Listen carefully for tones in each ear
   - Click "I Heard It!" immediately when you hear a tone
   - If you don't hear anything, wait for the next tone
   - Each tone is separated by 1.5+ seconds to give you time to respond
   - The test takes about 8-12 minutes

5. **View results**:
   - Your hearing profile will be displayed as graphs
   - Save results for future comparison

## Features

### Audio System
- **Continuous audio stream**: Maintains constant audio output for Bluetooth headphone compatibility
- **Precise tone generation**: Uses sinusoidal waves with anti-click envelopes
- **Multiple intensity levels**: Tests hearing at different volume levels
- **Frequency range**: Tests from 125 Hz to 16,000 Hz across 15 bands

### Test Methodology
- **Logarithmic frequency spacing**: More detail in critical hearing ranges
- **Randomized presentation**: Prevents anticipation bias
- **Separate ear testing**: Independent assessment of left and right ears
- **Multiple intensity levels**: 4 different volume levels per frequency
- **Statistical approach**: Multiple measurements per frequency for reliability

### Results Analysis
- **Hearing threshold graphs**: Visual representation of your hearing sensitivity
- **Frequency response curves**: Shows hearing ability across the frequency spectrum
- **Comparative analysis**: Compare left vs right ear performance
- **Data persistence**: Save and load results for tracking changes over time

## Understanding Your Results

### Graph Interpretation
- **X-axis**: Frequency in Hz (logarithmic scale)
- **Y-axis**: Hearing threshold in dB (lower is better)
- **Line shape**: Shows your hearing sensitivity across frequencies

### Common Patterns
- **Normal hearing**: Relatively flat line below 20 dB
- **Age-related loss**: Rising line at high frequencies (above 4000 Hz)
- **Noise-induced loss**: Notch around 4000-6000 Hz
- **Asymmetric loss**: Different patterns between ears

### Threshold Classifications
- **0-15 dB**: Normal hearing
- **16-25 dB**: Mild hearing loss
- **26-40 dB**: Moderate hearing loss
- **41-70 dB**: Severe hearing loss
- **>70 dB**: Profound hearing loss

## Tips for Accurate Testing

### Environment
- Use a quiet room (background noise < 30 dB)
- Avoid distractions (TV, music, conversations)
- Test when you're alert and focused
- Take breaks if you feel fatigued

### Equipment
- Use high-quality headphones or earphones
- Ensure proper fit and seal
- Check for damaged cables or connections
- Calibrate volume before each test session

### Technique
- Respond immediately when you hear a tone
- Don't guess - only respond if you clearly hear the tone
- Maintain consistent attention throughout the test
- Don't adjust volume during the test

## Advanced Features

### Data Analysis
Use the `hearing_analyzer.py` module for advanced analysis:

```python
from hearing_analyzer import load_and_analyze

# Analyze results with age comparison
analysis = load_and_analyze('my_results.json', age=35)
```

### Configuration
Edit `config.json` to customize:
- Test parameters (frequencies, intensities)
- Audio settings (sample rate, tone duration)
- UI preferences

### Batch Processing
Analyze multiple test sessions:

```python
import json
from hearing_analyzer import HearingAnalyzer

analyzer = HearingAnalyzer()

# Load multiple results files
for file in ['test1.json', 'test2.json', 'test3.json']:
    with open(file) as f:
        data = json.load(f)
    analysis = analyzer.analyze_hearing_profile(data['results'])
    print(f"Analysis for {file}: {analysis}")
```

## Troubleshooting

### Audio Issues
**Problem**: No sound or distorted audio
- Check audio drivers are up to date
- Try different headphones
- Run `python test_audio.py` to diagnose
- Restart the application

**Problem**: Bluetooth headphones cutting out
- The application uses continuous audio to prevent this
- Try reducing the silence duration in config
- Use wired headphones for most accurate results

**Problem**: Exception with "outputBufferTime" when clicking Test Calibration
- This has been fixed in the current version
- Make sure you're using the latest version of the application
- If the error persists, restart the application

### Performance Issues
**Problem**: Application runs slowly
- Close other audio applications
- Reduce the number of frequency bands in config
- Check system resources (CPU, memory)

### Test Accuracy
**Problem**: Inconsistent results
- Ensure quiet testing environment
- Check headphone fit and positioning
- Take multiple tests and compare
- Consider professional audiometry for verification

**Problem**: Tones come too quickly to respond
- This has been improved - tones now have 1.5+ second gaps
- You have 3+ seconds to respond after each tone
- If still too fast, you can edit the `silence_duration` in the code

**Problem**: Application doesn't start or crashes
- Verify Python environment is activated
- Check that all required packages are installed: `pip install -r requirements.txt`
- Run `python test_audio.py` to verify audio system
- Check Windows audio drivers are functioning

**Problem**: Application doesn't exit when window is closed
- This has been fixed in the current version
- The application now properly stops all audio streams and background processes
- If the issue persists, try pressing Ctrl+C in the terminal or Task Manager to force close

## Limitations and Disclaimers

### This Application Is Not
- A medical device
- A substitute for professional audiometry
- Diagnostic equipment
- Calibrated to medical standards

### Intended Use
- Educational purposes
- Rough hearing assessment
- Tracking changes over time
- General awareness of hearing health

### Recommendations
- Consult a healthcare professional for hearing concerns
- Get regular professional hearing tests
- Use this tool as a supplement, not replacement for medical care
- If you notice hearing changes, seek professional evaluation

## File Structure

```
HearMe/
├── hearing_profiler.py      # Main application
├── hearing_analyzer.py      # Advanced analysis module
├── test_audio.py           # Audio system test
├── config.json             # Configuration settings
├── requirements.txt        # Python dependencies
├── run_hearing_profiler.bat # Windows launcher
└── README.md               # This documentation
```

## Data Format

Results are saved in JSON format:

```json
{
  "timestamp": "2025-07-19T10:30:00",
  "calibration_volume": 0.5,
  "frequency_bands": [125, 177, 250, ...],
  "intensity_levels": [0.1, 0.3, 0.6, 1.0],
  "results": {
    "left": {
      "1000": [
        {"intensity": 0.1, "heard": false},
        {"intensity": 0.3, "heard": true},
        ...
      ]
    },
    "right": {...}
  }
}
```

## Version History

### v1.0
- Initial release
- Basic frequency testing
- GUI interface
- Results visualization
- Data saving/loading

## Support

For issues or questions:
1. Check this user guide
2. Run the audio test (`test_audio.py`)
3. Verify your Python environment and dependencies
4. Check Windows audio settings and drivers

## License

This software is provided for educational and personal use only.
No warranty is provided for accuracy or medical suitability.
