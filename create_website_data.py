
import pandas as pd
import os
import shutil
import random
import json

# Paths
csv_path = '/mnt/LIVELAB_NAS/rajesh/New_Gaming/GamingVQA/metadata/GamingVQA_final_metadata_complete_with_attributes_and_types.csv'
plot_path = '/mnt/LIVELAB_NAS/rajesh/New_Gaming/GamingVQA/metadata/train_test_splits/qwen3/good_results_visualizations/clips_count/gamingVQA_combined_ugc_ps5_game_clip_counts_by_resolution.png'
dest_dir = '/mnt/LIVELAB_NAS/rajesh/New_Gaming/gamescope_website'
videos_dest = os.path.join(dest_dir, 'videos')
images_dest = os.path.join(dest_dir, 'images')

os.makedirs(videos_dest, exist_ok=True)
os.makedirs(images_dest, exist_ok=True)

# Copy Plot
if os.path.exists(plot_path):
    print(f"Copying plot from {plot_path} to {images_dest}")
    shutil.copy(plot_path, os.path.join(images_dest, 'plot.png'))
else:
    print(f"WARNING: Plot not found at {plot_path}")

# Load CSV
df = pd.read_csv(csv_path)

# Ensure data types are strings
df['user_type'] = df['user_type'].astype(str)
df['most_common_clarity'] = df['most_common_clarity'].astype(str)
df['most_common_artifacts'] = df['most_common_artifacts'].astype(str)
df['most_common_immersion'] = df['most_common_immersion'].astype(str)

selected_indices = set()

# Strategy: Select diverse videos
# Target: ~12-15 videos total
# Priority: Coverage of user_type x clarity x artifacts

# Group by major categories
groups = df.groupby(['user_type', 'most_common_clarity'])

for name, group in groups:
    # Pick up to 2 videos per clarity group
    n = min(2, len(group))
    if n > 0:
        sample = group.sample(n)
        for idx in sample.index:
            selected_indices.add(idx)

# Ensure artifacts diversity
artifacts_groups = df.groupby(['most_common_artifacts'])
for name, group in artifacts_groups:
    # Check if we have this artifact level covered
    covered = False
    for idx in selected_indices:
        if df.loc[idx, 'most_common_artifacts'] == name:
            covered = True
            break
    if not covered:
         # Add one video with this artifact level
         n = min(1, len(group))
         if n > 0:
             idx = group.sample(n).index[0]
             selected_indices.add(idx)

# Ensure immersion diversity
immersion_groups = df.groupby(['most_common_immersion'])
for name, group in immersion_groups:
    covered = False
    for idx in selected_indices:
        if df.loc[idx, 'most_common_immersion'] == name:
            covered = True
            break
    if not covered:
         n = min(1, len(group))
         if n > 0:
             idx = group.sample(n).index[0]
             selected_indices.add(idx)

print(f"Selected {len(selected_indices)} videos.")

selected_videos = []
for idx in selected_indices:
    row = df.loc[idx]
    src_path = row['File']
    filename = os.path.basename(src_path)
    user_type = row['user_type']
    
    # Destination path: videos/user_type/filename
    user_dir = os.path.join(videos_dest, user_type)
    os.makedirs(user_dir, exist_ok=True)
    dst_path = os.path.join(user_dir, filename)
    
    # Only copy if not exists to save time, or force update? 
    # Use overwrite to ensure we have correct files if script changed
    try:
        if not os.path.exists(dst_path):
             print(f"Copying {src_path} to {dst_path}")
             shutil.copy(src_path, dst_path)
        else:
             print(f"File exists: {dst_path}")
        
        # Add metadata for JSON (convert series to dict)
        video_data = row.to_dict()
        video_data['relative_path'] = f'videos/{user_type}/{filename}'
        selected_videos.append(video_data)
    except Exception as e:
        print(f"Error copying {src_path}: {e}")

# Save Metadata JSON
with open(os.path.join(dest_dir, 'data.json'), 'w') as f:
    json.dump(selected_videos, f, indent=2)

print("Done.")
