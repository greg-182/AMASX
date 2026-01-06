"""Check special event formats"""
import requests
from bs4 import BeautifulSoup
import re

urls_to_check = [
    ("Indianapolis 250 (East/West Showdown)",
     "https://mxgpresults.com/sx/2025/indianapolis/250sx"),
    ("Glendale 250W (Overall only)", "https://mxgpresults.com/sx/2025/glendale/250sx"),
    ("Birmingham 250E (Overall only)",
     "https://mxgpresults.com/sx/2025/birmingham/250sx"),
    ("Anaheim 1 250W (No date)", "https://mxgpresults.com/sx/2025/anaheim-1/250sx"),
]

for name, url in urls_to_check:
    print("="*70)
    print(f"{name}")
    print(f"URL: {url}")
    print("="*70)

    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(response.content, 'html.parser')

    # Check headings
    print("\nHeadings (H3/H4):")
    headings = soup.find_all(['h3', 'h4'])
    for h in headings[:10]:
        text = h.get_text(strip=True)
        if any(kw in text.lower() for kw in ['heat', 'main', 'lcq', 'qualifying', 'showdown', 'race', 'overall']):
            print(f"  - {text}")

    # Check for date in different formats
    print("\nDate search:")

    # Format 1: "January 11, 2025"
    date1 = re.search(
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})', html, re.IGNORECASE)
    if date1:
        print(f"  Full month format: {date1.group(0)}")

    # Format 2: "Jan 11, 2025"
    date2 = re.search(
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+(\d{1,2}),?\s+(\d{4})', html, re.IGNORECASE)
    if date2:
        print(f"  Short month format: {date2.group(0)}")

    # Format 3: Look in meta tags
    metas = soup.find_all('meta')
    for meta in metas:
        content = meta.get('content', '')
        if re.search(r'\d{4}-\d{2}-\d{2}', content):
            print(f"  Meta tag: {meta}")

    # Format 4: Look for "Event Schedule" section
    schedule_heading = None
    for h in soup.find_all(['h2', 'h3']):
        if 'event schedule' in h.get_text(strip=True).lower():
            schedule_heading = h
            break

    if schedule_heading:
        print(f"  Found 'Event Schedule' section")
        # Get text after this heading
        next_text = schedule_heading.find_next('p')
        if next_text:
            print(f"    Text: {next_text.get_text(strip=True)[:200]}")

    # Check for round
    round_match = re.search(r'Round\s+(\d+)', html, re.IGNORECASE)
    if round_match:
        print(f"\nRound: {round_match.group(1)}")
    else:
        print(f"\nRound: NOT FOUND")

    # For Indianapolis, check the Showdown table structure
    if 'indianapolis' in url.lower():
        print("\nChecking East/West Showdown table:")
        showdown_heading = None
        for h in headings:
            if 'showdown' in h.get_text(strip=True).lower():
                showdown_heading = h
                break

        if showdown_heading:
            # Get HTML position
            heading_pos = html.find(str(showdown_heading))
            if heading_pos != -1:
                section_html = html[heading_pos:heading_pos + 3000]

                # Look for table
                table_start = section_html.find('<table')
                if table_start != -1:
                    table_html = section_html[table_start:table_start + 1000]
                    print(f"  Table HTML (first 500 chars):")
                    print(f"  {table_html[:500]}")

    print("\n")
