import pandas as pd
from src.features.feature_engineering import SupercrossFeatureEngineer

# Load data
df = pd.read_csv('data/raw/sx_all_results.csv')
main_450 = df[(df['class'] == '450sx') & (df['event_type'] == 'main_event')]

# Check specific riders
riders_to_check = ['Chase Sexton', 'Cooper Webb',
                   'Hunter Lawrence', 'Jett Lawrence']

print("="*70)
print("RIDER HISTORY CHECK - 450SX MAIN EVENTS")
print("="*70)

for rider in riders_to_check:
    rider_data = main_450[main_450['rider'] == rider].sort_values('year')

    print(f"\n{rider}:")
    print(f"  Total main events: {len(rider_data)}")
    print(f"  Years: {rider_data['year'].unique().tolist()}")
    print(f"  Career avg position: {rider_data['position'].mean():.2f}")

    if len(rider_data) > 0:
        print(f"\n  Last 10 races:")
        last_10 = rider_data.tail(10)[['year', 'round', 'race', 'position']]
        print(last_10.to_string(index=False))

        print(f"\n  2025 stats:")
        data_2025 = rider_data[rider_data['year'] == 2025]
        if len(data_2025) > 0:
            print(f"    Races: {len(data_2025)}")
            print(f"    Avg position: {data_2025['position'].mean():.2f}")
            print(f"    Best: {data_2025['position'].min()}")
            print(f"    Wins: {len(data_2025[data_2025['position'] == 1])}")
        else:
            print(f"    No 2025 races found!")

# Check what features would be created for these riders
print("\n" + "="*70)
print("FEATURE VALUES FOR PREDICTION")
print("="*70)

engineer = SupercrossFeatureEngineer()
features = engineer.create_features(df)

# Filter to 450sx main events
features_450 = features[
    (features['class'] == '450sx') &
    (features['event_type'] == 'main_event')
]

# Get most recent features for each rider
for rider in riders_to_check:
    rider_features = features_450[features_450['rider']
                                  == rider].sort_values('year')

    if len(rider_features) > 0:
        latest = rider_features.iloc[-1]
        print(f"\n{rider} (most recent race):")
        print(f"  Year: {latest['year']}, Round: {latest['round']}")
        print(
            f"  career_avg_position (f16): {latest['career_avg_position']:.2f}")
        print(
            f"  avg_position_last_5 (f5): {latest['avg_position_last_5']:.2f}")
        print(
            f"  avg_position_last_10 (f9): {latest['avg_position_last_10']:.2f}")
        print(f"  total_races (f15): {latest['total_races']:.0f}")
        print(f"  wins_last_10 (f13): {latest['wins_last_10']:.0f}")
    else:
        print(f"\n{rider}: No features found!")
