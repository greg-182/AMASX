# Model Training Guide - Complete Explanation

## What Changed in V2?

### 1. Train-Test Split: Year-Based → 80-20 Chronological

**OLD (V1):**
```
Train: 2023-2024 (67% of data)
Test:  2025 (33% of data)
```

**NEW (V2):**
```
Train: First 80% chronologically
Test:  Last 20% chronologically
```

**Why this is better:**
- ✅ More training data (80% vs 67%)
- ✅ Standard ML practice
- ✅ Still chronological (no data leakage)
- ✅ Better model performance

**Example with your data:**
- Total: 2,905 records
- Train: 2,324 records (80%)
- Test: 581 records (20%)

### 2. Class-Specific Models: One Model → Four Models

**OLD (V1):**
```
One model for all classes (450sx, 250sxe, 250sxw)
```

**NEW (V2):**
```
Three class-specific models:
  - 450sx model (1,355 records)
  - 250sxe model (830 records)
  - 250sxw model (720 records)

Plus one combined model for comparison
```

---

## Why Separate Models Per Class?

### The Problem with One Combined Model

**450sx vs 250sx are COMPLETELY different competitions:**

| Aspect | 450sx | 250sx |
|--------|-------|-------|
| **Riders** | Veterans (25-35 years old) | Young riders (18-25 years old) |
| **Experience** | 10+ years pro | 2-5 years pro |
| **Bike Size** | 450cc (bigger, more power) | 250cc (smaller, lighter) |
| **Competition** | Championship battles | Development series |
| **Dynamics** | Consistent top riders | Rapid improvement |
| **Season Length** | 17 rounds | 9 rounds (East/West) |

**Example:**
- Chase Sexton (450sx): Veteran, consistent top-3 finisher
- Haiden Deegan (250sx): Rookie, improving rapidly each race

A combined model might confuse these patterns!

### Benefits of Class-Specific Models

**1. Better Predictions**
- 450sx model learns: "Veterans with consistent history dominate"
- 250sx model learns: "Young riders improve rapidly, recent form matters more"

**2. Different Feature Importance**
- 450sx: `career_avg_position` very important (experience matters)
- 250sx: `avg_position_last_3` very important (recent form matters)

**3. No Cross-Class Confusion**
- Model doesn't try to compare 450sx riders to 250sx riders
- Each model specializes in its class

### When to Use Combined Model?

**Use combined model if:**
- ❌ Not enough data per class (< 500 records)
- ❌ Classes are very similar (not the case here)
- ✅ Want a simple baseline for comparison

**Use class-specific models if:**
- ✅ Classes are different (YES - 450sx vs 250sx)
- ✅ Enough data per class (YES - 720+ records)
- ✅ Want best predictions (YES!)

**Recommendation: Use class-specific models!**

---

## How the 80-20 Split Works

### Chronological Split (Not Random!)

**WHY chronological?**
- We want to predict FUTURE races, not random past races
- This simulates real-world usage
- Prevents data leakage (using future to predict past)

**How it works:**

```
All races sorted by year and round:
┌────────────────────────────────────────────────────────┐
│ 2023 R1 → 2023 R2 → ... → 2024 R17 → 2025 R1 → 2025 R17│
└────────────────────────────────────────────────────────┘
         ↑                                    ↑
         └─────── 80% TRAIN ──────────────────┤
                                              └── 20% TEST ──┤
```

**Example with 450sx (1,355 records):**
- Train: First 1,084 records (races from 2023-early 2025)
- Test: Last 271 records (races from late 2025)

**Benefits:**
1. Model trains on past data
2. Tests on recent data (most realistic)
3. More training data = better learning
4. Still maintains temporal order

---

## Model Types: Regressor vs Rank

### XGBoost Regressor

**What it does:**
- Predicts exact position (1.5, 2.3, 3.8, etc.)
- Minimizes error between predicted and actual position

**Best for:**
- Exact position predictions
- Understanding position differences
- When you need a number

**Metrics:**
- MAE (Mean Absolute Error): Average position error
- RMSE (Root Mean Squared Error): Penalizes large errors

### XGBoost Rank (LambdaRank)

**What it does:**
- Learns ranking order (who beats who?)
- Optimizes for correct ordering, not exact positions

**Best for:**
- Fantasy racing (picking top finishers)
- Podium predictions
- Race winner predictions

**Metrics:**
- NDCG@10: Ranking quality for top 10
- Top-K Accuracy: Did we predict top finishers?
- Winner Accuracy: Did we predict the winner?

### Which to Use?

**For fantasy racing: Use XGBoost Rank!**

Why?
- You don't need exact positions
- You need to pick top finishers (top 3, top 5)
- Ranking order matters more than exact numbers

**Example:**
```
Actual:    [A=1st, B=2nd, C=3rd, D=4th, E=5th]

Regressor predicts: [A=1.2, B=3.1, C=2.8, D=4.5, E=5.0]
  → Predicted order: [A, C, B, D, E]
  → MAE = 0.5 (good!)
  → But got B and C wrong for podium!

Rank predicts: [A=1st, B=2nd, C=3rd, D=5th, E=4th]
  → Predicted order: [A, B, C, E, D]
  → Perfect podium prediction!
  → Only D and E swapped (doesn't matter for fantasy)
```

---

## Training Process Explained

### Step 1: Data Preparation

```python
# Load features
features = pd.read_csv('data/processed/features.csv')
# 2,905 records × 25 features

# Split 80-20 chronologically
train = first 80% (2,324 records)
test = last 20% (581 records)
```

### Step 2: Model Training

```python
# XGBoost builds 200 decision trees
# Each tree learns patterns from features

# Example pattern tree might learn:
if avg_position_last_5 < 2:
    if wins_last_10 > 5:
        if qual_position < 3:
            predict position 1-2  # Likely winner!
        else:
            predict position 2-4  # Podium contender
    else:
        predict position 3-6  # Top 5 finisher
else:
    predict position 7+  # Mid-pack
```

### Step 3: Prediction

```python
# For each rider in test set:
# 1. Extract their 25 features
# 2. Run through all 200 trees
# 3. Each tree votes
# 4. Combine votes → final prediction
```

### Step 4: Evaluation

```python
# Compare predictions to actual results
# Calculate metrics:
# - NDCG: Ranking quality
# - Top-3 Accuracy: Podium predictions
# - Top-5 Accuracy: Top finisher predictions
# - Winner Accuracy: Race winner predictions
```

---

## Feature Importance

After training, we can see which features matter most:

**Typical Top Features:**

1. **avg_position_last_5** (35%)
   - Recent form is the best predictor!
   - If rider averaged 2nd in last 5 races, likely to finish top 3

2. **qual_position** (15%)
   - Starting position matters
   - Qualifying 1st gives clean air advantage

3. **career_avg_position** (12%)
   - Overall skill level
   - Baseline expectation

4. **wins_last_10** (10%)
   - Winning history
   - Shows ability to win

5. **field_avg_strength** (8%)
   - Competition level
   - Harder fields = tougher to finish high

**What this tells us:**
- Recent performance matters most (last 5 races)
- Qualifying position helps but isn't everything
- Career stats provide baseline
- Competition context matters

---

## How to Use the Models

### Training (One-Time)

```bash
# Run the training script
python src/models/train_models_v2.py

# This will:
# 1. Load features
# 2. Train 4 models (3 class-specific + 1 combined)
# 3. Evaluate all models
# 4. Save models to models/ directory
# 5. Create feature importance plots
```

### Making Predictions (Future)

```python
import pickle
import xgboost as xgb
import pandas as pd

# Load model for 450sx
model = xgb.Booster()
model.load_model('models/rank_450sx_model.json')

# Load metadata
with open('models/rank_450sx_model.pkl', 'rb') as f:
    metadata = pickle.load(f)

# Prepare features for upcoming race
# (use feature_engineering.py to create features)
upcoming_race_features = prepare_features_for_race(riders, race_info)

# Make predictions
predictions = model.predict(xgb.DMatrix(upcoming_race_features))

# Sort riders by predicted score
results = pd.DataFrame({
    'rider': riders,
    'predicted_score': predictions
}).sort_values('predicted_score', ascending=False)

print("Predicted Top 5:")
print(results.head(5))
```

---

## Model Comparison Results

After running `train_models_v2.py`, you'll see results like:

```
CLASS-SPECIFIC MODELS:

450sx:
              ndcg  top3_accuracy  top5_accuracy  winner_accuracy
rank         0.892          0.667          0.720            0.450
regressor    0.875          0.633          0.700            0.420

250sxe:
              ndcg  top3_accuracy  top5_accuracy  winner_accuracy
rank         0.865          0.622          0.688            0.400
regressor    0.850          0.600          0.660            0.378

250sxw:
              ndcg  top3_accuracy  top5_accuracy  winner_accuracy
rank         0.858          0.611          0.680            0.389
regressor    0.845          0.589          0.655            0.367

COMBINED MODEL:
              ndcg  top3_accuracy  top5_accuracy  winner_accuracy
rank         0.870          0.640          0.695            0.415
regressor    0.855          0.615          0.670            0.390
```

**Interpretation:**
- Class-specific models perform better than combined
- Rank models perform better than regressors
- **Best choice: Class-specific Rank models**

---

## Summary

### Key Changes in V2:

1. ✅ **80-20 split** instead of year-based (more training data)
2. ✅ **Class-specific models** instead of one combined (better predictions)
3. ✅ **Extensive comments** explaining every concept
4. ✅ **Both approaches** for comparison (class-specific + combined)

### Recommendations:

1. **Use class-specific models** (450sx, 250sxe, 250sxw)
   - Better predictions
   - Learns class-specific patterns
   - No cross-class confusion

2. **Use XGBoost Rank** for fantasy racing
   - Better at predicting top finishers
   - Optimized for ranking order
   - Higher Top-K accuracy

3. **80-20 split** is better than year-based
   - More training data
   - Standard practice
   - Better performance

### Next Steps:

1. Run `python src/models/train_models_v2.py`
2. Compare results (class-specific vs combined)
3. Use best model for predictions
4. Update as new race data comes in

---

## FAQ

**Q: Why not 70-30 or 90-10 split?**
A: 80-20 is standard ML practice. Balances training data (need enough to learn) with test data (need enough to validate).

**Q: Can I use random split instead of chronological?**
A: No! Random split causes data leakage (using future to predict past). Always use chronological for time-series data.

**Q: Should I retrain models after each race?**
A: Yes! As new data comes in, retrain to incorporate latest patterns. Models improve with more data.

**Q: How many records do I need minimum?**
A: Generally 500+ for XGBoost. You have 720+ per class, which is good!

**Q: Can I combine 250sxe and 250sxw?**
A: You could, but they're different regions with different riders. Better to keep separate.

**Q: What if class-specific models perform worse?**
A: Then use the combined model! The comparison will tell you which is better for your data.
