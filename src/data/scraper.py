import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from pathlib import Path
from typing import List, Dict, Optional
import re
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class MXGPResultsScraper:
    """Scraper for MXGPResults.com AMA Supercross data"""

    BASE_URL = "https://mxgpresults.com/sx"

    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_season_races(self, year: int, class_type: str = "450sx") -> List[Dict]:
        """
        Get list of all races for a given season and class

        Args:
            year: Season year (2023, 2024, 2025)
            class_type: "450sx", "250sxe" (East), or "250sxw" (West)

        Returns:
            List of race dictionaries with name and URL
        """
        if class_type == "450sx":
            url = f"{self.BASE_URL}/{year}/"
        else:
            url = f"{self.BASE_URL}/{year}/{class_type}"

        print(f"Fetching race list from: {url}")

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            races = []

            # Find race links - they typically have pattern like "/sx/2024/anaheim-1/"
            race_links = soup.find_all(
                'a', href=re.compile(f'/sx/{year}/[a-z0-9-]+/$'))

            seen_urls = set()
            for link in race_links:
                race_url = link.get('href')
                if race_url and race_url not in seen_urls:
                    # Extract race name from URL
                    race_slug = race_url.strip('/').split('/')[-1]
                    race_name = race_slug.replace('-', ' ').title()

                    # Skip if it's a class-specific page (250sxe, 250sxw)
                    if race_slug not in ['250sxe', '250sxw']:
                        races.append({
                            'name': race_name,
                            'slug': race_slug,
                            'url': f"https://mxgpresults.com{race_url}",
                            'year': year,
                            'class': class_type
                        })
                        seen_urls.add(race_url)

            print(f"Found {len(races)} races for {year} {class_type}")
            return races

        except Exception as e:
            print(f"Error fetching race list for {year} {class_type}: {e}")
            return []

    def scrape_race_results(self, race_url: str, year: int, race_name: str, class_type: str) -> Optional[pd.DataFrame]:
        """
        Scrape results from a single race

        Args:
            race_url: Full URL to race results page
            year: Season year
            race_name: Name of the race
            class_type: Class type (450sx, 250sxe, 250sxw)

        Returns:
            DataFrame with race results or None if failed
        """
        print(f"Scraping: {race_name} ({class_type})")

        # For 250 classes, append the class to the URL
        if class_type in ['250sxe', '250sxw']:
            if not race_url.endswith('/'):
                race_url += '/'
            race_url += '250sx'

        try:
            response = self.session.get(race_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            results = []

            # MXGPResults uses tables for results
            # Look for sections with headings like "450SX Main Event" or "250SX Main Event"
            headings = soup.find_all(['h2', 'h3', 'h4'])

            for heading in headings:
                heading_text = heading.get_text(strip=True).lower()

                # Look for main event or overall results
                if 'main event' in heading_text or 'overall results' in heading_text:
                    # Find the table after this heading (may not be immediate sibling)
                    table = heading.find_next('table')

                    if table:
                        rows = table.find_all('tr')

                        if len(rows) < 2:
                            continue

                        # Parse header to identify columns
                        header_row = rows[0]
                        headers = [th.get_text(strip=True).lower()
                                   for th in header_row.find_all(['th', 'td'])]

                        # Parse data rows
                        for row in rows[1:]:
                            cols = row.find_all(['td', 'th'])

                            if len(cols) < 1:
                                continue

                            try:
                                # The data is concatenated in the first column
                                # Format: "1#1Chase SextonKTM25" or similar
                                full_text = cols[0].get_text(strip=True)

                                # Extract position (starts with number)
                                position_match = re.match(r'^(\d+)', full_text)
                                if not position_match:
                                    continue

                                position = int(position_match.group(1))
                                remaining = full_text[len(
                                    position_match.group(1)):]

                                # Extract number (starts with #)
                                number_match = re.match(r'^#(\d+)', remaining)
                                number = number_match.group(
                                    1) if number_match else ""
                                if number_match:
                                    remaining = remaining[len(
                                        number_match.group(0)):]

                                # Extract rider name (look for known bike manufacturers)
                                bike_brands = [
                                    'KTM', 'Yamaha', 'Honda', 'Kawasaki', 'Suzuki', 'Husqvarna', 'GasGas']
                                rider_name = ""
                                bike = ""

                                for brand in bike_brands:
                                    if brand in remaining:
                                        idx = remaining.index(brand)
                                        rider_name = remaining[:idx].strip()
                                        bike_and_points = remaining[idx:]
                                        # Extract bike (brand name)
                                        bike = brand
                                        break

                                if not rider_name:
                                    # Fallback: use the whole remaining text as rider name
                                    rider_name = remaining

                                # Get points from last column if available
                                points_or_time = cols[4].get_text(
                                    strip=True) if len(cols) > 4 else ""

                                result = {
                                    'year': year,
                                    'race': race_name,
                                    'class': class_type,
                                    'position': position,
                                    'rider': rider_name,
                                    'number': number,
                                    'bike': bike,
                                    'points_or_time': points_or_time,
                                    'event_type': 'main_event' if 'main event' in heading_text else 'overall',
                                    'url': race_url
                                }

                                results.append(result)

                            except (ValueError, IndexError) as e:
                                continue

                        # Only process first main event/overall section found
                        if results:
                            break

            if results:
                df = pd.DataFrame(results)
                print(f"  ✓ Scraped {len(results)} results")
                return df
            else:
                print(f"  ✗ No results found")
                return None

        except Exception as e:
            print(f"  ✗ Error scraping {race_name}: {e}")
            return None

    def scrape_season(self, year: int, classes: List[str] = None) -> pd.DataFrame:
        """
        Scrape all races for a given season

        Args:
            year: Season year
            classes: List of classes to scrape (default: ["450sx", "250sxe", "250sxw"])

        Returns:
            Combined DataFrame with all results
        """
        if classes is None:
            classes = ["450sx", "250sxe", "250sxw"]

        all_results = []

        for class_type in classes:
            print(f"\n{'='*60}")
            print(f"Scraping {year} {class_type.upper()}")
            print(f"{'='*60}")

            races = self.get_season_races(year, class_type)

            for race in races:
                df = self.scrape_race_results(
                    race['url'],
                    year,
                    race['name'],
                    class_type
                )

                if df is not None:
                    all_results.append(df)

                # Be polite - wait between requests
                time.sleep(1)

        if all_results:
            combined_df = pd.concat(all_results, ignore_index=True)
            return combined_df
        else:
            return pd.DataFrame()

    def scrape_multiple_seasons(self, years: List[int], classes: List[str] = None) -> pd.DataFrame:
        """
        Scrape multiple seasons

        Args:
            years: List of years to scrape
            classes: List of classes to scrape

        Returns:
            Combined DataFrame with all results
        """
        all_seasons = []

        for year in years:
            print(f"\n{'#'*60}")
            print(f"# SEASON {year}")
            print(f"{'#'*60}")

            season_df = self.scrape_season(year, classes)

            if not season_df.empty:
                all_seasons.append(season_df)

                # Save individual season
                output_file = self.output_dir / f"sx_{year}_results.csv"
                season_df.to_csv(output_file, index=False)
                print(f"\n✓ Saved {year} results to {output_file}")

            # Wait between seasons
            time.sleep(2)

        if all_seasons:
            combined_df = pd.concat(all_seasons, ignore_index=True)

            # Save combined results
            output_file = self.output_dir / "sx_all_results.csv"
            combined_df.to_csv(output_file, index=False)
            print(f"\n{'='*60}")
            print(f"✓ Saved all results to {output_file}")
            print(f"Total races scraped: {combined_df['race'].nunique()}")
            print(f"Total results: {len(combined_df)}")
            print(f"{'='*60}")

            return combined_df
        else:
            return pd.DataFrame()

    def save_metadata(self, df: pd.DataFrame, filename: str = "metadata.json"):
        """Save metadata about the scraped data"""
        metadata = {
            'total_records': len(df),
            'years': sorted(df['year'].unique().tolist()),
            'classes': sorted(df['class'].unique().tolist()),
            'races': df['race'].nunique(),
            'riders': df['rider'].nunique(),
            'scrape_date': pd.Timestamp.now().isoformat()
        }

        output_file = self.output_dir / filename
        with open(output_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"\n✓ Saved metadata to {output_file}")


def main():
    """Main function to run the scraper"""
    scraper = MXGPResultsScraper(output_dir="data/raw")

    # Scrape 2023-2025 for both 450SX and 250SX (East and West)
    years = [2023, 2024, 2025]
    classes = ["450sx", "250sxe", "250sxw"]

    print("Starting MXGPResults.com scraper...")
    print(f"Years: {years}")
    print(f"Classes: {classes}")

    df = scraper.scrape_multiple_seasons(years, classes)

    if not df.empty:
        scraper.save_metadata(df)

        print("\n" + "="*60)
        print("SCRAPING COMPLETE!")
        print("="*60)
        print(f"\nData summary:")
        print(f"  Years: {df['year'].unique()}")
        print(f"  Classes: {df['class'].unique()}")
        print(f"  Total races: {df['race'].nunique()}")
        print(f"  Total results: {len(df)}")
        print(f"\nFiles saved in: data/raw/")
    else:
        print("\n✗ No data was scraped")


if __name__ == "__main__":
    main()
