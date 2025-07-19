#!/usr/bin/env python3
"""
Hearing Profile Data Analysis Module

Provides advanced analysis functions for hearing test results.
"""

import argparse
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
import json
from datetime import datetime


class HearingAnalyser:
    def __init__(self):
        self.age_hearing_norms = {
            # Age ranges and typical hearing thresholds (dB HL) by frequency
            20: {125: 5, 250: 5, 500: 5, 1000: 5, 2000: 5, 4000: 5, 8000: 10},
            30: {125: 5, 250: 5, 500: 5, 1000: 5, 2000: 10, 4000: 15, 8000: 20},
            40: {125: 5, 250: 5, 500: 5, 1000: 10, 2000: 15, 4000: 25, 8000: 30},
            50: {125: 10, 250: 10, 500: 10, 1000: 15, 2000: 20, 4000: 35, 8000: 40},
            60: {125: 15, 250: 15, 500: 15, 1000: 20, 2000: 30, 4000: 45, 8000: 50},
            70: {125: 20, 250: 20, 500: 20, 1000: 25, 2000: 35, 4000: 55, 8000: 60}
        }

    def calculate_hearing_threshold(self, test_results_for_frequency):
        """Calculate hearing threshold for a specific frequency"""
        heard_intensities = [r['intensity']
                             for r in test_results_for_frequency if r['heard']]

        if not heard_intensities:
            return 60  # Assume significant hearing loss if nothing heard

        min_heard = min(heard_intensities)
        # Convert intensity to approximate dB HL
        threshold_db = -20 * np.log10(min_heard)
        return max(0, threshold_db)  # Don't go below 0 dB

    def analyse_hearing_profile(self, test_results, age=None):
        """Comprehensive analysis of hearing test results"""
        analysis = {
            'left_ear': {},
            'right_ear': {},
            'comparison': {},
            'recommendations': []
        }

        for ear in ['left', 'right']:
            ear_key = f'{ear}_ear'
            ear_results = test_results[ear]

            # Handle both string and numeric frequency keys
            freq_data = {}
            for key, value in ear_results.items():
                numeric_freq = float(key)
                freq_data[numeric_freq] = value

            # Sort frequencies numerically
            frequencies = sorted(freq_data.keys())
            thresholds = []

            for freq in frequencies:
                threshold = self.calculate_hearing_threshold(freq_data[freq])
                thresholds.append(threshold)

            analysis[ear_key] = {
                'frequencies': frequencies,
                'thresholds': thresholds,
                'average_threshold': np.mean(thresholds),
                'high_frequency_loss': self.assess_high_frequency_loss(frequencies, thresholds),
                'hearing_classification': self.classify_hearing_loss(thresholds)
            }

        # Compare ears
        analysis['comparison'] = self.compare_ears(
            analysis['left_ear'], analysis['right_ear']
        )

        # Age comparison if provided
        if age:
            analysis['age_comparison'] = self.compare_to_age_norms(
                analysis, age
            )

        # Generate recommendations
        analysis['recommendations'] = self.generate_recommendations(analysis)

        return analysis

    def assess_high_frequency_loss(self, frequencies, thresholds):
        """Assess high-frequency hearing loss"""
        # Ensure frequencies are numeric for comparison
        numeric_frequencies = [float(f) for f in frequencies]
        high_freq_indices = [i for i, f in enumerate(
            numeric_frequencies) if f >= 4000]

        if not high_freq_indices:
            return {"severity": "unknown", "details": "No high frequency data"}

        high_freq_thresholds = [thresholds[i] for i in high_freq_indices]
        avg_high_freq_loss = np.mean(high_freq_thresholds)

        if avg_high_freq_loss < 15:
            severity = "normal"
        elif avg_high_freq_loss < 25:
            severity = "mild"
        elif avg_high_freq_loss < 40:
            severity = "moderate"
        else:
            severity = "severe"

        return {
            "severity": severity,
            "average_loss": avg_high_freq_loss,
            "details": f"Average high-frequency threshold: {avg_high_freq_loss:.1f} dB"
        }

    def classify_hearing_loss(self, thresholds):
        """Classify overall hearing loss severity"""
        avg_threshold = np.mean(thresholds)

        if avg_threshold <= 15:
            return "Normal hearing"
        elif avg_threshold <= 25:
            return "Mild hearing loss"
        elif avg_threshold <= 40:
            return "Moderate hearing loss"
        elif avg_threshold <= 70:
            return "Severe hearing loss"
        else:
            return "Profound hearing loss"

    def compare_ears(self, left_analysis, right_analysis):
        """Compare hearing between left and right ears"""
        left_avg = left_analysis['average_threshold']
        right_avg = right_analysis['average_threshold']

        difference = abs(left_avg - right_avg)

        if difference < 5:
            asymmetry = "symmetrical"
        elif difference < 15:
            asymmetry = "mild asymmetry"
        else:
            asymmetry = "significant asymmetry"

        better_ear = "left" if left_avg < right_avg else "right"

        return {
            "asymmetry": asymmetry,
            "difference_db": difference,
            "better_ear": better_ear,
            "details": f"{difference:.1f} dB difference between ears"
        }

    def compare_to_age_norms(self, analysis, age):
        """Compare results to age-appropriate norms"""
        # Find closest age group
        age_groups = sorted(self.age_hearing_norms.keys())
        closest_age = min(age_groups, key=lambda x: abs(x - age))
        norms = self.age_hearing_norms[closest_age]

        comparison = {}

        for ear in ['left_ear', 'right_ear']:
            ear_data = analysis[ear]
            frequencies = [float(f)
                           for f in ear_data['frequencies']]  # Ensure numeric
            thresholds = ear_data['thresholds']

            deviations = []
            for freq, threshold in zip(frequencies, thresholds):
                # Find closest norm frequency
                norm_freq = min(norms.keys(), key=lambda x: abs(x - freq))
                norm_threshold = norms[norm_freq]
                deviation = threshold - norm_threshold
                deviations.append(deviation)

            avg_deviation = np.mean(deviations)

            if avg_deviation < 5:
                assessment = "within normal limits for age"
            elif avg_deviation < 15:
                assessment = "slightly worse than age norms"
            else:
                assessment = "significantly worse than age norms"

            comparison[ear] = {
                "average_deviation": avg_deviation,
                "assessment": assessment,
                "reference_age": closest_age
            }

        return comparison

    def generate_recommendations(self, analysis):
        """Generate recommendations based on analysis"""
        recommendations = []

        # Check for significant hearing loss
        for ear in ['left_ear', 'right_ear']:
            classification = analysis[ear]['hearing_classification']
            if 'moderate' in classification.lower() or 'severe' in classification.lower():
                recommendations.append(
                    f"Consider consulting an audiologist about {classification.lower()} "
                    f"in your {ear.replace('_', ' ')}"
                )

        # Check for asymmetry
        if analysis['comparison']['asymmetry'] == "significant asymmetry":
            recommendations.append(
                "Significant hearing difference between ears detected. "
                "Consider professional evaluation."
            )

        # Check for high-frequency loss
        for ear in ['left_ear', 'right_ear']:
            hf_loss = analysis[ear]['high_frequency_loss']
            if hf_loss['severity'] in ['moderate', 'severe']:
                recommendations.append(
                    f"High-frequency hearing loss detected in {ear.replace('_', ' ')}. "
                    "This may affect speech understanding in noisy environments."
                )

        # General recommendations
        if not recommendations:
            recommendations.append(
                "Your hearing appears to be within normal ranges.")

        recommendations.append(
            "Regular hearing checks are recommended, especially if you notice changes.")

        return recommendations

    def create_detailed_report(self, test_results, age=None, save_path=None):
        """Create a detailed hearing analysis report"""
        analysis = self.analyse_hearing_profile(test_results, age)

        report = {
            "test_date": datetime.now().isoformat(),
            "analysis": analysis,
            "summary": {
                "left_ear_classification": analysis['left_ear']['hearing_classification'],
                "right_ear_classification": analysis['right_ear']['hearing_classification'],
                "ear_symmetry": analysis['comparison']['asymmetry'],
                # Top 2 recommendations
                "primary_recommendations": analysis['recommendations'][:2]
            }
        }

        if save_path:
            with open(save_path, 'w') as f:
                json.dump(report, f, indent=2)

        return report

    def plot_comparison_chart(self, test_results, age=None):
        """Create a comprehensive comparison chart"""
        analysis = self.analyse_hearing_profile(test_results, age)

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('Comprehensive Hearing Analysis', fontsize=16)

        # Individual ear plots
        for i, ear in enumerate(['left_ear', 'right_ear']):
            ax = ax1 if i == 0 else ax2
            ear_data = analysis[ear]

            ax.plot(ear_data['frequencies'], ear_data['thresholds'], 'o-',
                    linewidth=2, markersize=6, label=f'{ear.replace("_", " ").title()}')
            ax.set_title(
                f'{ear.replace("_", " ").title()} - {ear_data["hearing_classification"]}')
            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Hearing Threshold (dB HL)')
            ax.set_xscale('log')
            ax.grid(True, alpha=0.3)
            ax.set_xlim(100, 20000)
            ax.set_ylim(0, 70)
            ax.invert_yaxis()

        # Comparison plot
        left_data = analysis['left_ear']
        right_data = analysis['right_ear']

        ax3.plot(left_data['frequencies'], left_data['thresholds'], 'b-o',
                 label='Left Ear', linewidth=2, markersize=4)
        ax3.plot(right_data['frequencies'], right_data['thresholds'], 'r-s',
                 label='Right Ear', linewidth=2, markersize=4)

        ax3.set_title('Ear Comparison')
        ax3.set_xlabel('Frequency (Hz)')
        ax3.set_ylabel('Hearing Threshold (dB HL)')
        ax3.set_xscale('log')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        ax3.set_xlim(100, 20000)
        ax3.set_ylim(0, 70)
        ax3.invert_yaxis()

        # Age comparison (if age provided)
        if age and 'age_comparison' in analysis:
            ax4.text(0.1, 0.9, f"Age Comparison (Reference: {age} years)",
                     transform=ax4.transAxes, fontsize=12, fontweight='bold')

            y_pos = 0.7
            for ear in ['left_ear', 'right_ear']:
                comp = analysis['age_comparison'][ear]
                ax4.text(0.1, y_pos, f"{ear.replace('_', ' ').title()}: {comp['assessment']}",
                         transform=ax4.transAxes, fontsize=10)
                y_pos -= 0.1
        else:
            ax4.text(0.1, 0.5, "No age comparison\navailable",
                     transform=ax4.transAxes, fontsize=12, ha='center')

        ax4.axis('off')

        plt.tight_layout()
        return fig


def load_and_analyse(file_path, age=None):
    """Load test results and perform analysis"""
    with open(file_path, 'r') as f:
        data = json.load(f)

    analyser = HearingAnalyser()
    results = data['results']

    analysis = analyser.analyse_hearing_profile(results, age)

    print("Hearing Analysis Results")
    print("=" * 40)

    for ear in ['left_ear', 'right_ear']:
        print(f"\n{ear.replace('_', ' ').title()}:")
        print(f"  Classification: {analysis[ear]['hearing_classification']}")
        print(
            f"  Average threshold: {analysis[ear]['average_threshold']:.1f} dB")
        print(
            f"  High-frequency loss: {analysis[ear]['high_frequency_loss']['severity']}")

    print(f"\nEar comparison: {analysis['comparison']['asymmetry']}")

    print("\nRecommendations:")
    for i, rec in enumerate(analysis['recommendations'], 1):
        print(f"  {i}. {rec}")

    return analysis


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Generate a single tone using logarithmic volume scaling (same as hearing profiler)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  %(prog)s results.json 55  # Read from 'results.json' age = 55 years
"""
    )

    parser.add_argument('file', nargs='?', default='results.json',
                        help='JSON file name, from hearing_profiler')
    parser.add_argument('age', type=int,
                        help='Age (in years)')

    # If no arguments provided, show usage
    if len(sys.argv) == 1:
        parser.print_help()
        exit(1)
    try:
        args = parser.parse_args()
    except SystemExit:
        exit(1)

    load_and_analyse(args.file, args.age)