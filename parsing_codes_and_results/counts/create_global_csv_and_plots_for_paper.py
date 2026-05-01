import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import glob
from collections import defaultdict, Counter
import seaborn as sns
# Configuration
OUTPUT_DIRECTORY = "./parsing_codes_and_results/counts/global_analysis_output"


def read_all_batch_final_ratings():
    input_directory = "./parsing_codes_and_results/counts"
    """Read final ratings CSV files from all batch directories"""
    
    all_final_ratings = []
    batch_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
    
    for batch_letter in batch_letters:
        batch_dir = f'{input_directory}/batch{batch_letter}_secondparse/approve_reject_reports'
        
        if os.path.exists(batch_dir):
            print(f"Processing batch {batch_letter} final ratings...")
            
            # Look for final ratings CSV files
            final_ratings_files = [
                f'{batch_dir}/approve_reject_video_final_ratings.csv',
                f'{batch_dir}/approve_reject_videos_less_than_30_valid_ratings.csv'
            ]
            
            for file_path in final_ratings_files:
                if os.path.exists(file_path):
                    print(f"  Reading: {file_path}")
                    try:
                        df = pd.read_csv(file_path)
                        df['batch'] = batch_letter  # Add batch identifier
                        all_final_ratings.append(df)
                        print(f"    Added {len(df)} videos from {os.path.basename(file_path)}")
                    except Exception as e:
                        print(f"    Error reading {file_path}: {e}")
        else:
            print(f"Batch {batch_letter} directory not found: {batch_dir}")
    
    if all_final_ratings:
        combined_df = pd.concat(all_final_ratings, ignore_index=True)
        print(f"\nCombined final ratings: {len(combined_df)} total video entries")
        return combined_df
    else:
        print("No final ratings data found!")
        return pd.DataFrame()

def read_all_batch_attributes():
    input_directory = "./parsing_codes_and_results/counts"
    """Read attributes CSV files from all batch directories"""
    
    all_attributes = []
    batch_letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
    
    for batch_letter in batch_letters:
        batch_dir = f'{input_directory}/batch{batch_letter}_secondparse/approve_reject_reports'
        
        if os.path.exists(batch_dir):
            print(f"Processing batch {batch_letter} attributes...")
            
            # Look for attributes CSV files
            attributes_files = [
                f'{batch_dir}/approve_reject_video_attribute_counts.csv',
                f'{batch_dir}/approve_reject_video_attributes_less_than_30_valid_ratings.csv'
            ]
            
            for file_path in attributes_files:
                if os.path.exists(file_path):
                    print(f"  Reading: {file_path}")
                    try:
                        df = pd.read_csv(file_path)
                        df['batch'] = batch_letter  # Add batch identifier
                        all_attributes.append(df)
                        print(f"    Added {len(df)} videos from {os.path.basename(file_path)}")
                    except Exception as e:
                        print(f"    Error reading {file_path}: {e}")
        else:
            print(f"Batch {batch_letter} directory not found: {batch_dir}")
    
    if all_attributes:
        combined_df = pd.concat(all_attributes, ignore_index=True)
        print(f"\nCombined attributes: {len(combined_df)} total video entries")
        return combined_df
    else:
        print("No attributes data found!")
        return pd.DataFrame()

def calculate_average_ratings(df_final_ratings):
    """Calculate average final rating for each video"""
    
    print("Calculating average ratings...")
    video_averages = []
    
    for idx, row in df_final_ratings.iterrows():
        video_name = row['video_name']
        batch = row['batch']
        valid_count = row['valid_ratings_count']
        
        # Extract all final rating columns (final_rate1, final_rate2, etc.)
        rating_cols = [col for col in row.index if col.startswith('final_rate')]
        
        # Get valid ratings (not NaN, not 'unset')
        valid_ratings = []
        for col in rating_cols:
            value = row[col]
            if pd.notna(value) and value != 'unset' and str(value).strip() != '':
                try:
                    rating = float(value)
                    valid_ratings.append(rating)
                except ValueError:
                    continue
        
        if valid_ratings:
            avg_rating = np.mean(valid_ratings)
            video_averages.append({
                'video_name': video_name,
                'batch': batch,
                'average_final_rating': avg_rating,
                'valid_ratings_count': len(valid_ratings),
                'total_ratings_count': row['total_ratings_count'],
                'std_rating': np.std(valid_ratings) if len(valid_ratings) > 1 else 0,
                'min_rating': min(valid_ratings),
                'max_rating': max(valid_ratings)
            })
    
    df_averages = pd.DataFrame(video_averages)
    print(f"Calculated averages for {len(df_averages)} videos")
    return df_averages

def create_individual_ratings_matrix_csv(df_final_ratings, output_dir):
    """Create CSV with all individual ratings padded with NaNs to match maximum ratings count"""
    
    print("Creating individual ratings matrix CSV with NaN padding...")
    
    # First, extract all individual ratings for each video
    video_ratings_data = []
    max_ratings = 0
    
    for idx, row in df_final_ratings.iterrows():
        video_name = row['video_name']
        batch = row['batch']
        
        # Extract all final rating columns (final_rate1, final_rate2, etc.)
        rating_cols = [col for col in row.index if col.startswith('final_rate')]
        
        # Get valid ratings (not NaN, not 'unset')
        valid_ratings = []
        for col in rating_cols:
            value = row[col]
            if pd.notna(value) and value != 'unset' and str(value).strip() != '':
                try:
                    rating = float(value)
                    valid_ratings.append(rating)
                except ValueError:
                    continue
        
        if valid_ratings:
            video_ratings_data.append({
                'video_name': video_name,
                'batch': batch,
                'ratings': valid_ratings,
                'num_ratings': len(valid_ratings)
            })
            max_ratings = max(max_ratings, len(valid_ratings))
    
    print(f"Found maximum of {max_ratings} ratings for any single video")
    print(f"Processing {len(video_ratings_data)} videos with ratings")
    
    # Create the matrix with NaN padding
    matrix_data = []
    
    for video_data in video_ratings_data:
        row_data = {
            'video_name': video_data['video_name'],
            'batch': video_data['batch'],
            'num_valid_ratings': video_data['num_ratings']
        }
        
        # Add all ratings as separate columns
        ratings = video_data['ratings']
        for i in range(max_ratings):
            if i < len(ratings):
                row_data[f'rating_{i+1}'] = ratings[i]
            else:
                row_data[f'rating_{i+1}'] = np.nan
        
        matrix_data.append(row_data)
    
    # Create DataFrame
    df_matrix = pd.DataFrame(matrix_data)
    
    # Sort by video name for consistency
    df_matrix = df_matrix.sort_values('video_name')
    
    # Save to CSV
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'global_individual_ratings_matrix.csv')
    
    df_matrix.to_csv(output_path, index=False)
    
    print(f"Individual ratings matrix CSV saved to: {output_path}")
    print(f"Matrix dimensions: {len(df_matrix)} videos × {max_ratings} rating columns")
    print(f"Columns: video_name, batch, num_valid_ratings, rating_1 to rating_{max_ratings}")
    
    # Print some statistics
    total_ratings = df_matrix['num_valid_ratings'].sum()
    total_nans = len(df_matrix) * max_ratings - total_ratings
    fill_percentage = (total_ratings / (len(df_matrix) * max_ratings)) * 100
    
    print(f"\nMatrix Statistics:")
    print(f"Total valid ratings: {total_ratings}")
    print(f"Total NaN positions: {total_nans}")
    print(f"Matrix fill percentage: {fill_percentage:.1f}%")
    print(f"Average ratings per video: {total_ratings / len(df_matrix):.2f}")
    
    return df_matrix, max_ratings

def create_global_final_ratings_csv(df_averages, output_dir):
    """Save global final ratings with averages to CSV"""
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'global_video_final_ratings_with_averages.csv')
    
    # Sort by average rating (descending)
    df_sorted = df_averages.sort_values('average_final_rating', ascending=False)
    
    df_sorted.to_csv(output_path, index=False)
    print(f"Global final ratings CSV saved to: {output_path}")
    print(f"Contains {len(df_sorted)} videos with calculated averages")
    
    return df_sorted

def create_global_attributes_csv(df_attributes, output_dir):
    """Save global attributes CSV"""
    
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'global_video_attributes.csv')
    
    # Sort by video name for consistency
    df_sorted = df_attributes.sort_values('video_name')
    
    df_sorted.to_csv(output_path, index=False)
    print(f"Global attributes CSV saved to: {output_path}")
    print(f"Contains {len(df_sorted)} videos with attribute data")
    
    return df_sorted

def create_global_histogram(df_averages, output_dir):
    """Create global histogram of average final ratings"""
    
    avg_ratings = df_averages['average_final_rating'].values
    
    plt.figure(figsize=(12, 8))
    
    # Create histogram
    plt.hist(avg_ratings, bins=50, alpha=0.7, color='lightcoral', edgecolor='black')
    plt.title('Global Distribution of Average Final Ratings per Video\n(All Batches Combined)', 
              fontsize=16, fontweight='bold')
    plt.xlabel('Average Final Rating', fontsize=12)
    plt.ylabel('Number of Videos', fontsize=12)
    plt.grid(True, alpha=0.3)
    
    # Add statistics
    mean_rating = np.mean(avg_ratings)
    median_rating = np.median(avg_ratings)
    std_rating = np.std(avg_ratings)
    
    plt.axvline(mean_rating, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_rating:.2f}')
    plt.axvline(median_rating, color='green', linestyle='--', linewidth=2, label=f'Median: {median_rating:.2f}')
    
    plt.legend()
    
    # Add statistics text box
    stats_text = (f'Statistics:\n'
                  f'Mean: {mean_rating:.2f}\n'
                  f'Median: {median_rating:.2f}\n'
                  f'Std: {std_rating:.2f}\n'
                  f'Min: {min(avg_ratings):.2f}\n'
                  f'Max: {max(avg_ratings):.2f}\n'
                  f'Total Videos: {len(avg_ratings)}')
    
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    
    # Save plot
    output_path = os.path.join(output_dir, 'global_final_ratings_histogram.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Global histogram saved to: {output_path}")
    
    plt.show()
    
    return mean_rating, median_rating, std_rating

def create_global_attributes_plot(df_attributes, output_dir):
    """
    Create a professional global attributes distribution plot suitable for research papers.
    """
    # 1. Setup Styling
    sns.set_style("white")  # Clean background
    plt.rcParams['font.family'] = 'sans-serif'
    
    # Define cohesive, research-friendly colors (desaturated)
    colors = ['#4E79A7', '#76B7B2', '#59A14F'] # Blue, Red, Green
    
    # Count attributes
    clarity_counts = Counter(df_attributes['most_common_clarity'].dropna())
    artifacts_counts = Counter(df_attributes['most_common_artifacts'].dropna())
    immersion_counts = Counter(df_attributes['most_common_immersion'].dropna())
    
    # Categories
    clarity_categories = ['Highly Clear', 'Moderately Clear', 'Minimally Clear']
    artifacts_categories = ['No visible artifacts', 'Minor Artifacts Present', 'Severe Artifacts Present']
    immersion_categories = ['High level of immersion', 'Moderate level of immersion', 'Low level of immersion']
    
    categories_list = [clarity_categories, artifacts_categories, immersion_categories]
    counts_list = [clarity_counts, artifacts_counts, immersion_counts]
    titles = ['Clarity Distribution', 'Artifacts Distribution', 'Immersion Distribution']
    
    # 2. Create Figure with bar plots
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=False)
    
    for i, ax in enumerate(axes):
        cats = categories_list[i]
        vals = [counts_list[i].get(cat, 0) for cat in cats]
        
        # Plot bars with subtle styling
        bars = ax.bar(range(len(cats)), vals, color=colors[i], alpha=0.8, 
                      edgecolor='black', linewidth=0.8, width=0.7)
        
        # Header/Label Formatting
        ax.set_title(titles[i], fontweight='bold', fontsize=13, pad=15)
        ax.set_ylabel('Number of Videos', fontweight='bold', fontsize=11)
        ax.set_xticks(range(len(cats)))
        
        # Wrap labels or rotate them for better fit
        short_labels = [label.replace(' ', '\n') for label in cats]
        ax.set_xticklabels(short_labels, fontsize=9,fontweight='bold')
        
        # 3. Professional Refinement
        ax.grid(True, alpha=0.2, linestyle='--', axis='y')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # Add value labels on top of bars
        max_v = max(vals) if vals else 1
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + (max_v * 0.02),
                        f'{int(height)}', ha='center', va='bottom', 
                        fontsize=10, fontweight='bold', color='#333333')

    # Overall Figure Adjustment
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    # 4. Save bar plots in multiple formats
    os.makedirs(output_dir, exist_ok=True)
    
    # Save PNG for quick viewing
    png_path = os.path.join(output_dir, 'global_attributes_distribution.png')
    plt.savefig(png_path, dpi=300, bbox_inches='tight', facecolor='white')
    
    # Save PDF for Research Paper (Vector format stays sharp at any zoom)
    pdf_path = os.path.join(output_dir, 'global_attributes_distribution.pdf')
    plt.savefig(pdf_path, bbox_inches='tight', facecolor='white')
    
    print(f"✓ Saved professional bar plots to: {output_dir}")
    plt.show()
    
    # 5. Create combined pie chart for all three attributes
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Prepare combined data
    all_attributes_labels = []
    all_attributes_values = []
    all_attributes_colors = []
    
    # Color palettes for each attribute type (dark to light variations)
    clarity_colors = ['#2E5266', '#4E79A7', '#7FA5C4']      # Blues (Clarity) - dark to light
    artifacts_colors = ['#4A8E7E', '#76B7B2', '#A8D4CA']    # Teals (Artifacts) - dark to light
    immersion_colors = ['#3D7C2F', '#59A14F', '#85C77A']    # Greens (Immersion) - dark to light
    
    # Add clarity data (dark to light blue for different levels)
    for i, cat in enumerate(clarity_categories):
        count = clarity_counts.get(cat, 0)
        if count > 0:
            all_attributes_labels.append(f'{cat}\n(Clarity)')
            all_attributes_values.append(count)
            all_attributes_colors.append(clarity_colors[i])
    
    # Add artifacts data (dark to light teal for different levels)
    for i, cat in enumerate(artifacts_categories):
        count = artifacts_counts.get(cat, 0)
        if count > 0:
            all_attributes_labels.append(f'{cat}\n(Artifacts)')
            all_attributes_values.append(count)
            all_attributes_colors.append(artifacts_colors[i])
    
    # Add immersion data (dark to light green for different levels)
    for i, cat in enumerate(immersion_categories):
        count = immersion_counts.get(cat, 0)
        if count > 0:
            all_attributes_labels.append(f'{cat}\n(Immersion)')
            all_attributes_values.append(count)
            all_attributes_colors.append(immersion_colors[i])
    
    # Create pie chart
    wedges, texts, autotexts = ax.pie(all_attributes_values, 
                                        labels=all_attributes_labels,
                                        colors=all_attributes_colors,
                                        autopct='%1.1f%%',
                                        startangle=90,
                                        textprops={'fontsize': 10, 'fontweight': 'bold', 'color': '#333333'})
    
    # Enhance autotext (percentage labels)
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
        autotext.set_fontsize(9)
        autotext.set_bbox(dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.3, edgecolor='none'))
    
    # Enhance text labels
    for text in texts:
        text.set_fontsize(10)
        text.set_fontweight('bold')
        text.set_color('#333333')
    
    plt.tight_layout()
    
    # Save pie chart in multiple formats
    pie_png_path = os.path.join(output_dir, 'global_attributes_distribution_piechart.png')
    plt.savefig(pie_png_path, dpi=300, bbox_inches='tight', facecolor='white')
    
    pie_pdf_path = os.path.join(output_dir, 'global_attributes_distribution_piechart.pdf')
    plt.savefig(pie_pdf_path, bbox_inches='tight', facecolor='white')
    
    print(f"✓ Saved professional pie chart to: {output_dir}")
    plt.show()
    
    return clarity_counts, artifacts_counts, immersion_counts

def create_global_attributes_combined_bar_plot(df_attributes, output_dir):
    """
    Create a combined bar plot with all three attributes (Clarity, Artifacts, Immersion) 
    displayed together on a single plot with grouped bars.
    """
    # Setup Styling
    sns.set_style("white")
    plt.rcParams['font.family'] = 'sans-serif'
    
    # Count attributes
    clarity_counts = Counter(df_attributes['most_common_clarity'].dropna())
    artifacts_counts = Counter(df_attributes['most_common_artifacts'].dropna())
    immersion_counts = Counter(df_attributes['most_common_immersion'].dropna())
    
    # Full categories (for data lookup)
    clarity_categories = ['Highly Clear', 'Moderately Clear', 'Minimally Clear']
    artifacts_categories = ['No visible artifacts', 'Minor Artifacts Present', 'Severe Artifacts Present']
    immersion_categories = ['High level of immersion', 'Moderate level of immersion', 'Low level of immersion']
    
    # Shortened display names for x-axis
    clarity_short = ['Highly', 'Moderately', 'Minimally']
    artifacts_short = ['No visible', 'Minor', 'Severe']
    immersion_short = ['High', 'Moderate', 'Low']
    
    # Color palettes for each attribute type (dark to light variations)
    clarity_colors = ['#2E5266', '#4E79A7', '#7FA5C4']      # Blues (Clarity) - dark to light
    artifacts_colors = ['#8B1A1A', '#D32F2F', '#FF6B6B']    # Reds (Artifacts) - dark to light
    immersion_colors = ['#3D7C2F', '#59A14F', '#85C77A']    # Greens (Immersion) - dark to light
    
    # Prepare data for grouped bars
    categories = []
    clarity_values = []
    artifacts_values = []
    immersion_values = []
    
    # Clarity data
    for i, cat in enumerate(clarity_categories):
        count = clarity_counts.get(cat, 0)
        categories.append(f'{cat}\n(Clarity)')
        clarity_values.append(count)
    
    # Artifacts data
    for i, cat in enumerate(artifacts_categories):
        count = artifacts_counts.get(cat, 0)
        categories.append(f'{cat}\n(Artifacts)')
        artifacts_values.append(count)
    
    # Immersion data
    for i, cat in enumerate(immersion_categories):
        count = immersion_counts.get(cat, 0)
        categories.append(f'{cat}\n(Immersion)')
        immersion_values.append(count)
    
    # Create figure with extra width for legend
    fig, ax = plt.subplots(figsize=(5, 4))
    
    # Create bars with combined colors
    all_values = []
    all_colors = []
    
    # Prepare combined data with colors
    for i in range(3):  # 3 levels
        # Clarity level
        all_values.append(clarity_values[i] if i < len(clarity_values) else 0)
        all_colors.append(clarity_colors[i])
        
        # Artifacts level
        all_values.append(artifacts_values[i] if i < len(artifacts_values) else 0)
        all_colors.append(artifacts_colors[i])
        
        # Immersion level
        all_values.append(immersion_values[i] if i < len(immersion_values) else 0)
        all_colors.append(immersion_colors[i])
    
    # Reorganize for grouped plotting (group by attribute, show all 3 levels within each attribute)
    clarity_vals = [clarity_counts.get(cat, 0) for cat in clarity_categories]
    artifacts_vals = [artifacts_counts.get(cat, 0) for cat in artifacts_categories]
    immersion_vals = [immersion_counts.get(cat, 0) for cat in immersion_categories]
    
    # Create grouped bar positions (3 attributes, each with 3 levels)
    bar_width = 0.04
    
    # Within each group, plot 3 bars (one for each level)
    offset_positions = [-bar_width, 0, bar_width]
    
    # Plot Clarity bars (all 3 levels of clarity together) - Blue color family
    clarity_base = 0
    for i, val in enumerate(clarity_vals):
        ax.bar(clarity_base + offset_positions[i], val, bar_width, 
               color=clarity_colors[i], edgecolor='black', linewidth=0.5, alpha=0.85)
    
    # Plot Artifacts bars (all 3 levels of artifacts together) - Teal color family
    artifacts_base = 0.2
    for i, val in enumerate(artifacts_vals):
        ax.bar(artifacts_base + offset_positions[i], val, bar_width, 
               color=artifacts_colors[i], edgecolor='black', linewidth=0.5, alpha=0.85)
    
    # Plot Immersion bars (all 3 levels of immersion together) - Green color family
    immersion_base = 0.4
    for i, val in enumerate(immersion_vals):
        bar = ax.bar(immersion_base + offset_positions[i], val, bar_width, 
                     color=immersion_colors[i], edgecolor='black', linewidth=0.5, alpha=0.85)
    
    # Add value labels on bars
    for container in ax.containers:
        for bar in container:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom', 
                        fontsize=7, fontweight='bold', color='#333333')
    
    # Labels and formatting
    ax.set_ylabel('Number of Videos', fontweight='bold', fontsize=10)
    
    # Create x-axis with detailed labels showing each category
    x_ticks = []
    x_labels = []
    
    # Clarity ticks and labels
    for i, cat in enumerate(clarity_categories):
        x_ticks.append(0 + offset_positions[i])
        x_labels.append(clarity_short[i])
    
    # Artifacts ticks and labels
    for i, cat in enumerate(artifacts_categories):
        x_ticks.append(0.2 + offset_positions[i])
        x_labels.append(artifacts_short[i])
    
    # Immersion ticks and labels
    for i, cat in enumerate(immersion_categories):
        x_ticks.append(0.4 + offset_positions[i])
        x_labels.append(immersion_short[i])
    
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_labels, fontsize=7, fontweight='bold', rotation=45, ha='right')
    
    ax.tick_params(axis='y', labelsize=7)
    
    # Set y-axis limit to reduce bar height
    max_value = max(max(clarity_vals), max(artifacts_vals), max(immersion_vals))
    ax.set_ylim(0, max_value * 1.5)  # Extend y-axis to make bars appear shorter
    
    # Spines and grid
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    
    # Add legend for attribute colors
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#4E79A7', edgecolor='black', linewidth=0.5, label='Clarity'),
        Patch(facecolor='#D32F2F', edgecolor='black', linewidth=0.5, label='Artifacts'),
        Patch(facecolor='#59A14F', edgecolor='black', linewidth=0.5, label='Immersion')
    ]
    ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, 1.05), fontsize=9, frameon=True, fancybox=True, ncol=3)
    
    plt.tight_layout()
    
    # Save plot
    os.makedirs(output_dir, exist_ok=True)
    
    png_path = os.path.join(output_dir, 'global_attributes_combined_bar_plot.png')
    plt.savefig(png_path, dpi=300, bbox_inches='tight', facecolor='white')
    
    pdf_path = os.path.join(output_dir, 'global_attributes_combined_bar_plot_rgb.pdf')
    plt.savefig(pdf_path, bbox_inches='tight', facecolor='white')
    
    print(f"✓ Saved combined bar plot to: {output_dir}")
    plt.show()

def create_batch_comparison_plots(df_averages, df_attributes, output_dir):
    """Create comparison plots showing statistics per batch"""
    
    # 1. Average ratings per batch
    batch_avg_ratings = df_averages.groupby('batch')['average_final_rating'].agg(['mean', 'std', 'count'])
    
    plt.figure(figsize=(14, 6))
    
    # Plot 1: Average ratings per batch
    plt.subplot(1, 2, 1)
    batches = batch_avg_ratings.index
    means = batch_avg_ratings['mean']
    stds = batch_avg_ratings['std']
    
    bars = plt.bar(batches, means, yerr=stds, capsize=5, alpha=0.7, color='lightcoral', edgecolor='black')
    plt.title('Average Final Rating per Batch', fontsize=12, fontweight='bold')
    plt.xlabel('Batch', fontsize=10)
    plt.ylabel('Average Final Rating', fontsize=10)
    plt.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for i, (batch, mean_val) in enumerate(zip(batches, means)):
        plt.text(i, mean_val + 0.5, f'{mean_val:.1f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # Plot 2: Number of videos per batch
    plt.subplot(1, 2, 2)
    video_counts = batch_avg_ratings['count']
    bars = plt.bar(batches, video_counts, alpha=0.7, color='lightblue', edgecolor='black')
    plt.title('Number of Videos per Batch', fontsize=12, fontweight='bold')
    plt.xlabel('Batch', fontsize=10)
    plt.ylabel('Number of Videos', fontsize=10)
    plt.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for i, (batch, count) in enumerate(zip(batches, video_counts)):
        plt.text(i, count + max(video_counts) * 0.01, str(count), ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    plt.suptitle('Batch-wise Analysis of Final Ratings', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    # Save plot
    output_path = os.path.join(output_dir, 'batch_comparison_final_ratings.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Batch comparison plot saved to: {output_path}")
    
    plt.show()
    
    return batch_avg_ratings

def print_summary_statistics(df_averages, df_attributes, df_matrix=None, max_ratings=None):
    """Print comprehensive summary statistics"""
    
    print("\n" + "=" * 80)
    print("GLOBAL ANALYSIS SUMMARY STATISTICS")
    print("=" * 80)
    
    # Final ratings statistics
    print(f"\nFINAL RATINGS STATISTICS:")
    print(f"Total unique videos: {len(df_averages)}")
    print(f"Total batches processed: {len(df_averages['batch'].unique())}")
    print(f"Batches: {sorted(df_averages['batch'].unique())}")
    
    avg_ratings = df_averages['average_final_rating']
    print(f"\nRating Distribution:")
    print(f"Mean: {avg_ratings.mean():.2f}")
    print(f"Median: {avg_ratings.median():.2f}")
    print(f"Std: {avg_ratings.std():.2f}")
    print(f"Min: {avg_ratings.min():.2f}")
    print(f"Max: {avg_ratings.max():.2f}")
    
    # Individual ratings matrix statistics
    if df_matrix is not None and max_ratings is not None:
        print(f"\nINDIVIDUAL RATINGS MATRIX STATISTICS:")
        print(f"Matrix dimensions: {len(df_matrix)} videos × {max_ratings} rating columns")
        total_ratings = df_matrix['num_valid_ratings'].sum()
        total_possible = len(df_matrix) * max_ratings
        fill_percentage = (total_ratings / total_possible) * 100
        print(f"Total valid ratings: {total_ratings}")
        print(f"Total possible positions: {total_possible}")
        print(f"Matrix fill percentage: {fill_percentage:.1f}%")
        print(f"Average ratings per video: {total_ratings / len(df_matrix):.2f}")
    
    # Per-batch statistics
    print(f"\nPER-BATCH STATISTICS:")
    batch_stats = df_averages.groupby('batch').agg({
        'average_final_rating': ['count', 'mean', 'std'],
        'valid_ratings_count': 'mean'
    }).round(2)
    
    for batch in sorted(df_averages['batch'].unique()):
        batch_data = df_averages[df_averages['batch'] == batch]
        print(f"Batch {batch}: {len(batch_data)} videos, "
              f"avg rating: {batch_data['average_final_rating'].mean():.2f}, "
              f"avg ratings per video: {batch_data['valid_ratings_count'].mean():.1f}")
    
    # Attributes statistics
    if not df_attributes.empty:
        print(f"\nATTRIBUTES STATISTICS:")
        print(f"Total videos with attributes: {len(df_attributes)}")
        
        clarity_dist = df_attributes['most_common_clarity'].value_counts()
        artifacts_dist = df_attributes['most_common_artifacts'].value_counts()
        immersion_dist = df_attributes['most_common_immersion'].value_counts()
        
        print(f"\nMost common clarity distribution:")
        for clarity, count in clarity_dist.head().items():
            print(f"  {clarity}: {count} videos")
        
        print(f"\nMost common artifacts distribution:")
        for artifacts, count in artifacts_dist.head().items():
            print(f"  {artifacts}: {count} videos")
        
        print(f"\nMost common immersion distribution:")
        for immersion, count in immersion_dist.head().items():
            print(f"  {immersion}: {count} videos")

def main():
    """Main function to execute the global analysis"""
    
    print("Starting Global CSV and Plots Generation...")
    print("=" * 60)
    
    # Read all batch data
    print("\n1. Reading final ratings from all batches...")
    df_final_ratings = read_all_batch_final_ratings()
    
    print("\n2. Reading attributes from all batches...")
    df_attributes = read_all_batch_attributes()
    
    if df_final_ratings.empty:
        print("ERROR: No final ratings data found!")
        return
    
    # Calculate averages
    print("\n3. Calculating average ratings...")
    df_averages = calculate_average_ratings(df_final_ratings)
    
    # Create output directory
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    print(f"\nOutput directory: {OUTPUT_DIRECTORY}")
    
    # Save global CSV files
    print("\n4. Creating global CSV files...")
    df_final_sorted = create_global_final_ratings_csv(df_averages, OUTPUT_DIRECTORY)
    
    # Create individual ratings matrix CSV with NaN padding
    print("\n5. Creating individual ratings matrix CSV...")
    df_matrix, max_ratings = create_individual_ratings_matrix_csv(df_final_ratings, OUTPUT_DIRECTORY)
    
    if not df_attributes.empty:
        df_attr_sorted = create_global_attributes_csv(df_attributes, OUTPUT_DIRECTORY)
    
    # Create plots
    print("\n6. Creating global plots...")
    mean_rating, median_rating, std_rating = create_global_histogram(df_averages, OUTPUT_DIRECTORY)
    
    if not df_attributes.empty:
        clarity_counts, artifacts_counts, immersion_counts = create_global_attributes_plot(df_attributes, OUTPUT_DIRECTORY)
        create_global_attributes_combined_bar_plot(df_attributes, OUTPUT_DIRECTORY)
    
    # Create batch comparison plots
    print("\n7. Creating batch comparison plots...")
    batch_stats = create_batch_comparison_plots(df_averages, df_attributes, OUTPUT_DIRECTORY)
    
    # Print summary
    print("\n8. Summary statistics...")
    print_summary_statistics(df_averages, df_attributes, df_matrix, max_ratings)
    
    print(f"\n" + "=" * 60)
    print("GLOBAL ANALYSIS COMPLETE!")
    print(f"All files saved to: {OUTPUT_DIRECTORY}")
    print("\nCreated files:")
    print("1. global_video_final_ratings_with_averages.csv - Average ratings per video")
    print("2. global_individual_ratings_matrix.csv - All individual ratings with NaN padding")
    print("3. global_video_attributes.csv - Most common attributes per video")
    print("4. global_final_ratings_histogram.png - Distribution of average ratings")
    print("5. global_attributes_distribution.png - Distribution of attributes (3 subplots)")
    print("6. global_attributes_distribution_piechart.png - All attributes in single pie chart")
    print("7. global_attributes_combined_bar_plot.png - All attributes in single bar plot")
    print("8. batch_comparison_final_ratings.png - Batch-wise comparison")
    print("=" * 60)

if __name__ == "__main__":
    main() 