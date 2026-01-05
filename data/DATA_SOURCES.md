# AMA Supercross Data Sources

## Available Data Sources (Verified)

### 1. MXGPResults.com ⭐ **RECOMMENDED**
**URL**: https://mxgpresults.com/sx/

**Coverage**: 2022-2024 (and earlier years available)

**Data Available**:
- Race results (finishing positions)
- Main event results
- Heat race results
- Last Chance Qualifier (LCQ) results
- Combined qualifying times
- Rider links for historical stats
- Season statistics

**Format**: Web pages (requires scraping)

**Example URLs**:
- 2024: https://mxgpresults.com/sx/2024/
- 2023: https://mxgpresults.com/sx/2023/
- 2022: https://mxgpresults.com/sx/2022/
- Individual race: https://mxgpresults.com/sx/2024/anaheim-1/

**Pros**:
- Clean, structured data
- Consistent format across years
- Includes qualifying times
- Links to rider profiles

**Cons**:
- Requires web scraping
- No API available

---

### 2. Racer X Vault ⭐ **COMPREHENSIVE ARCHIVE**
**URL**: https://vault.racerxonline.com/

**Coverage**: 1974-2025 (complete historical archive)

**Data Available**:
- Race results
- Points standings
- Historical records
- Comprehensive rider statistics

**Format**: Web pages (requires scraping)

**Example URLs**:
- 2024 SX: https://vault.racerxonline.com/2024/sx/intro
- 2023 SX: https://vault.racerxonline.com/2023/sx/intro
- 2022 SX: https://vault.racerxonline.com/2022/sx/intro

**Pros**:
- Most comprehensive historical data
- Reliable source (Racer X is industry standard)
- Detailed statistics

**Cons**:
- Requires web scraping
- May have different formats across years

---

### 3. Official AMA Supercross
**URL**: https://www.supercrosslive.com/results/

**Coverage**: Current and recent seasons

**Data Available**:
- Official race results
- Live timing data
- Practice results

**Format**: Web pages

**Pros**:
- Official source
- Most accurate

**Cons**:
- May be harder to scrape
- Less historical depth

---

### 4. PulpMX Fantasy
**URL**: https://pulpmxfantasy.com/

**Coverage**: Active fantasy leagues

**Data Available**:
- Fantasy scoring rules
- Rider handicaps
- League results (if accessible)

**Format**: Web application (JavaScript-heavy)

**Status**: Need to investigate further
- Rules page exists but requires JavaScript rendering
- May need Selenium for scraping
- Account may be required for historical data

**Next Steps**:
- Create account to explore available data
- Document scoring rules
- Check if historical fantasy results are accessible

---

## Data Collection Strategy

### Phase 1: Core Race Data (2022-2024)
**Source**: MXGPResults.com
**Target Data**:
- 450SX class results
- ~17 races per season × 3 years = ~51 races
- Rider finishing positions
- Qualifying times
- Heat race results

### Phase 2: Enhanced Features
**Source**: Racer X Vault
**Target Data**:
- Historical rider performance
- Career statistics
- Additional context

### Phase 3: Fantasy Rules
**Source**: PulpMX Fantasy
**Target Data**:
- Scoring system
- Roster constraints
- Budget rules
- Historical fantasy standings (if available)

---

## Data Structure Needed

### Race Results
```
- Season (2022, 2023, 2024)
- Round number
- Track/Location
- Date
- Rider name
- Finishing position (Main Event)
- Heat race position
- Qualifying time/position
- Points earned
```

### Rider Stats
```
- Rider name
- Team
- Bike manufacturer
- Career wins
- Season-to-date performance
- Recent form (last 3-5 races)
```

### Track Information
```
- Track name
- Location
- Track type (standard, Triple Crown, Daytona)
- Historical data (if available)
```

---

## Next Steps

1. **Build web scraper for MXGPResults.com**
   - Start with 2024 season
   - Extract race results
   - Store in structured format (CSV/JSON)

2. **Validate data quality**
   - Check for missing races
   - Verify rider names consistency
   - Handle DNF/DNS cases

3. **Expand to 2022-2023**
   - Apply same scraper
   - Build complete dataset

4. **Investigate PulpMX Fantasy**
   - Create account
   - Document scoring rules
   - Attempt to access historical data

5. **Feature engineering**
   - Calculate rider statistics
   - Create performance metrics
   - Build temporal features
