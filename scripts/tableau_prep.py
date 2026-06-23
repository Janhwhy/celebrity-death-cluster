"""
Tableau Prep Script

This script merges:
1. data/outputs/stats_results.csv (weekly stats including poisson expected values and cluster flags)
2. data/outputs/monthly_summary.csv (monthly summaries)
3. data/cleaned/deaths_clean.csv (individual cleaned deaths)

To create a single, clean Tableau-ready file at data/outputs/tableau_final.csv with these columns:
- year
- month
- week
- profession
- death_count
- is_cluster_week
- expected_poisson_count
- avg_age_at_death
- covid_era (True for years 2020–2022, False otherwise)

Only pandas is used.
"""

import os
import pandas as pd

# Define paths relative to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATS_RESULTS_CSV = os.path.join(PROJECT_ROOT, 'data', 'outputs', 'stats_results.csv')
MONTHLY_SUMMARY_CSV = os.path.join(PROJECT_ROOT, 'data', 'outputs', 'monthly_summary.csv')
DEATHS_CLEAN_CSV = os.path.join(PROJECT_ROOT, 'data', 'cleaned', 'deaths_clean.csv')
OUTPUT_FINAL_CSV = os.path.join(PROJECT_ROOT, 'data', 'outputs', 'tableau_final.csv')

def main():
    print("=" * 80)
    print("Preparing final Tableau dataset...")
    print("=" * 80)

    # Verify input files exist
    for path, name in [(STATS_RESULTS_CSV, "stats_results.csv"), 
                       (MONTHLY_SUMMARY_CSV, "monthly_summary.csv"), 
                       (DEATHS_CLEAN_CSV, "deaths_clean.csv")]:
        if not os.path.exists(path):
            print(f"Error: Required file '{name}' not found at: {path}")
            print("Please ensure you have run previous scraping/cleaning/analysis scripts first.")
            return

    # 1. Load dataframes
    print("Loading data files...")
    stats_results = pd.read_csv(STATS_RESULTS_CSV)
    monthly_summary = pd.read_csv(MONTHLY_SUMMARY_CSV)
    deaths_clean = pd.read_csv(DEATHS_CLEAN_CSV)

    # 2. Extract week-to-month mapping from deaths_clean
    # Since some calendar weeks span two months, we assign the most common month (mode) for each week.
    print("Extracting week-to-month mapping...")
    week_month_map = deaths_clean.groupby(['year', 'week_number'])['month'].agg(lambda x: x.mode()[0]).reset_index()
    week_month_map.columns = ['year', 'week', 'month']

    # 3. Merge stats_results with week_month_map to bring in month
    print("Merging weekly stats with month map...")
    merged_df = pd.merge(stats_results, week_month_map, on=['year', 'week'], how='left')

    # 4. Calculate weekly average age of death per profession from deaths_clean
    print("Calculating weekly average age of death...")
    weekly_avg_age = deaths_clean.groupby(['year', 'week_number', 'profession'])['age_at_death'].mean().reset_index()
    weekly_avg_age.columns = ['year', 'week', 'profession', 'avg_age_at_death']

    # 5. Merge weekly average age of death
    print("Merging weekly average age of death...")
    merged_df = pd.merge(merged_df, weekly_avg_age, on=['year', 'week', 'profession'], how='left')

    # 6. Merge with monthly_summary to ensure monthly data is integrated (joining on year, month, profession)
    print("Merging monthly summary...")
    merged_df = pd.merge(merged_df, monthly_summary, on=['year', 'month', 'profession'], how='left', suffixes=('', '_monthly'))

    # 7. Add covid_era column (True for 2020-2022, False otherwise)
    print("Adding covid_era flag...")
    merged_df['covid_era'] = merged_df['year'].isin([2020, 2021, 2022])

    # 8. Filter and order final columns
    final_cols = [
        'year', 'month', 'week', 'profession', 'death_count', 
        'is_cluster_week', 'expected_poisson_count', 'avg_age_at_death', 'covid_era'
    ]
    tableau_final = merged_df[final_cols]

    # Save to CSV
    print(f"Exporting final dataset to {OUTPUT_FINAL_CSV}...")
    tableau_final.to_csv(OUTPUT_FINAL_CSV, index=False)

    print("\n" + "=" * 80)
    print("DATASET PREPARATION COMPLETE")
    print("=" * 80)
    print(f"Final Dataframe Shape: {tableau_final.shape}")
    print("\nFirst 5 rows of final dataset:")
    print(tableau_final.head(5))
    print("\nColumns in final dataset:")
    for col in tableau_final.columns:
        print(f" - {col}")
    print("=" * 80)

if __name__ == "__main__":
    main()
