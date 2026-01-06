# AMA Supercross Fantasy RL Project

## Project Overview
Using Reinforcement Learning and supervised learning to predict AMA Supercross race winners and optimize fantasy team selections.

## Objectives
1. **Supervised Learning**: Predict race results (finishing positions, podium probability)
2. **Reinforcement Learning**: Optimize fantasy team selection strategy over the season
3. **Evaluation**: Compare model performance against PulpMX fantasy league participants

## Project Structure
```
AMASX/
├── data/
│   ├── raw/              # Raw scraped data
│   ├── processed/        # Cleaned and feature-engineered data
│   └── external/         # External data sources (weather, track info)
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_supervised_models.ipynb
│   └── 04_rl_agent.ipynb
├── src/
│   ├── data/
│   │   ├── scraper.py
│   │   └── preprocessor.py
│   ├── models/
│   │   ├── supervised.py
│   │   └── rl_agent.py
│   ├── features/
│   │   └── engineering.py
│   └── utils/
│       └── helpers.py
├── tests/
├── models/               # Saved model checkpoints
├── results/              # Predictions and evaluations
├── requirements.txt
├── PROJECT_PROGRESS.md
└── README.md
```

## Data Requirements
- **Historical Race Results** (2023-2025): Finishing positions, lap times, qualifying results
- **Rider Information**: Career stats, injuries, team changes, bike specs
- **Track Data**: Track characteristics, weather conditions
- **Fantasy Scoring**: PulpMX scoring rules and historical fantasy results

## Approach

### Phase 1: Supervised Learning Baseline
- Predict race finishing positions
- Models to try: XGBoost, Random Forest, Neural Networks
- Features: Rider stats, recent performance, qualifying position, track history

### Phase 2: RL for Fantasy Optimization
- **State**: Current season standings, available budget, rider form
- **Action**: Select riders for weekly lineup
- **Reward**: Fantasy points earned
- **Algorithm**: PPO or DQN

### Phase 3: Evaluation & Iteration
- Backtest on historical seasons
- Compare against actual fantasy league results
- Refine features and model architecture

## Tech Stack
- **Python 3.10+**
- **Data**: pandas, numpy, BeautifulSoup/Selenium (scraping)
- **ML**: scikit-learn, XGBoost, LightGBM
- **RL**: Stable-Baselines3, Gymnasium
- **Deep Learning**: PyTorch
- **Visualization**: matplotlib, seaborn, plotly

## Getting Started
1. Install dependencies: `pip install -r requirements.txt`
2. Scrape/collect AMA SX data (2023-2025)
3. Run data exploration notebook
4. Build supervised baseline
5. Implement RL agent

## Resources
- [AMA Supercross Official](https://www.supercrosslive.com/)
- [PulpMX Fantasy](https://fantasy.pulpmx.com/)
- [Racer X Results](https://racerxonline.com/results)

## Next Steps
See `PROJECT_PROGRESS.md` for current status and tasks.
