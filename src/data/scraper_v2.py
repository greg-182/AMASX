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


class MXGPResultsScraperV2:
    """Improved scraper for MXGPResults.com that handles malformed HTML"""

    BASE_URL = "https://mxgpresults.com/sx"

    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_season_races(self, year: int, class_type: str = "450sx") -> List[Dict]:
        """Get list of all races for a given season"""
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

            # For 250 classes, look for links with /250sx suffix
            if class_type in ['250sxe', '250sxw']:
                race_links = soup.find_all(
                    'a', href=re.compile(f'/sx/{year}/[a-z0-9-]+/250sx'))
            else:
                race_links = soup.find_all(
                    'a', href=re.compile(f'/sx/{year}/[a-z0-9-]+/$'))

            seen_urls = set()
            for link in race_links:
                race_url = link.get('href')
                if race_url and race_url not in seen_urls:
                    # Extract race slug (before /250sx if present)
                    if '/250sx' in race_url:
                        race_slug = race_url.strip('/').split('/')[-2]
                    else:
                        race_slug = race_url.strip('/').split('/')[-1]

                    race_name = race_slug.replace('-', ' ').title()

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
            print(f"Error fetching race list: {e}")
            return []

    def parse_table_from_html(self, html_str: str, event_type: str) -> List[Dict]:
        """
        Parse table data directly from HTML string using regex
        Handles malformed HTML that's missing closing tags
        """
        results = []

        # Pattern to match table rows: <tr><td>pos<td>#num<td><a>rider</a><td>bike<td>time/points
        row_pattern = r'<tr><td>(\d+)<td>#?(\d+)<td><a[^>]*>([^<]+)</a><td>([^<]+)<td>([^<\n]+)'

        matches = re.findall(row_pattern, html_str)

        for match in matches:
            position, number, rider, bike, time_or_points = match

            results.append({
                'position': int(position),
                'number': number.strip(),
                'rider': rider.strip(),
                'bike': bike.strip(),
                'time_or_points': time_or_points.strip(),
                'event_type': event_type
            })

        return results

    def scrape_race_results(self, race_url: str, year: int, race_name: str, class_type: str) -> Optional[pd.DataFrame]:
        """Scrape all results from a single race (qualifying, heats, LCQ, main event)"""
        print(f"Scraping: {race_name} ({class_type})")

        try:
            response = self.session.get(race_url, timeout=10)
            response.raise_for_status()
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            # Extract date and round number from page
            date = None
            round_number = None

            # Look for round number (e.g., "Round 17")
            round_match = re.search(
                r'Round\s+(\d+)', html_content, re.IGNORECASE)
            if round_match:
                round_number = int(round_match.group(1))

            # Look for date - try multiple formats
            # Format 1: Full month name (e.g., "May 3, 2025")
            date_match = re.search(
                r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})', html_content, re.IGNORECASE)
            if date_match:
                month, day, year_str = date_match.groups()
                date = f"{month} {day}, {year_str}"
            else:
                # Format 2: Short month name (e.g., "Feb 1, 2025")
                date_match_short = re.search(
                    r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+(\d{1,2}),?\s+(\d{4})', html_content, re.IGNORECASE)
                if date_match_short:
                    month_short, day, year_str = date_match_short.groups()
                    # Convert short month to full
                    month_map = {'Jan': 'January', 'Feb': 'February', 'Mar': 'March', 'Apr': 'April',
                                 'May': 'May', 'Jun': 'June', 'Jul': 'July', 'Aug': 'August',
                                 'Sep': 'September', 'Oct': 'October', 'Nov': 'November', 'Dec': 'December'}
                    month = month_map.get(month_short, month_short)
                    date = f"{month} {day}, {year_str}"

            all_results = []

            # Find all result sections
            headings = soup.find_all(['h3', 'h4'])

            for heading in headings:
                heading_text = heading.get_text(strip=True)

                # Determine event type
                event_type = None
                if 'Combined Qualifying' in heading_text or 'Qualifying' in heading_text:
                    event_type = 'qualifying'
                elif 'Heat East' in heading_text:
                    event_type = 'heat_east'
                elif 'Heat West' in heading_text:
                    event_type = 'heat_west'
                elif 'Heat 1' in heading_text:
                    event_type = 'heat_1'
                elif 'Heat 2' in heading_text:
                    event_type = 'heat_2'
                elif 'Last Chance' in heading_text or 'LCQ' in heading_text:
                    event_type = 'lcq'
                elif 'East/West Showdown' in heading_text or 'Showdown' in heading_text:
                    event_type = 'main_event'  # Showdown is the main event for combined East/West
                elif 'Main Event' in heading_text:
                    event_type = 'main_event'
                elif 'Race 1' in heading_text:
                    event_type = 'race_1'  # Triple Crown format
                elif 'Race 2' in heading_text:
                    event_type = 'race_2'  # Triple Crown format
                elif 'Race 3' in heading_text:
                    event_type = 'race_3'  # Triple Crown format
                elif 'Overall Results' in heading_text:
                    event_type = 'overall'

                if event_type:
                    # Find the table HTML after this heading
                    # Get position of heading in HTML
                    heading_pos = html_content.find(str(heading))
                    if heading_pos != -1:
                        # Look for table after heading (next 5000 chars)
                        section_html = html_content[heading_pos:heading_pos + 5000]

                        # Find table start
                        table_start = section_html.find('<table')
                        if table_start != -1:
                            # Extract table HTML
                            table_html = section_html[table_start:]

                            # Parse results from this table
                            results = self.parse_table_from_html(
                                table_html, event_type)

                            # Add metadata
                            for result in results:
                                result['year'] = year
                                result['round'] = round_number
                                result['date'] = date
                                result['race'] = race_name
                                result['class'] = class_type
                                result['url'] = race_url

                            all_results.extend(results)

            if all_results:
                df = pd.DataFrame(all_results)
                # Reorder columns
                cols = ['year', 'round', 'date', 'race', 'class', 'event_type',
                        'position', 'rider', 'number', 'bike', 'time_or_points', 'url']
                df = df[cols]
                print(
                    f"  ✓ Scraped {len(all_results)} results across {df['event_type'].nunique()} events")
                return df
            else:
                print(f"  ✗ No results found")
                return None

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return None

    def scrape_season(self, year: int, classes: List[str] = None) -> pd.DataFrame:
        """Scrape all races for a season"""
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
                    race['url'], year, race['name'], class_type)

                if df is not None:
                    all_results.append(df)

                time.sleep(1)

        if all_results:
            return pd.concat(all_results, ignore_index=True)
        return pd.DataFrame()

    def scrape_multiple_seasons(self, years: List[int], classes: List[str] = None) -> pd.DataFrame:
        """Scrape multiple seasons"""
        all_seasons = []

        for year in years:
            print(f"\n{'#'*60}")
            print(f"# SEASON {year}")
            print(f"{'#'*60}")

            season_df = self.scrape_season(year, classes)

            if not season_df.empty:
                all_seasons.append(season_df)

                output_file = self.output_dir / f"sx_{year}_results.csv"
                season_df.to_csv(output_file, index=False)
                print(f"\n✓ Saved {year} results to {output_file}")

            time.sleep(2)

        if all_seasons:
            combined_df = pd.concat(all_seasons, ignore_index=True)

            output_file = self.output_dir / "sx_all_results.csv"
            combined_df.to_csv(output_file, index=False)
            print(f"\n{'='*60}")
            print(f"✓ Saved all results to {output_file}")
            print(f"{'='*60}")

            return combined_df
        return pd.DataFrame()

    def save_metadata(self, df: pd.DataFrame):
        """Save metadata"""
        metadata = {
            'total_records': len(df),
            'years': sorted(df['year'].unique().tolist()),
            'classes': sorted(df['class'].unique().tolist()),
            'event_types': sorted(df['event_type'].unique().tolist()),
            'races': df['race'].nunique(),
            'riders': df['rider'].nunique(),
            'scrape_date': pd.Timestamp.now().isoformat()
        }

        output_file = self.output_dir / "metadata.json"
        with open(output_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"✓ Saved metadata to {output_file}")


def main():
    """Main function"""
    scraper = MXGPResultsScraperV2(output_dir="data/raw")

    years = [2023, 2024, 2025]
    classes = ["450sx", "250sxe", "250sxw"]

    print("="*70)
    print("MXGPResults.com Scraper V2 - Improved HTML Parsing")
    print("="*70)
    print(f"\nYears: {years}")
    print(f"Classes: {classes}")
    print("\nStarting scraper...\n")

    df = scraper.scrape_multiple_seasons(years, classes)

    if not df.empty:
        scraper.save_metadata(df)

        print("\n" + "="*70)
        print("SCRAPING COMPLETE!")
        print("="*70)
        print(f"\nData Summary:")
        print(f"  • Years: {sorted(df['year'].unique())}")
        print(f"  • Classes: {sorted(df['class'].unique())}")
        print(f"  • Event types: {sorted(df['event_type'].unique())}")
        print(f"  • Total races: {df['race'].nunique()}")
        print(f"  • Total riders: {df['rider'].nunique()}")
        print(f"  • Total results: {len(df):,}")

        print(f"\n Sample data:")
        print(df.head(10).to_string())
    else:
        print("\n✗ No data scraped")


if __name__ == "__main__":
    main()
