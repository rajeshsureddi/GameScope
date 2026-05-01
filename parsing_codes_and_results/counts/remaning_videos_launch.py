#!/usr/bin/env python3

import pandas as pd
import os
import sys

def reformat_videos_for_relaunch(input_csv_path, output_directory):
    """
    Simple function to convert video names from CSV to relaunch format.
    
    Args:
        input_csv_path: Path to CSV with video_name column
        output_directory: Where to save the output CSV
    """
    
    # Read input CSV
    df = pd.read_csv(input_csv_path)
    video_names = df['video_name'].tolist()
    
    # Create output with video1, video2, ... columns
    output_data = {}
    for i, video_name in enumerate(video_names, 1):
        output_data[f'video{i}'] = video_name
    
    # Save as single row CSV
    output_df = pd.DataFrame([output_data])
    
    # Create output filename
    input_filename = os.path.basename(input_csv_path).replace('.csv', '')
    output_path = os.path.join(output_directory, f"{input_filename}_relaunch.csv")
    
    # Create directory and save
    os.makedirs(output_directory, exist_ok=True)
    output_df.to_csv(output_path, index=False)
    
    print(f"Processed {len(video_names)} videos")
    print(f"Output saved to: {output_path}")
    
    return output_path

if __name__ == "__main__":
    
    input_csv = './parsing_codes_and_results/counts/batchJ_secondparse/approve_reject_reports/approve_reject_videos_less_than_30_valid_ratings.csv'
    output_dir = './parsing_codes_and_results/counts/batchJ_secondparse/approve_reject_reports/relaunch_videos'
    
    reformat_videos_for_relaunch(input_csv, output_dir)
