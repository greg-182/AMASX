"""
Clean mislabeled LCQ data from main_event records.

Problem: Some LCQ results are mislabeled as "main_event", causing riders to appear
twice in the same race with different positions. The better position is always the
LCQ result (mislabeled), and the worse position is the actual main event result.

Solution: For any rider appearing twice in the same main_event race, keep only the
WORSE position (actual main event) and remove the BETTER position (mislabeled LCQ).
"""

import pandas as pd
import numpy as np

# Load data
print("Loading data...")
df = pd.read_csv('data/raw/sx_all_results.csv')
print(f"Total records: {len(df)}")

# Backup original data
df.to_csv('data/raw/sx_all_results_backup.csv', index=False)
print("Backup saved to: data/raw/sx_all_results_backup.csv")

# Find duplicate main_event records (same rider, same race)
main_events = df[df['event_type'] == 'main_event'].copy()
print(f"\nMain event records before cleaning: {len(main_events)}")

# Create race identifier
main_events['race_id'] = (
    main_events['year'].astype(str) + '_' +
    main_events['round'].astype(str) + '_' +
    main_events['race'] + '_' +
    main_events['class']
)

# Find duplicates
duplicates = main_events.groupby(['race_id', 'rider']).size()
duplicates = duplicates[duplicates > 1]

print(f"\nFound {len(duplicates)} duplicate rider-race combinations")

if len(duplicates) > 0:
    print("\nDuplicate records:")
    for (race_id, rider), count in duplicates.items():
        records = main_events[
            (main_events['race_id'] == race_id) &
            (main_events['rider'] == rider)
        ][['year', 'round', 'race', 'class', 'rider', 'position']].sort_values('position')

        print(f"\n  {rider} in {race_id}:")
        print(f"    Positions: {records['position'].tolist()}")
        print(f"    Keeping WORSE position (actual main event)")
        print(f"    Removing BETTER position (mislabeled LCQ)")

# For each duplicate, keep only the WORSE position (higher number = worse)
rows_to_remove = []

for (race_id, rider), count in duplicates.items():
    # Get all records for this rider in this race
    records = main_events[
        (main_events['race_id'] == race_id) &
        (main_events['rider'] == rider)
    ]

    # Keep the WORST position (actual main event)
    # Remove the BEST position (mislabeled LCQ)
    best_position = records['position'].min()

    # Get indices of records with the best position (these are mislabeled LCQ)
    indices_to_remove = records[records['position'] == best_position].index
    rows_to_remove.extend(indices_to_remove.tolist())

print(f"\nRemoving {len(rows_to_remove)} mislabeled LCQ records...")

# Remove the mislabeled records from the original dataframe
df_cleaned = df.drop(rows_to_remove)

print(f"Records after cleaning: {len(df_cleaned)}")
print(f"Records removed: {len(df) - len(df_cleaned)}")

# Verify cleaning
main_events_cleaned = df_cleaned[df_cleaned['event_type']
                                 == 'main_event'].copy()
main_events_cleaned['race_id'] = (
    main_events_cleaned['year'].astype(str) + '_' +
    main_events_cleaned['round'].astype(str) + '_' +
    main_events_cleaned['race'] + '_' +
    main_events_cleaned['class']
)

duplicates_after = main_events_cleaned.groupby(['race_id', 'rider']).size()
duplicates_after = duplicates_after[duplicates_after > 1]

print(f"\nDuplicates remaining: {len(duplicates_after)}")

if len(duplicates_after) == 0:
    print("All duplicates removed successfully!")
else:
    print("Warning: Some duplicates still remain:")
    print(duplicates_after)

# Save cleaned data
df_cleaned.to_csv('data/raw/sx_all_results.csv', index=False)
print(f"\nCleaned data saved to: data/raw/sx_all_results.csv")

# Show summary of changes
print("\n" + "="*70)
print("CLEANING SUMMARY")
print("="*70)

for class_type in ['450sx', '250sxe', '250sxw']:
    before = len(main_events[main_events['class'] == class_type])
    after = len(
        main_events_cleaned[main_events_cleaned['class'] == class_type])
    print(f"{class_type}: {before} -> {after} records ({before - after} removed)")

print("\n" + "="*70)
print("NEXT STEPS")
print("="*70)
print("1. Delete features: rm data/processed/features.csv")
print("2. Retrain models: python run_modeling_v2.py")
print("3. Make predictions: python predict_race.py --year 2026 --round 1 --race 'Anaheim I' --no-qual")
