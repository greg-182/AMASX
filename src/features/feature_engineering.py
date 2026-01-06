"""Feature engineering for supercross race prediction"""
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple


class SupercrossFeatureEngineer:
    """Create features for predicting race results"""

    def __init__(self):
        self.rider_history = {}

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create all features for modeling

        Args:
            df: Raw race results dataframe

        Returns:
            Feature dataframe ready for modeling
        """
        print("Creating features...")

        # Sort by date/round to ensure temporal ordering
        df = df.sort_values(['year', 'round', 'class']).copy()

        # Filter to main events only for prediction target
        main_events = df[df['event_type'] == 'main_event'].copy()

        # Get qualifying data
        qualifying = df[df['event_type'] == 'qualifying'][
            ['year', 'round', 'race', 'class', 'rider', 'position']
        ].copy()
        qualifying.columns = ['year', 'round',
                              'race', 'class', 'rider', 'qual_position']

        # Merge qualifying with main events
        features = main_events.merge(
            qualifying,
            on=['year', 'round', 'race', 'class', 'rider'],
            how='left'
        )

        print(f"  Base records: {len(features)}")

        # Create features
        features = self._add_historical_features(features)
        features = self._add_rider_features(features)
        features = self._add_temporal_features(features)
        features = self._add_competition_features(features)

        print(f"  Final records: {len(features)}")
        print(f"  Features created: {len(features.columns)}")

        return features

    def _add_historical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add historical performance features"""
        print("  Adding historical features...")

        df = df.sort_values(['year', 'round']).copy()

        # Initialize columns
        for window in [3, 5, 10]:
            df[f'avg_position_last_{window}'] = np.nan
            df[f'best_position_last_{window}'] = np.nan
            df[f'std_position_last_{window}'] = np.nan
            df[f'races_last_{window}'] = 0

        df['wins_last_10'] = 0
        df['podiums_last_10'] = 0
        df['total_races'] = 0
        df['career_avg_position'] = np.nan

        # Calculate for each rider
        for rider in df['rider'].unique():
            rider_mask = df['rider'] == rider
            rider_data = df[rider_mask].copy()

            for idx in rider_data.index:
                # Get all previous races for this rider (same class)
                current_class = df.loc[idx, 'class']
                current_year = df.loc[idx, 'year']
                current_round = df.loc[idx, 'round']

                # Previous races in same class
                prev_races = rider_data[
                    (rider_data['class'] == current_class) &
                    ((rider_data['year'] < current_year) |
                     ((rider_data['year'] == current_year) & (rider_data['round'] < current_round)))
                ].copy()

                if len(prev_races) > 0:
                    positions = prev_races['position'].values

                    # Career stats
                    df.loc[idx, 'total_races'] = len(prev_races)
                    df.loc[idx, 'career_avg_position'] = positions.mean()

                    # Windowed stats
                    for window in [3, 5, 10]:
                        recent = positions[-window:] if len(
                            positions) >= window else positions

                        if len(recent) > 0:
                            df.loc[idx,
                                   f'avg_position_last_{window}'] = recent.mean()
                            df.loc[idx,
                                   f'best_position_last_{window}'] = recent.min()
                            df.loc[idx, f'std_position_last_{window}'] = recent.std() if len(
                                recent) > 1 else 0
                            df.loc[idx, f'races_last_{window}'] = len(recent)

                    # Wins and podiums in last 10
                    last_10 = positions[-10:] if len(
                        positions) >= 10 else positions
                    df.loc[idx, 'wins_last_10'] = (last_10 == 1).sum()
                    df.loc[idx, 'podiums_last_10'] = (last_10 <= 3).sum()

        return df

    def _add_rider_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add rider-specific features"""
        print("  Adding rider features...")

        # Encode bike manufacturer
        df['bike_encoded'] = pd.Categorical(df['bike']).codes

        # Encode class
        class_map = {'450sx': 2, '250sxe': 1, '250sxw': 0}
        df['class_encoded'] = df['class'].map(class_map)

        # Rider number (some correlation with skill/sponsorship)
        df['rider_number'] = pd.to_numeric(df['number'], errors='coerce')

        # Qualifying position (if available)
        df['qual_position'] = df['qual_position'].fillna(
            df['qual_position'].median())

        return df

    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add temporal features"""
        print("  Adding temporal features...")

        # Round number (season progression)
        df['round_number'] = df['round']

        # Normalize round by max rounds in season
        df['round_pct'] = df.groupby(['year', 'class'])['round'].transform(
            lambda x: x / x.max()
        )

        # Year (for trend)
        df['year_encoded'] = df['year'] - df['year'].min()

        return df

    def _add_competition_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add competition/field features"""
        print("  Adding competition features...")

        # Field size
        df['field_size'] = df.groupby(['year', 'round', 'race', 'class'])[
            'rider'].transform('count')

        # Average field strength (based on career avg positions)
        df['field_avg_strength'] = df.groupby(['year', 'round', 'race', 'class'])[
            'career_avg_position'].transform('mean')

        return df

    def prepare_for_ranking(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Prepare data for XGBoost Rank (LambdaRank)

        Returns:
            features_df: Feature dataframe
            group_sizes: Array of group sizes for ranking
        """
        print("\nPreparing data for ranking model...")

        # Create group identifier (each race is a group)
        df['group_id'] = df['year'].astype(
            str) + '_' + df['round'].astype(str) + '_' + df['race'] + '_' + df['class']

        # Sort by group
        df = df.sort_values('group_id')

        # Get group sizes
        group_sizes = df.groupby('group_id').size().values

        print(f"  Total groups (races): {len(group_sizes)}")
        print(f"  Average group size: {group_sizes.mean():.1f}")

        return df, group_sizes

    def get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """Get list of feature columns for modeling"""

        # Exclude non-feature columns
        exclude = ['position', 'rider', 'race', 'date', 'url', 'year', 'round',
                   'class', 'event_type', 'number', 'bike', 'time_or_points', 'group_id']

        feature_cols = [col for col in df.columns if col not in exclude]

        return feature_cols


def main():
    """Test feature engineering"""
    from pathlib import Path

    # Load data
    data_path = Path('data/raw/sx_all_results.csv')
    df = pd.read_csv(data_path)

    # Create features
    engineer = SupercrossFeatureEngineer()
    features = engineer.create_features(df)

    # Get feature columns
    feature_cols = engineer.get_feature_columns(features)

    print("\n" + "="*70)
    print("FEATURE ENGINEERING COMPLETE")
    print("="*70)
    print(f"\nTotal features: {len(feature_cols)}")
    print(f"\nFeature list:")
    for col in sorted(feature_cols):
        print(f"  - {col}")

    # Check for missing values
    print(f"\nMissing values:")
    missing = features[feature_cols].isnull().sum()
    print(missing[missing > 0])

    # Save features
    output_path = Path('data/processed/features.csv')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(output_path, index=False)
    print(f"\nFeatures saved to: {output_path}")

    return features, feature_cols


if __name__ == "__main__":
    features, feature_cols = main()
