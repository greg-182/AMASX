"""
Predict race results for upcoming races

This script predicts top 20 finishers for 450sx, 250sxe, and 250sxw classes.

Usage:
    # Predict WITHOUT qualifying (before qualifying happens)
    python predict_race.py --year 2026 --round 1 --race "Anaheim I" --no-qual

    # Predict WITH qualifying (after qualifying, before main event)
    python predict_race.py --year 2026 --round 1 --race "Anaheim I" --qual-file data/2026_anaheim1_qual.csv

Features:
- Predicts with or without qualifying results
- Uses trained models (rank or regressor)
- Outputs top 20 predictions per class
- Shows prediction confidence
"""

from src.features.feature_engineering import SupercrossFeatureEngineer
import pandas as pd
import numpy as np
import xgboost as xgb
import pickle
import argparse
from pathlib import Path
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))


def load_model(model_path):
    """
    Load trained model and metadata.

    Args:
        model_path: Path to model .pkl file (e.g., 'models/regressor_450sx_model.pkl')

    Returns:
        model: XGBoost model
        metadata: Model metadata (feature columns, etc.)
    """
    # Load metadata
    with open(model_path, 'rb') as f:
        metadata = pickle.load(f)

    # Load XGBoost model
    model_json = str(model_path).replace('.pkl', '.json')
    model = xgb.Booster()
    model.load_model(model_json)

    return model, metadata


def prepare_rider_list(class_type, historical_data):
    """
    Get list of riders likely to race in this class.

    Uses riders who raced in MAIN EVENTS in this class in the last season.
    Filters out LCQ/qualifying-only riders.

    Args:
        class_type: '450sx', '250sxe', or '250sxw'
        historical_data: DataFrame with historical race results

    Returns:
        DataFrame with rider information
    """
    # Get riders from last season in this class - MAIN EVENTS ONLY
    last_season = historical_data['year'].max()
    class_riders = historical_data[
        (historical_data['class'] == class_type) &
        (historical_data['year'] == last_season) &
        (historical_data['event_type'] == 'main_event')
    ].copy()

    # Get unique riders with their most common bike and number
    riders = class_riders.groupby('rider').agg({
        'bike': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0],
        'number': lambda x: x.mode()[0] if len(x.mode()) > 0 else x.iloc[0],
        'position': 'mean'  # Track average position for filtering
    }).reset_index()

    # Filter to riders who likely make main events (avg position < 22)
    # Main events typically have ~22 riders
    riders = riders[riders['position'] < 22].copy()
    riders = riders.drop('position', axis=1)

    return riders


def create_prediction_features(riders, class_type, year, round_num, race_name,
                               historical_data, engineer, qual_results=None):
    """
    Create features for prediction.

    This builds the feature matrix for riders in the upcoming race.

    Args:
        riders: DataFrame with rider, bike, number
        class_type: '450sx', '250sxe', or '250sxw'
        year: Race year (2026)
        round_num: Round number (1 for Anaheim I)
        race_name: Race name ("Anaheim I")
        historical_data: Historical race results
        engineer: SupercrossFeatureEngineer instance
        qual_results: Optional DataFrame with qualifying results (rider, qual_position)

    Returns:
        DataFrame with features for each rider
    """
    # Create base race data
    race_data = []
    for _, rider_info in riders.iterrows():
        race_data.append({
            'year': year,
            'round': round_num,
            'race': race_name,
            'class': class_type,
            'rider': rider_info['rider'],
            'bike': rider_info['bike'],
            'number': rider_info['number'],
            'position': np.nan,  # Unknown (we're predicting this!)
            'event_type': 'main_event'
        })

    race_df = pd.DataFrame(race_data)

    # Combine with historical data
    combined = pd.concat([historical_data, race_df], ignore_index=True)

    # Create features
    features = engineer.create_features(combined)

    # Get only the prediction rows (last len(riders) rows)
    prediction_features = features.tail(len(riders)).copy()

    # Add qualifying results if provided
    if qual_results is not None:
        qual_dict = dict(
            zip(qual_results['rider'], qual_results['qual_position']))
        prediction_features['qual_position'] = prediction_features['rider'].map(
            qual_dict)
    else:
        # Use median qualifying position as default (mid-pack start)
        # This is a reasonable assumption when qualifying hasn't happened yet
        prediction_features['qual_position'] = prediction_features['qual_position'].fillna(
            11.0)

    return prediction_features


def predict_race(class_type, year, round_num, race_name, model_type='regressor',
                 qual_results=None, top_n=20):
    """
    Predict race results for a specific class.

    Args:
        class_type: '450sx', '250sxe', or '250sxw'
        year: Race year (2026)
        round_num: Round number (1-17)
        race_name: Race name ("Anaheim I")
        model_type: 'rank' or 'regressor'
        qual_results: Optional DataFrame with qualifying results
        top_n: Number of top predictions to show (default 20)

    Returns:
        DataFrame with predictions
    """
    print(f"\n{'='*70}")
    print(f"PREDICTING: {year} {race_name} - {class_type.upper()}")
    print(f"{'='*70}")

    # Load historical data
    historical_path = Path('data/raw/sx_all_results.csv')
    if not historical_path.exists():
        print(f"Error: Historical data not found at {historical_path}")
        return None

    historical_data = pd.read_csv(historical_path)

    # Load model
    model_path = Path(f'models/{model_type}_{class_type}_model.pkl')
    if not model_path.exists():
        print(f"Error: Model not found at {model_path}")
        print(f"Please train the model first using: python run_modeling_v2.py")
        return None

    model, metadata = load_model(model_path)
    feature_cols = metadata['feature_cols']

    print(f"Model loaded: {model_type}_{class_type}")
    print(
        f"Qualifying: {'Included' if qual_results is not None else 'Not included (using default)'}")

    # Get rider list
    riders = prepare_rider_list(class_type, historical_data)
    print(f"Riders in field: {len(riders)}")

    # Create features
    engineer = SupercrossFeatureEngineer()
    prediction_features = create_prediction_features(
        riders, class_type, year, round_num, race_name,
        historical_data, engineer, qual_results
    )

    # Check for missing features
    missing_features = prediction_features[feature_cols].isnull().sum()
    if missing_features.sum() > 0:
        print(f"\nWarning: Some features have missing values:")
        print(missing_features[missing_features > 0])
        print("Filling with median values...")
        prediction_features[feature_cols] = prediction_features[feature_cols].fillna(
            prediction_features[feature_cols].median()
        )

    # Make predictions
    X = prediction_features[feature_cols].values
    dmatrix = xgb.DMatrix(X)
    predictions = model.predict(dmatrix)

    # Create results DataFrame
    results = prediction_features[['rider', 'bike', 'number']].copy()
    results['predicted_score'] = predictions

    # Convert scores to predicted positions
    if model_type == 'rank':
        # For rank model, lower score = better rank
        results['predicted_position'] = results['predicted_score'].rank(
            ascending=True)
    else:
        # For regressor, score IS the predicted position
        results['predicted_position'] = results['predicted_score']

    # Sort by predicted position
    results = results.sort_values('predicted_position').reset_index(drop=True)
    results['predicted_position'] = range(1, len(results) + 1)

    # Show top N
    print(f"\n{'='*70}")
    print(f"TOP {top_n} PREDICTIONS")
    print(f"{'='*70}")
    print(f"\n{'Pos':<5} {'Rider':<25} {'Bike':<12} {'Number':<8} {'Score':<10}")
    print("-" * 70)

    for idx, row in results.head(top_n).iterrows():
        print(f"{row['predicted_position']:<5.0f} {row['rider']:<25} {row['bike']:<12} "
              f"{row['number']:<8.0f} {row['predicted_score']:<10.2f}")

    return results


def main():
    """
    Main prediction workflow.
    """
    parser = argparse.ArgumentParser(
        description='Predict supercross race results')
    parser.add_argument('--year', type=int, default=2026, help='Race year')
    parser.add_argument('--round', type=int, default=1, help='Round number')
    parser.add_argument('--race', type=str,
                        default='Anaheim I', help='Race name')
    parser.add_argument('--class-type', type=str, default='all',
                        choices=['all', '450sx', '250sxe', '250sxw'],
                        help='Class to predict (default: all)',
                        dest='class_type')
    parser.add_argument('--model', type=str, default='regressor',
                        choices=['rank', 'regressor'],
                        help='Model type to use')
    parser.add_argument('--qual-file', type=str, default=None,
                        help='CSV file with qualifying results (rider, qual_position)')
    parser.add_argument('--no-qual', action='store_true',
                        help='Predict without qualifying results')
    parser.add_argument('--top-n', type=int, default=20,
                        help='Number of top predictions to show')
    parser.add_argument('--output', type=str, default=None,
                        help='Save predictions to CSV file')

    args = parser.parse_args()

    print("="*70)
    print("SUPERCROSS RACE PREDICTION")
    print("="*70)
    print(f"\nRace: {args.year} {args.race} (Round {args.round})")
    print(f"Model: {args.model}")

    # Load qualifying results if provided
    qual_results = None
    if args.qual_file and not args.no_qual:
        qual_results = pd.read_csv(args.qual_file)
        print(f"Qualifying results loaded from: {args.qual_file}")
    elif args.no_qual:
        print("Predicting WITHOUT qualifying results")

    # Determine which classes to predict
    if args.class_type == 'all':
        classes = ['450sx', '250sxe', '250sxw']
    else:
        classes = [args.class_type]

    # Predict for each class
    all_predictions = {}
    for class_type in classes:
        predictions = predict_race(
            class_type=class_type,
            year=args.year,
            round_num=args.round,
            race_name=args.race,
            model_type=args.model,
            qual_results=qual_results,
            top_n=args.top_n
        )

        if predictions is not None:
            all_predictions[class_type] = predictions

    # Save to file if requested
    if args.output and all_predictions:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Combine all predictions
        for class_type, predictions in all_predictions.items():
            predictions['class'] = class_type

        combined = pd.concat(all_predictions.values(), ignore_index=True)
        combined.to_csv(output_path, index=False)
        print(f"\n✓ Predictions saved to: {output_path}")

    print("\n" + "="*70)
    print("PREDICTION COMPLETE")
    print("="*70)

    return all_predictions


if __name__ == "__main__":
    predictions = main()
