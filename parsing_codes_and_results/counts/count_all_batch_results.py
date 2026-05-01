#!/usr/bin/env python3

import pandas as pd
import os
import re
from collections import defaultdict, Counter
import logging
import matplotlib.pyplot as plt
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VideoQualityProcessor:
    """Process video quality assessment data from MTurk batch results."""
    
    def __init__(self, input_folder, generate_box_plots=True):
        """
        Initialize the processor.
        
        Args:
            input_folder (str): Path to folder containing CSV batch result files
            generate_box_plots (bool): Whether to generate individual box plots for each video
        """
        self.input_folder = input_folder
        self.generate_box_plots = generate_box_plots
        self.video_ratings = defaultdict(list)  # video_name -> list of all ratings
        self.attribute_counts = defaultdict(Counter)  # attribute_type -> Counter of values
        self.processed_files = []
        
    def parse_rating_string(self, rating_str):
        """
        Parse a complex rating string into components.
        
        Expected format: "score/time/attributes,artifacts,immersion,/timestamp"
        
        Args:
            rating_str (str): Raw rating string from CSV
            
        Returns:
            dict: Parsed rating components
        """
        if pd.isna(rating_str) or rating_str == 'unset' or not rating_str.strip():
            return {
                'final_score': None,
                'time': None,
                'clarity': 'unset',
                'artifacts': 'unset',
                'immersion': 'unset',
                'timestamp': None,
                'is_unset': True
            }
        
        try:
            # Split by '/' to get main components
            parts = str(rating_str).split('/')
            if len(parts) < 4:
                return {
                    'final_score': None,
                    'time': None,
                    'clarity': 'unset',
                    'artifacts': 'unset',
                    'immersion': 'unset',
                    'timestamp': None,
                    'is_unset': True
                }
            
            first_score = parts[0] if parts[0] and parts[0] != 'unset' else None
            final_score = parts[1] if parts[1] and parts[1] != 'unset' else None  # Second number is final score
            
            # Parse attributes (clarity, artifacts, immersion)
            attributes_str = parts[2]
            attribute_parts = attributes_str.split(',') if attributes_str else []
            
            clarity = attribute_parts[0] if len(attribute_parts) > 0 and attribute_parts[0] else 'unset'
            artifacts = attribute_parts[1] if len(attribute_parts) > 1 and attribute_parts[1] else 'unset'
            immersion = attribute_parts[2] if len(attribute_parts) > 2 and attribute_parts[2] else 'unset'
            
            timestamp = parts[3] if len(parts) > 3 and parts[3] else None
            
            return {
                'final_score': final_score,  # Now correctly using the second number
                'time': first_score,         # First number is time/duration
                'clarity': clarity,
                'artifacts': artifacts,
                'immersion': immersion,
                'timestamp': timestamp,
                'is_unset': False
            }
            
        except Exception as e:
            logger.warning(f"Error parsing rating string '{rating_str}': {e}")
            return {
                'final_score': None,
                'time': None,
                'clarity': 'unset',
                'artifacts': 'unset',
                'immersion': 'unset',
                'timestamp': None,
                'is_unset': True
            }
    
    def process_csv_file(self, file_path):
        """
        Process a single CSV file.
        
        Args:
            file_path (str): Path to the CSV file
        """
        logger.info(f"Processing file: {os.path.basename(file_path)}")
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            
            # Filter for approved assignments only
            approved_df = df[df['Approve'] == 'X'].copy()
            logger.info(f"Found {len(approved_df)} approved assignments out of {len(df)} total")
            
            if len(approved_df) == 0:
                logger.warning(f"No approved assignments found in {file_path}")
                return
            
            # Find input video columns (Input.videos1, Input.videos2, etc.)
            input_video_cols = [col for col in df.columns if col.startswith('Input.videos') and col[12:].isdigit()]
            input_video_cols.sort(key=lambda x: int(x.split('videos')[1]))
            
            # Find answer video columns (Answer.videos1, Answer.videos2, etc.)
            answer_video_cols = [col for col in df.columns if col.startswith('Answer.videos') and col[13:].isdigit()]
            answer_video_cols.sort(key=lambda x: int(x.split('videos')[1]))
            
            logger.info(f"Found {len(input_video_cols)} input video columns and {len(answer_video_cols)} answer video columns")
            
            # Process each approved assignment
            for _, row in approved_df.iterrows():
                # Process each video rating pair
                for i, input_col in enumerate(input_video_cols):
                    video_name = row.get(input_col)
                    
                    if pd.isna(video_name) or not video_name.strip():
                        continue
                    
                    # Find corresponding answer column
                    video_num = input_col.split('videos')[1]
                    answer_col = f'Answer.videos{video_num}'
                    
                    if answer_col in row:
                        rating_str = row.get(answer_col)
                        parsed_rating = self.parse_rating_string(rating_str)
                        
                        # Store the rating
                        rating_data = {
                            'video_name': video_name,
                            'worker_id': row.get('WorkerId', 'unknown'),
                            'assignment_id': row.get('AssignmentId', 'unknown'),
                            'raw_rating': rating_str,
                            **parsed_rating
                        }
                        
                        self.video_ratings[video_name].append(rating_data)
                        
                        # Update attribute counts for this specific video
                        if not parsed_rating['is_unset']:
                            # Store per-video attribute counts
                            if video_name not in self.attribute_counts:
                                self.attribute_counts[video_name] = {
                                    'clarity': Counter(),
                                    'artifacts': Counter(),
                                    'immersion': Counter()
                                }
                            
                            self.attribute_counts[video_name]['clarity'][parsed_rating['clarity']] += 1
                            self.attribute_counts[video_name]['artifacts'][parsed_rating['artifacts']] += 1
                            self.attribute_counts[video_name]['immersion'][parsed_rating['immersion']] += 1
            
            self.processed_files.append(os.path.basename(file_path))
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise
    
    def process_all_files(self):
        """Process all CSV files in the input folder."""
        logger.info(f"Starting to process all CSV files in: {self.input_folder}")
        
        csv_files = [f for f in os.listdir(self.input_folder) if f.endswith('.csv')]
        
        if not csv_files:
            raise ValueError(f"No CSV files found in {self.input_folder}")
        
        logger.info(f"Found {len(csv_files)} CSV files to process")
        
        for csv_file in csv_files:
            file_path = os.path.join(self.input_folder, csv_file)
            self.process_csv_file(file_path)
        
        logger.info(f"Successfully processed {len(self.processed_files)} files")
        logger.info(f"Total unique videos found: {len(self.video_ratings)}")
    
    def generate_video_ratings_summary(self):
        """
        Generate summary with video_name, counts, and final ratings only.
        
        Returns:
            pd.DataFrame: Summary with video names, counts, and final scores
        """
        logger.info("Generating video ratings summary...")
        
        summary_data = []
        
        for video_name, ratings in self.video_ratings.items():
            unset_count = sum(1 for rating in ratings if rating['is_unset'])
            total_ratings = len(ratings)
            valid_ratings_count = total_ratings - unset_count
            
            # Create final rating columns - extract only the final scores
            rating_columns = {}
            for i, rating in enumerate(ratings):
                if rating['is_unset']:
                    rating_columns[f'final_rate{i+1}'] = 'unset'
                else:
                    rating_columns[f'final_rate{i+1}'] = rating['final_score']
            
            summary_row = {
                'video_name': video_name,
                'total_ratings_count': total_ratings,
                'valid_ratings_count': valid_ratings_count,
                'unset_count': unset_count,
                **rating_columns
            }
            
            summary_data.append(summary_row)
        
        # Convert to DataFrame and sort by total ratings count
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('total_ratings_count', ascending=False)
        
        logger.info(f"Generated summary for {len(summary_df)} videos")
        return summary_df
    
    def generate_attribute_summary(self):
        """
        Generate summary with video_name, most common attributes, and detailed counts.
        
        Returns:
            pd.DataFrame: Summary with video names, most common attributes, and counts
        """
        logger.info("Generating attribute counts summary...")
        
        attribute_data = []
        
        for video_name, ratings in self.video_ratings.items():
            if video_name not in self.attribute_counts:
                # Handle case where video has no valid ratings
                summary_row = {
                    'video_name': video_name,
                    'most_common_clarity': 'unset',
                    'most_common_artifacts': 'unset',
                    'most_common_immersion': 'unset',
                    'highly_clear_count': 0,
                    'moderately_clear_count': 0,
                    'minimally_clear_count': 0,
                    'no_artifacts_count': 0,
                    'minor_artifacts_count': 0,
                    'severe_artifacts_count': 0,
                    'high_immersion_count': 0,
                    'moderate_immersion_count': 0,
                    'low_immersion_count': 0
                }
            else:
                video_attr_counts = self.attribute_counts[video_name]
                
                # Get most common attributes
                most_common_clarity = video_attr_counts['clarity'].most_common(1)[0][0] if video_attr_counts['clarity'] else 'unset'
                most_common_artifacts = video_attr_counts['artifacts'].most_common(1)[0][0] if video_attr_counts['artifacts'] else 'unset'
                most_common_immersion = video_attr_counts['immersion'].most_common(1)[0][0] if video_attr_counts['immersion'] else 'unset'
                
                # Get detailed counts for each category
                summary_row = {
                    'video_name': video_name,
                    'most_common_clarity': most_common_clarity,
                    'most_common_artifacts': most_common_artifacts,
                    'most_common_immersion': most_common_immersion,
                    
                    # Clarity counts
                    'highly_clear_count': video_attr_counts['clarity'].get('Highly Clear', 0),
                    'moderately_clear_count': video_attr_counts['clarity'].get('Moderately Clear', 0),
                    'minimally_clear_count': video_attr_counts['clarity'].get('Minimally Clear', 0),
                    
                    # Artifacts counts
                    'no_artifacts_count': video_attr_counts['artifacts'].get('No visible artifacts', 0),
                    'minor_artifacts_count': video_attr_counts['artifacts'].get('Minor Artifacts Present', 0),
                    'severe_artifacts_count': video_attr_counts['artifacts'].get('Severe Artifacts Present', 0),
                    
                    # Immersion counts
                    'high_immersion_count': video_attr_counts['immersion'].get('High level of immersion', 0),
                    'moderate_immersion_count': video_attr_counts['immersion'].get('Moderate level of immersion', 0),
                    'low_immersion_count': video_attr_counts['immersion'].get('Low level of immersion', 0)
                }
            
            attribute_data.append(summary_row)
        
        attribute_df = pd.DataFrame(attribute_data)
        attribute_df = attribute_df.sort_values('video_name')
        
        logger.info(f"Generated attribute summary with {len(attribute_df)} videos")
        return attribute_df
    
    def generate_rating_plots(self, output_folder, prefix):
        """
        Generate box plots (quartile plots) for each video's ratings and save them to a plots folder.
        
        Args:
            output_folder (str): Base output folder path
            prefix (str): Prefix to add to filenames
        """
        logger.info("Generating rating quartile plots (box plots) for each video...")
        
        # Create plots subfolder
        plots_folder = os.path.join(output_folder, f'{prefix}_rating_plots')
        os.makedirs(plots_folder, exist_ok=True)
        
        # Set matplotlib style for better-looking plots
        plt.style.use('default')
        
        plot_count = 0
        for video_name, ratings in self.video_ratings.items():
            try:
                # Extract final scores (exclude unset ratings)
                final_scores = []
                for rating in ratings:
                    if not rating['is_unset'] and rating['final_score'] is not None:
                        try:
                            score = float(rating['final_score'])
                            if 0 <= score <= 100:  # Valid score range
                                final_scores.append(score)
                        except (ValueError, TypeError):
                            continue
                
                if len(final_scores) == 0:
                    logger.warning(f"No valid ratings found for video: {video_name}")
                    continue
                
                # Create clean filename from video name
                # Remove prefix before last "/" and replace invalid characters
                clean_name = video_name.split('/')[-1] if '/' in video_name else video_name
                clean_name = re.sub(r'[<>:"/\\|?*]', '_', clean_name)
                clean_name = clean_name.replace(' ', '_')
                
                # Create figure and plot
                fig, ax = plt.subplots(figsize=(10, 8))
                
                # Create box plot (quartile plot)
                box_plot = ax.boxplot([final_scores], 
                                    labels=[clean_name],
                                    patch_artist=True,
                                    showmeans=True,
                                    meanline=True,
                                    showfliers=True,
                                    notch=True)
                
                # Customize box plot colors
                box_plot['boxes'][0].set_facecolor('lightblue')
                box_plot['boxes'][0].set_alpha(0.7)
                box_plot['medians'][0].set_color('red')
                box_plot['medians'][0].set_linewidth(2)
                box_plot['means'][0].set_color('green')
                box_plot['means'][0].set_linewidth(2)
                
                # Customize plot
                ax.set_ylabel('Final Score (0-100)', fontsize=12)
                ax.set_title(f'{clean_name}\nValid Ratings: {len(final_scores)}', fontsize=14, fontweight='bold')
                ax.set_ylim(0, 100)
                ax.grid(True, alpha=0.3, axis='y')
                
                # Calculate quartile statistics
                q1 = np.percentile(final_scores, 25)
                q2 = np.percentile(final_scores, 50)  # median
                q3 = np.percentile(final_scores, 75)
                mean_score = np.mean(final_scores)
                std_score = np.std(final_scores)
                iqr = q3 - q1
                
                # Add statistics text box
                stats_text = (f'Mean: {mean_score:.1f}\n'
                            f'Median: {q2:.1f}\n'
                            f'Q1: {q1:.1f}\n'
                            f'Q3: {q3:.1f}\n'
                            f'IQR: {iqr:.1f}\n'
                            f'Std: {std_score:.1f}\n'
                            f'Min: {min(final_scores):.0f}\n'
                            f'Max: {max(final_scores):.0f}')
                
                ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, fontsize=10,
                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
                
                # Add legend
                from matplotlib.lines import Line2D
                legend_elements = [
                    Line2D([0], [0], color='red', lw=2, label='Median'),
                    Line2D([0], [0], color='green', lw=2, label='Mean'),
                    plt.Rectangle((0, 0), 1, 1, facecolor='lightblue', alpha=0.7, label='IQR (Q1-Q3)')
                ]
                ax.legend(handles=legend_elements, loc='upper right')
                
                # Add individual data points as scatter plot
                y_positions = final_scores
                x_positions = [1] * len(final_scores)
                # Add some jitter to x-positions for better visibility
                x_jitter = np.random.normal(0, 0.02, len(final_scores))
                x_positions_jittered = [1 + jitter for jitter in x_jitter]
                
                ax.scatter(x_positions_jittered, y_positions, alpha=0.6, s=20, color='darkblue', zorder=10)
                
                # Adjust layout and save
                plt.tight_layout()
                
                # Save plot
                plot_filename = f'{clean_name}_quartile_plot.png'
                plot_path = os.path.join(plots_folder, plot_filename)
                plt.savefig(plot_path, dpi=300, bbox_inches='tight')
                plt.close()
                
                plot_count += 1
                
                # Log progress every 50 plots
                if plot_count % 50 == 0:
                    logger.info(f"Generated {plot_count} quartile plots so far...")
                    
            except Exception as e:
                logger.warning(f"Error creating quartile plot for video {video_name}: {e}")
                continue
        
        logger.info(f"Successfully generated {plot_count} quartile plots in: {plots_folder}")
        return plots_folder
    
    def generate_global_histogram(self, output_folder, prefix):
        """
        Generate a global histogram showing the distribution of average ratings per video.
        
        Args:
            output_folder (str): Base output folder path
            prefix (str): Prefix to add to filenames
        """
        logger.info("Generating global histogram of average video ratings...")
        
        # Collect average rating for each video
        video_averages = []
        video_stats = []
        
        for video_name, ratings in self.video_ratings.items():
            valid_scores = []
            
            for rating in ratings:
                if not rating['is_unset'] and rating['final_score'] is not None:
                    try:
                        score = float(rating['final_score'])
                        if 0 <= score <= 100:  # Valid score range
                            valid_scores.append(score)
                    except (ValueError, TypeError):
                        continue
            
            if len(valid_scores) > 0:
                avg_score = np.mean(valid_scores)
                video_averages.append(avg_score)
                video_stats.append({
                    'video_name': video_name,
                    'average': avg_score,
                    'count': len(valid_scores),
                    'std': np.std(valid_scores) if len(valid_scores) > 1 else 0
                })
        
        if len(video_averages) == 0:
            logger.warning("No valid video averages found for global histogram")
            return None
        
        # Create figure with larger size for better visibility
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Create histogram with appropriate bins
        n_bins = min(30, len(set([round(avg, 1) for avg in video_averages])))  # Adaptive bin count
        n, bins, patches = ax.hist(video_averages, bins=n_bins, 
                                  alpha=0.7, color='steelblue', 
                                  edgecolor='darkblue', linewidth=0.5)
        
        # Customize the plot
        ax.set_xlabel('Average Rating Score per Video (0-100)', fontsize=14)
        ax.set_ylabel('Number of Videos', fontsize=14)
        ax.set_title('Global Distribution of Average Video Ratings\n'
                    f'Total Videos: {len(video_averages):,} videos with valid ratings',
                    fontsize=16, fontweight='bold', pad=20)
        
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_xlim(0, 100)
        
        # Calculate and display statistics for video averages
        mean_avg = np.mean(video_averages)
        median_avg = np.median(video_averages)
        std_avg = np.std(video_averages)
        q1_avg = np.percentile(video_averages, 25)
        q3_avg = np.percentile(video_averages, 75)
        
        # Add vertical lines for key statistics
        ax.axvline(mean_avg, color='red', linestyle='--', linewidth=2, alpha=0.8, label=f'Mean: {mean_avg:.1f}')
        ax.axvline(median_avg, color='green', linestyle='--', linewidth=2, alpha=0.8, label=f'Median: {median_avg:.1f}')
        ax.axvline(q1_avg, color='orange', linestyle=':', linewidth=2, alpha=0.8, label=f'Q1: {q1_avg:.1f}')
        ax.axvline(q3_avg, color='purple', linestyle=':', linewidth=2, alpha=0.8, label=f'Q3: {q3_avg:.1f}')
        
        # Add statistics text box
        total_individual_ratings = sum(len([r for r in ratings if not r['is_unset'] and r['final_score'] is not None]) 
                                     for ratings in self.video_ratings.values())
        
        stats_text = (f'Video Statistics:\n'
                     f'Videos: {len(video_averages):,}\n'
                     f'Mean Avg: {mean_avg:.2f}\n'
                     f'Median Avg: {median_avg:.2f}\n'
                     f'Std Dev: {std_avg:.2f}\n'
                     f'Min Avg: {min(video_averages):.1f}\n'
                     f'Max Avg: {max(video_averages):.1f}\n'
                     f'Q1: {q1_avg:.1f}\n'
                     f'Q3: {q3_avg:.1f}\n'
                     f'IQR: {q3_avg-q1_avg:.1f}\n'
                     f'Total Ratings: {total_individual_ratings:,}')
        
        ax.text(0.98, 0.98, stats_text, transform=ax.transAxes, fontsize=11,
               verticalalignment='top', horizontalalignment='right',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9, pad=1))
        
        # Add legend
        ax.legend(loc='upper left', fontsize=10)
        
        # Color bars by value ranges for better visualization
        for i, (patch, bin_center) in enumerate(zip(patches, (bins[:-1] + bins[1:]) / 2)):
            if bin_center < 30:
                patch.set_facecolor('lightcoral')  # Low average scores
            elif bin_center < 70:
                patch.set_facecolor('lightyellow')  # Medium average scores
            else:
                patch.set_facecolor('lightgreen')  # High average scores
        
        # Adjust layout and save
        plt.tight_layout()
        
        # Save histogram
        histogram_path = os.path.join(output_folder, f'{prefix}_global_average_ratings_histogram.png')
        plt.savefig(histogram_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Successfully generated global histogram with {len(video_averages):,} video averages")
        logger.info(f"Average range: {min(video_averages):.1f} - {max(video_averages):.1f}")
        logger.info(f"Saved global histogram to: {histogram_path}")
        
        return histogram_path
    
    def save_results(self, output_folder=None):
        """
        Save the processed results to CSV files.
        
        Args:
            output_folder (str): Output folder path. If None, saves in same folder as input.
        """
        if output_folder is None:
            output_folder = os.path.dirname(self.input_folder)
        
        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Extract folder name from input_folder to use as prefix
        input_folder_name = os.path.basename(self.input_folder.rstrip('/'))
        logger.info(f"Using prefix from input folder: {input_folder_name}")
        
        # Create dedicated reports folder with input folder name prefix
        reports_folder = os.path.join(output_folder, f'{input_folder_name}_reports')
        os.makedirs(reports_folder, exist_ok=True)
        logger.info(f"Created reports folder: {reports_folder}")
        
        # Generate summaries
        video_summary = self.generate_video_ratings_summary()
        attribute_summary = self.generate_attribute_summary()
        
        # Separate videos by valid rating count (30+ vs less than 30)
        videos_30_plus = video_summary[video_summary['valid_ratings_count'] >= 30]
        videos_less_than_30 = video_summary[video_summary['valid_ratings_count'] < 30]
        
        # Save main video ratings summary (30+ valid ratings only)
        video_output_path = os.path.join(reports_folder, f'{input_folder_name}_video_final_ratings.csv')
        videos_30_plus.to_csv(video_output_path, index=False)
        logger.info(f"Saved video final ratings (30+ valid ratings) to: {video_output_path}")
        logger.info(f"Videos with 30+ valid ratings: {len(videos_30_plus)}")
        
        # Save videos with less than 30 valid ratings if any exist
        videos_less_30_path = None
        if len(videos_less_than_30) > 0:
            videos_less_30_path = os.path.join(reports_folder, f'{input_folder_name}_videos_less_than_30_valid_ratings.csv')
            videos_less_than_30.to_csv(videos_less_30_path, index=False)
            logger.info(f"Saved videos with <30 valid ratings to: {videos_less_30_path}")
            logger.info(f"Videos with <30 valid ratings: {len(videos_less_than_30)}")
        else:
            logger.info("All videos have 30+ valid ratings - no separate file needed for <30 valid ratings")
        
        # Save attribute counts summary (video_name, most_common_attributes, detailed_counts)
        # Filter attribute summary to match videos with 30+ valid ratings for main file
        attribute_30_plus = attribute_summary[attribute_summary['video_name'].isin(videos_30_plus['video_name'])]
        attribute_output_path = os.path.join(reports_folder, f'{input_folder_name}_video_attribute_counts.csv')
        attribute_30_plus.to_csv(attribute_output_path, index=False)
        logger.info(f"Saved video attribute counts (30+ valid ratings) to: {attribute_output_path}")
        
        # Save attribute counts for videos with <30 valid ratings if any exist
        attribute_less_30_path = None
        if len(videos_less_than_30) > 0:
            attribute_less_30 = attribute_summary[attribute_summary['video_name'].isin(videos_less_than_30['video_name'])]
            attribute_less_30_path = os.path.join(reports_folder, f'{input_folder_name}_video_attributes_less_than_30_valid_ratings.csv')
            attribute_less_30.to_csv(attribute_less_30_path, index=False)
            logger.info(f"Saved video attribute counts (<30 valid ratings) to: {attribute_less_30_path}")
        
        # Generate rating plots for all videos (conditionally)
        plots_folder = None
        if self.generate_box_plots:
            plots_folder = self.generate_rating_plots(reports_folder, input_folder_name)
            logger.info("Individual box plots generation: ENABLED")
        else:
            logger.info("Individual box plots generation: DISABLED")
        
        # Generate global histogram of all ratings
        histogram_path = self.generate_global_histogram(reports_folder, input_folder_name)
        
        # Generate and save processing report
        report_path = os.path.join(reports_folder, f'{input_folder_name}_processing_report.txt')
        with open(report_path, 'w') as f:
            f.write("Video Quality Assessment Processing Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Input folder: {self.input_folder}\n")
            f.write(f"Folder prefix: {input_folder_name}\n")
            f.write(f"Reports folder: {reports_folder}\n")
            f.write(f"Files processed: {len(self.processed_files)}\n")
            f.write(f"Processed files: {', '.join(self.processed_files)}\n\n")
            f.write(f"Total unique videos: {len(self.video_ratings)}\n")
            f.write(f"Total ratings collected: {sum(len(ratings) for ratings in self.video_ratings.values())}\n\n")
            
            # Video statistics
            f.write("Video Rating Statistics:\n")
            f.write("-" * 25 + "\n")
            rating_counts = [len(ratings) for ratings in self.video_ratings.values()]
            valid_rating_counts = [video_summary.loc[video_summary['video_name'] == video_name, 'valid_ratings_count'].iloc[0] 
                                  for video_name in self.video_ratings.keys()]
            f.write(f"Average total ratings per video: {sum(rating_counts) / len(rating_counts):.2f}\n")
            f.write(f"Average valid ratings per video: {sum(valid_rating_counts) / len(valid_rating_counts):.2f}\n")
            f.write(f"Max total ratings for a video: {max(rating_counts)}\n")
            f.write(f"Min total ratings for a video: {min(rating_counts)}\n")
            f.write(f"Max valid ratings for a video: {max(valid_rating_counts)}\n")
            f.write(f"Min valid ratings for a video: {min(valid_rating_counts)}\n")
            f.write(f"Videos with 30+ valid ratings: {len(videos_30_plus)}\n")
            f.write(f"Videos with <30 valid ratings: {len(videos_less_than_30)}\n\n")
            
            f.write("Output Files Generated (all in reports folder):\n")
            f.write("-" * 30 + "\n")
            f.write(f"1. {input_folder_name}_video_final_ratings.csv - Contains {len(videos_30_plus)} videos with 30+ valid ratings\n")
            f.write(f"2. {input_folder_name}_video_attribute_counts.csv - Contains attribute data for videos with 30+ valid ratings\n")
            
            file_counter = 3
            if len(videos_less_than_30) > 0:
                f.write(f"{file_counter}. {input_folder_name}_videos_less_than_30_valid_ratings.csv - Contains {len(videos_less_than_30)} videos with <30 valid ratings\n")
                file_counter += 1
                f.write(f"{file_counter}. {input_folder_name}_video_attributes_less_than_30_valid_ratings.csv - Contains attribute data for videos with <30 valid ratings\n")
                file_counter += 1
            
            if self.generate_box_plots:
                f.write(f"{file_counter}. {input_folder_name}_rating_plots/ - Folder containing {len(self.video_ratings)} quartile plots for individual video ratings\n")
                file_counter += 1
            
            f.write(f"{file_counter}. {input_folder_name}_global_average_ratings_histogram.png - Global histogram of average ratings per video\n")
        
        logger.info(f"Saved processing report to: {report_path}")
        
        # Return paths of all generated files and folders
        result_files = [video_output_path, attribute_output_path, histogram_path, report_path]
        if videos_less_30_path:
            result_files.extend([videos_less_30_path, attribute_less_30_path])
        if plots_folder:
            result_files.insert(-2, plots_folder)  # Insert before histogram and report
        
        logger.info(f"All output files saved in reports folder: {reports_folder}")
        return result_files


def main():
    """Main function to execute the video quality assessment processing."""
    batches = ['A','B','C','D','E','F','G','H','I','J','K','L']
    # batches = ['L']

    for batch in batches:
        input_folder = f"./parsing_codes_and_results/counts/batch{batch}_secondparse/approve_reject"
        # input_folder = "./parsing_codes_and_results/counts/batchB"
        
        # Set this to True to generate individual box plots for each video, False to skip them
        GENERATE_BOX_PLOTS = False  # Change this to False to disable individual box plot generation
        
        logger.info("Starting Video Quality Assessment Data Processing")
        logger.info(f"Input folder: {input_folder}")
        logger.info(f"Generate individual box plots: {GENERATE_BOX_PLOTS}")
        
        try:
            # Verify input folder exists
            if not os.path.exists(input_folder):
                raise FileNotFoundError(f"Input folder does not exist: {input_folder}")
            
            # Initialize processor
            processor = VideoQualityProcessor(input_folder, generate_box_plots=GENERATE_BOX_PLOTS)
            
            # Process all CSV files
            processor.process_all_files()
            
            # Save results
            result_files = processor.save_results()
            
            logger.info("Processing completed successfully!")
            logger.info(f"Output files generated:")
            for i, file_path in enumerate(result_files, 1):
                logger.info(f"  {i}. {os.path.basename(file_path)}: {file_path}")
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise


if __name__ == "__main__":
    main()
