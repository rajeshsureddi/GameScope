import pandas as pd
import numpy as np
import os

def map_video_names_to_mos():
    """
    Map video names from global ratings matrix to their corresponding MOS, SOS values
    and video attributes (clarity, artifacts, immersion) based on video index.
    """
    
    # File paths
    global_ratings_path = "./parsing_codes_and_results/counts/global_analysis_output/global_individual_ratings_matrix.csv"
    mos_results_path = "/mnt/LIVELAB_NAS/rajesh/New_Gaming/GamingVQA_benchmarks/sureal/itut_p910_demo/alternating_projection_video_metrics_GamingVQA.csv"
    attributes_path = "./parsing_codes_and_results/counts/global_analysis_output/global_video_attributes.csv"
    output_path = "./parsing_codes_and_results/counts/video_names_with_mos_sos_attributes.csv"
    
    # Read the data
    df_global = pd.read_csv(global_ratings_path)
    df_mos = pd.read_csv(mos_results_path)
    df_attributes = pd.read_csv(attributes_path)
    
    print(f"Loaded {len(df_global)} videos from global ratings")
    print(f"Loaded {len(df_mos)} MOS/SOS entries")
    print(f"Loaded {len(df_attributes)} video attributes")
    
    # Create a dictionary for quick attribute lookup by video name
    attributes_dict = {}
    for _, row in df_attributes.iterrows():
        attributes_dict[row['video_name']] = {
            'most_common_clarity': row['most_common_clarity'],
            'most_common_artifacts': row['most_common_artifacts'],
            'most_common_immersion': row['most_common_immersion']
        }
    
    # Create mapping
    mapped_data = []
    for idx, row in df_global.iterrows():
        if idx < len(df_mos):
            mos_row = df_mos.iloc[idx]
            video_name = row['video_name']
            
            # Get attributes for this video (if available)
            video_attrs = attributes_dict.get(video_name, {
                'most_common_clarity': 'Unknown',
                'most_common_artifacts': 'Unknown', 
                'most_common_immersion': 'Unknown'
            })
            
            mapped_data.append({
                'video_name': video_name,
                'batch': row['batch'],
                'video_index': mos_row['video_index'],
                'mos': mos_row['mos'],
                'sos': mos_row['sos'],
                'most_common_clarity': video_attrs['most_common_clarity'],
                'most_common_artifacts': video_attrs['most_common_artifacts'],
                'most_common_immersion': video_attrs['most_common_immersion']
            })
    
    # Save to CSV
    df_mapped = pd.DataFrame(mapped_data)
    df_mapped.to_csv(output_path, index=False)
    
    print(f"Saved {len(df_mapped)} mapped entries to {output_path}")
    print("\nSample of the first 5 entries:")
    print(df_mapped.head())
    
    # Print some statistics about the attributes
    print(f"\nClarity distribution:")
    print(df_mapped['most_common_clarity'].value_counts())
    print(f"\nArtifacts distribution:")
    print(df_mapped['most_common_artifacts'].value_counts())
    print(f"\nImmersion distribution:")
    print(df_mapped['most_common_immersion'].value_counts())
    
    return df_mapped

if __name__ == "__main__":
    map_video_names_to_mos() 