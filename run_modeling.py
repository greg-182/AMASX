"""Run feature engineering and model training pipeline"""
import matplotlib.pyplot as plt
import pandas as pd
from src.models.train_models import RacePredictor
from src.features.feature_engineering import SupercrossFeatureEngineer
import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    print("="*70)
    print("SUPERCROSS PREDICTION PIPELINE")
    print("="*70)

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

    print(f"\nFeature list:")
    for col in sorted(feature_cols):
        print(f"  - {col}")

    # Step 2: Model Training
    print("\n" + "="*70)
    print("STEP 2: MODEL TRAINING")
    print("="*70)

    results = {}

    for model_type in ['rank', 'regressor']:
        print(f"\n{'='*70}")
        print(f"Training {model_type.upper()} model")
        print(f"{'='*70}")

        predictor = RacePredictor(model_type=model_type)

        # Prepare data (2023-2024 train, 2025 test)
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
        print("\nPlotting feature importance...")
        importance_df = predictor.plot_feature_importance(top_n=15)

        # Save plot
        plot_path = Path(f'models/{model_type}_feature_importance.png')
        plot_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(plot_path, dpi=150, bbox_inches='tight')
        print(f"✓ Feature importance plot saved: {plot_path}")
        plt.close()

        # Save model
        predictor.save_model(f'models/{model_type}_model.pkl')

    # Step 3: Model Comparison
    print("\n" + "="*70)
    print("STEP 3: MODEL COMPARISON")
    print("="*70)

    comparison = pd.DataFrame(results).T
    print("\nPerformance Metrics:")
    print(comparison.to_string())

    # Determine best model
    print("\n" + "="*70)
    print("RECOMMENDATION")
    print("="*70)

    rank_ndcg = results['rank']['ndcg']
    reg_ndcg = results['regressor']['ndcg']

    if rank_ndcg > reg_ndcg:
        improvement = ((rank_ndcg - reg_ndcg) / reg_ndcg) * 100
        print(f"\n✓ XGBoost Rank is BETTER (+{improvement:.1f}% NDCG)")
        print("\nWhy XGBoost Rank is better for this problem:")
        print("  • Optimized for ranking/ordering predictions")
        print("  • Learns pairwise comparisons between riders")
        print("  • Better captures relative performance")
        print("  • More suitable for fantasy game scoring")
        print("\nRecommendation: Use XGBoost Rank for production")
    else:
        improvement = ((reg_ndcg - rank_ndcg) / rank_ndcg) * 100
        print(f"\n✓ XGBoost Regressor is BETTER (+{improvement:.1f}% NDCG)")
        print("\nRecommendation: Use XGBoost Regressor for production")

    print("\n" + "="*70)
    print("NEXT STEPS")
    print("="*70)
    print("""
1. Explore the Jupyter notebook: notebooks/01_data_exploration.ipynb
2. Review feature importance plots in models/ directory
3. Consider additional features:
   - Track-specific performance
   - Weather conditions
   - Head-to-head records
   - Momentum indicators
4. Tune hyperparameters for better performance
5. Design RL environment for fantasy game strategy
    """)

    print("\n✓ Pipeline complete!")

    return predictor, results, comparison


if __name__ == "__main__":
    predictor, results, comparison = main()
