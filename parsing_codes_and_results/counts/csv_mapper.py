#!/usr/bin/env python3
"""
CSV Mapper Script
Maps the second CSV file to first CSV file with video_name matching.
Adds MOS and SOS columns to the first CSV file.
"""

import pandas as pd
import os
from pathlib import Path

def extract_video_name_from_file_path(file_path):
    """Extract base video name from file path by removing .mp4 extension"""
    return Path(file_path).stem

def extract_video_name_from_amt_path(amt_path):
    """Extract video name from amt_gaming_vqa_dataset path"""
    if amt_path.startswith('amt_gaming_vqa_dataset/'):
        return amt_path.replace('amt_gaming_vqa_dataset/', '')
    return amt_path

def main():
    # File paths
    first_csv = "/mnt/LIVELAB_NAS/rajesh/New_Gaming/GamingVQA_benchmarks/GAMIVAL/mos_files/GamingVQA_metadata_modified_myst_graderscopes_this_is_final_pro.csv"
    second_csv = "./parsing_codes_and_results/counts/video_names_with_mos_sos_attributes.csv"
    output_csv = "/mnt/LIVELAB_NAS/rajesh/New_Gaming/GamingVQA/metadata/GamingVQA_final_metadata_after_study_with_attributes.csv"
    
    print("Loading CSV files...")
    
    # Load first CSV
    df1 = pd.read_csv(first_csv)
    print(f"First CSV loaded: {len(df1)} rows")
    print(f"Columns: {list(df1.columns)}")
    
    # Load second CSV  
    df2 = pd.read_csv(second_csv)
    print(f"Second CSV loaded: {len(df2)} rows")
    print(f"Columns: {list(df2.columns)}")
    
    # Extract video names for matching
    print("\nExtracting video names for matching...")
    
    # From first CSV: extract base filename from File column
    df1['video_name_extracted'] = df1['File'].apply(extract_video_name_from_file_path)
    print(f"Sample extracted names from first CSV: {df1['video_name_extracted'].head().tolist()}")
    
    # From second CSV: extract video name from video_name column
    df2['video_name_extracted'] = df2['video_name'].apply(extract_video_name_from_amt_path)
    print(f"Sample extracted names from second CSV: {df2['video_name_extracted'].head().tolist()}")
    
    # Create a lookup dictionary from second CSV
    # Handle multiple entries per video name by taking the first occurrence
    print("\nCreating lookup dictionary...")
    mos_sos_lookup = {}
    
    for _, row in df2.iterrows():
        video_name = row['video_name_extracted']
        if video_name not in mos_sos_lookup:
            mos_sos_lookup[video_name] = {
                'mos': row['mos'],
                'sos': row['sos'],
                'most_common_clarity': row['most_common_clarity'],
                'most_common_artifacts': row['most_common_artifacts'],
                'most_common_immersion': row['most_common_immersion']
            }
    
    print(f"Created lookup for {len(mos_sos_lookup)} unique video names")
    
    # Map MOS, SOS, and attributes to first CSV
    print("\nMapping MOS, SOS, and attribute values...")
    
    df1['MOS'] = df1['video_name_extracted'].map(lambda x: mos_sos_lookup.get(x, {}).get('mos', None))
    df1['SOS'] = df1['video_name_extracted'].map(lambda x: mos_sos_lookup.get(x, {}).get('sos', None))
    df1['most_common_clarity'] = df1['video_name_extracted'].map(lambda x: mos_sos_lookup.get(x, {}).get('most_common_clarity', None))
    df1['most_common_artifacts'] = df1['video_name_extracted'].map(lambda x: mos_sos_lookup.get(x, {}).get('most_common_artifacts', None))
    df1['most_common_immersion'] = df1['video_name_extracted'].map(lambda x: mos_sos_lookup.get(x, {}).get('most_common_immersion', None))
    
    # Remove the temporary column
    df1_final = df1.drop('video_name_extracted', axis=1)
    
    # Check matching statistics
    matched_count = df1_final['MOS'].notna().sum()
    total_count = len(df1_final)
    print(f"\nMatching Results:")
    print(f"Total rows in first CSV: {total_count}")
    print(f"Successfully matched: {matched_count}")
    print(f"Unmatched: {total_count - matched_count}")
    print(f"Match rate: {matched_count/total_count*100:.2f}%")
    
    # Show some examples of matched data
    print("\nSample of matched data:")
    matched_samples = df1_final[df1_final['MOS'].notna()].head()
    print(matched_samples[['File', 'MOS', 'SOS', 'most_common_clarity', 'most_common_artifacts', 'most_common_immersion']])
    
    # Show some examples of unmatched data
    unmatched_samples = df1_final[df1_final['MOS'].isna()]
    if len(unmatched_samples) > 0:
        print(f"\nSample of unmatched data (first 5):")
        print(unmatched_samples[['File']].head())
    
    # Show attribute statistics for matched data
    print(f"\nAttribute statistics for matched data:")
    matched_data = df1_final[df1_final['MOS'].notna()]
    print(f"Clarity distribution:")
    print(matched_data['most_common_clarity'].value_counts())
    print(f"\nArtifacts distribution:")
    print(matched_data['most_common_artifacts'].value_counts())
    print(f"\nImmersion distribution:")
    print(matched_data['most_common_immersion'].value_counts())
    
    # Save the result
    print(f"\nSaving merged CSV to: {output_csv}")
    df1_final.to_csv(output_csv, index=False)
    print("Done!")
    
    # Display final column information
    print(f"\nFinal CSV structure:")
    print(f"Columns: {list(df1_final.columns)}")
    print(f"Shape: {df1_final.shape}")
    
    return df1_final

if __name__ == "__main__":
    main() 