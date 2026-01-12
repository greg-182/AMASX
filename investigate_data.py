import pandas as pd

# Load data
df = pd.read_csv('data/raw/sx_all_results.csv')

# Check 450sx suspicious riders
print("="*70)
print("450SX SUSPICIOUS RIDERS IN MAIN_EVENT")
print("="*70)

main_450 = df[(df['class'] == '450sx') & (df['event_type'] == 'main_event')]
suspicious_450 = ['Michael Hicks', 'Joan Cros', 'Slade Varola']

for rider in suspicious_450:
    rider_races = main_450[main_450['rider'] == rider][
        ['year', 'round', 'race', 'position', 'rider', 'bike', 'number']
    ]
    print(f"\n{rider}:")
    if len(rider_races) > 0:
        print(rider_races.to_string(index=False))
        # Check what other riders are in these same races
        for _, race in rider_races.iterrows():
            same_race = main_450[
                (main_450['year'] == race['year']) &
                (main_450['round'] == race['round']) &
                (main_450['race'] == race['race'])
            ].sort_values('position')
            print(
                f"\n  Full field for {race['year']} {race['race']} (Round {race['round']}):")
            print(f"  Total riders: {len(same_race)}")
            print(f"  Top 5: {same_race.head(5)['rider'].tolist()}")
            print(f"  Winner: {same_race.iloc[0]['rider']}")
    else:
        print("  No main_event records found")

# Check 250sxe suspicious riders
print("\n" + "="*70)
print("250SXE SUSPICIOUS RIDERS IN MAIN_EVENT")
print("="*70)

main_250e = df[(df['class'] == '250sxe') & (df['event_type'] == 'main_event')]
suspicious_250e = ['Lux Turner', 'Gavin Towers']

for rider in suspicious_250e:
    rider_races = main_250e[main_250e['rider'] == rider][
        ['year', 'round', 'race', 'position', 'rider', 'bike', 'number']
    ]
    print(f"\n{rider}:")
    if len(rider_races) > 0:
        print(rider_races.to_string(index=False))
        # Check what other riders are in these same races
        for _, race in rider_races.iterrows():
            same_race = main_250e[
                (main_250e['year'] == race['year']) &
                (main_250e['round'] == race['round']) &
                (main_250e['race'] == race['race'])
            ].sort_values('position')
            print(
                f"\n  Full field for {race['year']} {race['race']} (Round {race['round']}):")
            print(f"  Total riders: {len(same_race)}")
            print(f"  Top 5: {same_race.head(5)['rider'].tolist()}")
            print(f"  Winner: {same_race.iloc[0]['rider']}")
    else:
        print("  No main_event records found")

# Check Haiden Deegan in 250sxw
print("\n" + "="*70)
print("HAIDEN DEEGAN IN 250SXW")
print("="*70)

main_250w = df[(df['class'] == '250sxw') & (df['event_type'] == 'main_event')]
deegan = main_250w[main_250w['rider'] == 'Haiden Deegan'][
    ['year', 'round', 'race', 'position', 'rider']
]
print(f"\nHaiden Deegan 250sxw main_event records: {len(deegan)}")
if len(deegan) > 0:
    print(deegan.to_string(index=False))
else:
    print("  No 250sxw main_event records (he races 250sxe)")

# Check Haiden Deegan in 250sxe
main_250e = df[(df['class'] == '250sxe') & (df['event_type'] == 'main_event')]
deegan_e = main_250e[main_250e['rider'] == 'Haiden Deegan'][
    ['year', 'round', 'race', 'position', 'rider']
]
print(f"\nHaiden Deegan 250sxe main_event records: {len(deegan_e)}")
if len(deegan_e) > 0:
    print(deegan_e.head(10).to_string(index=False))
    print(f"Average position: {deegan_e['position'].mean():.2f}")
