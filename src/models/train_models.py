"""Train XGBoost and XGBoost Rank models for race prediction"""
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
import pickle


class RacePredictor:
    """Train and evaluate race prediction models"""

    def __init__(self, model_type='rank'):
        """
        Args:
            model_type: 'rank' for XGBoost Rank, 'regressor' for standard XGBoost
        """
        self.model_type = model_type
        self.model = None
        self.feature_cols = None
        self.feature_importance = None

    def prepare_data(self, df: pd.DataFrame, feature_cols: list,
                     test_year: int = 2025) -> tuple:
        """
        Split data into train/test by year

        Args:
            df: Feature dataframe
            feature_cols: List of feature column names
            test_year: Year to use for testing

        Returns:
            X_train, X_test, y_train, y_test, groups_train, groups_test
        """
        print(f"\nPreparing data (test year: {test_year})...")

        # Remove rows with missing features
        df_clean = df.dropna(subset=feature_cols)
        print(f"  Records after removing missing: {len(df_clean)}")

        # Split by year
        train_mask = df_clean['year'] < test_year
        test_mask = df_clean['year'] == test_year

        train_df = df_clean[train_mask].copy()
        test_df = df_clean[test_mask].copy()

        print(
            f"  Train records: {len(train_df)} ({train_df['year'].min()}-{train_df['year'].max()})")
        print(f"  Test records: {len(test_df)} (year {test_year})")

        # Prepare features and target
        X_train = train_df[feature_cols].values
        X_test = test_df[feature_cols].values
        y_train = train_df['position'].values
        y_test = test_df['position'].values

        # Create group_id for both models (needed for evaluation)
        train_df['group_id'] = (train_df['year'].astype(str) + '_' +
                                train_df['round'].astype(str) + '_' +
                                train_df['race'] + '_' + train_df['class'])
        test_df['group_id'] = (test_df['year'].astype(str) + '_' +
                               test_df['round'].astype(str) + '_' +
                               test_df['race'] + '_' + test_df['class'])

        # For ranking model, prepare groups
        groups_train = None
        groups_test = None

        if self.model_type == 'rank':
            # Sort by group
            train_df = train_df.sort_values('group_id')
            test_df = test_df.sort_values('group_id')

            # Recompute X, y after sorting
            X_train = train_df[feature_cols].values
            X_test = test_df[feature_cols].values
            y_train = train_df['position'].values
            y_test = test_df['position'].values

            # Get group sizes
            groups_train = train_df.groupby('group_id').size().values
            groups_test = test_df.groupby('group_id').size().values

            print(f"  Train groups: {len(groups_train)}")
            print(f"  Test groups: {len(groups_test)}")

        self.feature_cols = feature_cols

        return X_train, X_test, y_train, y_test, groups_train, groups_test, train_df, test_df

    def train(self, X_train, y_train, groups_train=None, params=None):
        """Train the model"""
        print(f"\nTraining {self.model_type} model...")

        if params is None:
            if self.model_type == 'rank':
                params = {
                    'objective': 'rank:pairwise',
                    'eval_metric': 'ndcg',
                    'eta': 0.1,
                    'max_depth': 6,
                    'min_child_weight': 1,
                    'subsample': 0.8,
                    'colsample_bytree': 0.8,
                    'seed': 42
                }
            else:
                params = {
                    'objective': 'reg:squarederror',
                    'eval_metric': 'mae',
                    'eta': 0.1,
                    'max_depth': 6,
                    'min_child_weight': 1,
                    'subsample': 0.8,
                    'colsample_bytree': 0.8,
                    'seed': 42
                }

        # Create DMatrix
        if self.model_type == 'rank':
            dtrain = xgb.DMatrix(X_train, label=y_train)
            dtrain.set_group(groups_train)
        else:
            dtrain = xgb.DMatrix(X_train, label=y_train)

        # Train
        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=200,
            verbose_eval=50
        )

        # Get feature importance
        self.feature_importance = self.model.get_score(importance_type='gain')

        print("Training complete!")

    def predict(self, X_test, groups_test=None):
        """Make predictions"""
        if self.model_type == 'rank':
            dtest = xgb.DMatrix(X_test)
            dtest.set_group(groups_test)
        else:
            dtest = xgb.DMatrix(X_test)

        predictions = self.model.predict(dtest)
        return predictions

    def evaluate(self, y_true, y_pred, test_df):
        """Evaluate model performance"""
        print("\n" + "="*70)
        print("MODEL EVALUATION")
        print("="*70)

        if self.model_type == 'regressor':
            # Regression metrics
            mae = mean_absolute_error(y_true, y_pred)
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))

            print(f"\nRegression Metrics:")
            print(f"  MAE: {mae:.3f}")
            print(f"  RMSE: {rmse:.3f}")

        # Ranking metrics
        print(f"\nRanking Metrics:")

        # Add predictions to test dataframe
        test_df = test_df.copy()
        test_df['predicted_score'] = y_pred

        # Calculate ranking metrics per race
        ndcg_scores = []
        top3_accuracy = []
        top5_accuracy = []

        for group_id in test_df['group_id'].unique():
            group = test_df[test_df['group_id'] == group_id].copy()

            # Sort by predicted score (lower is better for ranking)
            if self.model_type == 'rank':
                # For rank model, higher score = better rank
                group['predicted_position'] = group['predicted_score'].rank(
                    ascending=False)
            else:
                # For regressor, lower position = better
                group['predicted_position'] = group['predicted_score'].rank(
                    ascending=True)

            # NDCG@10
            ndcg = self._calculate_ndcg(group['position'].values,
                                        group['predicted_position'].values, k=10)
            ndcg_scores.append(ndcg)

            # Top-3 accuracy (did we predict any of top 3?)
            actual_top3 = set(group.nsmallest(3, 'position')['rider'].values)
            predicted_top3 = set(group.nsmallest(
                3, 'predicted_position')['rider'].values)
            top3_acc = len(actual_top3 & predicted_top3) / 3
            top3_accuracy.append(top3_acc)

            # Top-5 accuracy
            actual_top5 = set(group.nsmallest(5, 'position')['rider'].values)
            predicted_top5 = set(group.nsmallest(
                5, 'predicted_position')['rider'].values)
            top5_acc = len(actual_top5 & predicted_top5) / 5
            top5_accuracy.append(top5_acc)

        print(
            f"  NDCG@10: {np.mean(ndcg_scores):.3f} (+/- {np.std(ndcg_scores):.3f})")
        print(
            f"  Top-3 Accuracy: {np.mean(top3_accuracy):.3f} (+/- {np.std(top3_accuracy):.3f})")
        print(
            f"  Top-5 Accuracy: {np.mean(top5_accuracy):.3f} (+/- {np.std(top5_accuracy):.3f})")

        # Winner prediction accuracy
        winner_correct = 0
        total_races = 0

        for group_id in test_df['group_id'].unique():
            group = test_df[test_df['group_id'] == group_id].copy()
            actual_winner = group[group['position'] == 1]['rider'].values[0]

            if self.model_type == 'rank':
                # For rank model, lower score = better rank
                predicted_winner = group.nsmallest(1, 'predicted_score')[
                    'rider'].values[0]
            else:
                # For regressor, use predicted_score directly (lower position = better)
                predicted_winner = group.nsmallest(1, 'predicted_score')[
                    'rider'].values[0]

            if actual_winner == predicted_winner:
                winner_correct += 1
            total_races += 1

        winner_acc = winner_correct / total_races
        print(
            f"  Winner Prediction Accuracy: {winner_acc:.3f} ({winner_correct}/{total_races})")

        return {
            'ndcg': np.mean(ndcg_scores),
            'top3_accuracy': np.mean(top3_accuracy),
            'top5_accuracy': np.mean(top5_accuracy),
            'winner_accuracy': winner_acc
        }

    def _calculate_ndcg(self, y_true, y_pred, k=10):
        """Calculate NDCG@k"""
        # Sort by predicted ranking
        order = np.argsort(y_pred)[:k]
        y_true_sorted = y_true[order]

        # DCG
        gains = 1.0 / np.log2(np.arange(2, len(y_true_sorted) + 2))
        dcg = np.sum((1.0 / y_true_sorted) * gains)

        # IDCG (ideal)
        ideal_order = np.argsort(y_true)[:k]
        y_true_ideal = y_true[ideal_order]
        idcg = np.sum((1.0 / y_true_ideal) * gains[:len(y_true_ideal)])

        return dcg / idcg if idcg > 0 else 0

    def plot_feature_importance(self, top_n=20):
        """Plot feature importance"""
        if self.feature_importance is None:
            print("No feature importance available")
            return

        # Convert to dataframe
        importance_df = pd.DataFrame([
            {'feature': k, 'importance': v}
            for k, v in self.feature_importance.items()
        ]).sort_values('importance', ascending=False).head(top_n)

        # Plot
        plt.figure(figsize=(10, 8))
        plt.barh(range(len(importance_df)), importance_df['importance'])
        plt.yticks(range(len(importance_df)), importance_df['feature'])
        plt.xlabel('Importance (Gain)')
        plt.title(
            f'Top {top_n} Feature Importance - {self.model_type.upper()}')
        plt.gca().invert_yaxis()
        plt.tight_layout()

        return importance_df

    def save_model(self, path: str):
        """Save model to disk"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        # Save XGBoost model
        model_path = path.replace('.pkl', '.json')
        self.model.save_model(model_path)

        # Save metadata
        metadata = {
            'model_type': self.model_type,
            'feature_cols': self.feature_cols,
            'feature_importance': self.feature_importance
        }

        with open(path, 'wb') as f:
            pickle.dump(metadata, f)

        print(f"\nModel saved to: {model_path}")
        print(f"Metadata saved to: {path}")


def main():
    """Train both models and compare"""
    from src.features.feature_engineering import SupercrossFeatureEngineer

    print("="*70)
    print("SUPERCROSS RACE PREDICTION - MODEL TRAINING")
    print("="*70)

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

    # Train both models
    results = {}

    for model_type in ['rank', 'regressor']:
        print("\n" + "="*70)
        print(f"TRAINING {model_type.upper()} MODEL")
        print("="*70)

        predictor = RacePredictor(model_type=model_type)

        # Prepare data
        X_train, X_test, y_train, y_test, groups_train, groups_test, train_df, test_df = \
            predictor.prepare_data(features, feature_cols, test_year=2025)

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
            f'models/{model_type}_feature_importance.png', dpi=150, bbox_inches='tight')
        plt.show()

        # Save model
        predictor.save_model(f'models/{model_type}_model.pkl')

    # Compare models
    print("\n" + "="*70)
    print("MODEL COMPARISON")
    print("="*70)

    comparison = pd.DataFrame(results).T
    print(comparison)

    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)

    if results['rank']['ndcg'] > results['regressor']['ndcg']:
        print("\n✓ XGBoost Rank performs better for ranking predictions")
        print("  Use this for predicting race order and top finishers")
    else:
        print("\n✓ XGBoost Regressor performs better")
        print("  Consider using this for position prediction")

    print("\nBoth models saved in models/ directory")

    return predictor, results


if __name__ == "__main__":
    predictor, results = main()
