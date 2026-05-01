import pandas as pd
import numpy as np
import os

def map_video_names_to_mos():
    """
    Map video names from global ratings matrix to their corresponding MOS and SOS values
    from alternating projection results based on video index.
    """
    
    # File paths
    global_ratings_path = "./parsing_codes_and_results/counts/global_analysis_output/global_individual_ratings_matrix.csv"
    mos_results_path = "/mnt/LIVELAB_NAS/rajesh/New_Gaming/GamingVQA_benchmarks/sureal/itut_p910_demo/alternating_projection_video_metrics_GamingVQA.csv"
    output_path = "./parsing_codes_and_results/counts/video_names_with_mos_sos.csv"
    
    # Read the data
    df_global = pd.read_csv(global_ratings_path)
    df_mos = pd.read_csv(mos_results_path)
    
    # Create mapping
    mapped_data = []
    for idx, row in df_global.iterrows():
        if idx < len(df_mos):
            mos_row = df_mos.iloc[idx]
            mapped_data.append({
                'video_name': row['video_name'],
                'batch': row['batch'],
                'video_index': mos_row['video_index'],
                'mos': mos_row['mos'],
                'sos': mos_row['sos']
            })
    
    # Save to CSV
    df_mapped = pd.DataFrame(mapped_data)
    df_mapped.to_csv(output_path, index=False)
    
    return df_mapped

if __name__ == "__main__":
    map_video_names_to_mos() 