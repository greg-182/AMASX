from src.features.feature_engineering import SupercrossFeatureEngineer
import pandas as pd

df = pd.read_csv('data/processed/features.csv')
engineer = SupercrossFeatureEngineer()
feature_cols = engineer.get_feature_columns(df)

print('FEATURE LIST (Index : Name):\n')
for i, col in enumerate(feature_cols):
    print(f'f{i:2d}: {col}')
