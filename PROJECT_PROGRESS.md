# Project Progress Tracker

## Current Status: Setup Phase
**Last Updated**: January 5, 2025

---

## Completed Tasks
- [x] Project structure created
- [x] Documentation initialized

---

## In Progress
- [ ] Data source identification and collection

---

## Next Steps

### Immediate (Week 1)
1. **Data Collection**
   - Identify reliable AMA SX data sources
   - Scrape/download 2022-2024 race results
   - Collect rider statistics and track information
   - Get PulpMX fantasy scoring rules

2. **Data Exploration**
   - Load and inspect data quality
   - Identify missing values and outliers
   - Understand data distributions
   - Create initial visualizations

### Short-term (Week 2-3)
3. **Feature Engineering**
   - Create rider performance metrics (avg finish, recent form)
   - Engineer track-specific features
   - Build temporal features (season progression)
   - Create target variables (finish position, podium probability)

4. **Supervised Baseline**
   - Train/test split by season
   - Implement baseline models (Linear, Random Forest)
   - Evaluate prediction accuracy
   - Feature importance analysis

### Medium-term (Week 4-6)
5. **Advanced Supervised Models**
   - XGBoost/LightGBM implementation
   - Neural network experiments
   - Hyperparameter tuning
   - Cross-validation across seasons

6. **RL Environment Setup**
   - Define state space (rider stats, budget, lineup constraints)
   - Define action space (rider selection combinations)
   - Implement reward function (fantasy points)
   - Create Gymnasium environment

### Long-term (Week 7+)
7. **RL Agent Training**
   - Implement PPO/DQN agent
   - Train on historical seasons
   - Tune hyperparameters
   - Evaluate against baseline

8. **Evaluation & Comparison**
   - Backtest on held-out season
   - Compare with actual fantasy league results
   - Analyze decision patterns
   - Document findings

---

## Data Sources to Explore
- [ ] Supercrosslive.com - Official results
- [ ] RacerX Online - Detailed race coverage
- [ ] PulpMX Fantasy - Fantasy rules and historical data
- [ ] Vital MX - Community data and stats
- [ ] Wikipedia - Season summaries

---

## Challenges & Notes

### Data Collection Challenges
- Need to verify data availability for 2022-2024
- May need web scraping if no API available
- Fantasy scoring rules need to be documented

### Technical Considerations
- Sample size: ~17 races/season × 3 years = ~51 races (limited for RL)
- May need data augmentation or transfer learning
- Consider using practice/qualifying data to increase samples

---

## Questions to Answer
1. What data is publicly available?
2. How many riders compete per race? (affects action space)
3. What are PulpMX fantasy constraints? (budget, roster size)
4. Can we access historical fantasy league results for comparison?

---

## Resources & Links
- AMA Supercross: https://www.supercrosslive.com/
- Racer X: https://racerxonline.com/results
- PulpMX Fantasy: https://fantasy.pulpmx.com/
