"""Find dates for races that are missing them"""
import requests
from bs4 import BeautifulSoup
import re

races_missing_dates = [
    ("Anaheim 1 2025", "https://mxgpresults.com/sx/2025/anaheim-1/"),
    ("Indianapolis 2025", "https://mxgpresults.com/sx/2025/indianapolis/"),
    ("Birmingham 2025", "https://mxgpresults.com/sx/2025/birmingham/"),
]

for name, url in races_missing_dates:
    print("="*70)
    print(f"{name}")
    print("="*70)

    response = requests.get(url)
    html = response.text
    soup = BeautifulSoup(response.content, 'html.parser')

    # Try to find date in Event Schedule section
    schedule_section = None
    for h in soup.find_all(['h2', 'h3']):
        if 'event schedule' in h.get_text(strip=True).lower():
            schedule_section = h
            break

    if schedule_section:
        print("\nFound Event Schedule section")
        # Get next few elements
        next_elem = schedule_section.find_next()
        for i in range(5):
            if next_elem:
                text = next_elem.get_text(strip=True)
                if text and len(text) < 200:
                    print(f"  {text}")
                next_elem = next_elem.find_next_sibling()

    # Look for any date patterns in the entire page
    print("\nSearching for date patterns:")

    # Pattern 1: "January 11, 2025"
    dates1 = re.findall(
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(2025|2024|2023)', html, re.IGNORECASE)
    if dates1:
        print(f"  Full month: {dates1[:3]}")

    # Pattern 2: "Jan 11, 2025"
    dates2 = re.findall(
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+(\d{1,2}),?\s+(2025|2024|2023)', html, re.IGNORECASE)
    if dates2:
        print(f"  Short month: {dates2[:3]}")

    # Pattern 3: "01/11/2025"
    dates3 = re.findall(r'(\d{1,2})/(\d{1,2})/(2025|2024|2023)', html)
    if dates3:
        print(f"  MM/DD/YYYY: {dates3[:3]}")

    # Pattern 4: "2025-01-11"
    dates4 = re.findall(r'(2025|2024|2023)-(\d{2})-(\d{2})', html)
    if dates4:
        print(f"  YYYY-MM-DD: {dates4[:3]}")

    # Check meta tags
    print("\nMeta tags with dates:")
    for meta in soup.find_all('meta'):
        content = str(meta.get('content', ''))
        if re.search(r'202[345]', content):
            print(
                f"  {meta.get('property', meta.get('name', 'unknown'))}: {content[:100]}")

    print("\n")

# Also check the main season page for a schedule
print("="*70)
print("CHECKING MAIN 2025 PAGE FOR SCHEDULE")
print("="*70)

response = requests.get("https://mxgpresults.com/sx/2025/")
soup = BeautifulSoup(response.content, 'html.parser')

# Look for schedule table or list
print("\nLooking for race schedule...")
tables = soup.find_all('table')
for i, table in enumerate(tables[:3]):
    text = table.get_text()
    if 'anaheim' in text.lower() or 'indianapolis' in text.lower():
        print(f"\nTable {i} (first 500 chars):")
        print(table.get_text()[:500])
