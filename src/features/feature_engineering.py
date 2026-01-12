"""
Feature Engineering for Supercross Race Prediction

This module transforms raw race results into meaningful features for machine learning.

Think of it like this:
- Raw data: "Chase Sexton finished 1st, 2nd, 1st in his last 3 races"
- Features: "avg_position_last_3 = 1.33, wins_last_10 = 7, career_avg = 2.5"

The model learns better from features than raw data!
"""

# Import required libraries
import pandas as pd      # For working with data tables (like Excel on steroids)
import numpy as np       # For mathematical operations and arrays
from typing import List, Dict, Tuple  # For type hints (makes code clearer)


class SupercrossFeatureEngineer:
    """
    Main class for creating features from raw race results.
    
    This class is like a factory that takes raw race data and produces
    25 useful features that help predict race outcomes.
    
    What it does:
    1. Loads raw race results (CSV file)
    2. Calculates historical statistics for each rider
    3. Adds context (competition level, season timing)
    4. Outputs a feature matrix ready for model training
    
    Example usage:
        engineer = SupercrossFeatureEngineer()
        features = engineer.create_features(raw_data)
        # Now 'features' has 25 columns of useful information!
    """

    def __init__(self):
        """
        Initialize the feature engineer.
        
        We create an empty dictionary to store rider history as we process.
        This helps us calculate rolling statistics efficiently.
        """
        # Dictionary to cache rider performance history
        # Key: rider name, Value: list of past positions
        self.rider_history = {}

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        MAIN METHOD: Create all features for modeling.
        
        This is the entry point - call this method to transform raw data into features.
        
        What happens here:
        1. Sort data chronologically (important for time-based features!)
        2. Filter to main events (what we want to predict)
        3. Merge in qualifying data (starting position)
        4. Call helper methods to create different feature categories
        5. Return complete feature matrix

        Args:
            df: Raw race results dataframe with columns:
                - year, round, race, class, rider, position, event_type, etc.

        Returns:
            Feature dataframe with 25+ columns ready for modeling:
                - Original columns (rider, position, etc.)
                - 25 new feature columns (avg_position_last_5, wins_last_10, etc.)
                
        Example:
            Input:  2,879 race results (raw data)
            Output: 2,524 records × 25 features (after filtering/cleaning)
        """
        print("Creating features...")

        # STEP 1: Sort by date/round to ensure temporal ordering
        # WHY: We need chronological order to calculate "last N races" correctly
        # If data is out of order, we might use future races to predict past!
        df = df.sort_values(['year', 'round', 'class']).copy()

        # STEP 2: Filter to main events only for prediction target
        # WHY: We want to predict main event results (not qualifying, heats, etc.)
        # Main event = the final race that determines the winner
        main_events = df[df['event_type'] == 'main_event'].copy()

        # STEP 3: Get qualifying data
        # WHY: Qualifying position is a useful feature (starting advantage)
        # We extract just the columns we need and rename 'position' to 'qual_position'
        qualifying = df[df['event_type'] == 'qualifying'][
            ['year', 'round', 'race', 'class', 'rider', 'position']
        ].copy()
        # Rename 'position' to 'qual_position' to distinguish from main event position
        qualifying.columns = ['year', 'round',
                              'race', 'class', 'rider', 'qual_position']

        # STEP 4: Merge qualifying with main events
        # WHY: We want both main event position AND qualifying position in same row
        # 'left' join = keep all main events, add qualifying if available
        # If rider didn't qualify, qual_position will be NaN (we'll fill it later)
        features = main_events.merge(
            qualifying,
            on=['year', 'round', 'race', 'class', 'rider'],  # Match on these columns
            how='left'  # Keep all main event records
        )

        print(f"  Base records: {len(features)}")

        # STEP 5: Create features by calling helper methods
        # Each method adds a different category of features
        features = self._add_historical_features(features)    # Past performance stats
        features = self._add_rider_features(features)         # Rider-specific info
        features = self._add_temporal_features(features)      # Time-based features
        features = self._add_competition_features(features)   # Field strength, size

        print(f"  Final records: {len(features)}")
        print(f"  Features created: {len(features.columns)}")

        return features

    def _add_historical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add historical performance features (MOST IMPORTANT FEATURES!).
        
        This creates features based on each rider's past performance.
        These are typically the most predictive features because:
        - Recent form indicates current skill level
        - Past wins show winning ability
        - Consistency shows reliability
        
        Features created (15 total):
        - avg_position_last_3/5/10: Average finish in last N races
        - best_position_last_3/5/10: Best finish in last N races
        - std_position_last_3/5/10: Consistency (lower = more consistent)
        - races_last_3/5/10: How many races competed in
        - wins_last_10: Number of wins in last 10 races
        - podiums_last_10: Number of top-3 finishes
        - total_races: Career total races
        - career_avg_position: Overall career average
        
        Example:
            Rider with positions [1, 2, 1, 3, 1] in last 5 races:
            - avg_position_last_5 = 1.6 (very good!)
            - best_position_last_5 = 1 (can win!)
            - std_position_last_5 = 0.8 (consistent!)
            - wins_last_5 = 3 (wins often!)
        """
        print("  Adding historical features...")

        # Sort chronologically (important for time-based calculations!)
        df = df.sort_values(['year', 'round']).copy()

        # Initialize columns with default values
        # We use NaN (Not a Number) for statistics that might not exist yet
        # We use 0 for counts (can't have negative races!)
        for window in [3, 5, 10]:  # Different time windows
            df[f'avg_position_last_{window}'] = np.nan    # Average position
            df[f'best_position_last_{window}'] = np.nan   # Best position
            df[f'std_position_last_{window}'] = np.nan    # Standard deviation (consistency)
            df[f'races_last_{window}'] = 0                # Count of races

        # Initialize achievement counts
        df['wins_last_10'] = 0           # Number of 1st place finishes
        df['podiums_last_10'] = 0        # Number of top-3 finishes
        df['total_races'] = 0            # Career total
        df['career_avg_position'] = np.nan  # Career average

        # MAIN LOOP: Calculate features for each rider
        # WHY: Each rider has their own history, so we process them separately
        for rider in df['rider'].unique():
            # Get all records for this rider
            rider_mask = df['rider'] == rider
            rider_data = df[rider_mask].copy()

            # INNER LOOP: For each race this rider competed in
            for idx in rider_data.index:
                # Get current race info
                current_class = df.loc[idx, 'class']    # 450sx, 250sxe, or 250sxw
                current_year = df.loc[idx, 'year']      # 2023, 2024, or 2025
                current_round = df.loc[idx, 'round']    # 1-17

                # CRITICAL: Get ONLY previous races (avoid data leakage!)
                # Data leakage = using future data to predict past (cheating!)
                # We only use races that happened BEFORE this one
                prev_races = rider_data[
                    (rider_data['class'] == current_class) &  # Same class only
                    ((rider_data['year'] < current_year) |    # Earlier year, OR
                     ((rider_data['year'] == current_year) & (rider_data['round'] < current_round)))  # Same year but earlier round
                ].copy()

                # Only calculate if rider has history
                if len(prev_races) > 0:
                    # Extract just the positions as an array
                    # Example: [1, 2, 1, 3, 2, 1, 4, 2, 1, 3]
                    positions = prev_races['position'].values

                    # CAREER STATS: Overall performance across all previous races
                    df.loc[idx, 'total_races'] = len(prev_races)
                    df.loc[idx, 'career_avg_position'] = positions.mean()
                    # Example: If positions = [1,2,1,3,2], career_avg = 1.8

                    # WINDOWED STATS: Recent performance in different time windows
                    # WHY 3 windows? Different time scales capture different patterns:
                    #   - Last 3: Current form (hot or cold?)
                    #   - Last 5: Recent trend (improving or declining?)
                    #   - Last 10: True skill level (consistent performance)
                    for window in [3, 5, 10]:
                        # Get last N races (or all if less than N)
                        # Example: positions = [1,2,1,3,2,1,4,2,1,3], window=5
                        #          recent = [1,4,2,1,3] (last 5)
                        recent = positions[-window:] if len(
                            positions) >= window else positions

                        if len(recent) > 0:
                            # Average position in window
                            df.loc[idx,
                                   f'avg_position_last_{window}'] = recent.mean()
                            # Example: [1,4,2,1,3].mean() = 2.2
                            
                            # Best position in window (lowest number = best)
                            df.loc[idx,
                                   f'best_position_last_{window}'] = recent.min()
                            # Example: [1,4,2,1,3].min() = 1
                            
                            # Standard deviation (consistency measure)
                            # Low std = consistent, High std = inconsistent
                            df.loc[idx, f'std_position_last_{window}'] = recent.std() if len(
                                recent) > 1 else 0
                            # Example: [1,1,1,1,1].std() = 0 (very consistent!)
                            #          [1,15,1,1,1].std() = 5.6 (one bad race!)
                            
                            # Count of races in window
                            df.loc[idx, f'races_last_{window}'] = len(recent)
                            # Example: If rider missed races, might be < window size

                    # ACHIEVEMENTS: Count wins and podiums in last 10 races
                    last_10 = positions[-10:] if len(
                        positions) >= 10 else positions
                    
                    # Count wins (position == 1)
                    df.loc[idx, 'wins_last_10'] = (last_10 == 1).sum()
                    # Example: [1,2,1,3,1,2,4,1,2,3] → 4 wins
                    
                    # Count podiums (position <= 3)
                    df.loc[idx, 'podiums_last_10'] = (last_10 <= 3).sum()
                    # Example: [1,2,1,3,1,2,4,1,2,3] → 9 podiums (all except 4th)

        return df

    def _add_rider_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add rider-specific features (bike, class, number).
        
        These features capture information about the rider and their equipment.
        
        Features created (4 total):
        - bike_encoded: Bike manufacturer as number (Honda=0, KTM=1, etc.)
        - class_encoded: Race class as number (450sx=2, 250sxe=1, 250sxw=0)
        - rider_number: Rider's bike number (23, 1, 450, etc.)
        - qual_position: Qualifying position (starting advantage)
        
        WHY encode text as numbers?
        - Machine learning models need numbers, not text!
        - "Honda" → 0, "KTM" → 1, etc.
        - Model can learn: "Riders on bike 0 tend to finish higher"
        """
        print("  Adding rider features...")

        # BIKE MANUFACTURER: Encode as numbers
        # WHY: Different bikes have different performance characteristics
        # Example: Honda → 0, KTM → 1, Yamaha → 2, Kawasaki → 3, etc.
        # Model might learn: "Honda riders finish 0.5 positions better on average"
        df['bike_encoded'] = pd.Categorical(df['bike']).codes

        # CLASS: Encode as numbers
        # WHY: Different classes are different competitions
        # 450sx = premier class (bigger bikes, more experienced riders)
        # 250sx = development class (smaller bikes, younger riders)
        # East/West = regional series (250sx is split into two regions)
        class_map = {'450sx': 2, '250sxe': 1, '250sxw': 0}
        df['class_encoded'] = df['class'].map(class_map)

        # RIDER NUMBER: Convert to numeric
        # WHY: Lower numbers often indicate better riders (earned through results)
        # Example: #1 = champion, #23 = top rider, #450 = privateer
        # errors='coerce' = if number is text, convert to NaN instead of error
        df['rider_number'] = pd.to_numeric(df['number'], errors='coerce')

        # QUALIFYING POSITION: Fill missing values
        # WHY: Some riders don't qualify (DNS, DNQ)
        # We fill missing values with median (middle value)
        # Example: If median qual_position = 11, missing values become 11
        # This is better than leaving NaN (model can't handle NaN)
        df['qual_position'] = df['qual_position'].fillna(
            df['qual_position'].median())

        return df

    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add temporal (time-based) features.
        
        These features capture WHEN in the season the race occurs.
        
        Features created (3 total):
        - round_number: Race number in season (1-17)
        - round_pct: Percentage through season (0.0-1.0)
        - year_encoded: Year as number (0, 1, 2 for 2023, 2024, 2025)
        
        WHY temporal features matter:
        - Early season: Riders finding form, new bike setups
        - Mid season: Peak performance, championship battles
        - Late season: Fatigue, injuries, some riders give up
        
        Example:
            Round 1: round_pct = 0.06 (6% through season)
            Round 9: round_pct = 0.53 (halfway point)
            Round 17: round_pct = 1.0 (season finale)
        """
        print("  Adding temporal features...")

        # ROUND NUMBER: Simple race number in season
        # Example: 1, 2, 3, ..., 17
        # WHY: Model can learn seasonal patterns
        df['round_number'] = df['round']

        # ROUND PERCENTAGE: Normalize by season length
        # WHY: Different classes have different season lengths
        # 450sx might have 17 rounds, 250sx might have 9 rounds
        # Percentage makes them comparable
        # 
        # How it works:
        # 1. Group by year and class (each season separately)
        # 2. For each group, divide round by max round
        # Example: Round 5 of 17 → 5/17 = 0.29 (29% through season)
        df['round_pct'] = df.groupby(['year', 'class'])['round'].transform(
            lambda x: x / x.max()
        )

        # YEAR: Encode as 0, 1, 2 instead of 2023, 2024, 2025
        # WHY: Smaller numbers are easier for model to learn
        # Also captures multi-year trends (riders improving over years)
        # Example: 2023 → 0, 2024 → 1, 2025 → 2
        df['year_encoded'] = df['year'] - df['year'].min()

        return df

    def _add_competition_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add competition/field features (who else is racing?).
        
        These features capture the DIFFICULTY of each race.
        
        Features created (2 total):
        - field_size: Number of riders in the race (15-22 typically)
        - field_avg_strength: Average skill level of all riders
        
        WHY competition features matter:
        - Finishing 5th in a strong field is more impressive than 5th in weak field
        - Larger fields are harder (more riders to beat)
        - Model learns to adjust predictions based on competition
        
        Example:
            Race A: field_size=22, field_avg_strength=4.5 (very competitive!)
            Race B: field_size=18, field_avg_strength=9.2 (easier field)
            
            Same rider finishing 5th:
            - In Race A: Great result! (beat 17 strong riders)
            - In Race B: Expected result (beat 13 weaker riders)
        """
        print("  Adding competition features...")

        # FIELD SIZE: Count riders in each race
        # How it works:
        # 1. Group by race (year + round + race + class uniquely identifies a race)
        # 2. Count how many riders in each group
        # 3. Assign that count to every rider in that race
        # 
        # Example:
        #   Race 1 has 22 riders → all 22 riders get field_size = 22
        #   Race 2 has 18 riders → all 18 riders get field_size = 18
        df['field_size'] = df.groupby(['year', 'round', 'race', 'class'])[
            'rider'].transform('count')

        # FIELD AVERAGE STRENGTH: Average skill of all riders in race
        # How it works:
        # 1. Group by race (same as above)
        # 2. Calculate mean of career_avg_position for all riders
        # 3. Lower average = stronger field (better riders have lower positions)
        # 
        # Example:
        #   Race 1: Riders with career avgs [2.5, 3.1, 4.2, ...] → mean = 7.3
        #   Race 2: Riders with career avgs [8.2, 9.5, 10.1, ...] → mean = 11.5
        #   Race 1 is stronger (lower average = better riders)
        df['field_avg_strength'] = df.groupby(['year', 'round', 'race', 'class'])[
            'career_avg_position'].transform('mean')

        return df

    def prepare_for_ranking(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Prepare data for XGBoost Rank (LambdaRank) model.
        
        Ranking models are different from regression models:
        - Regression: Predict exact position (1, 2, 3, ...)
        - Ranking: Order riders correctly (who beats who?)
        
        Ranking models need to know which riders raced together.
        We create "groups" where each group = one race.
        
        Example:
            Race 1 (Anaheim): 22 riders → group_id = "2023_1_Anaheim_450sx"
            Race 2 (San Diego): 21 riders → group_id = "2023_2_San Diego_450sx"
            
            Model learns: "In group 1, rider A should rank above rider B"

        Returns:
            features_df: Feature dataframe with group_id column added
            group_sizes: Array of group sizes [22, 21, 22, ...]
                        Used by XGBoost to know where groups start/end
        """
        print("\nPreparing data for ranking model...")

        # CREATE GROUP IDENTIFIER: Unique ID for each race
        # Format: "year_round_race_class"
        # Example: "2023_1_Anaheim 1_450sx"
        # 
        # WHY: Ranking model needs to know which riders competed together
        # All riders with same group_id raced against each other
        df['group_id'] = df['year'].astype(
            str) + '_' + df['round'].astype(str) + '_' + df['race'] + '_' + df['class']

        # SORT BY GROUP: Important for XGBoost Rank!
        # XGBoost expects all riders from same race to be consecutive
        # Example:
        #   Row 1-22: Anaheim (group 1)
        #   Row 23-43: San Diego (group 2)
        #   Row 44-65: Arlington (group 3)
        df = df.sort_values('group_id')

        # GET GROUP SIZES: How many riders in each race?
        # Example: [22, 21, 22, 20, 22, ...]
        # XGBoost uses this to know:
        #   - First 22 rows = group 1
        #   - Next 21 rows = group 2
        #   - Next 22 rows = group 3
        #   etc.
        group_sizes = df.groupby('group_id').size().values

        print(f"  Total groups (races): {len(group_sizes)}")
        print(f"  Average group size: {group_sizes.mean():.1f}")

        return df, group_sizes

    def get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """
        Get list of feature columns for modeling.
        
        Not all columns are features! Some are metadata or targets.
        This method filters out non-feature columns.
        
        EXCLUDED columns:
        - position: This is what we're PREDICTING (target variable)
        - rider, race, date, url: Metadata (not useful for prediction)
        - year, round, class: Already encoded as features
        - event_type, number, bike: Already encoded as features
        - time_or_points: Not useful for position prediction
        - group_id: Only used for ranking, not a feature
        
        INCLUDED columns (25 features):
        - All the features we created above!
        - avg_position_last_3/5/10
        - best_position_last_3/5/10
        - std_position_last_3/5/10
        - races_last_3/5/10
        - wins_last_10, podiums_last_10
        - total_races, career_avg_position
        - bike_encoded, class_encoded, rider_number
        - qual_position
        - round_number, round_pct, year_encoded
        - field_size, field_avg_strength
        
        Returns:
            List of feature column names (25 columns)
        """

        # List of columns to EXCLUDE (not features)
        exclude = ['position', 'rider', 'race', 'date', 'url', 'year', 'round',
                   'class', 'event_type', 'number', 'bike', 'time_or_points', 'group_id']

        # Keep all columns EXCEPT the excluded ones
        # This is a list comprehension: [item for item in list if condition]
        feature_cols = [col for col in df.columns if col not in exclude]

        return feature_cols


def main():
    """
    Test feature engineering (run this file directly to test).
    
    This function demonstrates how to use the SupercrossFeatureEngineer class.
    It's useful for:
    - Testing that feature engineering works
    - Checking which features are created
    - Verifying no missing values
    - Saving features for model training
    
    To run: python src/features/feature_engineering.py
    """
    from pathlib import Path

    # STEP 1: Load raw data
    # Path to the CSV file with race results
    data_path = Path('data/raw/sx_all_results.csv')
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df):,} raw records")

    # STEP 2: Create features
    # Initialize the feature engineer
    engineer = SupercrossFeatureEngineer()
    # Transform raw data → features
    features = engineer.create_features(df)

    # STEP 3: Get feature column names
    # This excludes metadata and target columns
    feature_cols = engineer.get_feature_columns(features)

    # STEP 4: Print summary
    print("\n" + "="*70)
    print("FEATURE ENGINEERING COMPLETE")
    print("="*70)
    print(f"\nTotal features: {len(feature_cols)}")
    print(f"\nFeature list:")
    for col in sorted(feature_cols):
        print(f"  - {col}")

    # STEP 5: Check for missing values
    # Missing values (NaN) can cause problems in model training
    print(f"\nMissing values:")
    missing = features[feature_cols].isnull().sum()
    if missing.sum() > 0:
        print(missing[missing > 0])
    else:
        print("  None! All features have values.")

    # STEP 6: Save features to CSV
    # This file will be used by the model training script
    output_path = Path('data/processed/features.csv')
    output_path.parent.mkdir(parents=True, exist_ok=True)  # Create folder if needed
    features.to_csv(output_path, index=False)
    print(f"\nFeatures saved to: {output_path}")
    print(f"  Rows: {len(features):,}")
    print(f"  Columns: {len(features.columns)}")

    return features, feature_cols


# If this file is run directly (not imported), run the main function
if __name__ == "__main__":
    features, feature_cols = main()
