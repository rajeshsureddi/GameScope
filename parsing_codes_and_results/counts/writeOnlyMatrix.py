import pandas as pd
import numpy as np

# Input and output file paths
input_file = './parsing_codes_and_results/counts/global_analysis_output/global_individual_ratings_matrix.csv'
output_file = './parsing_codes_and_results/counts/global_analysis_output/ratings_matrix_only.csv'

def extract_ratings_matrix():
    """Extract only the rating columns from the global individual ratings matrix CSV"""
    
    print("Reading the global individual ratings matrix CSV...")
    
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    print(f"Original CSV shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    # Find all rating columns (rating_1, rating_2, etc.)
    rating_columns = [col for col in df.columns if col.startswith('rating_')]
    
    print(f"Found {len(rating_columns)} rating columns: {rating_columns[:5]}...{rating_columns[-5:]}")
    
    # Extract only the rating columns
    ratings_matrix = df[rating_columns].copy()
    
    print(f"Extracted matrix shape: {ratings_matrix.shape}")
    
    # Replace NaN values with exactly 'nan' as string
    ratings_matrix = ratings_matrix.fillna('nan')
    
    # Count statistics
    total_cells = ratings_matrix.shape[0] * ratings_matrix.shape[1]
    nan_cells = (ratings_matrix == 'nan').sum().sum()
    valid_cells = total_cells - nan_cells
    
    print(f"\nMatrix Statistics:")
    print(f"Total cells: {total_cells:,}")
    print(f"Valid rating cells: {valid_cells:,}")
    print(f"NaN cells (replaced with 'nan'): {nan_cells:,}")
    print(f"Fill percentage: {(valid_cells/total_cells)*100:.1f}%")
    
    # Save the matrix to CSV
    print(f"\nSaving ratings matrix to: {output_file}")
    ratings_matrix.to_csv(output_file, index=False)
    
    print("✅ Ratings matrix CSV created successfully!")
    print(f"Output file contains only {len(rating_columns)} rating columns")
    print("NaN values are replaced with exactly 'nan' string")
    
    # Show a sample of the output
    print(f"\nSample of the output (first 5 rows, first 10 columns):")
    print(ratings_matrix.iloc[:5, :10].to_string())
    
    return ratings_matrix

if __name__ == "__main__":
    matrix = extract_ratings_matrix()
