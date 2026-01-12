# Project File Structure & Connections

## Visual Diagram: How Everything Connects

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AMASX PROJECT STRUCTURE                              │
└─────────────────────────────────────────────────────────────────────────────┘

                                    START HERE
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  STEP 1: DATA COLLECTION                                                   │
│  ─────────────────────────                                                 │
│                                                                             │
│  📁 src/data/scraper_v2.py                                                 │
│     └─ Scrapes race results from mxgpresults.com                          │
│     └─ Handles special cases (East/West, Triple Crown)                    │
│     └─ Extracts dates, round numbers, event types                         │
│                                                                             │
│  🔧 run_scraper.py                                                         │
│     └─ Runs the scraper for specified years/classes                       │
│                                                                             │
│  OUTPUT: data/raw/sx_all_results.csv (19,861 race results)               │
└───────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  STEP 2: DATA EXPLORATION                                                  │
│  ────────────────────────                                                  │
│                                                                             │
│  📓 notebooks/01_data_exploration.ipynb                                    │
│  📓 notebooks/01_data_exploration_explained.ipynb (Beginner version)      │
│     └─ Load CSV data                                                       │
│     └─ Analyze patterns (top riders, qualifying correlation)              │
│     └─ Check data quality (duplicates, missing values)                    │
│     └─ Create visualizations (charts, graphs)                             │
│     └─ Document findings                                                   │
│                                                                             │
│  INPUT:  data/raw/sx_all_results.csv                                      │
│  OUTPUT: Insights & understanding of the data                             │
└───────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  STEP 3: FEATURE ENGINEERING                                               │
│  ───────────────────────────                                               │
│                                                                             │
│  📁 src/features/feature_engineering.py                                    │
│     └─ SupercrossFeatureEngineer class                                    │
│     └─ Creates 25 features from raw data:                                 │
│         • Historical performance (avg position last 3/5/10 races)         │
│         • Recent form (wins, podiums, best position)                      │
│         • Rider stats (career avg, total races, consistency)              │
│         • Temporal features (year, round number, round %)                 │
│         • Competition context (field size, field strength)                │
│         • Qualifying position                                              │
│                                                                             │
│  INPUT:  data/raw/sx_all_results.csv                                      │
│  OUTPUT: data/processed/features.csv (2,524 records × 25 features)       │
└───────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  STEP 4: MODEL TRAINING                                                    │
│  ──────────────────────                                                    │
│                                                                             │
│  📁 src/models/train_models.py                                             │
│     └─ RacePredictor class                                                │
│     └─ Trains two models:                                                 │
│         • XGBoost Regressor (predicts exact position)                     │
│         • XGBoost Rank (optimizes ranking quality)                        │
│     └─ Splits data: 2023-2024 train, 2025 test                           │
│     └─ Evaluates with multiple metrics                                    │
│     └─ Creates feature importance plots                                   │
│     └─ Saves trained models                                               │
│                                                                             │
│  INPUT:  data/processed/features.csv                                      │
│  OUTPUT: models/regressor_model.json                                      │
│          models/rank_model.json                                           │
│          models/regressor_feature_importance.png                          │
│          models/rank_feature_importance.png                               │
└───────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  STEP 5: PIPELINE ORCHESTRATION                                            │
│  ──────────────────────────────                                            │
│                                                                             │
│  🔧 run_modeling.py                                                        │
│     └─ Runs the entire ML pipeline:                                       │
│         1. Load raw data                                                   │
│         2. Engineer features                                               │
│         3. Train both models                                               │
│         4. Evaluate performance                                            │
│         5. Compare models                                                  │
│         6. Save everything                                                 │
│                                                                             │
│  This is the MAIN script you run to build models!                         │
└───────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  STEP 6: PREDICTIONS (Future)                                              │
│  ────────────────────────────                                              │
│                                                                             │
│  📁 Load saved model (models/regressor_model.json)                        │
│  📁 Get rider stats for upcoming race                                     │
│  📁 Generate features                                                      │
│  📁 Predict finishing positions                                            │
│  📁 Use for fantasy game strategy                                         │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed File Connections

### 1. Data Flow

```
Raw Data → Feature Engineering → Model Training → Predictions
    ↓              ↓                    ↓              ↓
  CSV          Features.csv         Models.json    Predictions
```

### 2. File Dependencies

```
run_modeling.py
    │
    ├─ imports → src/features/feature_engineering.py
    │              └─ uses → data/raw/sx_all_results.csv
    │              └─ creates → data/processed/features.csv
    │
    └─ imports → src/models/train_models.py
                   └─ uses → data/processed/features.csv
                   └─ creates → models/*.json
                   └─ creates → models/*.png
```

### 3. Module Structure

```
AMASX/
│
├── data/
│   ├── raw/
│   │   └── sx_all_results.csv          ← Scraped race results
│   └── processed/
│       └── features.csv                 ← Engineered features
│
├── src/
│   ├── data/
│   │   └── scraper_v2.py               ← Web scraping
│   ├── features/
│   │   └── feature_engineering.py      ← Feature creation
│   └── models/
│       └── train_models.py             ← Model training
│
├── models/
│   ├── regressor_model.json            ← Trained regressor
│   ├── rank_model.json                 ← Trained ranker
│   ├── regressor_model.pkl             ← Model metadata
│   ├── rank_model.pkl                  ← Model metadata
│   ├── regressor_feature_importance.png ← Visualization
│   └── rank_feature_importance.png     ← Visualization
│
├── notebooks/
│   ├── 01_data_exploration.ipynb       ← Analysis
│   └── 01_data_exploration_explained.ipynb ← Beginner guide
│
├── docs/
│   ├── ML_WORKFLOW_GUIDE.md            ← This guide
│   └── FILE_CONNECTIONS_DIAGRAM.md     ← You are here
│
├── run_scraper.py                      ← Run data collection
└── run_modeling.py                     ← Run ML pipeline
```

---

## How to Use This Project

### First Time Setup

1. **Collect Data** (Already done!)
   ```bash
   python run_scraper.py
   ```
   Creates: `data/raw/sx_all_results.csv`

2. **Explore Data** (Optional but recommended)
   ```bash
   jupyter notebook notebooks/01_data_exploration_explained.ipynb
   ```
   Learn: What patterns exist in the data

3. **Build Models**
   ```bash
   python run_modeling.py
   ```
   Creates: Features, trains models, evaluates performance

### When Data Updates

If you manually update `data/raw/sx_all_results.csv`:

```bash
python run_modeling.py
```

This will:
- Regenerate features from updated data
- Retrain both models
- Create new evaluation metrics
- Save updated models

### Making Predictions (Future)

```python
# Load the trained model
import pickle
import xgboost as xgb

# Load model
model = xgb.Booster()
model.load_model('models/regressor_model.json')

# Load metadata (feature names, encoders, etc.)
with open('models/regressor_model.pkl', 'rb') as f:
    metadata = pickle.load(f)

# Prepare features for new race
# ... (use feature_engineering.py)

# Make predictions
predictions = model.predict(features)
```

---

## Key Concepts

### What Each File Does

| File | Purpose | Input | Output |
|------|---------|-------|--------|
| `scraper_v2.py` | Collects race data | Website HTML | CSV file |
| `feature_engineering.py` | Creates ML features | Raw CSV | Features CSV |
| `train_models.py` | Trains ML models | Features CSV | Model files |
| `run_modeling.py` | Orchestrates pipeline | Raw CSV | Everything |
| `01_data_exploration.ipynb` | Analyzes data | Raw CSV | Insights |

### Data Transformations

```
Race Results (Raw)
    ↓
[Feature Engineering]
    ↓
Features (25 columns per rider per race)
    ↓
[Model Training]
    ↓
Trained Model (can predict positions)
    ↓
[Prediction]
    ↓
Predicted Positions (for fantasy game)
```

### Why This Structure?

**Separation of Concerns:**
- `scraper_v2.py` only knows about web scraping
- `feature_engineering.py` only knows about creating features
- `train_models.py` only knows about training models
- `run_modeling.py` connects everything together

**Benefits:**
- Easy to modify one part without breaking others
- Can test each component independently
- Clear data flow from raw → features → models → predictions
- Reusable components (can use feature engineering elsewhere)

---

## Common Workflows

### 1. Update Data & Retrain

```bash
# Manually edit data/raw/sx_all_results.csv
python run_modeling.py
```

### 2. Try Different Features

```python
# Edit src/features/feature_engineering.py
# Add new features to create_features() method
python run_modeling.py  # Retrain with new features
```

### 3. Tune Model Parameters

```python
# Edit src/models/train_models.py
# Modify params in train_rank() or train_regressor()
python run_modeling.py  # Retrain with new parameters
```

### 4. Analyze Results

```bash
# Open Jupyter notebook
jupyter notebook notebooks/01_data_exploration.ipynb
# Load models/regressor_feature_importance.png
# Check model performance metrics
```

---

## Summary

**The Big Picture:**
1. **Scraper** gets data from website → CSV
2. **Feature Engineering** transforms CSV → useful features
3. **Model Training** learns from features → trained model
4. **Pipeline** (run_modeling.py) connects everything
5. **Notebooks** help you understand the data

**Main Entry Points:**
- `run_scraper.py` - Get new data
- `run_modeling.py` - Build models (THIS IS THE MAIN ONE)
- `notebooks/` - Explore and understand

**Key Files to Understand:**
1. `feature_engineering.py` - How features are created
2. `train_models.py` - How models are trained
3. `run_modeling.py` - How everything connects

Next, we'll dive deep into Feature Engineering to understand exactly how raw data becomes useful features for the model!
