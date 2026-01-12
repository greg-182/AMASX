# Machine Learning Workflow Guide for Beginners

## What is Machine Learning?

Machine Learning (ML) is teaching a computer to make predictions based on patterns it finds in data. Think of it like teaching a child to recognize animals:
- You show them many pictures of cats and dogs (training data)
- They learn the patterns (cats have pointy ears, dogs have floppy ears)
- They can then identify new animals they've never seen before (predictions)

In our case, we're teaching the computer to predict race results based on historical performance.

---

## The Complete ML Pipeline (Step-by-Step)

```
┌─────────────────────────────────────────────────────────────────┐
│                    MACHINE LEARNING PIPELINE                     │
└─────────────────────────────────────────────────────────────────┘

1. DATA COLLECTION
   ├─ Scrape race results from websites
   ├─ Clean and organize the data
   └─ Save to CSV files
   
   📁 Files: data/raw/sx_all_results.csv
   🎯 Goal: Get historical race data (2023-2025)

2. DATA EXPLORATION (Understanding Your Data)
   ├─ Look at the data to understand what we have
   ├─ Find patterns (who wins most? does qualifying matter?)
   ├─ Check for problems (missing data, errors)
   └─ Visualize trends with charts
   
   📁 Files: notebooks/01_data_exploration.ipynb
   🎯 Goal: Understand the data before building models

3. FEATURE ENGINEERING (Creating Useful Information)
   ├─ Transform raw data into useful "features"
   ├─ Example: "average position in last 5 races"
   ├─ Calculate historical statistics for each rider
   └─ Create new columns that help predict performance
   
   📁 Files: src/features/feature_engineering.py
   🎯 Goal: Create meaningful inputs for the model

4. MODEL TRAINING (Teaching the Computer)
   ├─ Split data: Old races for training, new races for testing
   ├─ Feed training data to the algorithm (XGBoost)
   ├─ Algorithm learns patterns (who performs well when?)
   └─ Test on new data to see if it learned correctly
   
   📁 Files: src/models/train_models.py
   🎯 Goal: Build a model that can predict race results

5. MODEL EVALUATION (Checking Performance)
   ├─ Compare predictions vs actual results
   ├─ Calculate accuracy metrics
   ├─ See which features are most important
   └─ Decide if model is good enough
   
   📁 Files: src/models/train_models.py (evaluate method)
   🎯 Goal: Measure how well the model works

6. PREDICTION (Using the Model)
   ├─ Input: Rider stats before a race
   ├─ Model: Calculates predicted finishing position
   └─ Output: "Rider X will finish in position Y"
   
   🎯 Goal: Make predictions for future races
```

---

## Key Concepts Explained Simply

### 1. **Features** (Input Variables)
Think of features as "clues" that help predict the outcome.

**Example:**
- Feature: "Average position in last 5 races"
- If a rider averaged position 2 → They're likely to finish near the front
- If a rider averaged position 15 → They're likely to finish mid-pack

**Our Features:**
- Historical performance (past race results)
- Qualifying position (starting position)
- Recent form (wins, podiums)
- Competition level (field strength)

### 2. **Target** (What We're Predicting)
The target is what we want to predict.

**Our Target:** Finishing position in the main event (1st, 2nd, 3rd, etc.)

### 3. **Training Data** (Learning Material)
Data the model uses to learn patterns.

**Our Training Data:** 2023-2024 race results

### 4. **Test Data** (Exam Questions)
Data the model has never seen, used to check if it learned correctly.

**Our Test Data:** 2025 race results

### 5. **Model** (The Prediction Engine)
An algorithm that learns patterns from training data.

**Our Model:** XGBoost (a powerful algorithm good at finding patterns)

### 6. **Evaluation Metrics** (Report Card)
Numbers that tell us how well the model performs.

**Our Metrics:**
- **MAE (Mean Absolute Error)**: Average position error (e.g., 4.7 positions off)
- **NDCG**: How well we rank riders (0 = terrible, 1 = perfect)
- **Top-3 Accuracy**: % of times we correctly predict podium finishers
- **Winner Accuracy**: % of times we correctly predict the winner

---

## The Workflow in Our Project

### Step 1: Data Exploration
**File:** `notebooks/01_data_exploration.ipynb`

**What it does:**
- Loads the race results CSV
- Shows statistics (how many races, riders, etc.)
- Creates charts to visualize patterns
- Checks for data quality issues

**Why we do it:**
- Understand what data we have
- Find patterns that might help predictions
- Catch errors before training models
- Decide what features to create

**Example Questions We Answer:**
- Who are the top winners?
- Does qualifying position predict main event finish?
- How consistent are riders?
- Are there missing values?

---

### Step 2: Feature Engineering
**File:** `src/features/feature_engineering.py`

**What it does:**
- Takes raw race results
- Calculates useful statistics for each rider
- Creates new columns (features) for the model

**Why we do it:**
- Models need meaningful inputs, not just raw data
- Historical stats help predict future performance
- Transform data into a format the model can learn from

**Example Transformations:**
```
Raw Data:
Rider A: Position 1, 3, 2, 1, 4 (last 5 races)

Features Created:
- avg_position_last_5: 2.2
- best_position_last_5: 1
- wins_last_5: 2
- podiums_last_5: 5
```

---

### Step 3: Model Training
**File:** `src/models/train_models.py`

**What it does:**
- Splits data into training (2023-2024) and test (2025)
- Trains XGBoost model on training data
- Makes predictions on test data
- Evaluates performance

**Why we do it:**
- Teach the computer to recognize patterns
- Test if it learned correctly on unseen data
- Compare different model types
- Save the best model for future use

**The Training Process:**
1. Show model 1,632 training examples
2. Model learns: "Riders with avg position 2 usually finish top 3"
3. Test on 892 new examples
4. Check: Did predictions match reality?

---

### Step 4: Running Everything
**File:** `run_modeling.py`

**What it does:**
- Orchestrates the entire pipeline
- Runs feature engineering
- Trains both model types
- Compares performance
- Saves results

**Why we do it:**
- Automate the entire workflow
- Ensure consistent process
- Easy to re-run when data updates
- Compare multiple approaches

---

## What Happens When You Run the Pipeline

```
1. Load raw data (19,861 race results)
   ↓
2. Create features (25 features per rider per race)
   ↓
3. Split data (1,632 train, 892 test)
   ↓
4. Train XGBoost model (learns patterns)
   ↓
5. Make predictions (predict 2025 results)
   ↓
6. Evaluate (compare predictions vs actual)
   ↓
7. Save model (ready to predict future races)
```

---

## Understanding the Results

### Current Performance:
- **MAE: 4.7 positions** → On average, predictions are 4-5 positions off
- **Top-3 Accuracy: 24%** → Correctly identifies 1 out of 3 podium finishers
- **Top-5 Accuracy: 36%** → Correctly identifies 2 out of 5 top finishers
- **Winner Accuracy: 10%** → Correctly predicts winner 3 out of 29 races

### What This Means:
- Model is learning patterns (better than random guessing)
- Still room for improvement (need better features)
- Good starting point for fantasy game predictions

---

## Next Steps to Improve

1. **Add More Features:**
   - Track-specific performance (some riders excel at certain tracks)
   - Weather conditions
   - Bike setup changes
   - Head-to-head records

2. **Tune Hyperparameters:**
   - Adjust model settings for better performance
   - Try different learning rates
   - Experiment with model depth

3. **Get More Data:**
   - Scrape older seasons (2020-2022)
   - Add practice session times
   - Include injury/mechanical DNF info

4. **Try Different Models:**
   - Neural networks
   - Ensemble methods
   - Specialized ranking algorithms

---

## Common ML Terms Explained

| Term | Simple Explanation | Our Example |
|------|-------------------|-------------|
| **Feature** | Input variable used for prediction | "Average position last 5 races" |
| **Target** | What we're trying to predict | Finishing position (1-22) |
| **Training** | Teaching the model with historical data | Using 2023-2024 races |
| **Testing** | Checking if model learned correctly | Using 2025 races |
| **Overfitting** | Model memorizes training data, fails on new data | Would predict 2024 perfectly but fail on 2025 |
| **Underfitting** | Model too simple, doesn't learn patterns | Predicting everyone finishes 10th |
| **Hyperparameters** | Settings that control how model learns | Learning rate, tree depth |
| **Cross-validation** | Testing on multiple data splits | Train on 2023, test on 2024, then reverse |

---

## Questions to Ask Yourself

### Before Training:
- ✓ Do I understand my data?
- ✓ Are there patterns I can see?
- ✓ What features might help predictions?
- ✓ Is my data clean and complete?

### After Training:
- ✓ Is the model better than random guessing?
- ✓ Does it work on new data (not just training)?
- ✓ Which features are most important?
- ✓ How can I improve it?

---

## Summary

**Machine Learning is:**
1. Collecting data (race results)
2. Understanding patterns (exploration)
3. Creating useful inputs (features)
4. Teaching a model (training)
5. Testing performance (evaluation)
6. Making predictions (inference)

**Our Goal:**
Predict race finishing positions to help with fantasy game decisions.

**Current Status:**
✓ Data collected and cleaned
✓ Features engineered
✓ Model trained and evaluated
✓ Ready to make predictions

**Next:**
Walk through each file with detailed comments to understand the code!
