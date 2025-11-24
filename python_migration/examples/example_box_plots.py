"""
Example script demonstrating PHUSE box plot generation.

Python equivalent of example_call_wpct-f.07.01.sas and WPCT-F.07.01.sas.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from sas_clinical.visualization.box_plots import PHUSEBoxPlot, generate_phuse_box_plots


def create_sample_data() -> pd.DataFrame:
    """Create sample ADaM data for demonstration."""
    
    np.random.seed(42)
    
    # Create sample ADLBC-like data
    n_subjects = 30
    n_visits = 4
    n_treatments = 3
    
    data = []
    
    for subj_id in range(1, n_subjects + 1):
        trtpn = (subj_id % n_treatments) + 1
        trtp = ['Placebo', 'Low Dose', 'High Dose'][trtpn - 1]
        
        for visit_num in range(n_visits):
            avisitn = visit_num * 2
            avisit = f"Week {avisitn}"
            
            # Generate measurement with treatment effect
            baseline = np.random.normal(100, 15)
            treatment_effect = (trtpn - 1) * 5
            aval = baseline + treatment_effect + np.random.normal(0, 10)
            
            # Reference ranges
            anrlo = 85
            anrhi = 115
            
            data.append({
                'studyid': 'STUDY001',
                'usubjid': f'SUBJ-{subj_id:03d}',
                'saffl': 'Y',
                'anl01fl': 'Y',
                'trtp': trtp,
                'trtpn': trtpn,
                'param': 'Albumin (g/L)',
                'paramcd': 'ALB',
                'aval': aval,
                'avisitn': avisitn,
                'avisit': avisit,
                'atptn': 1,
                'atpt': 'Pre-dose',
                'anrlo': anrlo,
                'anrhi': anrhi,
                'a1lo': anrlo,
                'a1hi': anrhi
            })
    
    df = pd.DataFrame(data)
    
    print(f"\nCreated sample dataset:")
    print(f"  Subjects: {n_subjects}")
    print(f"  Visits: {n_visits}")
    print(f"  Treatments: {n_treatments}")
    print(f"  Total records: {len(df)}")
    
    return df


def main():
    """Run box plot examples."""
    
    print("\n" + "="*80)
    print("Python PHUSE Box Plot Examples")
    print("="*80 + "\n")
    
    # Create sample data
    print("Creating sample ADaM data...")
    data = create_sample_data()
    
    # Set up output directory
    output_dir = Path(__file__).parent.parent / 'results' / 'python_box_plots'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nOutput directory: {output_dir}")
    
    # Example 1: Generate box plots using convenience function
    print("\n" + "="*80)
    print("Example 1: Generate PHUSE Box Plots")
    print("="*80 + "\n")
    
    generate_phuse_box_plots(
        data=data,
        output_dir=output_dir,
        treatment_var='trtp',
        treatment_num_var='trtpn',
        measurement_var='aval',
        visit_var='avisit',
        visit_num_var='avisitn',
        timepoint_var='atpt',
        timepoint_num_var='atptn',
        param_var='param',
        param_code_var='paramcd',
        low_ref_var='anrlo',
        high_ref_var='anrhi',
        population_flag='saffl',
        analysis_flag='anl01fl'
    )
    
    # Example 2: Using PHUSEBoxPlot class directly
    print("\n" + "="*80)
    print("Example 2: Using PHUSEBoxPlot Class")
    print("="*80 + "\n")
    
    plotter = PHUSEBoxPlot(
        data=data,
        treatment_var='trtp',
        treatment_num_var='trtpn',
        measurement_var='aval',
        visit_var='avisit',
        visit_num_var='avisitn',
        timepoint_var='atpt',
        timepoint_num_var='atptn',
        param_var='param',
        param_code_var='paramcd',
        low_ref_var='anrlo',
        high_ref_var='anrhi'
    )
    
    # Generate plots with custom settings
    plotter.generate_box_plots(
        output_dir=output_dir,
        param_codes=['ALB'],
        ref_lines='UNIFORM',
        max_boxes_per_page=20,
        figsize=(14, 8)
    )
    
    print("\n" + "="*80)
    print("Box Plot Generation Complete!")
    print(f"Outputs saved to: {output_dir}")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
