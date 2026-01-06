"""Test updated scraper with 250SX and date/round extraction"""
from src.data.scraper_v2 import MXGPResultsScraperV2
from pathlib import Path


def test():
    print("Testing updated scraper...")

    scraper = MXGPResultsScraperV2(output_dir="data/raw/test_v3")

    # Test 1: Check 250SX race discovery for 2025
    print("\n" + "="*70)
    print("TEST 1: 250SX Race Discovery")
    print("="*70)

    races_250e = scraper.get_season_races(2025, "250sxe")
    print(f"\n250SX East races found: {len(races_250e)}")
    for race in races_250e[:5]:
        print(f"  - {race['name']}: {race['url']}")

    races_250w = scraper.get_season_races(2025, "250sxw")
    print(f"\n250SX West races found: {len(races_250w)}")
    for race in races_250w[:5]:
        print(f"  - {race['name']}: {race['url']}")

    # Test 2: Check date and round extraction
    print("\n" + "="*70)
    print("TEST 2: Date and Round Number Extraction")
    print("="*70)

    # Test Anaheim 1 (should be Round 1)
    df_a1 = scraper.scrape_race_results(
        "https://mxgpresults.com/sx/2025/anaheim-1/",
        2025,
        "Anaheim 1",
        "450sx"
    )

    if df_a1 is not None:
        print(f"\nAnaheim 1:")
        print(f"  Round: {df_a1['round'].iloc[0]}")
        print(f"  Date: {df_a1['date'].iloc[0]}")
        print(f"  Results: {len(df_a1)}")

    # Test Salt Lake City (should be Round 17)
    df_slc = scraper.scrape_race_results(
        "https://mxgpresults.com/sx/2025/salt-lake-city/",
        2025,
        "Salt Lake City",
        "450sx"
    )

    if df_slc is not None:
        print(f"\nSalt Lake City:")
        print(f"  Round: {df_slc['round'].iloc[0]}")
        print(f"  Date: {df_slc['date'].iloc[0]}")
        print(f"  Results: {len(df_slc)}")

    # Test 3: Check 250SX data extraction
    print("\n" + "="*70)
    print("TEST 3: 250SX Data Extraction")
    print("="*70)

    df_250w = scraper.scrape_race_results(
        "https://mxgpresults.com/sx/2025/denver/250sx",
        2025,
        "Denver",
        "250sxw"
    )

    if df_250w is not None:
        print(f"\nDenver 250SX West:")
        print(f"  Round: {df_250w['round'].iloc[0]}")
        print(f"  Date: {df_250w['date'].iloc[0]}")
        print(f"  Results: {len(df_250w)}")
        print(f"  Event types: {df_250w['event_type'].unique()}")
        print(f"\nSample data:")
        print(df_250w.head(5).to_string())

    print("\n" + "="*70)
    print("ALL TESTS COMPLETED")
    print("="*70)

    # Summary
    success = (
        len(races_250e) > 1 and
        len(races_250w) > 1 and
        df_a1 is not None and
        df_slc is not None and
        df_250w is not None and
        df_a1['round'].iloc[0] == 1 and
        df_slc['round'].iloc[0] == 17
    )

    if success:
        print("\n✓ All tests PASSED!")
        print(f"  - 250SX East: {len(races_250e)} races")
        print(f"  - 250SX West: {len(races_250w)} races")
        print(f"  - Date/Round extraction: Working")
    else:
        print("\n✗ Some tests FAILED")

    return success


if __name__ == "__main__":
    test()
