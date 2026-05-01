from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
path = "./parsing_codes_and_results/counts/global_analysis_output/global_video_final_ratings_with_averages.csv"
df = pd.read_csv(path)
valid_ratings_count = df['valid_ratings_count'].tolist()
total_valid_ratings = 0
for i in range(len(valid_ratings_count)):
    total_valid_ratings += valid_ratings_count[i]

print(f'total valid ratings count:{total_valid_ratings}')
average_valid_rat = total_valid_ratings/len(valid_ratings_count)
print(f'average: {average_valid_rat}')

plt.plot(valid_ratings_count, 'bo')
plt.xlabel('total videos')
plt.ylabel('total valid ratings')
plt.title('Distribution of valid ratings per video')
plt.savefig('./parsing_codes_and_results/counts/global_analysis_output/valid_ratings.png',dpi=300)
plt.show()