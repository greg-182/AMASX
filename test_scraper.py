"""
Quick test script to verify the scraper works before full run
"""
from src.data.scraper import MXGPResultsScraper
import sys
from pathlib import Path
import io

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_single_race():
    """Test scraping a single race"""
    print("Testing scraper with 2024 Anaheim 1...")

    scraper = MXGPResultsScraper(output_dir="data/raw/test")

    # Test getting race list for 2024
    races = scraper.get_season_races(2024, "450sx")

    if races:
        print(f"\n✓ Found {len(races)} races for 2024 450SX")
        print("\nFirst 3 races:")
        for race in races[:3]:
            print(f"  - {race['name']}: {race['url']}")

        # Test scraping first race
        print(f"\nTesting scrape of first race...")
        first_race = races[0]
        df = scraper.scrape_race_results(
            first_race['url'],
            first_race['year'],
            first_race['name'],
            first_race['class']
        )

        if df is not None and not df.empty:
            print(f"\n✓ Successfully scraped {len(df)} results")
            print("\nSample data:")
            print(df.head(10).to_string())

            # Save test data
            test_file = Path("data/raw/test/test_results.csv")
            test_file.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(test_file, index=False)
            print(f"\n✓ Test data saved to {test_file}")

            return True
        else:
            print("\n✗ Failed to scrape race results")
            return False
    else:
        print("\n✗ Failed to get race list")
        return False


if __name__ == "__main__":
    success = test_single_race()

    if success:
        print("\n" + "="*60)
        print("TEST PASSED! Scraper is working correctly.")
        print("="*60)
        print("\nYou can now run the full scraper with:")
        print("  python run_scraper.py")
    else:
        print("\n" + "="*60)
        print("TEST FAILED! Please check the errors above.")
        print("="*60)
