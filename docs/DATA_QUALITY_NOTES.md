# Data Quality Notes

## Important Data Issues

### Issue 1: Mixed Event Types in Raw Data

**Problem:**
The raw data (`data/raw/sx_all_results.csv`) contains results from multiple event types:
- **main_event** - The main race (what we want to predict)
- **qualifying** - Qualifying sessions
- **heat_1, heat_2** - Heat races
- **lcq** - Last Chance Qualifier races
- **heat_east, heat_west** - 250 class regional heats
- **race_1, race_2, race_3** - Triple crown races
- **overall** - Overall standings

**Impact:**
When predicting 2026 Anaheim I, the model was including riders like:
- Michael Hicks (#468) - Predicted 2nd in 450sx
- Dominique Thury (#964) - Predicted 3rd in 450sx
- Slade Varola (#805) - Predicted 4th in 450sx

These riders have good stats from **qualifying/heats/LCQ** but rarely make main events. They are not title contenders.

**Root Cause:**
The `prepare_rider_list()` function was pulling ALL riders from 2025 data, including:
- LCQ-only riders (qualify well but don't make main events)
- Heat race participants (good in heats but not main events)
- Qualifying-only riders (fast lap times but inconsistent)

**Solution:**
Updated `predict_race.py` to filter riders by:
1. Only use `event_type == 'main_event'` data
2. Only include riders with avg position < 22 (main event field size)
3. This ensures we only predict for actual main event contenders

**Before Fix:**
```
450sx predictions:
1. Jett Lawrence (correct - main event star)
2. Michael Hicks (wrong - LCQ rider)
3. Dominique Thury (wrong - qualifying rider)
4. Slade Varola (wrong - heat race rider)
```

**After Fix:**
```
450sx predictions should show:
1. Jett Lawrence
2. Chase Sexton
3. Cooper Webb
4. Eli Tomac
5. Ken Roczen
... (actual main event contenders)
```

---

## Event Type Breakdown

From the raw data:

| Event Type | Count | Description |
|------------|-------|-------------|
| qualifying | 4,462 | Qualifying sessions (fastest lap) |
| lcq | 3,782 | Last Chance Qualifier (top 4 make main) |
| main_event | 2,856 | **Main race (what we predict)** |
| heat_1 | 2,761 | First heat race |
| heat_2 | 2,720 | Second heat race |
| race_2 | 611 | Triple crown race 2 |
| race_3 | 611 | Triple crown race 3 |
| race_1 | 593 | Triple crown race 1 |
| heat_west | 512 | 250 West heat |
| overall | 496 | Overall standings |
| heat_east | 434 | 250 East heat |

**Key insight:** Only **2,856 / 19,838 records (14%)** are actual main events!

---

## 450sx Main Event Contenders (2023-2025)

Based on main event data only (minimum 10 races):

| Rider | Avg Position | Main Events | Status |
|-------|--------------|-------------|--------|
| Cooper Webb | 2.97 | 38 | Elite |
| Jett Lawrence | 3.38 | 16 | Elite (newer) |
| Chase Sexton | 3.47 | 43 | Elite |
| Eli Tomac | 5.28 | 29 | Top 5 |
| Ken Roczen | 5.97 | 37 | Top 5 |
| Justin Cooper | 6.03 | 34 | Top 10 |
| Aaron Plessinger | 6.33 | 33 | Top 10 |
| Jason Anderson | 6.52 | 33 | Top 10 |
| Justin Barcia | 7.50 | 38 | Top 10 |
| Malcolm Stewart | 8.10 | 29 | Top 10 |

These are the riders who should appear in top predictions, not LCQ riders.

---

## Recommendations for Future Data Collection

### 1. Filter at Scraping Stage
When scraping new data, only collect `main_event` results:
```python
# In scraper
if event_type == 'main_event':
    save_result()
```

### 2. Separate Files by Event Type
```
data/raw/
  main_events.csv      # Main races (for predictions)
  qualifying.csv       # Qualifying data
  heats.csv           # Heat races
  lcq.csv             # Last chance qualifiers
```

### 3. Use Main Events for Training
When training models, filter to main events only:
```python
df = pd.read_csv('data/raw/sx_all_results.csv')
df_main = df[df['event_type'] == 'main_event']
# Use df_main for training
```

### 4. Validate Predictions
After making predictions, check if top riders make sense:
- Do they have main event experience?
- Are they known title contenders?
- Do they match expert predictions?

---

## Data Quality Checklist

Before training models or making predictions:

- [ ] Filter to `event_type == 'main_event'`
- [ ] Remove riders with < 5 main event starts
- [ ] Verify top riders are known contenders
- [ ] Check for duplicate entries
- [ ] Validate bike/number consistency
- [ ] Ensure year/round/class are correct

---

## Known Data Issues

### Issue: LCQ Riders in Predictions
**Status:** ✅ Fixed in `predict_race.py`
**Fix:** Filter to main event riders only

### Issue: Mixed Event Types in Training Data
**Status:** ⚠️ Needs fixing in `run_modeling_v2.py`
**Action Required:** Update training pipeline to filter main events

### Issue: Inconsistent Rider Names
**Status:** ⚠️ Needs investigation
**Examples:**
- "Jett Lawrence" vs "J. Lawrence"
- "RJ Hampshire" vs "Rj Hampshire"
**Impact:** May split rider history across multiple names

### Issue: Missing Event Type for Some Records
**Status:** ⚠️ Needs investigation
**Impact:** Some records might have `event_type = NaN`

---

## Next Steps

1. **Update training pipeline** (`run_modeling_v2.py`):
   - Filter to main events only
   - Retrain all models
   - Compare performance

2. **Validate predictions**:
   - Run predictions again
   - Verify top riders are main event contenders
   - Compare to expert predictions

3. **Clean historical data**:
   - Standardize rider names
   - Fill missing event types
   - Remove duplicate entries

4. **Document scraping process**:
   - Specify which event types to collect
   - Add validation checks
   - Create data quality tests

---

## Summary

**Main Issue:** Raw data mixes main events with qualifying/heats/LCQ, causing predictions to include non-contenders.

**Solution:** Filter to `event_type == 'main_event'` in both training and prediction.

**Impact:** Predictions now show actual title contenders instead of LCQ riders.

**Status:** 
- ✅ Prediction script fixed
- ⚠️ Training pipeline needs updating
- ⚠️ Data cleaning needed
