"""Test the improved scraper"""
from src.data.scraper_v2 import MXGPResultsScraperV2
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))


def test():
    print("Testing improved scraper with Anaheim 1 2025...")

    scraper = MXGPResultsScraperV2(output_dir="data/raw/test_v2")

    # Test single race
    df = scraper.scrape_race_results(
        "https://mxgpresults.com/sx/2025/anaheim-1/",
        2025,
        "Anaheim 1",
        "450sx"
    )

    if df is not None and not df.empty:
        print(f"\n✓ Successfully scraped {len(df)} results")
        print(f"\nEvent types found: {df['event_type'].unique()}")
        print(f"\nResults per event:")
        print(df.groupby('event_type').size())

        print(f"\nSample data (first 15 rows):")
        print(df.head(15).to_string())

        # Save test data
        test_file = Path("data/raw/test_v2/anaheim1_test.csv")
        test_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(test_file, index=False)
        print(f"\n✓ Test data saved to {test_file}")

        return True
    else:
        print("\n✗ Failed to scrape")
        return False


if __name__ == "__main__":
    success = test()

    if success:
        print("\n" + "="*60)
        print("TEST PASSED! Ready to run full scraper.")
        print("="*60)
    else:
        print("\n" + "="*60)
        print("TEST FAILED!")
        print("="*60)
