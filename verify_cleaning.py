import pandas as pd

df = pd.read_csv('data/raw/sx_all_results.csv')
main = df[df['event_type'] == 'main_event']

print('CLEANED DATA SUMMARY')
print('='*50)
print(f'Total main_event records: {len(main)}')
print(f'450sx: {len(main[main["class"] == "450sx"])}')
print(f'250sxe: {len(main[main["class"] == "250sxe"])}')
print(f'250sxw: {len(main[main["class"] == "250sxw"])}')

print('\n450sx top riders (by avg position):')
riders_450 = main[main['class'] == '450sx'].groupby('rider').agg({
    'position': ['mean', 'count']
}).reset_index()
riders_450.columns = ['rider', 'avg_pos', 'races']
riders_450 = riders_450[riders_450['races'] >= 10].sort_values('avg_pos')
print(riders_450.head(10).to_string(index=False))

print('\n250sxe top riders (by avg position):')
riders_250e = main[main['class'] == '250sxe'].groupby('rider').agg({
    'position': ['mean', 'count']
}).reset_index()
riders_250e.columns = ['rider', 'avg_pos', 'races']
riders_250e = riders_250e[riders_250e['races'] >= 10].sort_values('avg_pos')
print(riders_250e.head(10).to_string(index=False))

print('\n250sxw top riders (by avg position):')
riders_250w = main[main['class'] == '250sxw'].groupby('rider').agg({
    'position': ['mean', 'count']
}).reset_index()
riders_250w.columns = ['rider', 'avg_pos', 'races']
riders_250w = riders_250w[riders_250w['races'] >= 10].sort_values('avg_pos')
print(riders_250w.head(10).to_string(index=False))
