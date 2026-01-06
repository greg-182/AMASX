"""
Script to run the MXGPResults scraper
"""
from src.data.scraper import MXGPResultsScraper
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    """Run the scraper for 2023-2025 seasons"""
    scraper = MXGPResultsScraper(output_dir="data/raw")

    # Scrape 2023-2025 for both 450SX and 250SX (East and West)
    years = [2023, 2024, 2025]
    classes = ["450sx", "250sxe", "250sxw"]

    print("="*70)
    print("MXGPResults.com Scraper - AMA Supercross Data Collection")
    print("="*70)
    print(f"\nTarget Years: {years}")
    print(f"Target Classes: {classes}")
    print(f"Output Directory: data/raw/")
    print("\nStarting scraper...\n")

    df = scraper.scrape_multiple_seasons(years, classes)

    if not df.empty:
        scraper.save_metadata(df)

        print("\n" + "="*70)
        print("SCRAPING COMPLETE!")
        print("="*70)
        print(f"\nData Summary:")
        print(f"  • Years scraped: {sorted(df['year'].unique())}")
        print(f"  • Classes: {sorted(df['class'].unique())}")
        print(f"  • Total races: {df['race'].nunique()}")
        print(f"  • Total riders: {df['rider'].nunique()}")
        print(f"  • Total results: {len(df):,}")
        print(f"\nOutput Files:")
        print(f"  • Individual seasons: data/raw/sx_YEAR_results.csv")
        print(f"  • Combined data: data/raw/sx_all_results.csv")
        print(f"  • Metadata: data/raw/metadata.json")

        # Show sample of data
        print(f"\nSample Data (first 5 rows):")
        print(df.head().to_string())

    else:
        print("\n" + "="*70)
        print("ERROR: No data was scraped")
        print("="*70)
        print("\nPlease check:")
        print("  • Internet connection")
        print("  • MXGPResults.com is accessible")
        print("  • The website structure hasn't changed")


if __name__ == "__main__":
    main()
