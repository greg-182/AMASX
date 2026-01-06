"""Test scraper with special cases"""
from src.data.scraper_v2 import MXGPResultsScraperV2


def test():
    scraper = MXGPResultsScraperV2(output_dir="data/raw/test_special")

    test_cases = [
        ("Indianapolis 250 East/West Showdown",
         "https://mxgpresults.com/sx/2025/indianapolis/250sx", 2025, "Indianapolis", "250sxe"),
        ("Glendale 250W Triple Crown",
         "https://mxgpresults.com/sx/2025/glendale/250sx", 2025, "Glendale", "250sxw"),
        ("Birmingham 250E Triple Crown",
         "https://mxgpresults.com/sx/2025/birmingham/250sx", 2025, "Birmingham", "250sxe"),
        ("Anaheim 1 250W (no date)", "https://mxgpresults.com/sx/2025/anaheim-1/250sx",
         2025, "Anaheim 1", "250sxw"),
    ]

    for name, url, year, race_name, class_type in test_cases:
        print("="*70)
        print(f"Testing: {name}")
        print("="*70)

        df = scraper.scrape_race_results(url, year, race_name, class_type)

        if df is not None and not df.empty:
            print(f"\nResults: {len(df)} rows")
            print(f"Round: {df['round'].iloc[0]}")
            print(f"Date: {df['date'].iloc[0]}")
            print(f"\nEvent types found:")
            print(df['event_type'].value_counts())

            # Check for main event or showdown
            main_events = df[df['event_type'] == 'main_event']
            if not main_events.empty:
                print(f"\nMain Event winner: {main_events.iloc[0]['rider']}")

            # Check for triple crown races
            race_events = df[df['event_type'].str.contains('race_', na=False)]
            if not race_events.empty:
                print(f"\nTriple Crown races found:")
                for race_type in ['race_1', 'race_2', 'race_3']:
                    race_df = df[df['event_type'] == race_type]
                    if not race_df.empty:
                        winner = race_df.iloc[0]['rider']
                        print(f"  {race_type}: {winner}")

            # Check for Heat East/West
            heat_east = df[df['event_type'] == 'heat_east']
            heat_west = df[df['event_type'] == 'heat_west']
            if not heat_east.empty:
                print(f"\nHeat East winner: {heat_east.iloc[0]['rider']}")
            if not heat_west.empty:
                print(f"Heat West winner: {heat_west.iloc[0]['rider']}")
        else:
            print("\nFAILED - No data scraped")

        print("\n")


if __name__ == "__main__":
    test()
