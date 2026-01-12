"""
Train XGBoost and XGBoost Rank models for race prediction

This module trains machine learning models to predict supercross race results.

KEY CONCEPTS:
1. Train-Test Split: 80% training, 20% testing (chronological)
2. Two Model Types: XGBoost Regressor vs XGBoost Rank
3. Class-Specific Models: Separate models for 450sx, 250sxe, 250sxw
4. Evaluation Metrics: NDCG, Top-K Accuracy, Winner Prediction

WHY MACHINE LEARNING?
- Humans can't process 25 features × 2,905 races in their head
- ML models find patterns we might miss
- Can predict race outcomes better than random guessing
"""

# Import required libraries
import pandas as pd              # Data manipulation
import numpy as np               # Numerical operations
import xgboost as xgb           # Machine learning library
from sklearn.model_selection import train_test_split  # Data splitting
from sklearn.metrics import mean_absolute_error, mean_squared_error  # Evaluation
import matplotlib.pyplot as plt  # Plotting
import seaborn as sns           # Better plotting
from pathlib import Path        # File path handling
import json                     # Save model parameters
import pickle                   # Save Python objects


class RacePredictor:
    """
    Train and evaluate race prediction models.

    This class handles the entire machine learning workflow:
    1. Data preparation (split into train/test)
    2. Model training (learn from historical data)
    3. Prediction (predict future races)
    4. Evaluation (measure accuracy)
    5. Feature importance (understand what matters)

    Two model types available:
    - 'regressor': Predicts exact position (1, 2, 3, ...)
    - 'rank': Optimizes ranking order (who beats who?)

    Example usage:
        predictor = RacePredictor(model_type='rank')
        predictor.prepare_data(features, feature_cols)
        predictor.train(X_train, y_train)
        predictions = predictor.predict(X_test)
    """

    def __init__(self, model_type='rank', class_filter=None):
        """
        Initialize the race predictor.

        Args:
            model_type: 'rank' for XGBoost Rank, 'regressor' for standard XGBoost
            class_filter: Optional class to filter ('450sx', '250sxe', '250sxw', or None for all)

        Example:
            # Train on all classes
            predictor = RacePredictor(model_type='rank')

            # Train only on 450sx
            predictor = RacePredictor(model_type='rank', class_filter='450sx')
        """
        self.model_type = model_type
        self.class_filter = class_filter
        self.model = None
        self.feature_cols = None
        self.feature_importance = None

    def prepare_data(self, df: pd.DataFrame, feature_cols: list,
                     test_size: float = 0.2, random_state: int = 42) -> tuple:
        """
        Split data into train/test sets using 80-20 split.

        IMPORTANT: We use CHRONOLOGICAL split, not random!
        WHY? Because we want to predict FUTURE races, not random past races.

        How it works:
        1. Filter to specific class if requested
        2. Sort by year and round (chronological order)
        3. Take first 80% for training
        4. Take last 20% for testing
        5. Remove rows with missing features

        This simulates real-world usage:
        - Train on past races (2023 early + 2024 + 2025 early)
        - Test on recent races (2025 late)

        Args:
            df: Feature dataframe with all races
            feature_cols: List of feature column names (25 features)
            test_size: Fraction for testing (0.2 = 20%)
            random_state: Random seed for reproducibility

        Returns:
            X_train: Training features (2D array)
            X_test: Testing features (2D array)
            y_train: Training targets (positions)
            y_test: Testing targets (positions)
            groups_train: Training group sizes (for ranking)
            groups_test: Testing group sizes (for ranking)
            train_df: Training dataframe (with metadata)
            test_df: Testing dataframe (with metadata)
        """
        print(f"\nPreparing data...")
        print(f"  Model type: {self.model_type}")
        print(
            f"  Class filter: {self.class_filter if self.class_filter else 'All classes'}")
        print(f"  Test size: {test_size*100:.0f}%")

        # STEP 1: Filter to specific class if requested
        if self.class_filter:
            df = df[df['class'] == self.class_filter].copy()
            print(f"  Filtered to {self.class_filter}: {len(df)} records")

        # STEP 2: Remove rows with missing features
        # WHY: Models can't handle NaN (Not a Number) values
        # We need complete data for all features
        df_clean = df.dropna(subset=feature_cols).copy()
        print(f"  Records after removing missing: {len(df_clean)}")

        # STEP 3: Sort chronologically (CRITICAL!)
        # WHY: We want to split by time, not randomly
        # This ensures we train on past and test on future
        df_clean = df_clean.sort_values(
            ['year', 'round', 'class']).reset_index(drop=True)

        # STEP 4: Calculate split point
        # Example: 2,905 records × 0.8 = 2,324 for training
        split_idx = int(len(df_clean) * (1 - test_size))

        # STEP 5: Split into train and test
        # First 80% = training, Last 20% = testing
        train_df = df_clean.iloc[:split_idx].copy()
        test_df = df_clean.iloc[split_idx:].copy()

        print(
            f"  Train records: {len(train_df)} ({len(train_df)/len(df_clean)*100:.1f}%)")
        print(
            f"    Year range: {train_df['year'].min()}-{train_df['year'].max()}")
        print(
            f"    Round range: {train_df['round'].min()}-{train_df['round'].max()}")
        print(
            f"  Test records: {len(test_df)} ({len(test_df)/len(df_clean)*100:.1f}%)")
        print(
            f"    Year range: {test_df['year'].min()}-{test_df['year'].max()}")
        print(
            f"    Round range: {test_df['round'].min()}-{test_df['round'].max()}")

        # STEP 6: Extract features (X) and target (y)
        # X = features (25 columns of rider stats, competition info, etc.)
        # y = target (position we want to predict)
        X_train = train_df[feature_cols].values  # Convert to numpy array
        X_test = test_df[feature_cols].values
        y_train = train_df['position'].values    # Actual finishing positions
        y_test = test_df['position'].values

        # STEP 7: Create group_id for both models
        # WHY: We need to know which riders raced together
        # group_id = unique identifier for each race
        # Format: "year_round_racename_class"
        train_df['group_id'] = (train_df['year'].astype(str) + '_' +
                                train_df['round'].astype(str) + '_' +
                                train_df['race'] + '_' + train_df['class'])
        test_df['group_id'] = (test_df['year'].astype(str) + '_' +
                               test_df['round'].astype(str) + '_' +
                               test_df['race'] + '_' + test_df['class'])

        # STEP 8: Prepare groups for ranking model
        groups_train = None
        groups_test = None

        if self.model_type == 'rank':
            # Ranking models need to know which riders competed together
            # We sort by group_id so all riders from same race are consecutive
            train_df = train_df.sort_values('group_id')
            test_df = test_df.sort_values('group_id')

            # Recompute X, y after sorting (order changed!)
            X_train = train_df[feature_cols].values
            X_test = test_df[feature_cols].values
            y_train = train_df['position'].values
            y_test = test_df['position'].values

            # Get group sizes (how many riders in each race?)
            # Example: [22, 21, 22, 20, ...] means:
            #   - First 22 rows = race 1
            #   - Next 21 rows = race 2
            #   - Next 22 rows = race 3
            groups_train = train_df.groupby('group_id').size().values
            groups_test = test_df.groupby('group_id').size().values

            print(f"  Train groups (races): {len(groups_train)}")
            print(f"  Test groups (races): {len(groups_test)}")

        # Store feature columns for later use
        self.feature_cols = feature_cols

        return X_train, X_test, y_train, y_test, groups_train, groups_test, train_df, test_df

    def train(self, X_train, y_train, groups_train=None, params=None):
        """
        Train the machine learning model.

        This is where the "learning" happens!
        The model analyzes training data to find patterns.

        How XGBoost works (simplified):
        1. Start with a simple prediction (average position)
        2. Find which features help predict better
        3. Build decision trees based on those features
        4. Combine trees to make final prediction
        5. Repeat 200 times (num_boost_round)

        Example pattern it might learn:
        "If avg_position_last_5 < 2 AND wins_last_10 > 5 
         AND qual_position < 3, then predict position 1-2"

        Args:
            X_train: Training features (2D array)
            y_train: Training targets (positions)
            groups_train: Group sizes for ranking model
            params: Model hyperparameters (optional)
        """
        print(f"\nTraining {self.model_type} model...")

        # STEP 1: Set default parameters if not provided
        if params is None:
            if self.model_type == 'rank':
                # RANKING MODEL PARAMETERS
                params = {
                    # Learn pairwise comparisons (A beats B?)
                    'objective': 'rank:pairwise',
                    'eval_metric': 'ndcg',         # Normalized Discounted Cumulative Gain
                    # Learning rate (smaller = slower but better)
                    'eta': 0.1,
                    # Tree depth (deeper = more complex)
                    'max_depth': 6,
                    'min_child_weight': 1,         # Minimum data in leaf node
                    # Use 80% of data per tree (prevents overfitting)
                    'subsample': 0.8,
                    'colsample_bytree': 0.8,       # Use 80% of features per tree
                    'seed': 42                     # Random seed for reproducibility
                }
            else:
                # REGRESSION MODEL PARAMETERS
                params = {
                    'objective': 'reg:squarederror',  # Minimize squared error
                    'eval_metric': 'mae',             # Mean Absolute Error
                    'eta': 0.1,                       # Learning rate
                    'max_depth': 6,                   # Tree depth
                    'min_child_weight': 1,            # Minimum data in leaf
                    'subsample': 0.8,                 # Data sampling
                    'colsample_bytree': 0.8,          # Feature sampling
                    'seed': 42                        # Random seed
                }

        # STEP 2: Create DMatrix (XGBoost's data structure)
        # DMatrix is optimized for XGBoost (faster than pandas/numpy)
        if self.model_type == 'rank':
            dtrain = xgb.DMatrix(X_train, label=y_train)
            # Tell XGBoost which riders raced together
            dtrain.set_group(groups_train)
        else:
            dtrain = xgb.DMatrix(X_train, label=y_train)

        # STEP 3: Train the model!
        # num_boost_round = number of trees to build
        # verbose_eval = print progress every N rounds
        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=200,  # Build 200 trees
            verbose_eval=50       # Print progress every 50 trees
        )

        # STEP 4: Extract feature importance
        # This tells us which features the model used most
        # 'gain' = how much each feature improved predictions
        self.feature_importance = self.model.get_score(importance_type='gain')

        print("Training complete!")

    def predict(self, X_test, groups_test=None):
        """
        Make predictions on new data.

        This is where we use the trained model to predict race results!

        How it works:
        1. Take rider's features (avg_position_last_5, wins_last_10, etc.)
        2. Run through all 200 decision trees
        3. Each tree votes on the prediction
        4. Combine votes to get final prediction

        For ranking model:
        - Output = score (higher = better rank)
        - We sort riders by score to get predicted order

        For regression model:
        - Output = predicted position (1.5, 2.3, 3.1, etc.)
        - We round to get final position

        Args:
            X_test: Testing features (2D array)
            groups_test: Group sizes for ranking model

        Returns:
            predictions: Array of predicted scores/positions
        """
        # Create DMatrix for test data
        if self.model_type == 'rank':
            dtest = xgb.DMatrix(X_test)
            dtest.set_group(groups_test)
        else:
            dtest = xgb.DMatrix(X_test)

        # Make predictions!
        predictions = self.model.predict(dtest)
        return predictions

    def evaluate(self, y_true, y_pred, test_df):
        """
        Evaluate model performance with multiple metrics.

        WHY MULTIPLE METRICS?
        Different metrics measure different aspects of performance:
        - MAE/RMSE: How far off are exact position predictions?
        - NDCG: How good is the ranking order?
        - Top-K Accuracy: Did we predict the top finishers?
        - Winner Accuracy: Did we predict the race winner?

        For fantasy racing, Top-K accuracy matters most!
        (You need to pick top finishers, not exact positions)

        Args:
            y_true: Actual positions
            y_pred: Predicted scores/positions
            test_df: Test dataframe with metadata

        Returns:
            Dictionary of evaluation metrics
        """
        print("\n" + "="*70)
        print("MODEL EVALUATION")
        print("="*70)

        # REGRESSION METRICS (for regressor model only)
        if self.model_type == 'regressor':
            # MAE = Mean Absolute Error
            # Example: Predicted [2, 3, 5], Actual [1, 4, 6]
            #          Errors = [1, 1, 1], MAE = 1.0
            mae = mean_absolute_error(y_true, y_pred)

            # RMSE = Root Mean Squared Error (penalizes large errors more)
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))

            print(f"\nRegression Metrics:")
            print(f"  MAE: {mae:.3f} positions")
            print(f"  RMSE: {rmse:.3f} positions")
            print(
                f"  Interpretation: On average, predictions are off by {mae:.1f} positions")

        # RANKING METRICS (for all models)
        print(f"\nRanking Metrics:")

        # Add predictions to test dataframe
        test_df = test_df.copy()
        test_df['predicted_score'] = y_pred

        # Calculate metrics per race
        ndcg_scores = []
        top3_accuracy = []
        top5_accuracy = []

        # Loop through each race
        for group_id in test_df['group_id'].unique():
            group = test_df[test_df['group_id'] == group_id].copy()

            # Convert predicted scores to predicted positions
            if self.model_type == 'rank':
                # For rank model, higher score = better rank
                # So we rank in descending order (highest score = position 1)
                group['predicted_position'] = group['predicted_score'].rank(
                    ascending=False)
            else:
                # For regressor, lower position = better
                # So we rank in ascending order (lowest score = position 1)
                group['predicted_position'] = group['predicted_score'].rank(
                    ascending=True)

            # METRIC 1: NDCG@10 (Normalized Discounted Cumulative Gain)
            # Measures ranking quality for top 10 positions
            # Score of 1.0 = perfect ranking, 0.0 = worst ranking
            # Higher positions matter more (1st place > 10th place)
            ndcg = self._calculate_ndcg(group['position'].values,
                                        group['predicted_position'].values, k=10)
            ndcg_scores.append(ndcg)

            # METRIC 2: Top-3 Accuracy
            # Did we predict any of the actual top 3 finishers?
            # Example: Actual top 3 = [A, B, C], Predicted top 3 = [A, D, E]
            #          Overlap = 1 rider (A), Accuracy = 1/3 = 0.33
            actual_top3 = set(group.nsmallest(3, 'position')['rider'].values)
            predicted_top3 = set(group.nsmallest(
                3, 'predicted_position')['rider'].values)
            top3_acc = len(actual_top3 & predicted_top3) / 3
            top3_accuracy.append(top3_acc)

            # METRIC 3: Top-5 Accuracy
            # Same as top-3 but for top 5 finishers
            actual_top5 = set(group.nsmallest(5, 'position')['rider'].values)
            predicted_top5 = set(group.nsmallest(
                5, 'predicted_position')['rider'].values)
            top5_acc = len(actual_top5 & predicted_top5) / 5
            top5_accuracy.append(top5_acc)

        # Print average metrics across all races
        print(
            f"  NDCG@10: {np.mean(ndcg_scores):.3f} (+/- {np.std(ndcg_scores):.3f})")
        print(
            f"    Interpretation: Ranking quality is {np.mean(ndcg_scores)*100:.1f}% of perfect")
        print(
            f"  Top-3 Accuracy: {np.mean(top3_accuracy):.3f} (+/- {np.std(top3_accuracy):.3f})")
        print(
            f"    Interpretation: We correctly predict {np.mean(top3_accuracy)*3:.1f}/3 podium finishers")
        print(
            f"  Top-5 Accuracy: {np.mean(top5_accuracy):.3f} (+/- {np.std(top5_accuracy):.3f})")
        print(
            f"    Interpretation: We correctly predict {np.mean(top5_accuracy)*5:.1f}/5 top finishers")

        # METRIC 4: Winner Prediction Accuracy
        # Did we correctly predict the race winner?
        # This is the hardest metric (only 1 winner per race!)
        winner_correct = 0
        total_races = 0

        for group_id in test_df['group_id'].unique():
            group = test_df[test_df['group_id'] == group_id].copy()

            # Check if there's a winner in this group (position == 1)
            # Some test splits might have incomplete race data
            winner_rows = group[group['position'] == 1]
            if len(winner_rows) == 0:
                # Skip this race if no winner (incomplete data)
                continue

            # Get actual winner (position == 1)
            actual_winner = winner_rows['rider'].values[0]

            # Get predicted winner (lowest predicted score)
            if self.model_type == 'rank':
                # For rank model, lowest score = best rank
                predicted_winner = group.nsmallest(1, 'predicted_score')[
                    'rider'].values[0]
            else:
                # For regressor, lowest position = best
                predicted_winner = group.nsmallest(1, 'predicted_score')[
                    'rider'].values[0]

            if actual_winner == predicted_winner:
                winner_correct += 1
            total_races += 1

        winner_acc = winner_correct / total_races if total_races > 0 else 0
        print(
            f"  Winner Prediction Accuracy: {winner_acc:.3f} ({winner_correct}/{total_races})")
        print(
            f"    Interpretation: We correctly predict the winner {winner_acc*100:.1f}% of the time")

        return {
            'ndcg': np.mean(ndcg_scores),
            'top3_accuracy': np.mean(top3_accuracy),
            'top5_accuracy': np.mean(top5_accuracy),
            'winner_accuracy': winner_acc
        }

    def _calculate_ndcg(self, y_true, y_pred, k=10):
        """
        Calculate NDCG@k (Normalized Discounted Cumulative Gain).

        NDCG measures ranking quality. It's complicated, but here's the idea:

        1. DCG (Discounted Cumulative Gain):
           - Rewards correct predictions at top positions more
           - Position 1 matters more than position 10
           - Formula uses logarithmic discount

        2. IDCG (Ideal DCG):
           - Best possible DCG (perfect ranking)

        3. NDCG = DCG / IDCG:
           - Normalizes to 0-1 range
           - 1.0 = perfect ranking
           - 0.5 = okay ranking
           - 0.0 = terrible ranking

        Example:
            Actual:    [1, 2, 3, 4, 5]
            Predicted: [1, 3, 2, 4, 5]  → NDCG ≈ 0.95 (very good!)
            Predicted: [5, 4, 3, 2, 1]  → NDCG ≈ 0.20 (terrible!)

        Args:
            y_true: Actual positions
            y_pred: Predicted positions
            k: Number of top positions to consider

        Returns:
            NDCG score (0.0 to 1.0)
        """
        # Sort by predicted ranking and take top k
        order = np.argsort(y_pred)[:k]
        y_true_sorted = y_true[order]

        # Calculate DCG (Discounted Cumulative Gain)
        # Discount factor: 1/log2(position+1)
        # Position 1: 1/log2(2) = 1.0
        # Position 2: 1/log2(3) = 0.63
        # Position 3: 1/log2(4) = 0.5
        # Higher positions have more weight!
        gains = 1.0 / np.log2(np.arange(2, len(y_true_sorted) + 2))
        dcg = np.sum((1.0 / y_true_sorted) * gains)

        # Calculate IDCG (Ideal DCG - best possible)
        ideal_order = np.argsort(y_true)[:k]
        y_true_ideal = y_true[ideal_order]
        idcg = np.sum((1.0 / y_true_ideal) * gains[:len(y_true_ideal)])

        # Normalize: NDCG = DCG / IDCG
        return dcg / idcg if idcg > 0 else 0

    def plot_feature_importance(self, top_n=20):
        """
        Plot which features the model used most.

        Feature importance shows:
        - Which features help predictions most
        - What patterns the model learned
        - Which features we can ignore

        Example insights:
        - "avg_position_last_5 is most important" → Recent form matters!
        - "qual_position is important" → Starting position helps!
        - "rider_number is not important" → Number doesn't predict performance

        This helps us understand the model and improve features.

        Args:
            top_n: Number of top features to show

        Returns:
            DataFrame of feature importance
        """
        if self.feature_importance is None:
            print("No feature importance available")
            return

        # Convert to dataframe and sort
        importance_df = pd.DataFrame([
            {'feature': k, 'importance': v}
            for k, v in self.feature_importance.items()
        ]).sort_values('importance', ascending=False).head(top_n)

        # Create horizontal bar plot
        plt.figure(figsize=(10, 8))
        plt.barh(range(len(importance_df)), importance_df['importance'])
        plt.yticks(range(len(importance_df)), importance_df['feature'])
        plt.xlabel('Importance (Gain)')
        plt.title(
            f'Top {top_n} Feature Importance - {self.model_type.upper()}')
        plt.gca().invert_yaxis()  # Highest importance at top
        plt.tight_layout()

        return importance_df

    def save_model(self, path: str):
        """
        Save trained model to disk for later use.

        We save two files:
        1. Model file (.json): The actual XGBoost model
        2. Metadata file (.pkl): Feature names, importance, settings

        This allows us to:
        - Load model later without retraining
        - Use model in production (real predictions)
        - Share model with others

        Args:
            path: Path to save model (e.g., 'models/rank_450sx.pkl')
        """
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        # Save XGBoost model as JSON (XGBoost format)
        model_path = path.replace('.pkl', '.json')
        self.model.save_model(model_path)

        # Save metadata as pickle (Python format)
        metadata = {
            'model_type': self.model_type,
            'class_filter': self.class_filter,
            'feature_cols': self.feature_cols,
            'feature_importance': self.feature_importance
        }

        with open(path, 'wb') as f:
            pickle.dump(metadata, f)

        print(f"\nModel saved to: {model_path}")
        print(f"Metadata saved to: {path}")


def train_class_specific_models(features, feature_cols, test_size=0.2):
    """
    Train separate models for each class (450sx, 250sxe, 250sxw).

    WHY SEPARATE MODELS?
    - 450sx and 250sx are DIFFERENT competitions
    - Different riders, different skill levels, different dynamics
    - Class-specific models learn class-specific patterns

    Example:
        450sx model learns: "Veterans with 10+ years experience dominate"
        250sx model learns: "Young riders improving rapidly each race"

    Args:
        features: Feature dataframe
        feature_cols: List of feature columns
        test_size: Fraction for testing (0.2 = 20%)

    Returns:
        Dictionary of results for each class
    """
    print("\n" + "="*70)
    print("TRAINING CLASS-SPECIFIC MODELS")
    print("="*70)

    classes = ['450sx', '250sxe', '250sxw']
    results = {}

    for class_name in classes:
        print(f"\n{'='*70}")
        print(f"CLASS: {class_name.upper()}")
        print(f"{'='*70}")

        # Train both model types for this class
        class_results = {}

        for model_type in ['rank', 'regressor']:
            print(f"\n--- {model_type.upper()} MODEL ---")

            # Initialize predictor for this class
            predictor = RacePredictor(
                model_type=model_type, class_filter=class_name)

            # Prepare data (filtered to this class)
            X_train, X_test, y_train, y_test, groups_train, groups_test, train_df, test_df = \
                predictor.prepare_data(
                    features, feature_cols, test_size=test_size)

            # Train
            predictor.train(X_train, y_train, groups_train)

            # Predict
            y_pred = predictor.predict(X_test, groups_test)

            # Evaluate
            metrics = predictor.evaluate(y_test, y_pred, test_df)
            class_results[model_type] = metrics

            # Plot feature importance
            importance_df = predictor.plot_feature_importance(top_n=15)
            plt.savefig(
                f'models/{model_type}_{class_name}_feature_importance.png',
                dpi=150, bbox_inches='tight')
            plt.close()

            # Save model
            predictor.save_model(f'models/{model_type}_{class_name}_model.pkl')

        results[class_name] = class_results

    return results


def train_combined_model(features, feature_cols, test_size=0.2):
    """
    Train a single model on all classes combined.

    WHY COMBINED MODEL?
    - More training data (all classes together)
    - Can learn cross-class patterns
    - Simpler (one model instead of three)
    - Good baseline for comparison

    Uses 'class_encoded' feature to distinguish between classes.

    Args:
        features: Feature dataframe
        feature_cols: List of feature columns
        test_size: Fraction for testing (0.2 = 20%)

    Returns:
        Dictionary of results for combined model
    """
    print("\n" + "="*70)
    print("TRAINING COMBINED MODEL (ALL CLASSES)")
    print("="*70)

    results = {}

    for model_type in ['rank', 'regressor']:
        print(f"\n--- {model_type.upper()} MODEL ---")

        # Initialize predictor (no class filter)
        predictor = RacePredictor(model_type=model_type, class_filter=None)

        # Prepare data (all classes)
        X_train, X_test, y_train, y_test, groups_train, groups_test, train_df, test_df = \
            predictor.prepare_data(features, feature_cols, test_size=test_size)

        # Train
        predictor.train(X_train, y_train, groups_train)

        # Predict
        y_pred = predictor.predict(X_test, groups_test)

        # Evaluate
        metrics = predictor.evaluate(y_test, y_pred, test_df)
        results[model_type] = metrics

        # Plot feature importance
        importance_df = predictor.plot_feature_importance(top_n=15)
        plt.savefig(
            f'models/{model_type}_combined_feature_importance.png',
            dpi=150, bbox_inches='tight')
        plt.close()

        # Save model
        predictor.save_model(f'models/{model_type}_combined_model.pkl')

    return results


def main():
    """
    Main training pipeline - trains all models and compares results.

    This function:
    1. Loads features
    2. Trains class-specific models (450sx, 250sxe, 250sxw)
    3. Trains combined model (all classes)
    4. Compares all models
    5. Recommends best approach

    To run: python src/models/train_models_v2.py
    """
    from src.features.feature_engineering import SupercrossFeatureEngineer

    print("="*70)
    print("SUPERCROSS RACE PREDICTION - MODEL TRAINING V2")
    print("="*70)
    print("\nChanges from V1:")
    print("  ✓ 80-20 train-test split (instead of year-based)")
    print("  ✓ Class-specific models (450sx, 250sxe, 250sxw)")
    print("  ✓ Combined model for comparison")
    print("  ✓ Extensive comments explaining everything")

    # Load features
    features_path = Path('data/processed/features.csv')

    if not features_path.exists():
        print("\nFeatures not found. Creating features...")
        df = pd.read_csv('data/raw/sx_all_results.csv')
        engineer = SupercrossFeatureEngineer()
        features = engineer.create_features(df)
        features.to_csv(features_path, index=False)
        feature_cols = engineer.get_feature_columns(features)
    else:
        print("\nLoading existing features...")
        features = pd.read_csv(features_path)
        engineer = SupercrossFeatureEngineer()
        feature_cols = engineer.get_feature_columns(features)

    print(
        f"Features loaded: {len(features)} records, {len(feature_cols)} features")

    # Train class-specific models
    class_results = train_class_specific_models(
        features, feature_cols, test_size=0.2)

    # Train combined model
    combined_results = train_combined_model(
        features, feature_cols, test_size=0.2)

    # Compare all models
    print("\n" + "="*70)
    print("MODEL COMPARISON")
    print("="*70)

    print("\n--- CLASS-SPECIFIC MODELS ---")
    for class_name, results in class_results.items():
        print(f"\n{class_name.upper()}:")
        comparison = pd.DataFrame(results).T
        print(comparison)

    print("\n--- COMBINED MODEL ---")
    comparison = pd.DataFrame(combined_results).T
    print(comparison)

    # Recommendations
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)

    print("\n1. CLASS-SPECIFIC vs COMBINED:")
    print("   Compare NDCG scores above to see which approach works better")
    print("   Generally, class-specific models perform better because:")
    print("   - 450sx and 250sx are different competitions")
    print("   - Different riders, different dynamics")
    print("   - Models learn class-specific patterns")

    print("\n2. RANK vs REGRESSOR:")
    print("   For fantasy racing, use the model with higher:")
    print("   - Top-3 Accuracy (picking podium finishers)")
    print("   - Top-5 Accuracy (picking top finishers)")
    print("   - Winner Accuracy (picking race winner)")

    print("\n3. USAGE:")
    print("   All models saved in models/ directory")
    print("   Load and use for predictions on future races!")

    return class_results, combined_results


if __name__ == "__main__":
    class_results, combined_results = main()
