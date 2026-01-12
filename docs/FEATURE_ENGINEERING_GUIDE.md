# Feature Engineering - Complete Beginner's Guide

## What is Feature Engineering?

**Simple Explanation:**
Feature engineering is like being a detective who gathers clues. Raw data (race results) is just facts. Features are the **meaningful patterns** we extract from those facts to help the model make predictions.

**Analogy:**
Imagine you're trying to predict if a student will pass an exam:
- **Raw Data**: "Student took 5 tests, scored 70, 80, 75, 85, 90"
- **Features**: 
  - Average score: 80
  - Trend: Improving (scores going up)
  - Consistency: Low variation (scores similar)
  - Recent performance: 90 (last test)

The model learns better from features than raw data!

---

## Why Do We Need Feature Engineering?

### The Problem
Machine learning models can't understand context like humans do. If you tell a model:
- "Chase Sexton finished 1st, 2nd, 1st, 3rd, 1st in his last 5 races"

The model just sees: `[1, 2, 1, 3, 1]`

### The Solution
We create features that capture the **meaning**:
- `avg_position_last_5`: 1.6 (he's very fast!)
- `wins_last_5`: 3 (he wins often!)
- `consistency`: 0.75 (he's reliable!)

Now the model understands: "This rider is fast, wins often, and is consistent" → Predict top finish!

---

## Our Feature Engineering Process

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEATURE ENGINEERING PIPELINE                  │
└─────────────────────────────────────────────────────────────────┘

INPUT: Raw Race Results
┌──────────────────────────────────────────────────────────────┐
│ year | race | rider | position | bike | event_type | ...    │
│ 2023 | Ana1 | Chase |    1     | Honda| main_event | ...    │
│ 2023 | Ana1 | Jett  |    2     | Honda| main_event | ...    │
└──────────────────────────────────────────────────────────────┘
                            ↓
                   [STEP 1: FILTER]
                            ↓
        Keep only main events with qualifying data
                            ↓
                   [STEP 2: SORT]
                            ↓
        Sort by year, round, class (chronological order)
                            ↓
              [STEP 3: CREATE FEATURES]
                            ↓
        ┌─────────────────────────────────────┐
        │  For each rider in each race:       │
        │  1. Look at their history           │
        │  2. Calculate statistics            │
        │  3. Add context (field, round, etc) │
        └─────────────────────────────────────┘
                            ↓
OUTPUT: Feature Matrix
┌──────────────────────────────────────────────────────────────────────┐
│ rider | position | avg_last_5 | wins_last_10 | qual_pos | ... (25) │
│ Chase |    1     |    2.1     |      7       |    3     | ...      │
│ Jett  |    2     |    2.8     |      5       |    1     | ...      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## The 25 Features We Create

### Category 1: Historical Performance (Rolling Windows)

**What it means:** How has the rider performed recently?

| Feature | What It Measures | Example | Why It Matters |
|---------|------------------|---------|----------------|
| `avg_position_last_3` | Average finish in last 3 races | 2.3 | Recent form |
| `avg_position_last_5` | Average finish in last 5 races | 3.1 | Medium-term form |
| `avg_position_last_10` | Average finish in last 10 races | 4.2 | Long-term form |
| `best_position_last_3` | Best finish in last 3 races | 1 | Peak performance |
| `best_position_last_5` | Best finish in last 5 races | 1 | Winning capability |
| `best_position_last_10` | Best finish in last 10 races | 1 | Consistency at top |
| `std_position_last_3` | Variation in last 3 races | 1.2 | Recent consistency |
| `std_position_last_5` | Variation in last 5 races | 2.1 | Medium consistency |
| `std_position_last_10` | Variation in last 10 races | 3.5 | Long-term consistency |

**Why different windows?**
- **Last 3**: Captures current momentum (hot streak or slump)
- **Last 5**: Balances recent form with stability
- **Last 10**: Shows overall skill level

**Example:**
```
Rider A: Last 10 races = [1, 1, 1, 15, 1, 1, 1, 1, 1, 1]
  - avg_last_10 = 2.5 (good!)
  - std_last_10 = 4.2 (inconsistent - one bad race)
  - best_last_10 = 1 (can win!)

Rider B: Last 10 races = [3, 2, 4, 3, 2, 3, 4, 2, 3, 4]
  - avg_last_10 = 3.0 (good!)
  - std_last_10 = 0.8 (very consistent!)
  - best_last_10 = 2 (podium, but no wins)
```

---

### Category 2: Recent Achievements

**What it means:** Counting specific accomplishments

| Feature | What It Measures | Example | Why It Matters |
|---------|------------------|---------|----------------|
| `wins_last_10` | Number of wins in last 10 races | 5 | Winning ability |
| `podiums_last_10` | Number of top-3 finishes | 8 | Consistent excellence |
| `races_last_3` | Races competed in (last 3) | 3 | Activity level |
| `races_last_5` | Races competed in (last 5) | 5 | Activity level |
| `races_last_10` | Races competed in (last 10) | 9 | Injury/absence check |

**Why count races?**
If a rider has `races_last_10 = 4`, they missed 6 races. Why?
- Injury? (might not be 100%)
- New to series? (less experience)
- Suspension? (disciplinary issues)

**Example:**
```
Rider A: wins_last_10 = 7, podiums_last_10 = 9
  → Wins most races, almost always on podium (dominant!)

Rider B: wins_last_10 = 0, podiums_last_10 = 8
  → Never wins but always top 3 (consistent but not dominant)

Rider C: races_last_10 = 3
  → Missed 7 races (injury? new rider?)
```

---

### Category 3: Career Statistics

**What it means:** Overall skill level across entire career

| Feature | What It Measures | Example | Why It Matters |
|---------|------------------|---------|----------------|
| `career_avg_position` | Average position across all races | 5.2 | Overall skill level |
| `total_races` | Total races competed in | 45 | Experience |

**Why career stats?**
- New riders: `total_races = 5` → Less experience
- Veterans: `total_races = 100` → Lots of experience
- Career average shows baseline skill

**Example:**
```
Veteran: career_avg = 3.5, total_races = 80
  → Experienced, consistently good

Rookie: career_avg = 12.0, total_races = 5
  → New, still learning

Improving: career_avg = 8.0, avg_last_10 = 3.0
  → Getting much better!
```

---

### Category 4: Temporal Features

**What it means:** When in the season is this race?

| Feature | What It Measures | Example | Why It Matters |
|---------|------------------|---------|----------------|
| `year_encoded` | Season year (encoded) | 0, 1, 2 | Different seasons |
| `round_number` | Race number in season | 5 | Early/mid/late season |
| `round_pct` | Percentage through season | 0.29 | Season progress |

**Why temporal features?**
- **Early season** (round 1-5): Riders still finding form
- **Mid season** (round 6-12): Peak performance
- **Late season** (round 13-17): Fatigue, championship pressure

**Example:**
```
Round 1 (round_pct = 0.06):
  - New bike setup
  - Riders shaking off rust
  - Unpredictable results

Round 17 (round_pct = 1.0):
  - Championship decided?
  - Some riders pushing hard
  - Others may have given up
```

---

### Category 5: Competition Context

**What it means:** Who else is racing?

| Feature | What It Measures | Example | Why It Matters |
|---------|------------------|---------|----------------|
| `field_size` | Number of riders in race | 22 | Competition level |
| `field_avg_strength` | Average skill of all riders | 8.5 | How tough is field? |

**Why competition context?**
- **Small field** (15 riders): Easier to finish top 10
- **Large field** (22 riders): Harder to finish top 10
- **Weak field** (avg strength = 12): Easier race
- **Strong field** (avg strength = 5): Tough race

**Example:**
```
Race A: field_size = 22, field_avg_strength = 4.5
  → Full field of top riders (very competitive!)

Race B: field_size = 18, field_avg_strength = 9.2
  → Smaller field, weaker competition (easier)

Same rider finishing 5th in Race A is more impressive than 5th in Race B!
```

---

### Category 6: Qualifying Position

**What it means:** Starting position advantage

| Feature | What It Measures | Example | Why It Matters |
|---------|------------------|---------|----------------|
| `qual_position` | Qualifying position | 3 | Starting advantage |

**Why qualifying matters?**
From our data exploration, we found correlation = 0.21 (weak but exists)
- Qualifying 1st gives you clean air (no one to pass)
- Qualifying 20th means you must pass 19 riders!

**Example:**
```
Rider qualifies 1st:
  - Clean start
  - No traffic
  - Can set own pace
  - Likely to finish top 5

Rider qualifies 20th:
  - Stuck in traffic
  - Must make risky passes
  - Likely to finish mid-pack
```

---

### Category 7: Encoded Categories

**What it means:** Converting text to numbers

| Feature | What It Measures | Example | Why It Matters |
|---------|------------------|---------|----------------|
| `class_encoded` | Bike class (250/450) | 0, 1, 2 | Different competitions |
| `bike_encoded` | Manufacturer | 0-5 | Bike performance |
| `rider_number` | Rider's number | 23 | Unique identifier |

**Why encode?**
Models need numbers, not text!
- "450sx" → 0
- "250sxe" → 1
- "250sxw" → 2

**Example:**
```
Honda → 0
KTM → 1
Yamaha → 2
Kawasaki → 3
Suzuki → 4
GASGAS → 5

Model learns: "Riders on bike 0 (Honda) tend to finish higher"
```

---

## How Features Are Calculated (Step-by-Step)

### Example: Calculating `avg_position_last_5`

**Scenario:** It's Round 6, we want to predict Chase Sexton's finish

**Step 1: Get his history**
```
Round 1: Position 2
Round 2: Position 1
Round 3: Position 3
Round 4: Position 1
Round 5: Position 2
```

**Step 2: Take last 5 races**
```
[2, 1, 3, 1, 2]
```

**Step 3: Calculate average**
```
avg_position_last_5 = (2 + 1 + 3 + 1 + 2) / 5 = 1.8
```

**Step 4: Use as feature**
```
When predicting Round 6, model sees:
  - avg_position_last_5 = 1.8
  - Model thinks: "He's been averaging 1.8, probably will finish top 3"
```

---

### Example: Calculating `field_avg_strength`

**Scenario:** Round 6 has 22 riders

**Step 1: Get each rider's career average**
```
Chase Sexton: 2.5
Jett Lawrence: 2.8
Eli Tomac: 3.2
...
Rookie Rider: 15.0
```

**Step 2: Calculate average of all riders**
```
field_avg_strength = (2.5 + 2.8 + 3.2 + ... + 15.0) / 22 = 7.3
```

**Step 3: Use as feature**
```
For each rider in this race:
  - field_avg_strength = 7.3
  - Model thinks: "Medium difficulty field"
```

---

## The Feature Engineering Code Structure

### Main Class: `SupercrossFeatureEngineer`

```python
class SupercrossFeatureEngineer:
    """
    This class transforms raw race results into features for ML models.
    
    Think of it as a factory:
    - INPUT: Raw race results (CSV)
    - PROCESS: Calculate statistics, rolling averages, etc.
    - OUTPUT: Feature matrix ready for model training
    """
```

### Key Methods:

1. **`create_features()`** - Main entry point
   - Loads raw data
   - Filters to main events
   - Calls other methods to create features
   - Returns feature matrix

2. **`_calculate_historical_features()`** - Rolling statistics
   - For each rider, looks back at their history
   - Calculates averages, best positions, consistency
   - Uses windows of 3, 5, and 10 races

3. **`_calculate_rider_features()`** - Career statistics
   - Calculates overall career averages
   - Counts total races
   - Encodes rider number

4. **`_calculate_temporal_features()`** - Time-based features
   - Encodes year
   - Adds round number
   - Calculates season progress percentage

5. **`_calculate_competition_features()`** - Field context
   - Counts riders in each race
   - Calculates average field strength
   - Adds context about competition level

6. **`_add_qualifying_position()`** - Qualifying data
   - Merges qualifying results with main event
   - Fills missing values with median

7. **`prepare_for_ranking()`** - Ranking-specific prep
   - Groups riders by race
   - Creates group IDs for ranking models
   - Returns data in ranking format

---

## Common Questions

### Q: Why so many features?
**A:** Different features capture different aspects:
- Historical: How good are they?
- Recent: Are they hot or cold?
- Career: Overall skill level
- Temporal: Season effects
- Competition: Difficulty adjustment
- Qualifying: Starting advantage

More features = more information for model to learn from!

### Q: What if a rider is new (no history)?
**A:** We handle missing values:
- `avg_position_last_10 = NaN` → Fill with median (around 10)
- Model learns: "No history = average prediction"
- As they race more, features become more accurate

### Q: Why rolling windows (3, 5, 10)?
**A:** Different time scales:
- **3 races**: Current form (hot streak?)
- **5 races**: Recent trend (improving?)
- **10 races**: True skill level (consistent?)

Example:
```
Rider: [15, 14, 13, 12, 11, 10, 2, 1, 1]
       └─────────────┘  └────┘
       Long-term: 11.0  Recent: 1.3
       
Model sees: "Was mid-pack, now winning! Predict top finish!"
```

### Q: How do we avoid data leakage?
**A:** **CRITICAL RULE:** Only use past data!

**WRONG:**
```python
# Using future races to predict current race
avg_position = df['position'].mean()  # Includes future!
```

**CORRECT:**
```python
# Only use races BEFORE current race
past_races = df[df['round'] < current_round]
avg_position = past_races['position'].mean()
```

Our code ensures this by:
1. Sorting data chronologically
2. Using `.shift()` to look back only
3. Never using current race in its own features

---

## Feature Importance (What Model Learns)

After training, we can see which features matter most:

**Top Features (typical):**
1. `avg_position_last_5` (35%) - Recent form is key!
2. `qual_position` (15%) - Starting position helps
3. `career_avg_position` (12%) - Overall skill matters
4. `field_avg_strength` (10%) - Competition level
5. `wins_last_10` (8%) - Winning history
6. `round_pct` (5%) - Season timing
7. ... (other features)

**What this means:**
- Model relies heavily on recent performance
- Qualifying position is important
- Career stats provide baseline
- Competition context adjusts predictions

---

## Summary

**Feature Engineering is:**
1. **Transforming** raw data into meaningful patterns
2. **Extracting** historical statistics (averages, trends)
3. **Adding** context (competition, timing)
4. **Encoding** categories (text → numbers)
5. **Preparing** data for model training

**Our 25 Features Capture:**
- ✅ Recent form (last 3/5/10 races)
- ✅ Winning ability (wins, podiums)
- ✅ Career skill (overall average)
- ✅ Experience (total races)
- ✅ Season timing (round number, %)
- ✅ Competition level (field size, strength)
- ✅ Starting advantage (qualifying position)
- ✅ Bike/class differences (encoded)

**Why It Matters:**
Good features = Good predictions!
- Raw data: "Chase finished 1st"
- Features: "Chase averages 1.8, wins 70%, qualified 3rd, strong field"
- Model: "Predict 2nd place" ✓

Next, we'll look at the actual code with detailed comments!
