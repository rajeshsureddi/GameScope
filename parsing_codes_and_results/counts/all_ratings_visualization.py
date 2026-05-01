import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
import re
from collections import defaultdict, Counter

# ============================================================
# CONFIGURATION: Set your desired output directory here
# ============================================================
OUTPUT_DIRECTORY = "./parsing_codes_and_results/counts/global_ratings_output"  # Change this path as needed
# Set to None to save in current directory: OUTPUT_DIRECTORY = None
# ============================================================

def extract_final_rating_from_value(value):
    """
    Extract the final rating (second number) from a value like:
    '17/52/Moderately Clear,Minor Artifacts Present,Moderate level of immersion,/0.061700000002980815'
    Returns final_rating (the second number) or None if invalid
    """
    if pd.isna(value) or value == 'unset' or value == '' or str(value).strip() == '':
        return None
    
    # Convert to string for processing
    value_str = str(value).strip()
    
    # Check for other invalid values
    if value_str.lower() in ['unset', 'nan', 'none', 'null']:
        return None
    
    # Handle multiple ratings separated by ' | '
    if ' | ' in value_str:
        # Take the first rating if multiple exist
        value_str = value_str.split(' | ')[0]
    
    # Extract ratings pattern: number/number at the beginning
    match = re.match(r'^(\d+)/(\d+)/', value_str)
    if match:
        # Return only the final rating (the second number)
        final_rating = int(match.group(2))
        # Additional validation: check if rating is in reasonable range
        if 0 <= final_rating <= 100:  # Assuming ratings are 0-100
            return final_rating
    return None

def extract_all_components_from_value(value):
    """
    Extract all components from a value like:
    '17/52/Moderately Clear,Minor Artifacts Present,Moderate level of immersion,/0.061700000002980815'
    Returns a dictionary with final_rating, clarity, artifacts, immersion or None if invalid
    
    Expected categories:
    Clarity: Highly Clear, Moderately Clear, Minimally Clear
    Artifacts: No visible artifacts, Minor artifacts present, Severe Artifacts present
    Immersion: High level of immersion, Moderate level of immersion, Low level of immersion
    """
    if pd.isna(value) or value == 'unset' or value == '' or str(value).strip() == '':
        return None
    
    # Convert to string for processing
    value_str = str(value).strip()
    
    # Check for other invalid values
    if value_str.lower() in ['unset', 'nan', 'none', 'null']:
        return None
    
    # Handle multiple ratings separated by ' | '
    if ' | ' in value_str:
        # Take the first rating if multiple exist
        value_str = value_str.split(' | ')[0]
    
    # Extract the full pattern: number/number/text1,text2,text3,/number
    match = re.match(r'^(\d+)/(\d+)/(.+?),/[\d.]+', value_str)
    if match:
        first_rating = int(match.group(1))
        final_rating = int(match.group(2))
        descriptions = match.group(3)
        
        # Additional validation: check if rating is in reasonable range
        if 0 <= final_rating <= 100:  # Assuming ratings are 0-100
            # Split descriptions by commas
            desc_parts = descriptions.split(',')
            if len(desc_parts) >= 3:
                clarity = desc_parts[0].strip()
                artifacts = desc_parts[1].strip()
                immersion = desc_parts[2].strip()
                
                # Normalize common variations in attribute names
                clarity = normalize_clarity(clarity)
                artifacts = normalize_artifacts(artifacts)
                immersion = normalize_immersion(immersion)
                
                return {
                    'final_rating': final_rating,
                    'clarity': clarity,
                    'artifacts': artifacts,
                    'immersion': immersion
                }
    
    return None

def normalize_clarity(clarity_text):
    """Normalize clarity text to standard categories"""
    clarity_lower = clarity_text.lower().strip()
    
    if 'highly clear' in clarity_lower or 'very clear' in clarity_lower:
        return 'Highly Clear'
    elif 'moderately clear' in clarity_lower:
        return 'Moderately Clear'
    elif 'minimally clear' in clarity_lower or 'slightly clear' in clarity_lower or 'low clear' in clarity_lower:
        return 'Minimally Clear'
    else:
        # Return original if no match found
        return clarity_text

def normalize_artifacts(artifacts_text):
    """Normalize artifacts text to standard categories"""
    artifacts_lower = artifacts_text.lower().strip()
    
    if 'no visible artifacts' in artifacts_lower or 'no artifacts' in artifacts_lower:
        return 'No visible artifacts'
    elif 'minor artifacts' in artifacts_lower:
        return 'Minor artifacts Present'
    elif 'severe artifacts' in artifacts_lower or 'major artifacts' in artifacts_lower:
        return 'Severe Artifacts Present'
    else:
        # Return original if no match found
        return artifacts_text

def normalize_immersion(immersion_text):
    """Normalize immersion text to standard categories"""
    immersion_lower = immersion_text.lower().strip()
    
    if 'high level of immersion' in immersion_lower:
        return 'High level of immersion'
    elif 'moderate level of immersion' in immersion_lower:
        return 'Moderate level of immersion'
    elif 'low level of immersion' in immersion_lower:
        return 'Low level of immersion'
    else:
        # Return original if no match found
        return immersion_text

def process_all_approval_files():
    """Process all approval CSV files and collect final ratings per video name"""
    
    # Get current directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Dictionary to store all final ratings per video name
    video_ratings = defaultdict(list)
    
    # Counters for statistics
    total_valid_ratings = 0
    total_invalid_ratings = 0
    total_workers = 0
    approved_workers = 0
    total_files_processed = 0
    
    # Process batches A through L
    batch_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
    
    for batch_letter in batch_letters:
        # Look for the approval CSV files in the secondparse directories
        approve_reject_dir = os.path.join(current_dir, f'batch{batch_letter}_secondparse', 'approve_reject')
        
        if os.path.exists(approve_reject_dir):
            print(f"Processing batch{batch_letter}_secondparse/approve_reject...")
            
            # Find all CSV files in the approve_reject directory
            csv_files = glob.glob(os.path.join(approve_reject_dir, '*_with_approval.csv'))
            
            for csv_file in csv_files:
                print(f"  Processing file: {os.path.basename(csv_file)}")
                total_files_processed += 1
                
                try:
                    # Read the CSV file
                    df = pd.read_csv(csv_file)
                    total_workers += len(df)
                    
                    # Filter only rows where Approve='X'
                    df_filtered = df[df['Approve'] == 'X']
                    approved_workers += len(df_filtered)
                    
                    print(f"    Total workers: {len(df)}, Approved (X): {len(df_filtered)}")
                    
                    # Process each approved worker (row)
                    for idx, row in df_filtered.iterrows():
                        # Find all Input.videos columns and their corresponding Answer.videos columns
                        input_cols = [col for col in df_filtered.columns if col.startswith('Input.videos') and col != 'Input.videos']
                        
                        for input_col in input_cols:
                            # Extract the number from Input.videos[X]
                            video_num_match = re.search(r'Input\.videos(\d+)', input_col)
                            if video_num_match:
                                video_num = video_num_match.group(1)
                                answer_col = f'Answer.videos{video_num}'
                                
                                # Get the video name from Input.videos[X]
                                video_name = row[input_col]
                                
                                # Check if video name exists and is not NaN
                                if pd.notna(video_name) and video_name != '':
                                    # Get the corresponding rating from Answer.videos[X]
                                    if answer_col in df_filtered.columns:
                                        final_rating = extract_final_rating_from_value(row[answer_col])
                                        if final_rating is not None:
                                            video_ratings[video_name].append(final_rating)
                                            total_valid_ratings += 1
                                        else:
                                            total_invalid_ratings += 1
                
                except Exception as e:
                    print(f"    Error processing {csv_file}: {e}")
        else:
            print(f"Approve-reject directory not found: batch{batch_letter}_secondparse/approve_reject")
    
    return video_ratings, total_valid_ratings, total_invalid_ratings, total_workers, approved_workers, total_files_processed

def process_all_approval_files_with_attributes():
    """Process all approval CSV files and collect final ratings and attributes per video name"""
    
    # Get current directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Dictionary to store all final ratings per video name
    video_ratings = defaultdict(list)
    
    # Dictionaries to store all attributes
    video_clarity = defaultdict(list)
    video_artifacts = defaultdict(list)
    video_immersion = defaultdict(list)
    
    # Counters for statistics
    total_valid_ratings = 0
    total_invalid_ratings = 0
    total_workers = 0
    approved_workers = 0
    total_files_processed = 0
    
    # Process batches A through L
    batch_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
    
    for batch_letter in batch_letters:
        # Look for the approval CSV files in the secondparse directories
        approve_reject_dir = os.path.join(current_dir, f'batch{batch_letter}_secondparse', 'approve_reject')
        
        if os.path.exists(approve_reject_dir):
            print(f"Processing batch{batch_letter}_secondparse/approve_reject...")
            
            # Find all CSV files in the approve_reject directory
            csv_files = glob.glob(os.path.join(approve_reject_dir, '*_with_approval.csv'))
            
            for csv_file in csv_files:
                print(f"  Processing file: {os.path.basename(csv_file)}")
                total_files_processed += 1
                
                try:
                    # Read the CSV file
                    df = pd.read_csv(csv_file)
                    total_workers += len(df)
                    
                    # Filter only rows where Approve='X'
                    df_filtered = df[df['Approve'] == 'X']
                    approved_workers += len(df_filtered)
                    
                    print(f"    Total workers: {len(df)}, Approved (X): {len(df_filtered)}")
                    
                    # Process each approved worker (row)
                    for idx, row in df_filtered.iterrows():
                        # Find all Input.videos columns and their corresponding Answer.videos columns
                        input_cols = [col for col in df_filtered.columns if col.startswith('Input.videos') and col != 'Input.videos']
                        
                        for input_col in input_cols:
                            # Extract the number from Input.videos[X]
                            video_num_match = re.search(r'Input\.videos(\d+)', input_col)
                            if video_num_match:
                                video_num = video_num_match.group(1)
                                answer_col = f'Answer.videos{video_num}'
                                
                                # Get the video name from Input.videos[X]
                                video_name = row[input_col]
                                
                                # Check if video name exists and is not NaN
                                if pd.notna(video_name) and video_name != '':
                                    # Get the corresponding rating from Answer.videos[X]
                                    if answer_col in df_filtered.columns:
                                        components = extract_all_components_from_value(row[answer_col])
                                        if components is not None:
                                            video_ratings[video_name].append(components['final_rating'])
                                            video_clarity[video_name].append(components['clarity'])
                                            video_artifacts[video_name].append(components['artifacts'])
                                            video_immersion[video_name].append(components['immersion'])
                                            total_valid_ratings += 1
                                        else:
                                            total_invalid_ratings += 1
                
                except Exception as e:
                    print(f"    Error processing {csv_file}: {e}")
        else:
            print(f"Approve-reject directory not found: batch{batch_letter}_secondparse/approve_reject")
    
    return (video_ratings, video_clarity, video_artifacts, video_immersion, 
            total_valid_ratings, total_invalid_ratings, total_workers, approved_workers, total_files_processed)

def count_attribute_frequencies(video_attributes):
    """Count frequencies of all attribute values across all videos"""
    all_values = []
    for video_name, attributes in video_attributes.items():
        all_values.extend(attributes)
    
    return Counter(all_values)

def create_attributes_histogram(video_clarity, video_artifacts, video_immersion, output_dir=None, output_file='attributes_distribution_histogram.png'):
    """Create a 1x3 subplot showing histograms for clarity, artifacts, and immersion"""
    
    # Define the expected categories in order
    clarity_categories = ['Highly Clear', 'Moderately Clear', 'Minimally Clear']
    artifacts_categories = ['No visible artifacts', 'Minor artifacts Present', 'Severe Artifacts Present']
    immersion_categories = ['High level of immersion', 'Moderate level of immersion', 'Low level of immersion']
    
    # Count frequencies for each attribute
    clarity_counts = count_attribute_frequencies(video_clarity)
    artifacts_counts = count_attribute_frequencies(video_artifacts)
    immersion_counts = count_attribute_frequencies(video_immersion)
    
    # Create the 1x3 subplot
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
    
    # Plot 1: Clarity
    clarity_values = [clarity_counts.get(cat, 0) for cat in clarity_categories]
    bars1 = ax1.bar(range(len(clarity_categories)), clarity_values, color='lightblue', alpha=0.7, edgecolor='black')
    ax1.set_title('Clarity Ratings Distribution', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Clarity Categories', fontsize=10)
    ax1.set_ylabel('Frequency', fontsize=10)
    ax1.set_xticks(range(len(clarity_categories)))
    ax1.set_xticklabels(clarity_categories, rotation=45, ha='right', fontsize=9)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, v in enumerate(clarity_values):
        if v > 0:  # Only show label if count > 0
            ax1.text(i, v + max(clarity_values) * 0.01, str(v), ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Plot 2: Artifacts
    artifacts_values = [artifacts_counts.get(cat, 0) for cat in artifacts_categories]
    bars2 = ax2.bar(range(len(artifacts_categories)), artifacts_values, color='lightcoral', alpha=0.7, edgecolor='black')
    ax2.set_title('Artifacts Ratings Distribution', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Artifacts Categories', fontsize=10)
    ax2.set_ylabel('Frequency', fontsize=10)
    ax2.set_xticks(range(len(artifacts_categories)))
    ax2.set_xticklabels(artifacts_categories, rotation=45, ha='right', fontsize=9)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, v in enumerate(artifacts_values):
        if v > 0:  # Only show label if count > 0
            ax2.text(i, v + max(artifacts_values) * 0.01, str(v), ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Plot 3: Immersion
    immersion_values = [immersion_counts.get(cat, 0) for cat in immersion_categories]
    bars3 = ax3.bar(range(len(immersion_categories)), immersion_values, color='lightgreen', alpha=0.7, edgecolor='black')
    ax3.set_title('Immersion Ratings Distribution', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Immersion Categories', fontsize=10)
    ax3.set_ylabel('Frequency', fontsize=10)
    ax3.set_xticks(range(len(immersion_categories)))
    ax3.set_xticklabels(immersion_categories, rotation=45, ha='right', fontsize=9)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, v in enumerate(immersion_values):
        if v > 0:  # Only show label if count > 0
            ax3.text(i, v + max(immersion_values) * 0.01, str(v), ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Add overall title
    fig.suptitle('Distribution of Video Quality Attributes (Approve=X Only)', fontsize=16, fontweight='bold')
    
    # Adjust layout to prevent overlap
    plt.tight_layout()
    
    # Determine output path
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_file)
    else:
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Attributes histogram saved to: {output_path}")
    
    # Display the plot
    plt.show()
    
    # Print summary statistics
    total_clarity = sum(clarity_values)
    total_artifacts = sum(artifacts_values)
    total_immersion = sum(immersion_values)
    
    print(f"\nAttribute Distribution Summary:")
    print(f"Clarity Ratings (Total: {total_clarity}):")
    for cat, count in zip(clarity_categories, clarity_values):
        percentage = (count / total_clarity * 100) if total_clarity > 0 else 0
        print(f"  - {cat}: {count} ({percentage:.1f}%)")
    
    print(f"\nArtifacts Ratings (Total: {total_artifacts}):")
    for cat, count in zip(artifacts_categories, artifacts_values):
        percentage = (count / total_artifacts * 100) if total_artifacts > 0 else 0
        print(f"  - {cat}: {count} ({percentage:.1f}%)")
    
    print(f"\nImmersion Ratings (Total: {total_immersion}):")
    for cat, count in zip(immersion_categories, immersion_values):
        percentage = (count / total_immersion * 100) if total_immersion > 0 else 0
        print(f"  - {cat}: {count} ({percentage:.1f}%)")
    
    # Check for any unrecognized categories
    print(f"\nUnrecognized categories found:")
    unrecognized_clarity = [cat for cat in clarity_counts.keys() if cat not in clarity_categories]
    unrecognized_artifacts = [cat for cat in artifacts_counts.keys() if cat not in artifacts_categories]
    unrecognized_immersion = [cat for cat in immersion_counts.keys() if cat not in immersion_categories]
    
    if unrecognized_clarity:
        print(f"  Clarity: {unrecognized_clarity}")
    if unrecognized_artifacts:
        print(f"  Artifacts: {unrecognized_artifacts}")
    if unrecognized_immersion:
        print(f"  Immersion: {unrecognized_immersion}")
    if not (unrecognized_clarity or unrecognized_artifacts or unrecognized_immersion):
        print(f"  None - all categories properly recognized!")
    
    return clarity_counts, artifacts_counts, immersion_counts

def save_attributes_to_csv(video_clarity, video_artifacts, video_immersion, output_dir=None, output_file='video_attributes_data.csv'):
    """Save all attributes data to CSV file"""
    
    # Find all unique video names
    all_video_names = set()
    all_video_names.update(video_clarity.keys())
    all_video_names.update(video_artifacts.keys())
    all_video_names.update(video_immersion.keys())
    
    # Find maximum number of ratings any video has
    max_ratings = 0
    for video_name in all_video_names:
        max_ratings = max(max_ratings, 
                         len(video_clarity.get(video_name, [])),
                         len(video_artifacts.get(video_name, [])),
                         len(video_immersion.get(video_name, [])))
    
    # Prepare data for CSV
    csv_data = []
    for video_name in sorted(all_video_names):
        clarity_list = video_clarity.get(video_name, [])
        artifacts_list = video_artifacts.get(video_name, [])
        immersion_list = video_immersion.get(video_name, [])
        
        row_data = {'video_name': video_name}
        
        # Add clarity attributes
        for i, clarity in enumerate(clarity_list, 1):
            row_data[f'clarity_{i}'] = clarity
        for i in range(len(clarity_list) + 1, max_ratings + 1):
            row_data[f'clarity_{i}'] = None
            
        # Add artifacts attributes
        for i, artifacts in enumerate(artifacts_list, 1):
            row_data[f'artifacts_{i}'] = artifacts
        for i in range(len(artifacts_list) + 1, max_ratings + 1):
            row_data[f'artifacts_{i}'] = None
            
        # Add immersion attributes
        for i, immersion in enumerate(immersion_list, 1):
            row_data[f'immersion_{i}'] = immersion
        for i in range(len(immersion_list) + 1, max_ratings + 1):
            row_data[f'immersion_{i}'] = None
        
        csv_data.append(row_data)
    
    # Create DataFrame and save
    df_attributes = pd.DataFrame(csv_data)
    
    # Determine output path
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_file)
    else:
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
    
    df_attributes.to_csv(output_path, index=False)
    print(f"Attributes data saved to: {output_path}")
    print(f"Format: One row per video, up to {max_ratings} attribute columns per type")
    
    return df_attributes

def calculate_video_averages(video_ratings):
    """Calculate average final rating for each video"""
    video_averages = {}
    
    for video_name, ratings in video_ratings.items():
        if ratings:  # If there are ratings for this video
            avg_rating = np.mean(ratings)
            video_averages[video_name] = {
                'average_rating': avg_rating,
                'num_ratings': len(ratings),
                'ratings': ratings,
                'std_rating': np.std(ratings) if len(ratings) > 1 else 0,
                'min_rating': min(ratings),
                'max_rating': max(ratings)
            }
    
    return video_averages

def save_individual_ratings_to_csv(video_ratings, output_dir=None, output_file='individual_final_ratings_per_video.csv'):
    """Save all individual final ratings per video name to a CSV file with one row per video"""
    
    # Find the maximum number of ratings any video has
    max_ratings = max(len(ratings) for ratings in video_ratings.values()) if video_ratings else 0
    
    # Prepare data for CSV - one row per video
    csv_data = []
    for video_name, ratings in video_ratings.items():
        row_data = {'video_name': video_name}
        
        # Add all individual ratings as separate columns
        for i, rating in enumerate(ratings, 1):
            row_data[f'final_rating_{i}'] = rating
        
        # Fill remaining columns with NaN for videos with fewer ratings
        for i in range(len(ratings) + 1, max_ratings + 1):
            row_data[f'final_rating_{i}'] = None
        
        csv_data.append(row_data)
    
    # Create DataFrame and save
    df_individual = pd.DataFrame(csv_data)
    df_individual = df_individual.sort_values('video_name')
    
    # Determine output path
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_file)
    else:
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
    
    df_individual.to_csv(output_path, index=False)
    print(f"Individual final ratings saved to: {output_path}")
    print(f"Format: One row per video, up to {max_ratings} final_rating columns")
    
    return df_individual

def save_results_to_csv(video_averages, output_dir=None, output_file='video_average_final_ratings_approved_X.csv'):
    """Save the results to a CSV file"""
    
    # Prepare data for CSV
    csv_data = []
    for video_name, data in video_averages.items():
        csv_data.append({
            'video_name': video_name,
            'average_final_rating': data['average_rating'],
            'num_ratings': data['num_ratings'],
            'std_rating': data['std_rating'],
            'min_rating': data['min_rating'],
            'max_rating': data['max_rating']
        })
    
    # Create DataFrame and save
    df_results = pd.DataFrame(csv_data)
    df_results = df_results.sort_values('average_final_rating', ascending=False)
    
    # Determine output path
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_file)
    else:
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
    
    df_results.to_csv(output_path, index=False)
    print(f"Results saved to: {output_path}")
    
    return df_results

def create_histogram(video_averages, total_ratings, output_dir=None, output_file='final_ratings_histogram_approved_X.png'):
    """Create and save histogram of average final ratings per video"""
    
    # Extract average ratings
    avg_ratings = [data['average_rating'] for data in video_averages.values()]
    
    # Calculate average number of ratings per video
    avg_ratings_per_video = total_ratings / len(video_averages) if len(video_averages) > 0 else 0
    
    # Create histogram
    plt.figure(figsize=(12, 8))
    
    # Create histogram with better styling
    plt.hist(avg_ratings, bins=30, alpha=0.7, color='lightcoral', edgecolor='black')
    plt.title('Distribution of Average Final Ratings per Video (Approve=X Only)', fontsize=16, fontweight='bold')
    plt.xlabel('Average Final Rating per Video', fontsize=12)
    plt.ylabel('Number of Videos', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Add statistics to the plot
    mean_rating = np.mean(avg_ratings)
    median_rating = np.median(avg_ratings)
    std_rating = np.std(avg_ratings)
    
    plt.axvline(mean_rating, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_rating:.2f}')
    plt.axvline(median_rating, color='green', linestyle='--', linewidth=2, label=f'Median: {median_rating:.2f}')
    
    plt.legend()
    
    # Add text box with statistics including average ratings per video
    stats_text = f'Statistics:\nMean: {mean_rating:.2f}\nMedian: {median_rating:.2f}\nStd: {std_rating:.2f}\nTotal Videos: {len(avg_ratings)}\nAvg Ratings/Video: {avg_ratings_per_video:.2f}'
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    
    # Determine output path
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_file)
    else:
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Histogram saved to: {output_path}")
    
    # Show the plot
    plt.show()
    
    return mean_rating, median_rating, std_rating

def create_boxplot_visualization(video_ratings, output_dir=None, output_file='individual_ratings_boxplot.png'):
    """Create and save box plots showing distribution of individual ratings per video"""
    
    # Prepare data for box plots
    video_names = []
    all_ratings_data = []
    
    # Sort videos by average rating for better visualization
    video_avg_ratings = []
    for video_name, ratings in video_ratings.items():
        if ratings:  # Only include videos with ratings
            avg_rating = np.mean(ratings)
            video_avg_ratings.append((video_name, avg_rating, ratings))
    
    # Sort by average rating (descending)
    video_avg_ratings.sort(key=lambda x: x[1], reverse=True)
    
    total_videos = len(video_avg_ratings)
    print(f"Total videos to visualize: {total_videos}")
    
    # If too many videos, create multiple plots or sample
    max_videos_per_plot = 200  # Limit to prevent image size issues
    
    if total_videos > max_videos_per_plot:
        print(f"Too many videos ({total_videos}). Creating visualization with top {max_videos_per_plot} videos by rating variance.")
        
        # Calculate variance for each video and select most variable ones
        video_variances = []
        for video_name, avg_rating, ratings in video_avg_ratings:
            if len(ratings) > 1:  # Need at least 2 ratings to calculate variance
                variance = np.var(ratings)
                video_variances.append((video_name, avg_rating, ratings, variance))
        
        # Sort by variance (descending) to show most variable videos
        video_variances.sort(key=lambda x: x[3], reverse=True)
        
        # Take top videos by variance
        selected_videos = video_variances[:max_videos_per_plot]
        print(f"Selected {len(selected_videos)} videos with highest rating variance")
        
        # Extract data for selected videos
        for video_name, avg_rating, ratings, variance in selected_videos:
            video_names.append(f"{video_name}\n(var:{variance:.1f})")
            all_ratings_data.append(ratings)
            
    else:
        # Use all videos if manageable number
        for video_name, avg_rating, ratings in video_avg_ratings:
            video_names.append(video_name)
            all_ratings_data.append(ratings)
    
    if not all_ratings_data:
        print("No data available for box plot visualization")
        return 0, 0
    
    # Calculate reasonable figure size
    num_videos = len(video_names)
    fig_width = min(50, max(15, num_videos * 0.2))  # Cap at 50 inches, minimum 15 inches
    fig_height = 10
    
    print(f"Creating box plot with {num_videos} videos, figure size: {fig_width}x{fig_height} inches")
    
    plt.figure(figsize=(fig_width, fig_height))
    
    # Create box plots
    box_plot = plt.boxplot(all_ratings_data, labels=video_names, patch_artist=True)
    
    # Customize box plot colors
    colors = plt.cm.viridis(np.linspace(0, 1, len(box_plot['boxes'])))
    for patch, color in zip(box_plot['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # Customize the plot
    title = 'Distribution of Individual Final Ratings per Video (Approve=X Only)'
    if total_videos > max_videos_per_plot:
        title += f'\nShowing Top {num_videos} Videos by Rating Variance'
    
    plt.title(title, fontsize=14, fontweight='bold', pad=20)
    plt.xlabel('Video Names', fontsize=12)
    plt.ylabel('Final Rating', fontsize=12)
    plt.grid(True, alpha=0.3, axis='y')
    
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90, ha='right', fontsize=8)
    
    # Add statistics text box
    total_ratings_shown = sum(len(ratings) for ratings in all_ratings_data)
    avg_ratings_per_video = total_ratings_shown / num_videos if num_videos > 0 else 0
    
    stats_text = f'Statistics:\nVideos Shown: {num_videos}/{total_videos}\nTotal Ratings: {total_ratings_shown}\nAvg Ratings/Video: {avg_ratings_per_video:.2f}'
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # Adjust layout to prevent label cutoff
    try:
        plt.tight_layout()
    except ValueError as e:
        print(f"Warning: tight_layout failed: {e}")
        print("Continuing with default layout...")
    
    # Determine output path
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_file)
    else:
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
    
    plt.savefig(output_path, dpi=200, bbox_inches='tight')  # Reduced DPI to 200 for large plots
    print(f"Box plot visualization saved to: {output_path}")
    print(f"Plot shows distribution of individual ratings for {num_videos} videos")
    
    # Close the plot instead of showing it to save memory
    plt.close()
    
    return num_videos, total_ratings_shown

def create_batch_wise_boxplots(video_ratings, output_dir=None):
    """Create separate box plots for each batch (A through L)"""
    
    # Get current directory path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Dictionary to store video ratings per batch
    batch_video_ratings = {}
    
    # Process batches A through L
    batch_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
    
    for batch_letter in batch_letters:
        batch_video_ratings[batch_letter] = defaultdict(list)
        
        # Look for the approval CSV files in the secondparse directories
        approve_reject_dir = os.path.join(current_dir, f'batch{batch_letter}_secondparse', 'approve_reject')
        
        if os.path.exists(approve_reject_dir):
            print(f"Processing batch{batch_letter} for box plots...")
            
            # Find all CSV files in the approve_reject directory
            csv_files = glob.glob(os.path.join(approve_reject_dir, '*_with_approval.csv'))
            
            for csv_file in csv_files:
                try:
                    # Read the CSV file
                    df = pd.read_csv(csv_file)
                    
                    # Filter only rows where Approve='X'
                    df_filtered = df[df['Approve'] == 'X']
                    
                    # Process each approved worker (row)
                    for idx, row in df_filtered.iterrows():
                        # Find all Input.videos columns and their corresponding Answer.videos columns
                        input_cols = [col for col in df_filtered.columns if col.startswith('Input.videos') and col != 'Input.videos']
                        
                        for input_col in input_cols:
                            # Extract the number from Input.videos[X]
                            video_num_match = re.search(r'Input\.videos(\d+)', input_col)
                            if video_num_match:
                                video_num = video_num_match.group(1)
                                answer_col = f'Answer.videos{video_num}'
                                
                                # Get the video name from Input.videos[X]
                                video_name = row[input_col]
                                
                                # Check if video name exists and is not NaN
                                if pd.notna(video_name) and video_name != '':
                                    # Get the corresponding rating from Answer.videos[X]
                                    if answer_col in df_filtered.columns:
                                        final_rating = extract_final_rating_from_value(row[answer_col])
                                        if final_rating is not None:
                                            batch_video_ratings[batch_letter][video_name].append(final_rating)
                
                except Exception as e:
                    print(f"    Error processing {csv_file}: {e}")
    
    # Create box plots for each batch
    total_plots_created = 0
    
    for batch_letter in batch_letters:
        batch_ratings = batch_video_ratings[batch_letter]
        
        if not batch_ratings:
            print(f"No data found for batch {batch_letter}, skipping...")
            continue
        
        # Prepare data for box plots
        video_names = []
        all_ratings_data = []
        
        # Sort videos by average rating for better visualization
        video_avg_ratings = []
        for video_name, ratings in batch_ratings.items():
            if ratings:  # Only include videos with ratings
                avg_rating = np.mean(ratings)
                video_avg_ratings.append((video_name, avg_rating, ratings))
        
        # Sort by average rating (descending)
        video_avg_ratings.sort(key=lambda x: x[1], reverse=True)
        
        # Extract data for all videos in this batch
        for video_name, avg_rating, ratings in video_avg_ratings:
            # Truncate long video names for better display
            display_name = video_name.split('/')[-1] if '/' in video_name else video_name
            if len(display_name) > 30:
                display_name = display_name[:27] + "..."
            video_names.append(display_name)
            all_ratings_data.append(ratings)
        
        if not all_ratings_data:
            print(f"No rating data for batch {batch_letter}, skipping...")
            continue
        
        # Calculate figure size based on number of videos
        num_videos = len(video_names)
        fig_width = min(50, max(15, num_videos * 0.3))  # More space per video for readability
        fig_height = 10
        
        print(f"Creating box plot for batch {batch_letter} with {num_videos} videos, figure size: {fig_width}x{fig_height} inches")
        
        plt.figure(figsize=(fig_width, fig_height))
        
        # Create box plots
        box_plot = plt.boxplot(all_ratings_data, labels=video_names, patch_artist=True)
        
        # Customize box plot colors - use different color schemes for different batches
        colormap = plt.cm.Set3 if batch_letter in ['A', 'B', 'C', 'D'] else \
                  plt.cm.viridis if batch_letter in ['E', 'F', 'G', 'H'] else \
                  plt.cm.plasma
        colors = colormap(np.linspace(0, 1, len(box_plot['boxes'])))
        
        for patch, color in zip(box_plot['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        # Customize the plot
        plt.title(f'Batch {batch_letter}: Distribution of Individual Final Ratings per Video (Approve=X Only)', 
                  fontsize=14, fontweight='bold', pad=20)
        plt.xlabel('Video Names', fontsize=12)
        plt.ylabel('Final Rating', fontsize=12)
        plt.grid(True, alpha=0.3, axis='y')
        
        # Rotate x-axis labels for better readability
        plt.xticks(rotation=90, ha='right', fontsize=8)
        
        # Add statistics text box
        total_ratings_in_batch = sum(len(ratings) for ratings in all_ratings_data)
        avg_ratings_per_video = total_ratings_in_batch / num_videos if num_videos > 0 else 0
        
        stats_text = f'Batch {batch_letter} Statistics:\nVideos: {num_videos}\nTotal Ratings: {total_ratings_in_batch}\nAvg Ratings/Video: {avg_ratings_per_video:.2f}'
        plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
                 verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        # Adjust layout to prevent label cutoff
        try:
            plt.tight_layout()
        except ValueError as e:
            print(f"Warning: tight_layout failed for batch {batch_letter}: {e}")
            print("Continuing with default layout...")
        
        # Determine output path
        output_file = f'batch_{batch_letter}_individual_ratings_boxplot.png'
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, output_file)
        else:
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
        
        plt.savefig(output_path, dpi=200, bbox_inches='tight')
        print(f"Batch {batch_letter} box plot saved to: {output_path}")
        
        # Close the plot to save memory
        plt.close()
        
        total_plots_created += 1
    
    print(f"\nCreated {total_plots_created} batch-wise box plots")
    return total_plots_created

def get_attribute_score(attribute_type, attribute_value):
    """
    Get numerical score for an attribute value (higher score = better quality)
    
    Args:
        attribute_type: 'clarity', 'artifacts', or 'immersion'
        attribute_value: the actual attribute string value
    
    Returns:
        int: Score from 1-3 (3 = best quality, 1 = worst quality)
    """
    if attribute_type == 'clarity':
        if attribute_value == 'Highly Clear':
            return 3
        elif attribute_value == 'Moderately Clear':
            return 2
        elif attribute_value == 'Minimally Clear':
            return 1
    elif attribute_type == 'artifacts':
        if attribute_value == 'No visible artifacts':
            return 3
        elif attribute_value == 'Minor artifacts Present':
            return 2
        elif attribute_value == 'Severe Artifacts Present':
            return 1
    elif attribute_type == 'immersion':
        if attribute_value == 'High level of immersion':
            return 3
        elif attribute_value == 'Moderate level of immersion':
            return 2
        elif attribute_value == 'Low level of immersion':
            return 1
    
    # Return 0 for unrecognized values
    return 0

def determine_major_attributes(video_clarity, video_artifacts, video_immersion):
    """
    Determine the major (best performing) attribute for each individual rating
    
    Returns:
        list: List of major attributes for each rating
    """
    major_attributes = []
    
    # Get all video names that have any attributes
    all_video_names = set()
    all_video_names.update(video_clarity.keys())
    all_video_names.update(video_artifacts.keys())
    all_video_names.update(video_immersion.keys())
    
    for video_name in all_video_names:
        clarity_list = video_clarity.get(video_name, [])
        artifacts_list = video_artifacts.get(video_name, [])
        immersion_list = video_immersion.get(video_name, [])
        
        # Find the maximum number of ratings for this video
        max_ratings = max(len(clarity_list), len(artifacts_list), len(immersion_list))
        
        # Process each rating index
        for i in range(max_ratings):
            # Get attribute values for this rating (if available)
            clarity_val = clarity_list[i] if i < len(clarity_list) else None
            artifacts_val = artifacts_list[i] if i < len(artifacts_list) else None
            immersion_val = immersion_list[i] if i < len(immersion_list) else None
            
            # Calculate scores for each attribute
            clarity_score = get_attribute_score('clarity', clarity_val) if clarity_val else 0
            artifacts_score = get_attribute_score('artifacts', artifacts_val) if artifacts_val else 0
            immersion_score = get_attribute_score('immersion', immersion_val) if immersion_val else 0
            
            # Determine which attribute has the highest score (best performance)
            scores = {
                'Clarity': clarity_score,
                'Artifacts': artifacts_score,
                'Immersion': immersion_score
            }
            
            # Find the attribute with maximum score
            max_score = max(scores.values())
            if max_score > 0:  # Only count if at least one attribute has a valid score
                # Get all attributes with the maximum score
                best_attributes = [attr for attr, score in scores.items() if score == max_score]
                
                # If there's a tie, we can choose the first one or handle it differently
                # For now, let's choose the first one alphabetically for consistency
                major_attribute = sorted(best_attributes)[0]
                major_attributes.append(major_attribute)
    
    return major_attributes

def create_major_attributes_histogram(video_clarity, video_artifacts, video_immersion, output_dir=None, output_file='major_attributes_distribution_histogram.png'):
    """Create a histogram showing the distribution of major (best performing) attributes"""
    
    # Determine major attributes for all ratings
    major_attributes = determine_major_attributes(video_clarity, video_artifacts, video_immersion)
    
    if not major_attributes:
        print("No major attributes found to plot.")
        return None
    
    # Count frequencies of major attributes
    major_attr_counts = Counter(major_attributes)
    
    # Define the attribute categories and colors
    attribute_categories = ['Artifacts', 'Clarity', 'Immersion']  # Sorted alphabetically
    colors = ['lightcoral', 'lightblue', 'lightgreen']
    
    # Get counts for each category
    attr_values = [major_attr_counts.get(cat, 0) for cat in attribute_categories]
    
    # Create the histogram
    plt.figure(figsize=(12, 8))
    
    bars = plt.bar(range(len(attribute_categories)), attr_values, 
                   color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)
    
    plt.title('Distribution of Major (Best Performing) Attributes\n(Approve=X Only)', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Major Attribute Categories', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.xticks(range(len(attribute_categories)), attribute_categories, fontsize=11)
    plt.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, v in enumerate(attr_values):
        if v > 0:  # Only show label if count > 0
            plt.text(i, v + max(attr_values) * 0.01, str(v), 
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # Add percentage labels
    total_ratings = sum(attr_values)
    for i, v in enumerate(attr_values):
        if v > 0 and total_ratings > 0:
            percentage = (v / total_ratings) * 100
            plt.text(i, v/2, f'{percentage:.1f}%', 
                    ha='center', va='center', fontsize=10, fontweight='bold', color='white')
    
    # Determine output path
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_file)
    else:
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Major attributes histogram saved to: {output_path}")
    
    # Display the plot
    plt.show()
    
    # Print summary statistics
    print(f"\nMajor Attribute Distribution Summary:")
    print(f"Total individual ratings analyzed: {total_ratings}")
    
    for cat, count in zip(attribute_categories, attr_values):
        percentage = (count / total_ratings * 100) if total_ratings > 0 else 0
        print(f"  - {cat} (best performing): {count} ({percentage:.1f}%)")
    
    # Additional analysis
    print(f"\nInterpretation:")
    print(f"  - Each rating was analyzed to determine which of the three attributes")
    print(f"    (Clarity, Artifacts, Immersion) performed best (highest quality score)")
    print(f"  - Scores: Highly/High/No = 3, Moderately/Moderate/Minor = 2, Minimally/Low/Severe = 1")
    print(f"  - The histogram shows which attribute most often achieved the best performance")
    
    return major_attr_counts

def create_most_common_attributes_histogram(video_clarity, video_artifacts, video_immersion, output_dir=None, output_file='most_common_attributes_per_video_histogram.png'):
    """Create a histogram showing the distribution of most common attributes per video"""
    
    # Get all video names that have any attributes
    all_video_names = set()
    all_video_names.update(video_clarity.keys())
    all_video_names.update(video_artifacts.keys())
    all_video_names.update(video_immersion.keys())
    
    if not all_video_names:
        print("No video attributes found to analyze.")
        return None
    
    print(f"Debug: Total unique videos found: {len(all_video_names)}")
    
    # Determine most common attribute for each video
    video_most_common_clarity = []
    video_most_common_artifacts = []
    video_most_common_immersion = []
    
    # Track videos with missing data
    videos_missing_clarity = []
    videos_missing_artifacts = []
    videos_missing_immersion = []
    
    for video_name in all_video_names:
        # Get most common clarity for this video
        clarity_list = video_clarity.get(video_name, [])
        if clarity_list:
            clarity_counter = Counter(clarity_list)
            most_common_clarity = clarity_counter.most_common(1)[0][0]
            video_most_common_clarity.append(most_common_clarity)
        else:
            videos_missing_clarity.append(video_name)
        
        # Get most common artifacts for this video
        artifacts_list = video_artifacts.get(video_name, [])
        if artifacts_list:
            artifacts_counter = Counter(artifacts_list)
            most_common_artifacts = artifacts_counter.most_common(1)[0][0]
            video_most_common_artifacts.append(most_common_artifacts)
        else:
            videos_missing_artifacts.append(video_name)
        
        # Get most common immersion for this video
        immersion_list = video_immersion.get(video_name, [])
        if immersion_list:
            immersion_counter = Counter(immersion_list)
            most_common_immersion = immersion_counter.most_common(1)[0][0]
            video_most_common_immersion.append(most_common_immersion)
        else:
            videos_missing_immersion.append(video_name)
    
    # Debug information
    print(f"Debug: Videos with clarity data: {len(video_most_common_clarity)}")
    print(f"Debug: Videos with artifacts data: {len(video_most_common_artifacts)}")
    print(f"Debug: Videos with immersion data: {len(video_most_common_immersion)}")
    print(f"Debug: Videos missing clarity data: {len(videos_missing_clarity)}")
    print(f"Debug: Videos missing artifacts data: {len(videos_missing_artifacts)}")
    print(f"Debug: Videos missing immersion data: {len(videos_missing_immersion)}")
    
    # Show examples of missing videos if any
    if videos_missing_clarity:
        print(f"Debug: First few videos missing clarity: {videos_missing_clarity[:3]}")
    if videos_missing_artifacts:
        print(f"Debug: First few videos missing artifacts: {videos_missing_artifacts[:3]}")
    if videos_missing_immersion:
        print(f"Debug: First few videos missing immersion: {videos_missing_immersion[:3]}")
    
    # Count frequencies of most common attributes across all videos
    clarity_counts = Counter(video_most_common_clarity)
    artifacts_counts = Counter(video_most_common_artifacts)
    immersion_counts = Counter(video_most_common_immersion)
    
    # Define the expected categories in order
    clarity_categories = ['Highly Clear', 'Moderately Clear', 'Minimally Clear']
    artifacts_categories = ['No visible artifacts', 'Minor artifacts Present', 'Severe Artifacts Present']
    immersion_categories = ['High level of immersion', 'Moderate level of immersion', 'Low level of immersion']
    
    # Create the 1x3 subplot
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
    
    # Plot 1: Most Common Clarity per Video
    clarity_values = [clarity_counts.get(cat, 0) for cat in clarity_categories]
    bars1 = ax1.bar(range(len(clarity_categories)), clarity_values, color='lightblue', alpha=0.7, edgecolor='black')
    ax1.set_title('Most Common Clarity Ratings\nper Video Distribution', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Clarity Categories', fontsize=10)
    ax1.set_ylabel('Number of Videos', fontsize=10)
    ax1.set_xticks(range(len(clarity_categories)))
    ax1.set_xticklabels(clarity_categories, rotation=45, ha='right', fontsize=9)
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, v in enumerate(clarity_values):
        if v > 0:  # Only show label if count > 0
            ax1.text(i, v + max(clarity_values) * 0.01, str(v), ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Plot 2: Most Common Artifacts per Video
    artifacts_values = [artifacts_counts.get(cat, 0) for cat in artifacts_categories]
    bars2 = ax2.bar(range(len(artifacts_categories)), artifacts_values, color='lightcoral', alpha=0.7, edgecolor='black')
    ax2.set_title('Most Common Artifacts Ratings\nper Video Distribution', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Artifacts Categories', fontsize=10)
    ax2.set_ylabel('Number of Videos', fontsize=10)
    ax2.set_xticks(range(len(artifacts_categories)))
    ax2.set_xticklabels(artifacts_categories, rotation=45, ha='right', fontsize=9)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, v in enumerate(artifacts_values):
        if v > 0:  # Only show label if count > 0
            ax2.text(i, v + max(artifacts_values) * 0.01, str(v), ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Plot 3: Most Common Immersion per Video
    immersion_values = [immersion_counts.get(cat, 0) for cat in immersion_categories]
    bars3 = ax3.bar(range(len(immersion_categories)), immersion_values, color='lightgreen', alpha=0.7, edgecolor='black')
    ax3.set_title('Most Common Immersion Ratings\nper Video Distribution', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Immersion Categories', fontsize=10)
    ax3.set_ylabel('Number of Videos', fontsize=10)
    ax3.set_xticks(range(len(immersion_categories)))
    ax3.set_xticklabels(immersion_categories, rotation=45, ha='right', fontsize=9)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, v in enumerate(immersion_values):
        if v > 0:  # Only show label if count > 0
            ax3.text(i, v + max(immersion_values) * 0.01, str(v), ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Add overall title
    fig.suptitle('Distribution of Most Common Attributes per Video (Approve=X Only)', fontsize=16, fontweight='bold')
    
    # Adjust layout to prevent overlap
    plt.tight_layout()
    
    # Determine output path
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_file)
    else:
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_file)
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Most common attributes per video histogram saved to: {output_path}")
    
    # Display the plot
    plt.show()
    
    # Print summary statistics
    total_videos_clarity = sum(clarity_values)
    total_videos_artifacts = sum(artifacts_values)
    total_videos_immersion = sum(immersion_values)
    total_videos_analyzed = len(all_video_names)
    
    print(f"\nMost Common Attributes per Video Distribution Summary:")
    print(f"Total videos analyzed: {total_videos_analyzed}")
    print(f"Videos with clarity data: {total_videos_clarity}")
    print(f"Videos with artifacts data: {total_videos_artifacts}")
    print(f"Videos with immersion data: {total_videos_immersion}")
    print(f"Expected total: 4048")
    
    # Alert if counts don't match expected
    if total_videos_clarity != 4048:
        print(f"⚠️  WARNING: Clarity count ({total_videos_clarity}) doesn't match expected (4048). Missing: {4048 - total_videos_clarity}")
    if total_videos_artifacts != 4048:
        print(f"⚠️  WARNING: Artifacts count ({total_videos_artifacts}) doesn't match expected (4048). Missing: {4048 - total_videos_artifacts}")
    if total_videos_immersion != 4048:
        print(f"⚠️  WARNING: Immersion count ({total_videos_immersion}) doesn't match expected (4048). Missing: {4048 - total_videos_immersion}")
    
    print(f"\nMost Common Clarity per Video (Total: {total_videos_clarity}):")
    for cat, count in zip(clarity_categories, clarity_values):
        percentage = (count / total_videos_clarity * 100) if total_videos_clarity > 0 else 0
        print(f"  - {cat}: {count} videos ({percentage:.1f}%)")
    
    print(f"\nMost Common Artifacts per Video (Total: {total_videos_artifacts}):")
    for cat, count in zip(artifacts_categories, artifacts_values):
        percentage = (count / total_videos_artifacts * 100) if total_videos_artifacts > 0 else 0
        print(f"  - {cat}: {count} videos ({percentage:.1f}%)")
    
    print(f"\nMost Common Immersion per Video (Total: {total_videos_immersion}):")
    for cat, count in zip(immersion_categories, immersion_values):
        percentage = (count / total_videos_immersion * 100) if total_videos_immersion > 0 else 0
        print(f"  - {cat}: {count} videos ({percentage:.1f}%)")
    
    # Check for any unrecognized categories
    print(f"\nUnrecognized categories found:")
    unrecognized_clarity = [cat for cat in clarity_counts.keys() if cat not in clarity_categories]
    unrecognized_artifacts = [cat for cat in artifacts_counts.keys() if cat not in artifacts_categories]
    unrecognized_immersion = [cat for cat in immersion_counts.keys() if cat not in immersion_categories]
    
    if unrecognized_clarity:
        print(f"  Clarity: {unrecognized_clarity}")
    if unrecognized_artifacts:
        print(f"  Artifacts: {unrecognized_artifacts}")
    if unrecognized_immersion:
        print(f"  Immersion: {unrecognized_immersion}")
    if not (unrecognized_clarity or unrecognized_artifacts or unrecognized_immersion):
        print(f"  None - all categories properly recognized!")
    
    return clarity_counts, artifacts_counts, immersion_counts

def main(output_directory=None):
    """Main function to process all data and generate results"""
    
    if output_directory:
        print(f"Output directory: {output_directory}")
    else:
        print("Output directory: Current working directory")
    
    print("Starting processing of approval files with Approve='X'...")
    print("Extracting final ratings for each video name across all workers...")
    print("=" * 70)
    
    # Process all batch files with attributes (new enhanced version)
    (video_ratings, video_clarity, video_artifacts, video_immersion, 
     total_valid_ratings, total_invalid_ratings, total_workers, approved_workers, total_files) = process_all_approval_files_with_attributes()
    
    print(f"\nProcessing completed!")
    print(f"Total files processed: {total_files}")
    print(f"Total unique videos found: {len(video_ratings)}")
    print(f"Total valid final ratings collected: {total_valid_ratings}")
    print(f"Total invalid/unset ratings skipped: {total_invalid_ratings}")
    print(f"Valid rating percentage: {total_valid_ratings/(total_valid_ratings+total_invalid_ratings)*100:.2f}%" if (total_valid_ratings+total_invalid_ratings) > 0 else "N/A")
    print(f"Total workers across all files: {total_workers}")
    print(f"Approved workers (X): {approved_workers}")
    print(f"Approval rate: {approved_workers/total_workers*100:.2f}%" if total_workers > 0 else "N/A")
    
    if len(video_ratings) == 0:
        print("No video ratings found. Please check the file paths and data format.")
        return
    
    # Calculate averages per video
    print("\nCalculating average final rating per video...")
    video_averages = calculate_video_averages(video_ratings)
    
    # Save individual ratings to CSV
    print("\nSaving individual final ratings to CSV...")
    df_individual = save_individual_ratings_to_csv(video_ratings, output_directory)
    
    # Save attributes data to CSV (NEW)
    print("\nSaving attributes data to CSV...")
    df_attributes = save_attributes_to_csv(video_clarity, video_artifacts, video_immersion, output_directory)
    
    # Save results to CSV
    print("\nSaving average results to CSV...")
    df_results = save_results_to_csv(video_averages, output_directory)
    
    # Create and save histogram
    print("\nCreating histogram...")
    mean_rating, median_rating, std_rating = create_histogram(video_averages, total_valid_ratings, output_directory)
    
    # Create attributes histogram (NEW)
    print("\nCreating attributes distribution histogram...")
    clarity_counts, artifacts_counts, immersion_counts = create_attributes_histogram(
        video_clarity, video_artifacts, video_immersion, output_directory)
    
    # Create major attributes histogram (NEW)
    print("\nCreating major attributes distribution histogram...")
    major_attr_counts = create_major_attributes_histogram(
        video_clarity, video_artifacts, video_immersion, output_directory)
    
    # Create most common attributes per video histogram (NEW)
    print("\nCreating most common attributes per video histogram...")
    most_common_attr_counts = create_most_common_attributes_histogram(
        video_clarity, video_artifacts, video_immersion, output_directory)
    
    # Create batch-wise box plots instead of single large box plot
    print("\nCreating batch-wise box plots...")
    total_plots = create_batch_wise_boxplots(video_ratings, output_directory)
    
    # Print summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS (Final Ratings per Video, Approve='X' Only)")
    print("=" * 70)
    print(f"Total unique videos: {len(video_averages)}")
    print(f"Total valid final ratings collected: {total_valid_ratings}")
    print(f"Total invalid/unset ratings skipped: {total_invalid_ratings}")
    print(f"Valid rating percentage: {total_valid_ratings/(total_valid_ratings+total_invalid_ratings)*100:.2f}%" if (total_valid_ratings+total_invalid_ratings) > 0 else "N/A")
    print(f"Total workers: {total_workers}")
    print(f"Approved workers (X): {approved_workers}")
    print(f"Approval rate: {approved_workers/total_workers*100:.2f}%" if total_workers > 0 else "N/A")
    print(f"Average number of valid ratings per video: {total_valid_ratings / len(video_averages):.2f}")
    print(f"Average number of videos rated per approved worker: {total_valid_ratings / approved_workers:.2f}" if approved_workers > 0 else "N/A")
    print(f"Total batch-wise box plots created: {total_plots}")
    
    print(f"\nFinal Rating Distribution Statistics:")
    print(f"Mean average final rating: {mean_rating:.2f}")
    print(f"Median average final rating: {median_rating:.2f}")
    print(f"Standard deviation: {std_rating:.2f}")
    print(f"Min average final rating: {min(data['average_rating'] for data in video_averages.values()):.2f}")
    print(f"Max average final rating: {max(data['average_rating'] for data in video_averages.values()):.2f}")
    
    # Show videos with most and least ratings
    rating_counts = [data['num_ratings'] for data in video_averages.values()]
    print(f"\nRating Count Statistics:")
    print(f"Min ratings per video: {min(rating_counts)}")
    print(f"Max ratings per video: {max(rating_counts)}")
    print(f"Average ratings per video: {np.mean(rating_counts):.2f}")
    
    # Show top and bottom rated videos
    print(f"\nTop 10 highest rated videos (by average final rating):")
    top_videos = df_results.head(10)
    for idx, row in top_videos.iterrows():
        print(f"  {row['video_name']}: {row['average_final_rating']:.2f} (n={row['num_ratings']})")
    
    print(f"\nTop 10 lowest rated videos (by average final rating):")
    bottom_videos = df_results.tail(10)
    for idx, row in bottom_videos.iterrows():
        print(f"  {row['video_name']}: {row['average_final_rating']:.2f} (n={row['num_ratings']})")
    
    # Print attribute statistics (NEW)
    print(f"\n" + "=" * 70)
    print("ATTRIBUTE DISTRIBUTION STATISTICS")
    print("=" * 70)
    print(f"Total unique clarity categories: {len(clarity_counts)}")
    print(f"Total unique artifacts categories: {len(artifacts_counts)}")
    print(f"Total unique immersion categories: {len(immersion_counts)}")
    
    # Show top 5 most common for each attribute
    print(f"\nTop 5 Most Common Clarity Ratings:")
    for i, (category, count) in enumerate(clarity_counts.most_common(5), 1):
        print(f"  {i}. '{category}': {count} occurrences")
    
    print(f"\nTop 5 Most Common Artifacts Ratings:")
    for i, (category, count) in enumerate(artifacts_counts.most_common(5), 1):
        print(f"  {i}. '{category}': {count} occurrences")
    
    print(f"\nTop 5 Most Common Immersion Ratings:")
    for i, (category, count) in enumerate(immersion_counts.most_common(5), 1):
        print(f"  {i}. '{category}': {count} occurrences")
    
    # Print major attribute statistics (NEW)
    print(f"\n" + "=" * 70)
    print("MAJOR ATTRIBUTE DISTRIBUTION STATISTICS")
    print("=" * 70)
    print(f"Total unique major attributes: {len(major_attr_counts)}")
    
    # Show top 5 most common major attributes
    print(f"\nTop 5 Most Common Major Attributes:")
    for i, (category, count) in enumerate(major_attr_counts.most_common(5), 1):
        print(f"  {i}. '{category}': {count} occurrences")
    
    # Print most common attributes per video histogram statistics (NEW)
    if most_common_attr_counts:
        most_common_clarity_counts, most_common_artifacts_counts, most_common_immersion_counts = most_common_attr_counts
        print(f"\n" + "=" * 70)
        print("MOST COMMON ATTRIBUTES PER VIDEO DISTRIBUTION STATISTICS")
        print("=" * 70)
        print(f"Total unique most common clarity categories: {len(most_common_clarity_counts)}")
        print(f"Total unique most common artifacts categories: {len(most_common_artifacts_counts)}")
        print(f"Total unique most common immersion categories: {len(most_common_immersion_counts)}")
        
        # Show distribution of most common categories per video
        print(f"\nMost Common Clarity Categories per Video:")
        for i, (category, count) in enumerate(most_common_clarity_counts.most_common(3), 1):
            print(f"  {i}. '{category}': {count} videos")
        
        print(f"\nMost Common Artifacts Categories per Video:")
        for i, (category, count) in enumerate(most_common_artifacts_counts.most_common(3), 1):
            print(f"  {i}. '{category}': {count} videos")
        
        print(f"\nMost Common Immersion Categories per Video:")
        for i, (category, count) in enumerate(most_common_immersion_counts.most_common(3), 1):
            print(f"  {i}. '{category}': {count} videos")

    print("\nAnalysis complete!")

if __name__ == "__main__":
    # You can specify an output directory here
    # main(output_directory="./global_ratings_output")
    main(output_directory=OUTPUT_DIRECTORY)
