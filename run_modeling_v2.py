"""
Run complete modeling pipeline with class-specific and combined models

This script trains 8 models total:
- 3 class-specific models × 2 types = 6 models (450sx, 250sxe, 250sxw)
- 1 combined model × 2 types = 2 models
- Total: 8 models (4 rank + 4 regressor)

Then compares all models to find the best approach.
"""
from src.features.feature_engineering import SupercrossFeatureEngineer
from src.models.train_models_v2 import RacePredictor
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path so imports work
sys.path.insert(0, str(Path(__file__).parent))


def train_all_models(features, feature_cols, test_size=0.2):
    """
    Train all 8 models and return results.

    Models trained:
    1. 450sx Rank
    2. 450sx Regressor
    3. 250sxe Rank
    4. 250sxe Regressor
    5. 250sxw Rank
    6. 250sxw Regressor
    7. Combined Rank
    8. Combined Regressor
    """
    all_results = {}

    # Classes to train on
    classes = {
        '450sx': '450sx',
        '250sxe': '250sxe',
        '250sxw': '250sxw',
        'combined': None  # None = all classes
    }

    model_types = ['rank', 'regressor']

    print("\n" + "="*70)
    print("TRAINING ALL MODELS")
    print("="*70)
    print(f"\nTotal models to train: {len(classes) * len(model_types)}")
    print(f"  - 3 class-specific × 2 types = 6 models")
    print(f"  - 1 combined × 2 types = 2 models")
    print(f"  - Total: 8 models")

    model_count = 0

    for class_name, class_filter in classes.items():
        for model_type in model_types:
            model_count += 1

            print(f"\n{'='*70}")
            print(
                f"MODEL {model_count}/8: {class_name.upper()} - {model_type.upper()}")
            print(f"{'='*70}")

            # Initialize predictor
            predictor = RacePredictor(model_type=model_type)

            # Filter data if needed
            # IMPORTANT: Only use MAIN EVENT data (not qualifying/heats/LCQ)
            if class_filter:
                df_filtered = features[
                    (features['class'] == class_filter) &
                    (features['event_type'] == 'main_event')
                ].copy()
                print(
                    f"Filtered to {class_filter} main events: {len(df_filtered)} records")
            else:
                df_filtered = features[features['event_type']
                                       == 'main_event'].copy()
                print(
                    f"Using all classes (main events only): {len(df_filtered)} records")

            # Prepare data with 80-20 split (chronological BY RACE, not by record)
            df_clean = df_filtered.dropna(subset=feature_cols).copy()
            df_clean = df_clean.sort_values(
                ['year', 'round', 'class']).reset_index(drop=True)

            # Create race IDs BEFORE splitting
            df_clean['race_id'] = (df_clean['year'].astype(str) + '_' +
                                   df_clean['round'].astype(str) + '_' +
                                   df_clean['race'] + '_' + df_clean['class'])

            # Get unique races in chronological order
            unique_races = df_clean.groupby('race_id').first().sort_values(
                ['year', 'round']).index.tolist()

            # Split races 80-20
            n_races = len(unique_races)
            split_idx = int(n_races * (1 - test_size))
            train_races = unique_races[:split_idx]
            test_races = unique_races[split_idx:]

            # Split data by race membership
            train_df = df_clean[df_clean['race_id'].isin(train_races)].copy()
            test_df = df_clean[df_clean['race_id'].isin(test_races)].copy()

            print(f"\nData split (by races):")
            print(f"  Total races: {n_races}")
            print(
                f"  Train races: {len(train_races)} ({len(train_races)/n_races*100:.1f}%)")
            print(
                f"  Test races:  {len(test_races)} ({len(test_races)/n_races*100:.1f}%)")
            print(f"  Train records: {len(train_df)}")
            print(f"  Test records:  {len(test_df)}")

            # Extract features and targets
            X_train = train_df[feature_cols].values
            X_test = test_df[feature_cols].values
            y_train = train_df['position'].values
            y_test = test_df['position'].values

            # Create group IDs
            train_df['group_id'] = (train_df['year'].astype(str) + '_' +
                                    train_df['round'].astype(str) + '_' +
                                    train_df['race'] + '_' + train_df['class'])
            test_df['group_id'] = (test_df['year'].astype(str) + '_' +
                                   test_df['round'].astype(str) + '_' +
                                   test_df['race'] + '_' + test_df['class'])

            # Prepare groups for ranking model
            groups_train = None
            groups_test = None

            if model_type == 'rank':
                train_df = train_df.sort_values('group_id')
                test_df = test_df.sort_values('group_id')

                X_train = train_df[feature_cols].values
                X_test = test_df[feature_cols].values
                y_train = train_df['position'].values
                y_test = test_df['position'].values

                groups_train = train_df.groupby('group_id').size().values
                groups_test = test_df.groupby('group_id').size().values

                print(f"  Train groups: {len(groups_train)}")
                print(f"  Test groups:  {len(groups_test)}")

            predictor.feature_cols = feature_cols

            # Train
            print(f"\nTraining...")
            predictor.train(X_train, y_train, groups_train)

            # Predict
            y_pred = predictor.predict(X_test, groups_test)

            # Evaluate
            metrics = predictor.evaluate(y_test, y_pred, test_df)

            # Store results
            model_key = f"{class_name}_{model_type}"
            all_results[model_key] = {
                'class': class_name,
                'model_type': model_type,
                'metrics': metrics,
                'train_size': len(train_df),
                'test_size': len(test_df)
            }

            # Plot and save feature importance
            print("\nSaving feature importance plot...")
            importance_df = predictor.plot_feature_importance(top_n=15)
            plot_path = Path(
                f'models/{model_type}_{class_name}_feature_importance.png')
            plot_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(plot_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"✓ Saved: {plot_path}")

            # Save model
            predictor.save_model(f'models/{model_type}_{class_name}_model.pkl')

    return all_results


def compare_all_models(all_results):
    """
    Compare all 8 models and provide recommendations.
    """
    print("\n" + "="*70)
    print("COMPREHENSIVE MODEL COMPARISON")
    print("="*70)

    # Create comparison dataframe
    comparison_data = []
    for model_key, result in all_results.items():
        row = {
            'Model': model_key,
            'Class': result['class'],
            'Type': result['model_type'],
            'Train Size': result['train_size'],
            'Test Size': result['test_size'],
            'NDCG': result['metrics']['ndcg'],
            'Top-3 Acc': result['metrics']['top3_accuracy'],
            'Top-5 Acc': result['metrics']['top5_accuracy'],
            'Winner Acc': result['metrics']['winner_accuracy']
        }
        comparison_data.append(row)

    comparison_df = pd.DataFrame(comparison_data)

    # Sort by NDCG (best first)
    comparison_df = comparison_df.sort_values('NDCG', ascending=False)

    print("\n" + "="*70)
    print("ALL MODELS RANKED BY NDCG")
    print("="*70)
    print(comparison_df.to_string(index=False))

    # Compare class-specific vs combined
    print("\n" + "="*70)
    print("CLASS-SPECIFIC vs COMBINED")
    print("="*70)

    class_specific = comparison_df[comparison_df['Class'] != 'combined']
    combined = comparison_df[comparison_df['Class'] == 'combined']

    print("\nClass-Specific Models (Average):")
    print(f"  NDCG: {class_specific['NDCG'].mean():.3f}")
    print(f"  Top-3 Accuracy: {class_specific['Top-3 Acc'].mean():.3f}")
    print(f"  Top-5 Accuracy: {class_specific['Top-5 Acc'].mean():.3f}")
    print(f"  Winner Accuracy: {class_specific['Winner Acc'].mean():.3f}")

    print("\nCombined Model (Average):")
    print(f"  NDCG: {combined['NDCG'].mean():.3f}")
    print(f"  Top-3 Accuracy: {combined['Top-3 Acc'].mean():.3f}")
    print(f"  Top-5 Accuracy: {combined['Top-5 Acc'].mean():.3f}")
    print(f"  Winner Accuracy: {combined['Winner Acc'].mean():.3f}")

    if class_specific['NDCG'].mean() > combined['NDCG'].mean():
        improvement = ((class_specific['NDCG'].mean(
        ) - combined['NDCG'].mean()) / combined['NDCG'].mean()) * 100
        print(
            f"\n✓ Class-specific models are BETTER (+{improvement:.1f}% NDCG)")
    else:
        improvement = ((combined['NDCG'].mean(
        ) - class_specific['NDCG'].mean()) / class_specific['NDCG'].mean()) * 100
        print(f"\n✓ Combined model is BETTER (+{improvement:.1f}% NDCG)")

    # Compare rank vs regressor
    print("\n" + "="*70)
    print("RANK vs REGRESSOR")
    print("="*70)

    rank_models = comparison_df[comparison_df['Type'] == 'rank']
    regressor_models = comparison_df[comparison_df['Type'] == 'regressor']

    print("\nRank Models (Average):")
    print(f"  NDCG: {rank_models['NDCG'].mean():.3f}")
    print(f"  Top-3 Accuracy: {rank_models['Top-3 Acc'].mean():.3f}")
    print(f"  Top-5 Accuracy: {rank_models['Top-5 Acc'].mean():.3f}")
    print(f"  Winner Accuracy: {rank_models['Winner Acc'].mean():.3f}")

    print("\nRegressor Models (Average):")
    print(f"  NDCG: {regressor_models['NDCG'].mean():.3f}")
    print(f"  Top-3 Accuracy: {regressor_models['Top-3 Acc'].mean():.3f}")
    print(f"  Top-5 Accuracy: {regressor_models['Top-5 Acc'].mean():.3f}")
    print(f"  Winner Accuracy: {regressor_models['Winner Acc'].mean():.3f}")

    if rank_models['NDCG'].mean() > regressor_models['NDCG'].mean():
        improvement = ((rank_models['NDCG'].mean(
        ) - regressor_models['NDCG'].mean()) / regressor_models['NDCG'].mean()) * 100
        print(f"\n✓ Rank models are BETTER (+{improvement:.1f}% NDCG)")
    else:
        improvement = ((regressor_models['NDCG'].mean(
        ) - rank_models['NDCG'].mean()) / rank_models['NDCG'].mean()) * 100
        print(f"\n✓ Regressor models are BETTER (+{improvement:.1f}% NDCG)")

    # Best model overall
    print("\n" + "="*70)
    print("BEST MODEL OVERALL")
    print("="*70)

    best_model = comparison_df.iloc[0]
    print(f"\n🏆 WINNER: {best_model['Model']}")
    print(f"\n  Class: {best_model['Class']}")
    print(f"  Type: {best_model['Type']}")
    print(f"  NDCG: {best_model['NDCG']:.3f}")
    print(f"  Top-3 Accuracy: {best_model['Top-3 Acc']:.3f}")
    print(f"  Top-5 Accuracy: {best_model['Top-5 Acc']:.3f}")
    print(f"  Winner Accuracy: {best_model['Winner Acc']:.3f}")

    # Recommendations
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)

    print("\n1. BEST APPROACH:")
    if class_specific['NDCG'].mean() > combined['NDCG'].mean():
        print("   ✓ Use CLASS-SPECIFIC models")
        print("     - Train separate models for 450sx, 250sxe, 250sxw")
        print("     - Each model learns class-specific patterns")
        print("     - Better predictions per class")
    else:
        print("   ✓ Use COMBINED model")
        print("     - One model for all classes")
        print("     - More training data")
        print("     - Simpler to maintain")

    print("\n2. BEST MODEL TYPE:")
    if rank_models['NDCG'].mean() > regressor_models['NDCG'].mean():
        print("   ✓ Use RANK models")
        print("     - Better for ranking/ordering predictions")
        print("     - Optimized for fantasy game scoring")
        print("     - Higher Top-K accuracy")
    else:
        print("   ✓ Use REGRESSOR models")
        print("     - Better for exact position predictions")
        print("     - Lower MAE/RMSE")
        print("     - Good baseline performance")

    print("\n3. FOR PRODUCTION:")
    print(f"   ✓ Use: {best_model['Model']}")
    print(
        f"     - File: models/{best_model['Type']}_{best_model['Class']}_model.pkl")
    print(f"     - NDCG: {best_model['NDCG']:.3f}")

    return comparison_df


def main():
    """
    Main pipeline: Feature engineering → Train all models → Compare
    """
    print("="*70)
    print("SUPERCROSS PREDICTION PIPELINE V2")
    print("="*70)
    print("\nThis pipeline will:")
    print("  1. Load/create features")
    print("  2. Train 8 models (3 class-specific + 1 combined) × 2 types")
    print("  3. Compare all models")
    print("  4. Recommend best approach")

    # Step 1: Feature Engineering
    print("\n" + "="*70)
    print("STEP 1: FEATURE ENGINEERING")
    print("="*70)

    features_path = Path('data/processed/features.csv')

    if not features_path.exists():
        print("\nCreating features from raw data...")
        df = pd.read_csv('data/raw/sx_all_results.csv')

        engineer = SupercrossFeatureEngineer()
        features = engineer.create_features(df)

        # Save features
        features_path.parent.mkdir(parents=True, exist_ok=True)
        features.to_csv(features_path, index=False)

        feature_cols = engineer.get_feature_columns(features)
        print(f"\n✓ Features created and saved: {len(feature_cols)} features")
    else:
        print("\nLoading existing features...")
        features = pd.read_csv(features_path)
        engineer = SupercrossFeatureEngineer()
        feature_cols = engineer.get_feature_columns(features)
        print(f"✓ Features loaded: {len(feature_cols)} features")

    print(f"\nDataset summary:")
    print(f"  Total records: {len(features)}")
    print(f"  Classes: {features['class'].unique()}")
    print(f"  Years: {features['year'].unique()}")
    print(f"\nRecords by class:")
    print(features.groupby('class').size())

    # Step 2: Train all models
    print("\n" + "="*70)
    print("STEP 2: TRAIN ALL MODELS")
    print("="*70)

    all_results = train_all_models(features, feature_cols, test_size=0.2)

    # Step 3: Compare all models
    print("\n" + "="*70)
    print("STEP 3: COMPARE ALL MODELS")
    print("="*70)

    comparison_df = compare_all_models(all_results)

    # Save comparison to CSV
    comparison_path = Path('models/model_comparison.csv')
    comparison_df.to_csv(comparison_path, index=False)
    print(f"\n✓ Comparison saved to: {comparison_path}")

    print("\n" + "="*70)
    print("PIPELINE COMPLETE!")
    print("="*70)
    print("\nAll models saved in models/ directory:")
    print("  - 8 model files (.pkl and .json)")
    print("  - 8 feature importance plots (.png)")
    print("  - 1 comparison table (model_comparison.csv)")

    return all_results, comparison_df


if __name__ == "__main__":
    all_results, comparison_df = main()
