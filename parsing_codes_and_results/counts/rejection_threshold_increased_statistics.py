import pandas as pd
import os
import numpy as np
import csv
import matplotlib.pyplot as plt

# Global lists for tracking rejections and assignments
rejected_reason = []
rejected_worker_id = []
rejected_hit_id = []
rejected_assgn_id = []
rejected_details = []
participated_worker_id = []

class VideoRatingParser:
    def __init__(self, csv_path, sample_csv, backup_csv, gold_csv, base_path, row_index=0, print_analysis=True):
        """Initialize parser with all required file paths"""
        self.csv_path = csv_path
        self.sample_csv = sample_csv
        self.backup_csv = backup_csv
        self.gold_csv = gold_csv
        self.base_path = base_path
        self.row_index = row_index
        self.print_analysis = print_analysis
        
        # Initialize data structures
        self.sample_records = []
        self.backup_records = []
        self.gold_records = []
        self.repeated_records = []
        self.true_scores = {}
        self.rejection_reasons = []
        self.should_reject = False
        
        # Video reporting functionality
        self.reported_videos = []
        self.reported_video_reasons = []
        
        # Rejection logging
        self.reject_log = {}
        
        # Define thresholds for statistical checks
        self.std_threshold = 5  # threshold for standard deviation of differences between initial and final values
        self.repeat_diff_threshold = 25 #30  # threshold for repeated scores difference
        self.gold_diff_threshold = 25 #30  # threshold for golden scores difference
        self.delay_threshold = 1.0  # threshold for delay
        
        # Define count thresholds
        self.max_repeat_exceed = 3  # maximum allowed repeated scores exceeding threshold
        self.max_gold_exceed = 2 # maximum allowed golden scores exceeding threshold
        self.max_delay_exceed = 40  # maximum allowed delays exceeding threshold
        self.max_same_pattern_count =50  # maximum allowed videos with same attribute pattern (50->18 (L) for other batches)
        self.max_unset_count = 24  # maximum allowed unset video ratings (24->8 (L) for other batches)
        # self.max_same_pattern_count =18  # maximum allowed videos with same attribute pattern (50->18 (L) for other batches)
        # self.max_unset_count = 8  # maximum allowed unset video ratings (24->8 (L) for other batches)
        self.printwithcount = True  # whether to print with count in rejection reasons
        # Define attribute mappings
        self.attribute_mappings = {
            'clarity': {
                'Highly Clear': 'a',
                'Moderately Clear': 'b',
                'Minimally Clear': 'c'
            },
            'artifacts': {
                'No visible artifacts': 'a',
                'Minor Artifacts Present': 'b',
                'Severe Artifacts Present': 'c'
            },
            'immersion': {
                'High level of immersion': 'a',
                'Moderate level of immersion': 'b',
                'Low level of immersion': 'c'
            }
        }
        
        # Initialize video index counter
        self.video_idx = 1
        
        # Load all data
        self._load_data()

    def _load_data(self):
        """Load all required data from CSV files"""
        # Load AMT results
        df = pd.read_csv(self.csv_path)
        self.row = df.iloc[self.row_index]
        
        # Load mapping files
        sample_map = pd.read_csv(self.sample_csv)
        backup_df = pd.read_csv(self.backup_csv)
        gold_df = pd.read_csv(self.gold_csv)
        
        # Load sample files from the first row of sample CSV
        self.sample_files = sample_map.iloc[0].tolist()
        print(f"Loaded {len(self.sample_files)} sample videos")
        
        # Load backup and gold files (these are typically the same for all HITs)
        self.backup_files = backup_df['backup_vids'].tolist()
        self.gold_files = gold_df['gold_vids'].tolist()

        # Load true scores for golden videos
        if 'true_score' in gold_df.columns:
            for _, row in gold_df.iterrows():
                self.true_scores[row['gold_vids']] = row['true_score']

    def initialize_rejection_log(self):
        """Initialize rejection log with assignment details"""
        self.reject_log = {
            'HIT_ID': self.row.get('HITId', 'unknown'),
            'Worker_ID': self.row.get('WorkerId', 'unknown'),
            'Assignment_ID': self.row.get('AssignmentId', 'unknown'),
            'Sample_Row_Name': 'row_0',
            'Sample_Row_Index': 0,
            'Unique_HIT_Index': 0,
            'Unset': 0,
            'Stalls': 0,
            'ConsSD': 0,
            'DiffSD': 0,
            'repeatDiffs': [],
            'Goldcount': 0,
            'goldDiffs': []
        }

    def parse_answer_entry(self, entry_str):
        """Parse a single answer entry string into structured data"""
        records = []
        if not isinstance(entry_str, str) or not entry_str.strip():
            return records

        for rec in entry_str.split(' | '):
            parts = rec.split('/')
            if len(parts) != 4:
                continue
                
            init_val, final_val, attr_str, delay = parts
            
            # Keep "unset" values as strings, convert others to float
            if init_val.strip() == 'unset':
                init_val = 'unset'
            else:
                try:
                    init_val = float(init_val)
                except ValueError:
                    init_val = 'unset'
            
            if final_val.strip() == 'unset':
                final_val = 'unset'
            else:
                try:
                    final_val = float(final_val)
                except ValueError:
                    final_val = 'unset'
            
            if delay.strip() == 'unset':
                delay = 'unset'
            else:
                try:
                    delay = float(delay)
                except ValueError:
                    delay = 'unset'
            
            # Handle attributes
            if attr_str.strip() == 'unset':
                attributes = ['unset']
            else:
                attributes = attr_str.split(',') if attr_str else []
            
            records.append({
                'init_val': init_val,
                'final_val': final_val,
                'attributes': attributes,
                'delay': delay
            })
        return records

    def process_all_videos(self):
        """Process all videos by iterating through Input.videos[x] and Answer.videos[x] columns"""
        # Get the lengths from each CSV file
        sample_df = pd.read_csv(self.sample_csv)
        backup_df = pd.read_csv(self.backup_csv)
        gold_df = pd.read_csv(self.gold_csv)
        
        # Get the number of videos from each CSV
        sample_row = sample_df.iloc[0]  # Use first row of sample CSV
        sample_length = len(sample_row)  # Number of columns in the sample row
        
        backup_length = len(backup_df)  # Number of rows in backup CSV
        gold_length = len(gold_df)      # Number of rows in gold CSV
        
        # Process sample videos (Answer.videos[1] to Answer.videos[sample_length])
        for video_num in range(1, sample_length + 1):
            input_col = f'Input.videos{video_num}'
            answer_col = f'Answer.videos{video_num}'
            
            if input_col in self.row.index and answer_col in self.row.index:
                input_video_name = self.row.get(input_col, '')
                answer_data = self.row.get(answer_col, '')
                
                # Handle "unset" case
                if answer_data.strip() == 'unset':
                    rec_main = {
                        'video_name': input_video_name, 
                        'category': 'sample',
                        'init_val': 'unset',
                        'final_val': 'unset',
                        'attributes': ['unset'],
                        'delay': 'unset'
                    }
                    self.sample_records.append(rec_main)
                else:
                    entries = self.parse_answer_entry(answer_data)
                    if entries:
                        first = entries[0]
                        rec_main = {'video_name': input_video_name, 'category': 'sample', **first}
                        self.sample_records.append(rec_main)
                        
                        if len(entries) > 1:
                            for rec in entries:
                                rec_rep = {'video_name': input_video_name, 'category': 'sample', **rec}
                                self.repeated_records.append(rec_rep)
            
            self.video_idx += 1
        
        # Process backup videos (Answer.videos[sample_length+1] to Answer.videos[sample_length+backup_length])
        for i, backup_video_name in enumerate(self.backup_files):
            video_num = sample_length + 1 + i
            answer_col = f'Answer.videos{video_num}'
            
            if answer_col in self.row.index:
                answer_data = self.row.get(answer_col, '')
                
                # Handle "unset" case
                if answer_data.strip() == 'unset':
                    rec_main = {
                        'video_name': backup_video_name, 
                        'category': 'backup',
                        'init_val': 'unset',
                        'final_val': 'unset',
                        'attributes': ['unset'],
                        'delay': 'unset'
                    }
                    self.backup_records.append(rec_main)
                else:
                    entries = self.parse_answer_entry(answer_data)
                    if entries:
                        first = entries[0]
                        rec_main = {'video_name': backup_video_name, 'category': 'backup', **first}
                        self.backup_records.append(rec_main)
                        
                        if len(entries) > 1:
                            for rec in entries:
                                rec_rep = {'video_name': backup_video_name, 'category': 'backup', **rec}
                                self.repeated_records.append(rec_rep)
            
            self.video_idx += 1
        
        # Process gold videos (Answer.videos[sample_length+backup_length+1] to Answer.videos[sample_length+backup_length+gold_length])
        for i, gold_video_name in enumerate(self.gold_files):
            video_num = sample_length + backup_length + 1 + i
            answer_col = f'Answer.videos{video_num}'
            
            if answer_col in self.row.index:
                answer_data = self.row.get(answer_col, '')
                
                # Handle "unset" case
                if answer_data.strip() == 'unset':
                    rec_main = {
                        'video_name': gold_video_name, 
                        'category': 'gold',
                        'init_val': 'unset',
                        'final_val': 'unset',
                        'attributes': ['unset'],
                        'delay': 'unset'
                    }
                    self.gold_records.append(rec_main)
                else:
                    entries = self.parse_answer_entry(answer_data)
                    if entries:
                        first = entries[0]
                        rec_main = {'video_name': gold_video_name, 'category': 'gold', **first}
                        self.gold_records.append(rec_main)
                        
                        if len(entries) > 1:
                            for rec in entries:
                                rec_rep = {'video_name': gold_video_name, 'category': 'gold', **rec}
                                self.repeated_records.append(rec_rep)
            
            self.video_idx += 1

    def analyze_sample_videos(self):
        """Analyze sample videos for initial-final differences and final value statistics"""
        if not self.sample_records:
            return None, None, None

        # Filter out records with "unset" values for analysis
        valid_records = []
        for record in self.sample_records:
            if (record['init_val'] != 'unset' and record['final_val'] != 'unset' and 
                isinstance(record['init_val'], (int, float)) and isinstance(record['final_val'], (int, float))):
                valid_records.append(record)
        
        if not valid_records:
            return None, None, None

        # Calculate differences between initial and final values
        differences = [abs(record['final_val'] - record['init_val']) for record in valid_records]
        std_diff = np.std(differences)  # Standard deviation of differences
        
        # Calculate statistics for final values
        final_values = [record['final_val'] for record in valid_records]
        final_std = np.std(final_values)
        final_mean = np.mean(final_values)
        
        return std_diff, final_std, final_mean

    def analyze_repeated_videos(self):
        """Analyze differences between repeated video ratings"""
        video_scores = {}
        for record in self.repeated_records:
            # Skip records with "unset" values
            if record['final_val'] == 'unset' or not isinstance(record['final_val'], (int, float)):
                continue
                
            video_name = record['video_name']
            if video_name not in video_scores:
                video_scores[video_name] = []
            video_scores[video_name].append(record['final_val'])

        differences = {}
        for video_name, scores in video_scores.items():
            if len(scores) > 1:
                diff = abs(scores[0] - scores[1])
                differences[video_name] = {
                    'scores': scores,
                    'difference': diff
                }
        return differences

    def analyze_golden_videos(self):
        """Analyze differences between rated and true scores for golden videos"""
        differences = {}
        for record in self.gold_records:
            # Skip records with "unset" values
            if record['final_val'] == 'unset' or not isinstance(record['final_val'], (int, float)):
                continue
                
            video_name = record['video_name']
            if video_name in self.true_scores:
                rated_score = record['final_val']
                true_score = self.true_scores[video_name]
                diff = abs(rated_score - true_score)
                differences[video_name] = {
                    'rated_score': rated_score,
                    'true_score': true_score,
                    'difference': diff
                }
        return differences

    def save_results(self):
        """Save all results to CSV files"""
        # Get worker ID, HIT ID, and Assignment ID
        worker_id = self.row.get('WorkerId', 'unknown')
        hit_id = self.row.get('HITId', 'unknown')
        assignment_id = self.row.get('AssignmentId', 'unknown')
        
        # Extract batch name from sample_csv path
        batch_name = os.path.splitext(os.path.basename(self.sample_csv))[0]
        
        # Create base directory with batch name using the provided base_path
        base_dir = os.path.join(self.base_path, f'parsed_{batch_name}/')
        os.makedirs(base_dir, exist_ok=True)
        
        # Create worker-specific directory with HIT ID and Assignment ID
        worker_dir = os.path.join(base_dir, f'hit_{hit_id}_worker_{worker_id}_assignment_{assignment_id}')
        os.makedirs(worker_dir, exist_ok=True)
        
        # Save all CSVs in the worker directory
        pd.DataFrame(self.sample_records).to_csv(os.path.join(worker_dir, 'sample_ratings.csv'), index=False)
        pd.DataFrame(self.backup_records).to_csv(os.path.join(worker_dir, 'backup_ratings.csv'), index=False)
        pd.DataFrame(self.gold_records).to_csv(os.path.join(worker_dir, 'gold_ratings.csv'), index=False)
        pd.DataFrame(self.repeated_records).to_csv(os.path.join(worker_dir, 'repeated_ratings.csv'), index=False)
        
        # Save worker's comments to a separate CSV file
        comments = self.row.get('Answer.Comments', '')
        comments_df = pd.DataFrame({'Comments': [comments]})
        comments_df.to_csv(os.path.join(worker_dir, 'worker_comments.csv'), index=False)
        
        # Save mapping information
        mapping_info = {
            'hit_id': hit_id,
            'worker_id': worker_id,
            'assignment_id': assignment_id,
            'sample_files_count': len(self.sample_files),
            'backup_files_count': len(self.backup_files),
            'gold_files_count': len(self.gold_files)
        }
        mapping_df = pd.DataFrame([mapping_info])
        mapping_df.to_csv(os.path.join(worker_dir, 'mapping_info.csv'), index=False)
        
        # Create and save histogram of final values from sample ratings
        if self.sample_records:
            # Filter out 'unset' values for histogram
            final_values = []
            for record in self.sample_records:
                if record['final_val'] != 'unset' and isinstance(record['final_val'], (int, float)):
                    final_values.append(record['final_val'])
            
            if final_values:
                plt.figure(figsize=(10, 6))
                plt.hist(final_values, bins=20, edgecolor='black', alpha=0.7)
                plt.xlabel('Final Rating Values')
                plt.ylabel('Frequency')
                plt.title(f'Sample Ratings Histogram - Worker {worker_id}')
                plt.grid(True, alpha=0.3)
                plt.tight_layout()
                plt.savefig(os.path.join(worker_dir, 'sample_ratings_histogram.png'), dpi=300, bbox_inches='tight')
                plt.close()
        
        print(f"\nSaved worker {worker_id}'s results to {worker_dir}")

    def print_analysis(self):
        """Print analysis of sample, repeated and golden videos"""
        # Analyze sample videos
        std_diff, final_std, final_mean = self.analyze_sample_videos()
        print("\nAnalysis of Sample Videos:")
        print("-" * 80)
        if std_diff is not None:
            print(f"Standard deviation of differences between initial and final values: {std_diff:.2f}")
            print(f"Final values - Mean: {final_mean:.2f}, Standard Deviation: {final_std:.2f}")
        print("\n" + "-" * 80)

        # Analyze repeated videos
        repeated_diffs = self.analyze_repeated_videos()
        print("\nAnalysis of Repeated Videos:")
        print("-" * 80)
        for video_name, stats in repeated_diffs.items():
            print(f"\nVideo: {video_name}")
            print(f"Scores: {[f'{s:.2f}' for s in stats['scores']]}")
            print(f"Absolute Difference: {stats['difference']:.2f}")
        print("\n" + "-" * 80)

        # Analyze golden videos
        golden_diffs = self.analyze_golden_videos()
        print("\nAnalysis of Golden Videos:")
        print("-" * 80)
        for video_name, stats in golden_diffs.items():
            print(f"\nVideo: {video_name}")
            print(f"Rated Score: {stats['rated_score']:.2f}")
            print(f"True Score: {stats['true_score']:.2f}")
            print(f"Absolute Difference: {stats['difference']:.2f}")
        print("\n" + "-" * 80)

        # Print reported videos
        if self.reported_videos:
            print("\nReported Videos:")
            print("-" * 80)
            for i, video in enumerate(self.reported_videos):
                print(f"Video: {video}")
                print(f"Reason: {self.reported_video_reasons[i]}")
            print("\n" + "-" * 80)

    def check_basic_rejections(self):
        """Check for basic rejection criteria"""
        try:
            # Check device type
            if self.row.get('Answer.display') in ['Phone', 'Tablet']:
                self.rejection_reasons.append('Used phone or tablet')
                self.should_reject = True

            # Check debug info
            if self.row.get('Answer.debugInfo') == 'unset':
                self.rejection_reasons.append('No Debug info')
                self.should_reject = True

            # Check lens usage
            if self.row.get('Answer.lens') == 'Yes' and self.row.get('Answer.wearlens') == 'No':
                self.rejection_reasons.append('Did not wear lens')
                self.should_reject = True  # Commented out as in reference

            # Check for unset values in video ratings
            unset_count = 0
            total_videos = len(self.sample_files) + len(self.backup_files) + len(self.gold_files)
            
            for i in range(1, total_videos + 1):  # Check all video entries
                video_key = f'Answer.videos{i}'
                if video_key in self.row and self.row[video_key] == 'unset':
                    unset_count += 1
            
            self.reject_log['Unset'] = unset_count
            print(f"DEBUG: Unset count = {unset_count}, threshold = {self.max_unset_count}, should reject = {unset_count > self.max_unset_count}")
            if unset_count > self.max_unset_count:  # More than 6 unset video ratings

                if self.printwithcount:
                    self.rejection_reasons.append(f'Too many unset video ratings ({unset_count} > {self.max_unset_count})')
                else:
                    self.rejection_reasons.append(f'Too many unset video ratings, this could be due to not using latest version of the browser or not using the correct browser. Please use latest version of Chrome browser.')
                self.should_reject = True  # Enable unset count rejection

        except Exception as e:
            print('Error in collected data: possibly worker didnt submit all the data and used bot!')
            print("Rejecting Submission")
            self.rejection_reasons.append('Missing or invalid data submission')
            self.should_reject = True

    def check_statistical_rejections(self):
        """Check for statistical rejection criteria"""
        # 1. Check standard deviation between initial and final values in sample videos (test videos)
        if self.sample_records:
            # std_diff is the standard deviation of differences between initial and final values
            # final_std is the standard deviation of final values
            std_diff, final_std, _ = self.analyze_sample_videos()
            
            # Check standard deviation of differences
            if std_diff < self.std_threshold:
                self.rejection_reasons.append(f'Low standard deviation of slider ratings, the slider was not moved much.')
                self.should_reject = True
                ###########################################
                # Add to blocked_violated_rejects.csv immediately
                ###########################################
                worker_id = self.row.get('WorkerId', 'unknown')
                block_file = './parsing_codes_and_results/block_subjects_rrrrr.csv'
                if not os.path.exists(block_file):
                    with open(block_file, 'w', newline='') as f:
                        writer = csv.writer(f, lineterminator='\n')
                        writer.writerow(['WorkerId'])
                        writer.writerow([worker_id])
                else:
                    existing_ids = set()
                    with open(block_file, newline='') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            existing_ids.add(row['WorkerId'])
                    if worker_id not in existing_ids:
                        with open(block_file, 'a', newline='') as f:
                            writer = csv.writer(f, lineterminator='\n')
                            writer.writerow([worker_id])

            # Check standard deviation of final scores
            if final_std < self.std_threshold:
                self.rejection_reasons.append(f'all slider ratings are very similar, the slider moved to same range of scores.')
                self.should_reject = True
                ###########################################
                # Add to blocked_violated_rejects.csv immediately
                worker_id = self.row.get('WorkerId', 'unknown')
                block_file = './parsing_codes_and_results/block_subjects_rrrrr.csv'
                if not os.path.exists(block_file):
                    with open(block_file, 'w', newline='') as f:
                        writer = csv.writer(f, lineterminator='\n')
                        writer.writerow(['WorkerId'])
                        writer.writerow([worker_id])
                else:
                    existing_ids = set()
                    with open(block_file, newline='') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            existing_ids.add(row['WorkerId'])
                    if worker_id not in existing_ids:
                        with open(block_file, 'a', newline='') as f:
                            writer = csv.writer(f, lineterminator='\n')
                            writer.writerow([worker_id])

        # 2. Check repeated scores
        repeat_exceed_count = 0
        repeated_diffs = self.analyze_repeated_videos()
        diffs = []
        for video_name, stats in repeated_diffs.items():
            diffs.append(stats['difference'])
            if stats['difference'] > self.repeat_diff_threshold:
                repeat_exceed_count += 1
        
        self.reject_log['repeatDiffs'] = diffs
        if repeat_exceed_count > self.max_repeat_exceed:
            if self.printwithcount:
                self.rejection_reasons.append(f'The scores for repeated videos are not consistent ({repeat_exceed_count} > {self.max_repeat_exceed})')
            else:
                self.rejection_reasons.append(f'The scores for repeated videos are not consistent.')

            self.should_reject = True

        # 3. Check golden scores
        gold_exceed_count = 0
        golden_diffs = self.analyze_golden_videos()
        gold_diffs = []
        gold_count = 0
        for video_name, stats in golden_diffs.items():
            gold_diffs.append(stats['difference'])
            gold_count += 1
            if stats['difference'] > self.gold_diff_threshold:
                gold_exceed_count += 1
        
        self.reject_log['Goldcount'] = gold_count
        self.reject_log['goldDiffs'] = gold_diffs
        if gold_exceed_count > self.max_gold_exceed:
            self.rejection_reasons.append(f'The scores for golden videos are not consistent with the true scores.')
            self.should_reject = True

        # 4. Check delays
        delay_exceed_count = 0
        all_records = self.sample_records + self.backup_records + self.gold_records
        for record in all_records:
            # Skip records with "unset" delay values
            if record.get('delay') == 'unset' or not isinstance(record.get('delay'), (int, float)):
                continue
                
            # Get the delay value from the record
            delay = float(record.get('delay', 0))
            if delay > self.delay_threshold:
                delay_exceed_count += 1
        
        self.reject_log['Stalls'] = delay_exceed_count
        if delay_exceed_count > self.max_delay_exceed:
            if self.printwithcount:
                self.rejection_reasons.append(f'The delays in video ratings are too high ({delay_exceed_count} > {self.max_delay_exceed})')
            else:
                self.rejection_reasons.append(f'The delays in video ratings are too high.')

            self.should_reject = True

        # 5. Calculate and log standard deviations
        if self.sample_records:
            # Filter out "unset" values for calculations
            valid_records = []
            for record in self.sample_records:
                if (record['final_val'] != 'unset' and record['init_val'] != 'unset' and 
                    isinstance(record['final_val'], (int, float)) and isinstance(record['init_val'], (int, float))):
                    valid_records.append(record)
            
            if valid_records:
                final_values = [record['final_val'] for record in valid_records]
                differences = [abs(record['final_val'] - record['init_val']) for record in valid_records]
                
                self.reject_log['ConsSD'] = np.std(final_values)
                self.reject_log['DiffSD'] = np.mean(differences)
            else:
                self.reject_log['ConsSD'] = 0
                self.reject_log['DiffSD'] = 0

    def check_attribute_patterns(self):
        """Check for suspicious patterns in attribute ratings across all three attributes"""
        all_records = self.sample_records + self.backup_records + self.gold_records
        pattern_counts = {}  # Dictionary to store counts of each pattern
        
        print(f"DEBUG: Checking patterns with max_same_pattern_count = {self.max_same_pattern_count}")
        print(f"DEBUG: Total records to check = {len(all_records)}")
        
        for record in all_records:
            # Skip if no attributes or if attributes contain "unset"
            if not record.get('attributes') or 'unset' in record['attributes']:
                continue
                
            # Create pattern key from attributes
            pattern = []
            for attr_type, mapping in self.attribute_mappings.items():
                found = False
                for attr in record['attributes']:
                    if attr in mapping:
                        pattern.append(mapping[attr])
                        found = True
                        break
                if not found:
                    pattern.append('?')  # Use '?' for missing attributes
            
            # Convert pattern to string key
            pattern_key = ''.join(pattern)
            
            # Count pattern occurrences
            pattern_counts[pattern_key] = pattern_counts.get(pattern_key, 0) + 1
        
        print(f"DEBUG: Pattern counts = {pattern_counts}")
        
        # Check for suspicious patterns
        for pattern, count in pattern_counts.items():
            if count > self.max_same_pattern_count:
                # Convert pattern back to readable format
                clarity = {'a': 'Highly Clear', 'b': 'Moderately Clear', 'c': 'Minimally Clear'}.get(pattern[0], 'Unknown')
                artifacts = {'a': 'No visible artifacts', 'b': 'Minor Artifacts Present', 'c': 'Severe Artifacts Present'}.get(pattern[1], 'Unknown')
                immersion = {'a': 'High level of immersion', 'b': 'Moderate level of immersion', 'c': 'Low level of immersion'}.get(pattern[2], 'Unknown')
                
                print(f"DEBUG: Pattern rejection triggered: {pattern} with count {count} > {self.max_same_pattern_count}")
                if self.printwithcount:
                    self.rejection_reasons.append(
                        f'Too many videos rated with same pattern: Clarity={clarity}, '
                        f'Artifacts={artifacts}, Immersion={immersion} with count={count}'
                    )
                else:
                    self.rejection_reasons.append(
                        f'Too many videos rated with same pattern: Clarity={clarity}, '
                        f'Artifacts={artifacts}, Immersion={immersion}'
                    )
                self.should_reject = True
                break

    def process_all(self):
        """Process all categories and perform analysis"""
        # Initialize rejection log
        self.initialize_rejection_log()
        
        # Add worker to participated list
        participated_worker_id.append(self.row.get('WorkerId', 'unknown'))
        
        # Reset video index counter
        self.video_idx = 1
        
        # Process all videos once and categorize them
        self.process_all_videos()

        # Check for basic rejections
        self.check_basic_rejections()
        
        # Check for statistical rejections
        self.check_statistical_rejections()
        
        # Check for attribute pattern rejections
        self.check_attribute_patterns()
        
        if self.should_reject:
            print("\nSubmission should be rejected for the following reasons:")
            print(f"WorkerID: {self.row.get('WorkerId', 'N/A')}")
            print(f"HITID: {self.row.get('HITId', 'N/A')}")
            print(f"AssignmentID: {self.row.get('AssignmentId', 'N/A')}")
            for reason in self.rejection_reasons:
                print(f"- {reason}")
            
            # Add to global rejection lists
            rejected_worker_id.append(self.row.get('WorkerId', 'unknown'))
            rejected_hit_id.append(self.row.get('HITId', 'unknown'))
            rejected_assgn_id.append(self.row.get('AssignmentId', 'unknown'))
            rejected_reason.append(' | '.join(self.rejection_reasons))
            rejected_details.append(self.reject_log.copy())
            
            return False, ' | '.join(self.rejection_reasons)

        # Print analysis
        if self.print_analysis:
            self.print_analysis()

        # Save results
        self.save_results()
        print("\nCSVs written: sample_ratings.csv, backup_ratings.csv, gold_ratings.csv, repeated_ratings.csv")

        # Collect reported videos
        self.collect_reported_videos()
        self.save_reported_videos()

        return True, None

    def collect_reported_videos(self):
        """Collect videos that were reported by the worker"""
        # Check for reported videos in the worker's response
        # This assumes the MTurk interface has a way for workers to report problematic videos
        # The exact field name may need to be adjusted based on your MTurk interface
        
        # Check for reported videos field
        reported_videos_field = self.row.get('Answer.reportedVideos', '')
        if reported_videos_field and reported_videos_field != 'unset':
            # Parse reported videos (assuming format: "video1.mp4:reason1|video2.mp4:reason2")
            for report in reported_videos_field.split('|'):
                if ':' in report:
                    video_name, reason = report.split(':', 1)
                    self.reported_videos.append(video_name.strip())
                    self.reported_video_reasons.append(reason.strip())
        
        # Also check for individual video report fields if they exist
        for i in range(1, 110):  # Check up to 100 video entries
            report_key = f'Answer.videoReport{i}'
            if report_key in self.row and self.row[report_key] not in ['unset', '', None]:
                # Extract video name from the report
                video_name = f"video_{i}.mp4"  # This may need adjustment based on actual video naming
                reason = self.row[report_key]
                self.reported_videos.append(video_name)
                self.reported_video_reasons.append(reason)

    def save_reported_videos(self):
        """Save reported videos to CSV file"""
        if not self.reported_videos:
            return
            
        # Extract batch name from sample_csv path
        batch_name = os.path.splitext(os.path.basename(self.sample_csv))[0]
        
        # Create base directory with batch name using the provided base_path
        base_dir = os.path.join(self.base_path, f'parsed_{batch_name}/')
        os.makedirs(base_dir, exist_ok=True)
        
        # Define reported videos file path
        reported_videos_file = os.path.join(base_dir, 'reported_videos.csv')
        
        # Check if file exists
        file_exists = os.path.isfile(reported_videos_file)
        
        if not file_exists:
            # Create new file with headers
            with open(reported_videos_file, mode='w', newline='') as csv_file:
                fieldnames = ['Video', 'Reason', 'WorkerID', 'HITID']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames, lineterminator='\n')
                writer.writeheader()
                
                # Write reported videos
                worker_id = self.row.get('WorkerId', 'unknown')
                hit_id = self.row.get('HITId', 'unknown')
                for i in range(len(self.reported_videos)):
                    writer.writerow({
                        'Video': self.reported_videos[i], 
                        'Reason': self.reported_video_reasons[i],
                        'WorkerID': worker_id,
                        'HITID': hit_id
                    })
        else:
            # Read existing file to check for duplicates
            existing_videos = []
            with open(reported_videos_file, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    existing_videos.append(row['Video'])
            
            # Append new reported videos (avoiding duplicates)
            worker_id = self.row.get('WorkerId', 'unknown')
            hit_id = self.row.get('HITId', 'unknown')
            with open(reported_videos_file, mode='a', newline='') as csv_file:
                fieldnames = ['Video', 'Reason', 'WorkerID', 'HITID']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames, lineterminator='\n')
                
                for i in range(len(self.reported_videos)):
                    if self.reported_videos[i] not in existing_videos:
                        writer.writerow({
                            'Video': self.reported_videos[i], 
                            'Reason': self.reported_video_reasons[i],
                            'WorkerID': worker_id,
                            'HITID': hit_id
                        })
        
        if self.reported_videos:
            print(f"\n📝 Saved {len(self.reported_videos)} reported videos to {reported_videos_file}")

def calculate_rejection_percentages(
    base_path,
    batch_name,
    total_submissions,
    total_rejections_override=None,
    rejection_counts_override=None,
):
    """
    Calculate rejection percentage for each rejection reason.
    If an assignment has multiple rejection reasons, it's counted as 'multiple_reasons'.
    Saves results to CSV file.
    
    Args:
        base_path (str): Base path where results are stored
        batch_name (str): Name of the batch being processed
        total_submissions (int): Total submissions processed (approved + rejected)
    
    Args:
        total_rejections_override (int | None): If provided, use this rejected count instead of
            summing counts from rejected_reason. Useful to keep totals consistent with
            the already-computed HIT-level stats.
        rejection_counts_override (dict | None): If provided, use this pre-counted
            breakdown (reason -> count) instead of deriving from rejected_reason list.

    Returns:
        pd.DataFrame: DataFrame with rejection percentages
    """
    # Check if rejected_reason list exists and has data
    if not rejected_reason:
        print("⚠️ No rejection data available to calculate percentages")
        return None
    
    # Initialize counters
    rejection_counts = {} if rejection_counts_override is None else dict(rejection_counts_override)
    
    # Process each rejection entry (only if not overridden)
    if rejection_counts_override is None:
        for reason_str in rejected_reason:
            if not reason_str or reason_str.strip() == '':
                # This is an approval, not a rejection
                continue
            
            # Split by ' | ' to get individual rejection reasons
            reasons = [r.strip() for r in reason_str.split(' | ') if r.strip()]
            
            # Normalize reasons - consolidate variants
            normalized_reasons = []
            for reason in reasons:
                if reason.startswith("Too many videos rated with same pattern:"):
                    normalized_reasons.append("Too many videos rated with same pattern:")
                elif reason.startswith("Too many unset video ratings"):
                    normalized_reasons.append("Too many unset video ratings")
                elif reason.startswith("The delays in video ratings are too high"):
                    normalized_reasons.append("The delays in video ratings are too high")
                else:
                    normalized_reasons.append(reason)
            
            if len(normalized_reasons) > 1:
                # Multiple rejection reasons
                reason_key = 'multiple_reasons'
                rejection_counts[reason_key] = rejection_counts.get(reason_key, 0) + 1
            elif len(normalized_reasons) == 1:
                # Single rejection reason
                reason_key = normalized_reasons[0]
                rejection_counts[reason_key] = rejection_counts.get(reason_key, 0) + 1
    
    # Calculate total rejections (optionally override to keep parity with HIT counts)
    total_rejections = total_rejections_override if total_rejections_override is not None else sum(rejection_counts.values())
    
    # Calculate percentages
    rejection_data = []
    for reason, count in sorted(rejection_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_rejections * 100) if total_rejections > 0 else 0
        percentage_of_total = (count / total_submissions * 100) if total_submissions > 0 else 0
        rejection_data.append({
            'Rejection_Reason': reason,
            'Count': count,
            'Percentage_of_Rejections': round(percentage, 2),
            'Percentage_of_Total_Submissions': round(percentage_of_total, 2)
        })
    
    # Create DataFrame
    df_rejection_stats = pd.DataFrame(rejection_data)
    
    # Add summary row
    summary_row = {
        'Rejection_Reason': 'TOTAL',
        'Count': total_rejections,
        'Percentage_of_Rejections': 100.0,
        'Percentage_of_Total_Submissions': round((total_rejections / total_submissions * 100) if total_submissions > 0 else 0, 2)
    }
    df_rejection_stats = pd.concat([df_rejection_stats, pd.DataFrame([summary_row])], ignore_index=True)
    
    # Save to CSV
    base_dir = os.path.join(base_path, f'parsed_{batch_name}/')
    os.makedirs(base_dir, exist_ok=True)
    
    output_file = os.path.join(base_dir, 'rejection_reason_percentages.csv')
    df_rejection_stats.to_csv(output_file, index=False)
    
    print(f"\n📊 Rejection Percentage Statistics:")
    print(f"   Total Submissions: {total_submissions}")
    print(f"   Total Rejections: {total_rejections}")
    print(f"   Overall Rejection Rate: {(total_rejections / total_submissions * 100):.2f}%")
    print(f"\n📁 Saved rejection percentage statistics to: {output_file}")
    
    # Print the statistics table
    print("\n" + "="*80)
    print("REJECTION REASON BREAKDOWN")
    print("="*80)
    print(df_rejection_stats.to_string(index=False))
    print("="*80)
    
    return df_rejection_stats

def save_comprehensive_results(batch_name, base_path, clear_existing=False):
    """Save comprehensive results including rejection details, worker history, and AMT files"""
    # Create base directory using the provided base_path
    base_dir = os.path.join(base_path, f'parsed_{batch_name}/')
    os.makedirs(base_dir, exist_ok=True)
    
    # 1. Detailed Rejection File
    rejection_file_path = os.path.join(base_dir, 'rejection_details.csv')
    file_exists = os.path.isfile(rejection_file_path)
    if file_exists and clear_existing:
        os.remove(rejection_file_path)
        file_exists = False

    if not file_exists and rejected_details:
        with open(rejection_file_path, mode='w', newline='') as csv_file:
            fieldnames = list(rejected_details[0].keys())
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, lineterminator='\n')
            writer.writeheader()
            for reject_log in rejected_details:
                writer.writerow(reject_log)
    elif file_exists and rejected_details:
        existing_ids = []
        with open(rejection_file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_ids.append(row['Assignment_ID'])
        with open(rejection_file_path, mode='a', newline='') as csv_file:
            fieldnames = list(rejected_details[0].keys())
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, lineterminator='\n')
            for reject_log in rejected_details:
                if reject_log['Assignment_ID'] not in existing_ids:
                    writer.writerow(reject_log)
    
    print(f"📊 Detailed rejection file saved: {rejection_file_path}")

    # 2. AMT Approval/Rejection File
    amt_file_path = os.path.join(base_dir, 'rejection_amt_file.csv')
    file_exists = os.path.isfile(amt_file_path)
    if file_exists and clear_existing:
        os.remove(amt_file_path)
        file_exists = False

    if not file_exists:
        with open(amt_file_path, mode='w', newline='') as csv_file:
            fieldnames = ['AssignmentId', 'HITId', 'WorkerId', 'Sample_Row_Name', 'Sample_Row_Index', 'Approve', 'Reject']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, lineterminator='\n')
            writer.writeheader()
            for i in range(len(rejected_assgn_id)):
                # Get sample row information from rejection details
                sample_row_name = "unknown"
                sample_row_index = 0
                for reject_log in rejected_details:
                    if reject_log['Assignment_ID'] == rejected_assgn_id[i]:
                        sample_row_name = reject_log.get('Sample_Row_Name', 'unknown')
                        sample_row_index = reject_log.get('Sample_Row_Index', 0)
                        break
                
                writer.writerow({
                    'HITId': rejected_hit_id[i], 
                    'AssignmentId': rejected_assgn_id[i],
                    'WorkerId': rejected_worker_id[i],
                    'Sample_Row_Name': sample_row_name,
                    'Sample_Row_Index': sample_row_index,
                    'Reject': rejected_reason[i]
                })
    else:
        existing_ids = []
        with open(amt_file_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_ids.append(row['AssignmentId'])
        with open(amt_file_path, mode='a', newline='') as csv_file:
            fieldnames = ['AssignmentId', 'HITId', 'WorkerId', 'Sample_Row_Name', 'Sample_Row_Index', 'Approve', 'Reject']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, lineterminator='\n')
            for i in range(len(rejected_assgn_id)):
                if rejected_assgn_id[i] not in existing_ids:
                    # Get sample row information from rejection details
                    sample_row_name = "unknown"
                    sample_row_index = 0
                    for reject_log in rejected_details:
                        if reject_log['Assignment_ID'] == rejected_assgn_id[i]:
                            sample_row_name = reject_log.get('Sample_Row_Name', 'unknown')
                            sample_row_index = reject_log.get('Sample_Row_Index', 0)
                            break
                    
                    writer.writerow({
                        'HITId': rejected_hit_id[i], 
                        'AssignmentId': rejected_assgn_id[i],
                        'WorkerId': rejected_worker_id[i],
                        'Sample_Row_Name': sample_row_name,
                        'Sample_Row_Index': sample_row_index,
                        'Reject': rejected_reason[i]
                    })
    
    print(f"📊 AMT rejection file saved: {amt_file_path}")

    # 3. Worker Rejection History
    rejection_update_file = os.path.join(base_dir, 'rejection_update.csv')
    rejection_history_file = os.path.join(base_path, 'rejection_history.csv')
    
    # Load or create rejection update dataframe
    file_exists = os.path.isfile(rejection_update_file)
    if file_exists and clear_existing:
        os.remove(rejection_update_file)
        file_exists = False

    if file_exists:
        df_reject_update = pd.read_csv(rejection_update_file, index_col='WorkerId')
    else:
        df_reject_update = pd.DataFrame(columns=['AssignmentId', 'Reasons', 'Rejections', 'WorkerId'])
        df_reject_update.set_index('WorkerId', inplace=True)

    # Load or create rejection history
    history_exists = os.path.isfile(rejection_history_file)
    if history_exists:
        df_rejection_history = pd.read_csv(rejection_history_file, index_col='WorkerId')
    else:
        df_rejection_history = pd.DataFrame(columns=['AssignmentId', 'Reasons', 'Rejections', 'WorkerId'])
        df_rejection_history.set_index('WorkerId', inplace=True)

    # Update rejection history for each rejected worker
    print(f"DEBUG: Processing {len(rejected_worker_id)} rejections for rejection history update")
    
    if len(rejected_worker_id) == 0:
        print("DEBUG: No rejections to process for rejection history update")
    else:
        for worker_id, assignment_id, reason in zip(rejected_worker_id, rejected_assgn_id, rejected_reason):
            print(f"DEBUG: Updating rejection history for worker {worker_id}, assignment {assignment_id}")
            
            # Update the rejection_update dataframe
            if worker_id in df_reject_update.index:
                df_reject_update.loc[worker_id, 'AssignmentId'] += '/' + assignment_id
                df_reject_update.loc[worker_id, 'Reasons'] += reason
            elif worker_id in df_rejection_history.index:
                df_reject_update.loc[worker_id, 'AssignmentId'] = df_rejection_history.loc[worker_id, 'AssignmentId'] + '/' + assignment_id
                df_reject_update.loc[worker_id, 'Reasons'] = df_rejection_history.loc[worker_id, 'Reasons'] + reason
            else:
                df_reject_update.loc[worker_id, 'AssignmentId'] = assignment_id
                df_reject_update.loc[worker_id, 'Reasons'] = reason

            df_reject_update.loc[worker_id, 'Rejections'] = len(df_reject_update.loc[worker_id, 'AssignmentId'].split('/'))
            
            # Also update the main rejection_history dataframe
            if worker_id in df_rejection_history.index:
                df_rejection_history.loc[worker_id, 'AssignmentId'] += '/' + assignment_id
                df_rejection_history.loc[worker_id, 'Reasons'] += reason
            else:
                df_rejection_history.loc[worker_id, 'AssignmentId'] = assignment_id
                df_rejection_history.loc[worker_id, 'Reasons'] = reason

            df_rejection_history.loc[worker_id, 'Rejections'] = len(df_rejection_history.loc[worker_id, 'AssignmentId'].split('/'))

    # Save both files
    df_reject_update.sort_values('Rejections', inplace=True)
    df_reject_update.to_csv(rejection_update_file, index_label='WorkerId')
    
    df_rejection_history.sort_values('Rejections', inplace=True)
    df_rejection_history.to_csv(rejection_history_file, index_label='WorkerId')
    
    print(f"📊 Worker rejection history saved: {rejection_update_file}")
    print(f"📊 Main rejection history updated: {rejection_history_file}")

    # 4. Create empty blocked rejects file
    blocked_file = os.path.join(base_dir, 'blocked_rejects.csv')
    if not os.path.exists(blocked_file) or clear_existing:
        df_blocked = pd.DataFrame(columns=df_reject_update.columns)
        df_blocked.to_csv(blocked_file, index_label='WorkerId')
        print(f"📊 Empty blocked rejects file created: {blocked_file}")

    # 5. Participants file
    participants_file = os.path.join(base_dir, 'participants.csv')
    participated_worker_id_unique = list(dict.fromkeys(participated_worker_id))
    
    file_exists = os.path.isfile(participants_file)
    if file_exists and clear_existing:
        os.remove(participants_file)
        file_exists = False

    if not file_exists:
        with open(participants_file, mode='w', newline='') as csv_file:
            fieldnames = ['Joined']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, lineterminator='\n')
            writer.writeheader()
            for worker_id in participated_worker_id_unique:
                writer.writerow({'Joined': worker_id})
    else:
        existing_ids = []
        with open(participants_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                existing_ids.append(row['Joined'])
        with open(participants_file, mode='a', newline='') as csv_file:
            fieldnames = ['Joined']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, lineterminator='\n')
            for worker_id in participated_worker_id_unique:
                if worker_id not in existing_ids:
                    writer.writerow({'Joined': worker_id})
    
    print(f"📊 Participants file saved: {participants_file}")

def process_batch(csv_path, sample_csv, backup_csv, gold_csv, base_path=None, clear_existing=False, print_analysis=True):
    """Process all rows in the batch CSV and update approval/rejection columns"""
    # Set default base_path if not provided
    if base_path is None:
        base_path = os.path.dirname(csv_path)
    
    # Read the batch CSV
    df = pd.read_csv(csv_path)
    
    # Ensure Approve and Reject columns exist and are string dtype
    if 'Approve' not in df.columns:
        df['Approve'] = ''
    else:
        df['Approve'] = df['Approve'].astype(str)
    
    if 'Reject' not in df.columns:
        df['Reject'] = ''
    else:
        df['Reject'] = df['Reject'].astype(str)
    
    # Load sample CSV
    sample_df = pd.read_csv(sample_csv)
    print(f"Sample CSV has {len(sample_df)} rows")
    print(f"Batch CSV has {len(df)} rows")
    
    # Process each row
    for idx in range(len(df)):
        print(f"\nProcessing row {idx + 1}/{len(df)}")
        
        # Check assignment status before processing
        if 'AssignmentStatus' in df.columns:
            assignment_status = df.iloc[idx]['AssignmentStatus']
            if assignment_status not in ['Approved', 'Accepted', 'Rejected', 'Submitted']:
                print(f"Invalid assignment status: {assignment_status}")
                raise ValueError('Invalid assignment status!!')
        
        parser = VideoRatingParser(
            csv_path=csv_path,
            sample_csv=sample_csv,
            backup_csv=backup_csv,
            gold_csv=gold_csv,
            base_path=base_path,
            row_index=idx,
            print_analysis=print_analysis
        )
        
        approved, reject_reason = parser.process_all()
        
        if approved:
            df.at[idx, 'Approve'] = 'X'
            df.at[idx, 'Reject'] = ''  # Clear any existing rejection reason
        else:
            df.at[idx, 'Approve'] = ''  # Clear any existing approval
            df.at[idx, 'Reject'] = reject_reason
    
    # Save the updated CSV
    # Create approve_reject folder within base_path
    approve_reject_dir = os.path.join(base_path, 'approve_reject')
    os.makedirs(approve_reject_dir, exist_ok=True)
    
    # Save the approval CSV in the approve_reject folder
    csv_filename = os.path.basename(csv_path).replace('.csv', '_with_approval.csv')
    output_path = os.path.join(approve_reject_dir, csv_filename)
    df.to_csv(output_path, index=False)
    print(f"\nSaved results to {output_path}")
    
    # Save comprehensive results
    batch_name = os.path.splitext(os.path.basename(sample_csv))[0]
    save_comprehensive_results(batch_name, base_path, clear_existing)
    
    # Track HIT-level statistics for this batch
    batch_total_hits = len(df)  # Total HITs (rows) in this batch
    batch_approved_hits = len(df[df['Approve'].astype(str).str.strip() == 'X'])
    batch_rejected_hits = len(df[df['Reject'].astype(str).str.strip() != ''])
    
    # Track rejection reasons for this batch
    batch_rejection_reasons = {}
    for reject_str in df[df['Reject'].astype(str).str.strip() != '']['Reject']:
        if reject_str and reject_str.strip():
            reasons = [r.strip() for r in reject_str.split(' | ') if r.strip()]
            
            # Normalize reasons - consolidate variants
            normalized_reasons = []
            for reason in reasons:
                if reason.startswith("Too many videos rated with same pattern:"):
                    normalized_reasons.append("Too many videos rated with same pattern:")
                elif reason.startswith("Too many unset video ratings"):
                    normalized_reasons.append("Too many unset video ratings")
                elif reason.startswith("The delays in video ratings are too high"):
                    normalized_reasons.append("The delays in video ratings are too high")
                else:
                    normalized_reasons.append(reason)
            
            if len(normalized_reasons) > 1:
                reason_key = 'multiple_reasons'
            else:
                reason_key = normalized_reasons[0] if normalized_reasons else 'unknown'
            batch_rejection_reasons[reason_key] = batch_rejection_reasons.get(reason_key, 0) + 1
    
    print(f"\n{'='*80}")
    print(f"BATCH STATISTICS FOR {batch_name}")
    print(f"{'='*80}")
    print(f"Total HITs (Submissions): {batch_total_hits}")
    print(f"Approved HITs: {batch_approved_hits}")
    print(f"Rejected HITs: {batch_rejected_hits}")
    print(f"Batch Rejection Rate: {(batch_rejected_hits/batch_total_hits*100) if batch_total_hits > 0 else 0:.2f}%")
    
    if batch_rejection_reasons:
        print(f"\nRejection Reason Breakdown:")
        for reason, count in sorted(batch_rejection_reasons.items(), key=lambda x: x[1], reverse=True):
            pct = (count / batch_rejected_hits * 100) if batch_rejected_hits > 0 else 0
            print(f"  • {reason}: {count} ({pct:.1f}%)")
    
    # Store batch statistics in global tracker (if it doesn't exist, create it)
    if not hasattr(process_batch, 'all_batch_stats'):
        process_batch.all_batch_stats = {
            'total_hits': 0,
            'approved_hits': 0,
            'rejected_hits': 0,
            'rejection_reasons': {}
        }
    
    # Accumulate statistics
    process_batch.all_batch_stats['total_hits'] += batch_total_hits
    process_batch.all_batch_stats['approved_hits'] += batch_approved_hits
    process_batch.all_batch_stats['rejected_hits'] += batch_rejected_hits
    
    for reason, count in batch_rejection_reasons.items():
        process_batch.all_batch_stats['rejection_reasons'][reason] = (
            process_batch.all_batch_stats['rejection_reasons'].get(reason, 0) + count
        )
    
    return df



if __name__ == '__main__':
    # Define the input folder containing CSV files to process
    batches = ['A','B','C','D','E','F','G','H','I','J','K']
    # batches = ['L']
    
    # Track overall rejections across all batches
    batch_rejection_counts = {}
    batch_total_submissions = {}
    overall_total_submissions = 0
    overall_total_rejections = 0
    
    print("="*80)
    print("STARTING BATCH PROCESSING - REJECTION ANALYSIS")
    print("="*80)

    # Initialize HIT-level statistics accumulator for process_batch function
    process_batch.all_batch_stats = {
        'total_hits': 0,
        'approved_hits': 0,
        'rejected_hits': 0,
        'rejection_reasons': {}
    }

    # Reset global accumulators once for all batches
    rejected_reason = []
    rejected_worker_id = []
    rejected_hit_id = []
    rejected_assgn_id = []
    rejected_details = []
    participated_worker_id = []
    
    for batch in batches:
        print(f"\n{'='*60}")
        print(f"PROCESSING BATCH {batch}")
        print(f"{'='*60}")
        
        input_folder = f'./parsing_codes_and_results/counts/batch{batch}'
        # Define the mapping CSV files
        sample_csv = f'./create_hit_batches_non_overlap/sessions/batch{batch}.csv'
        backup_csv = './backup_test.csv'
        gold_csv = './gold_vids_parse.csv'
        
        # Process all CSV files in the directory and collect results
        print(f"Processing all CSV files in {input_folder}...")
        
        # Find all CSV files in the input folder
        import os
        csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]
        
        batch_rejections = 0
        batch_submissions = 0
        
        # Process each CSV file in this batch
        for csv_file in csv_files:
            csv_path = os.path.join(input_folder, csv_file)
            print(f"\nProcessing {csv_file}...")
            
            # Extract folder name for output directory
            input_folder_name = os.path.basename(input_folder.rstrip('/'))
            
            # Set base path to parent directory with secondparse suffix
            parent_dir = os.path.dirname(input_folder)
            base_path = os.path.join(parent_dir, f'{input_folder_name}_secondparse_statistics')
            
            try:
                # Process the batch and get the resulting DataFrame
                df_result = process_batch(
                    csv_path=csv_path,
                    sample_csv=sample_csv,
                    backup_csv=backup_csv,
                    gold_csv=gold_csv,
                    base_path=base_path,
                    clear_existing=False,
                    print_analysis=False  # Set to False to suppress detailed analysis output
                )
                
                # Count submissions and rejections from the actual DataFrame
                csv_submissions = len(df_result)
                csv_rejections = len(df_result[df_result['Reject'].str.strip() != ''])
                
                batch_submissions += csv_submissions
                batch_rejections += csv_rejections
                
                print(f"  {csv_file}: {csv_submissions} submissions, {csv_rejections} rejections")
                
            except Exception as e:
                print(f"❌ Error processing {csv_file}: {e}")
                continue
        
        # Store batch totals
        batch_rejection_counts[batch] = batch_rejections
        batch_total_submissions[batch] = batch_submissions
        overall_total_submissions += batch_submissions
        overall_total_rejections += batch_rejections
        
        # Calculate batch rejection rate
        batch_rejection_rate = (batch_rejections / batch_submissions * 100) if batch_submissions > 0 else 0
        
        # Print batch summary
        print(f"\n📊 BATCH {batch} SUMMARY:")
        print(f"   Total Submissions: {batch_submissions}")
        print(f"   Total Rejections: {batch_rejections}")
        print(f"   Rejection Rate: {batch_rejection_rate:.1f}%")
        print(f"   Running Overall Total Submissions: {overall_total_submissions}")
        print(f"   Running Overall Total Rejections: {overall_total_rejections}")
        
        ###############################
        # CHECK BASE DIRECTORY IN SAVE RESULTS FUNCTION LINE 184
        ###############################
    
    # Calculate overall rejection rate
    overall_rejection_rate = (overall_total_rejections / overall_total_submissions * 100) if overall_total_submissions > 0 else 0
    
    print("="*80)

    # Print HIT-level aggregated statistics
    print(f"\n{'='*80}")
    print("HIT-LEVEL AGGREGATED STATISTICS")
    print(f"{'='*80}")
    
    if hasattr(process_batch, 'all_batch_stats'):
        stats = process_batch.all_batch_stats
        total_hits = stats['total_hits']
        approved_hits = stats['approved_hits']
        rejected_hits = stats['rejected_hits']
        overall_hit_rejection_rate = (rejected_hits / total_hits * 100) if total_hits > 0 else 0
        
        print(f"Total HITs: {total_hits}")
        print(f"Approved HITs: {approved_hits}")
        print(f"Rejected HITs: {rejected_hits}")
        print(f"Rejection Rate: {overall_hit_rejection_rate:.2f}%")
        
        # Check if multiple_reasons exists and print separately
        if 'multiple_reasons' in stats['rejection_reasons']:
            multiple_count = stats['rejection_reasons']['multiple_reasons']
            multiple_pct = (multiple_count / rejected_hits * 100) if rejected_hits > 0 else 0
            print(f"(Rejected with multiple reasons: {multiple_pct:.2f}%)")

    # Aggregate rejection percentages across all batches using HIT-level counts for consistency
    if hasattr(process_batch, 'all_batch_stats') and process_batch.all_batch_stats['total_hits'] > 0:
        stats = process_batch.all_batch_stats
        overall_base_dir = os.path.join(os.path.dirname(__file__), 'overall_rejection_statistics')

        # If the rejected_reason list count mismatches the HIT-level rejected count, log it
        if len(rejected_reason) != stats['rejected_hits']:
            print(f"WARNING: rejected_reason entries ({len(rejected_reason)}) do not match HIT-level rejected count ({stats['rejected_hits']}). Using HIT-level counts for totals and reason breakdown.")

        calculate_rejection_percentages(
            overall_base_dir,
            'all_batches',
            total_submissions=stats['total_hits'],
            total_rejections_override=stats['rejected_hits'],
            rejection_counts_override=stats['rejection_reasons']
        )
    else:
        print("No submissions processed; skipping aggregate rejection percentages.")
