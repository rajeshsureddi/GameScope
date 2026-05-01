import os
import csv
import random
from collections import defaultdict

# ─── USER PARAMETERS ────────────────────────────────────────────────────────────
# Directory containing original .mp4 videos
ORIGINAL_DIR = "/mnt/LIVELAB_NAS/rajesh/New_Gaming/GamingVQA/original"
# Directory containing distorted .mp4 videos
DISTORTED_DIR = "/mnt/LIVELAB_NAS/rajesh/New_Gaming/GamingVQA/distorted"
# Number of videos per batch (including original + distorted versions)
BATCH_SIZE = 93
# Output folder for batch CSVs
OUTPUT_DIR = "./create_hit_batches_non_overlap/"
# Prefix for AMT dataset
PREFIX = "amt_gaming_vqa_dataset/"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── GATHER ALL ORIGINAL .mp4 FILES ────────────────────────────────────────────
print("Gathering original files...")
original_files = []
for root, _, filenames in os.walk(ORIGINAL_DIR):
    for fname in filenames:
        if fname.lower().endswith('.mp4'):
            original_files.append(fname)

# Extract base names (without extension) for original files
original_base_names = [os.path.splitext(f)[0] for f in original_files]
print(f"Found {len(original_base_names)} original files")

# ─── GATHER ALL DISTORTED .mp4 FILES AND GROUP BY ORIGINAL ──────────────────────
print("Gathering distorted files and grouping by original...")
distorted_groups = defaultdict(list)
orphaned_distorted = []  # Distorted files without originals

for root, _, filenames in os.walk(DISTORTED_DIR):
    for fname in filenames:
        if fname.lower().endswith('.mp4'):
            # Find the original base name by removing quality suffix
            # Distorted files have format: original_name_quality_params.mp4
            base_name = os.path.splitext(fname)[0]
            
            # Find which original this distorted file belongs to
            matched = False
            for original_base in original_base_names:
                if base_name.startswith(original_base + '_'):
                    distorted_groups[original_base].append(fname)
                    matched = True
                    break
            
            # If no original found, add to orphaned list
            if not matched:
                orphaned_distorted.append(fname)

print(f"Found distorted versions for {len(distorted_groups)} original files")
print(f"Found {len(orphaned_distorted)} distorted files without originals")

# ─── CREATE GROUPED DATA STRUCTURE ──────────────────────────────────────────────
print("Creating grouped data structure...")
grouped_data = []

# Add groups with originals
for original_base in original_base_names:
    group = {
        'original': original_base,
        'original_path': f"{PREFIX}{original_base}.mp4",
        'distorted_versions': []
    }
    
    if original_base in distorted_groups:
        for distorted_file in distorted_groups[original_base]:
            group['distorted_versions'].append(f"{PREFIX}{distorted_file}")
    
    grouped_data.append(group)

# Add orphaned distorted files as individual groups
if orphaned_distorted:
    print(f"Grouping {len(orphaned_distorted)} orphaned distorted files by original names...")
    
    # Group orphaned files by their original names (split by ".", then by "_", remove quality params)
    orphaned_groups = defaultdict(list)
    
    for distorted_file in orphaned_distorted:
        # First split by "." to remove extension, then split by "_"
        base_name = distorted_file.split(".")[0]  # Remove .mp4 extension
        parts = base_name.split("_")
        
        # Check if filename contains "av1"
        if "av1" in distorted_file:
            # Remove last 3 parts if "av1" is present
            if len(parts) >= 4:  # Need at least 4 parts to remove last 3
                original_name = "_".join(parts[:-3])
            else:
                original_name = base_name
        else:
            # Remove last 4 parts otherwise
            if len(parts) >= 5:  # Need at least 5 parts to remove last 4
                original_name = "_".join(parts[:-4])
            else:
                original_name = base_name
        
        orphaned_groups[original_name].append(distorted_file)
        print(f"DEBUG: File '{distorted_file}' -> Group '{original_name}'")
    
    # Create groups for orphaned files
    for original_name, distorted_files in orphaned_groups.items():
        group = {
            'original': None,
            'original_path': None,
            'distorted_versions': [f"{PREFIX}{f}" for f in distorted_files]
        }
        grouped_data.append(group)
        print(f"Created orphaned group '{original_name}' with {len(distorted_files)} files")

# ─── SAVE GROUPED DATA TO CSV ───────────────────────────────────────────────────
grouped_csv_path = os.path.join(OUTPUT_DIR, "grouped_original_distorted.csv")
print(f"Saving grouped data to {grouped_csv_path}")

with open(grouped_csv_path, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # Header
    writer.writerow(['original_name', 'original_path', 'distorted_count', 'distorted_paths', 'has_original'])
    
    for group in grouped_data:
        distorted_paths_str = ';'.join(group['distorted_versions']) if group['distorted_versions'] else ''
        has_original = group['original'] is not None
        writer.writerow([
            group['original'] or 'NO_ORIGINAL',
            group['original_path'] or 'NO_ORIGINAL',
            len(group['distorted_versions']),
            distorted_paths_str,
            has_original
        ])

print(f"Saved grouped data with {len(grouped_data)} groups")

# ─── SHUFFLE GROUPS AND CREATE BATCHES ──────────────────────────────────────────
print("Creating batches...")

# Separate groups with exactly 30 videos and other groups
groups_30 = []
groups_other = []

for group in grouped_data:
    # Count total videos in this group
    if group['original'] is not None:
        group_size = 1 + len(group['distorted_versions'])  # original + distorted
    else:
        group_size = len(group['distorted_versions'])  # only distorted
    
    if group_size == 31:  # 1 original + 30 distorted
        groups_30.append(group)
    else:
        groups_other.append(group)

print(f"Found {len(groups_30)} groups with exactly 31 videos (1 original + 30 distorted)")
print(f"Found {len(groups_other)} groups with other sizes")

# Shuffle both lists
random.shuffle(groups_30)
random.shuffle(groups_other)

# Create batches prioritizing groups with 31 videos (1 original + 30 distorted)
batches = []
current_batch = []
current_batch_size = 0

# First, add groups with 31 videos (3 groups = 93 videos)
for group in groups_30:
    group_size = 31  # 1 original + 30 distorted
    
    # If adding this group would exceed batch size, start a new batch
    if current_batch_size + group_size > BATCH_SIZE and current_batch:
        batches.append(current_batch)
        current_batch = []
        current_batch_size = 0
    
    # Add the group to current batch
    current_batch.append(group)
    current_batch_size += group_size

# Then add remaining groups
for group in groups_other:
    # Count total videos in this group
    if group['original'] is not None:
        group_size = 1 + len(group['distorted_versions'])  # original + distorted
    else:
        group_size = len(group['distorted_versions'])  # only distorted
    
    # If adding this group would exceed batch size, start a new batch
    if current_batch_size + group_size > BATCH_SIZE and current_batch:
        batches.append(current_batch)
        current_batch = []
        current_batch_size = 0
    
    # Add the group to current batch
    current_batch.append(group)
    current_batch_size += group_size

# Add the last batch if it has content
if current_batch:
    batches.append(current_batch)

# ─── WRITE BATCH CSV FILES ──────────────────────────────────────────────────────
print(f"Writing {len(batches)} batch files...")

# Create a list to track batch statistics
batch_stats = []

for batch_idx, batch in enumerate(batches, 1):
    # Flatten all videos in this batch
    all_videos = []
    for group in batch:
        # Add original first (if exists)
        if group['original_path']:
            all_videos.append(group['original_path'])
        # Add distorted versions
        all_videos.extend(group['distorted_versions'])
    
    # Track batch statistics
    batch_stats.append({
        'batch_number': batch_idx,
        'content_groups': len(batch),
        'total_videos': len(all_videos),
        'original_videos': sum(1 for group in batch if group['original'] is not None),
        'distorted_videos': sum(len(group['distorted_versions']) for group in batch),
        'batch_data': batch,  # Store the actual batch data for later writing
        'all_videos': all_videos  # Store the flattened video list
    })

# Sort batches by total_videos in descending order
batch_stats.sort(key=lambda x: x['total_videos'], reverse=True)

# Write CSV files in descending order of batch size
for new_batch_idx, stats in enumerate(batch_stats, 1):
    # Create header
    header = [f"videos{i+1}" for i in range(len(stats['all_videos']))]
    
    # CSV filename (renumbered based on size)
    csv_filename = f"batch_{new_batch_idx}.csv"
    csv_path = os.path.join(OUTPUT_DIR, csv_filename)
    
    # Write CSV
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        writer.writerow(stats['all_videos'])
    
    # Update batch number to reflect new ordering
    stats['batch_number'] = new_batch_idx
    
    print(f"Wrote batch {new_batch_idx} (originally {stats['batch_number']}) with {stats['content_groups']} groups ({stats['total_videos']} total videos) to {csv_path}")

# ─── WRITE BATCH STATISTICS CSV ────────────────────────────────────────────────
batch_stats_csv_path = os.path.join(OUTPUT_DIR, "batch_statistics.csv")
print(f"Saving batch statistics to {batch_stats_csv_path}")

with open(batch_stats_csv_path, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # Header
    writer.writerow(['batch_number', 'content_groups', 'total_videos', 'original_videos', 'distorted_videos'])
    
    for stats in batch_stats:
        writer.writerow([
            stats['batch_number'],
            stats['content_groups'],
            stats['total_videos'],
            stats['original_videos'],
            stats['distorted_videos']
        ])

print(f"Saved batch statistics with {len(batch_stats)} batches")

# ─── VERIFICATION ───────────────────────────────────────────────────────────────
total_groups = len(grouped_data)
total_originals = sum(1 for group in grouped_data if group['original'] is not None)
total_distorted = sum(len(group['distorted_versions']) for group in grouped_data)
total_videos = total_originals + total_distorted

in_batch_groups = sum(len(batch) for batch in batches)
# Fix: correctly count videos in batches by summing all videos across all batches
in_batch_videos = 0
for batch in batches:
    for group in batch:
        if group['original'] is not None:
            in_batch_videos += 1 + len(group['distorted_versions'])  # 1 original + distorted versions
        else:
            in_batch_videos += len(group['distorted_versions'])  # only distorted versions

print(f"\nVerification:")
print(f"Total groups: {total_groups}")
print(f"Groups with originals: {total_originals}")
print(f"Groups without originals: {total_groups - total_originals}")
print(f"Total original videos: {total_originals}")
print(f"Total distorted videos: {total_distorted}")
print(f"Total videos: {total_videos}")
print(f"Groups in batches: {in_batch_groups}")
print(f"Videos in batches: {in_batch_videos}")
print(f"Groups not batched: {total_groups - in_batch_groups}")
print(f"Videos not batched: {total_videos - in_batch_videos}")

assert in_batch_groups == total_groups, (
    f"Group count mismatch: in_batch ({in_batch_groups}) != total ({total_groups})"
)
assert in_batch_videos == total_videos, (
    f"Video count mismatch: in_batch ({in_batch_videos}) != total ({total_videos})"
)

print("\nBatch creation completed successfully!")
