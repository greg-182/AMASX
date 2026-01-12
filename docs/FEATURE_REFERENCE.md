# Feature Reference Guide

## Complete Feature List

This document maps feature indices (f0, f1, etc.) to their actual names and descriptions.

### Quick Reference Table

| Index | Feature Name | Category | Description |
|-------|--------------|----------|-------------|
| **f0** | `qual_position` | Qualifying | Starting position from qualifying |
| **f1** | `avg_position_last_3` | Recent Form | Average finish in last 3 races |
| **f2** | `best_position_last_3` | Recent Form | Best finish in last 3 races |
| **f3** | `std_position_last_3` | Recent Form | Consistency in last 3 races (lower = more consistent) |
| **f4** | `races_last_3` | Recent Form | Number of races completed in last 3 |
| **f5** | `avg_position_last_5` | Recent Form | Average finish in last 5 races |
| **f6** | `best_position_last_5` | Recent Form | Best finish in last 5 races |
| **f7** | `std_position_last_5` | Recent Form | Consistency in last 5 races |
| **f8** | `races_last_5` | Recent Form | Number of races completed in last 5 |
| **f9** | `avg_position_last_10` | Historical | Average finish in last 10 races |
| **f10** | `best_position_last_10` | Historical | Best finish in last 10 races |
| **f11** | `std_position_last_10` | Historical | Consistency in last 10 races |
| **f12** | `races_last_10` | Historical | Number of races completed in last 10 |
| **f13** | `wins_last_10` | Historical | Number of wins in last 10 races |
| **f14** | `podiums_last_10` | Historical | Number of podiums (top 3) in last 10 races |
| **f15** | `total_races` | Career Stats | Total career races |
| **f16** | `career_avg_position` | Career Stats | **Career average finishing position** ⭐ |
| **f17** | `bike_encoded` | Equipment | Bike manufacturer (encoded as number) |
| **f18** | `class_encoded` | Competition | Race class: 450sx, 250sxe, or 250sxw (encoded) |
| **f19** | `rider_number` | Rider Info | Rider's race number |
| **f20** | `round_number` | Temporal | Round number in season (1-17) |
| **f21** | `round_pct` | Temporal | Percentage through season (0.0-1.0) |
| **f22** | `year_encoded` | Temporal | Year (encoded as number) |
| **f23** | `field_size` | Competition | Number of riders in this race |
| **f24** | `field_avg_strength` | Competition | Average skill level of competitors |

---

## Feature Categories Explained

### 1. Qualifying Features (1 feature)
**Purpose:** Starting position advantage

- **f0 - qual_position**: Where the rider qualified
  - Lower = better starting position
  - Important because clean air and track position matter

### 2. Recent Form Features (8 features)
**Purpose:** Capture current performance trends

**Last 3 Races (f1-f4):**
- Most recent performance indicator
- Shows immediate form

**Last 5 Races (f5-f8):**
- Slightly longer trend
- Balances recency with sample size

**Why these matter:**
- Recent form often predicts near-term performance
- Riders on hot streaks tend to continue
- Injuries or improvements show up here

### 3. Historical Features (6 features)
**Purpose:** Longer-term performance patterns

**Last 10 Races (f9-f14):**
- Broader performance baseline
- Includes wins and podiums
- Shows consistency over time

**Why these matter:**
- Establishes rider's typical performance level
- Wins/podiums show ability to compete for victory
- More stable than very recent form

### 4. Career Statistics (2 features)
**Purpose:** Overall skill level

- **f15 - total_races**: Experience level
  - More races = more experience
  - Rookies vs veterans

- **f16 - career_avg_position**: ⭐ **MOST IMPORTANT FEATURE**
  - Overall skill indicator
  - Baseline expectation for performance
  - Example: Career avg of 2.5 = elite rider, 15.0 = mid-pack

### 5. Equipment Features (1 feature)
**Purpose:** Bike performance differences

- **f17 - bike_encoded**: Manufacturer
  - Different bikes have different characteristics
  - Some years certain brands dominate
  - Encoded: Honda=0, Kawasaki=1, KTM=2, etc.

### 6. Competition Context (3 features)
**Purpose:** Race-specific factors

- **f18 - class_encoded**: Which class (450sx, 250sxe, 250sxw)
- **f23 - field_size**: How many riders competing
- **f24 - field_avg_strength**: Quality of competition
  - Higher = tougher field
  - Harder to finish high against strong competitors

### 7. Temporal Features (3 features)
**Purpose:** Season progression effects

- **f20 - round_number**: Which round (1-17)
- **f21 - round_pct**: How far through season (0.0-1.0)
- **f22 - year_encoded**: Which year

**Why these matter:**
- Riders improve/decline through season
- Championship pressure late in season
- Year-to-year rule changes

### 8. Rider Info (1 feature)
**Purpose:** Rider identification

- **f19 - rider_number**: Race number
  - Usually not predictive (just an identifier)
  - Lower numbers often given to top riders

---

## Most Important Features (Typical Rankings)

Based on model training, these features typically have the highest importance:

### Top 5 Most Important:

1. **f16 - career_avg_position** (35-40% importance)
   - Overall skill level is the best predictor
   - Elite riders consistently finish high

2. **f5 - avg_position_last_5** (15-20% importance)
   - Recent form matters a lot
   - Shows current performance level

3. **f0 - qual_position** (10-15% importance)
   - Starting position advantage
   - Hard to pass in supercross

4. **f9 - avg_position_last_10** (8-12% importance)
   - Longer-term baseline
   - More stable than last 3-5

5. **f24 - field_avg_strength** (5-8% importance)
   - Competition quality matters
   - Harder to win against strong field

### Least Important Features:

- **f19 - rider_number**: Usually <1% importance (just an identifier)
- **f22 - year_encoded**: Low importance (year doesn't predict much)
- **f4, f8, f12 - races_last_X**: Lower importance (completion rate)

---

## How to Interpret Feature Importance

When you see a feature importance plot:

```
f16 (career_avg_position)     ████████████████████ 2500
f5  (avg_position_last_5)     ████████████ 1200
f0  (qual_position)           ████████ 800
f9  (avg_position_last_10)    ██████ 600
f24 (field_avg_strength)      ████ 400
```

**This means:**
- The model uses `career_avg_position` most heavily in predictions
- Recent form (`avg_position_last_5`) is second most important
- Qualifying position helps but isn't everything
- Other features contribute but less significantly

---

## Feature Engineering Insights

### Why f16 (career_avg_position) is Most Important:

**Example:**
- Rider A: Career avg = 2.5 (elite)
- Rider B: Career avg = 15.0 (mid-pack)

Even if Rider B qualified better or had a good last race, Rider A is still more likely to win because:
- Proven track record of success
- Consistent high performance
- Skill level advantage

### Why Recent Form (f1-f8) Matters:

**Example:**
- Rider with career avg of 5.0 but averaging 2.0 in last 5 races
- Likely improving or on a hot streak
- Model adjusts prediction upward

### Why Qualifying (f0) Helps:

**Supercross specifics:**
- Tight tracks, hard to pass
- Starting up front = clean air
- Avoiding first-turn crashes

---

## Using This Reference

**When analyzing model results:**

1. Check feature importance plot
2. Look up feature indices in this document
3. Understand what the model is learning

**Example:**
```
Model shows f16 is most important
→ Look up f16 = career_avg_position
→ Model relies heavily on overall skill level
→ Makes sense! Elite riders consistently win
```

**When improving the model:**

1. Identify low-importance features (might remove)
2. Identify missing patterns (might add new features)
3. Understand which aspects of racing matter most

---

## Quick Lookup by Name

| Feature Name | Index | Category |
|--------------|-------|----------|
| avg_position_last_3 | f1 | Recent Form |
| avg_position_last_5 | f5 | Recent Form |
| avg_position_last_10 | f9 | Historical |
| best_position_last_3 | f2 | Recent Form |
| best_position_last_5 | f6 | Recent Form |
| best_position_last_10 | f10 | Historical |
| bike_encoded | f17 | Equipment |
| career_avg_position | **f16** | **Career Stats** ⭐ |
| class_encoded | f18 | Competition |
| field_avg_strength | f24 | Competition |
| field_size | f23 | Competition |
| podiums_last_10 | f14 | Historical |
| qual_position | f0 | Qualifying |
| races_last_3 | f4 | Recent Form |
| races_last_5 | f8 | Recent Form |
| races_last_10 | f12 | Historical |
| rider_number | f19 | Rider Info |
| round_number | f20 | Temporal |
| round_pct | f21 | Temporal |
| std_position_last_3 | f3 | Recent Form |
| std_position_last_5 | f7 | Recent Form |
| std_position_last_10 | f11 | Historical |
| total_races | f15 | Career Stats |
| wins_last_10 | f13 | Historical |
| year_encoded | f22 | Temporal |

---

## Summary

**Total Features: 25**

- **Qualifying:** 1 feature
- **Recent Form (last 3-5):** 8 features
- **Historical (last 10):** 6 features
- **Career Stats:** 2 features (including f16 ⭐)
- **Equipment:** 1 feature
- **Competition Context:** 3 features
- **Temporal:** 3 features
- **Rider Info:** 1 feature

**Key Takeaway:**
The model primarily relies on **career average position (f16)** and **recent form (f1-f8)** to make predictions, which aligns with racing intuition: skilled riders who are performing well recently are most likely to win.
