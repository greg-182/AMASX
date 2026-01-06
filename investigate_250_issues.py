"""Investigate missing 250SX data and special cases"""
import requests
from bs4 import BeautifulSoup
import re

print("="*70)
print("INVESTIGATING 250SX DATA ISSUES")
print("="*70)

# Check 2025 250SX West - should have Anaheim 1, San Diego, etc.
print("\n" + "="*70)
print("2025 250SX WEST - Checking for missing races")
print("="*70)

url_250w = "https://mxgpresults.com/sx/2025/250sxw"
response = requests.get(url_250w)
soup = BeautifulSoup(response.content, 'html.parser')

# Get all race links
links = soup.find_all('a', href=True)
race_links = []

for link in links:
    href = link.get('href')
    text = link.get_text(strip=True)
    if '/sx/2025/' in href and '/250sx' in href:
        race_links.append((text, href))

print(f"\nFound {len(race_links)} 250SX West race links:")
for text, href in race_links[:15]:
    print(f"  {text}: {href}")

# Check specific races mentioned by user
print("\n" + "="*70)
print("CHECKING SPECIFIC RACES")
print("="*70)

test_urls = [
    ("Anaheim 1 250W", "https://mxgpresults.com/sx/2025/anaheim-1/250sx"),
    ("San Diego 250W", "https://mxgpresults.com/sx/2025/san-diego/250sx"),
    ("Indianapolis 450", "https://mxgpresults.com/sx/2025/indianapolis/"),
    ("Indianapolis 250E", "https://mxgpresults.com/sx/2025/indianapolis/250sx"),
]

for name, url in test_urls:
    print(f"\n{name}: {url}")
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Get H1 title
        h1 = soup.find('h1')
        if h1:
            print(f"  Title: {h1.get_text(strip=True)}")

        # Look for all headings
        headings = soup.find_all(['h3', 'h4'])
        print(f"  Headings found:")
        for h in headings[:15]:
            h_text = h.get_text(strip=True)
            if any(keyword in h_text.lower() for keyword in ['heat', 'main', 'lcq', 'qualifying', 'showdown', 'east', 'west']):
                print(f"    - {h_text}")

        # Check for date
        text = soup.get_text()
        date_match = re.search(
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})', text, re.IGNORECASE)
        if date_match:
            print(f"  Date: {date_match.group(0)}")
        else:
            print(f"  Date: NOT FOUND")

        # Check for round
        round_match = re.search(r'Round\s+(\d+)', text, re.IGNORECASE)
        if round_match:
            print(f"  Round: {round_match.group(1)}")
        else:
            print(f"  Round: NOT FOUND")

    except Exception as e:
        print(f"  ERROR: {e}")

# Check East/West combined event structure
print("\n" + "="*70)
print("CHECKING EAST/WEST COMBINED EVENT (Indianapolis)")
print("="*70)

url = "https://mxgpresults.com/sx/2025/indianapolis/250sx"
response = requests.get(url)
html = response.text
soup = BeautifulSoup(response.content, 'html.parser')

print("\nAll H3/H4 headings:")
headings = soup.find_all(['h3', 'h4'])
for i, h in enumerate(headings):
    print(f"{i}: {h.get_text(strip=True)}")

print("\n" + "="*70)
print("CHECKING 2024 FOR COMPARISON")
print("="*70)

# Check 2024 to see if it has similar issues
url_2024 = "https://mxgpresults.com/sx/2024/indianapolis/250sx"
response_2024 = requests.get(url_2024)
soup_2024 = BeautifulSoup(response_2024.content, 'html.parser')

print("\n2024 Indianapolis 250SX headings:")
headings_2024 = soup_2024.find_all(['h3', 'h4'])
for i, h in enumerate(headings_2024[:20]):
    print(f"{i}: {h.get_text(strip=True)}")

# Check if there's a pattern for East/West events
print("\n" + "="*70)
print("LOOKING FOR EAST/WEST SHOWDOWN PATTERN")
print("="*70)

# Search for "Showdown" or "East/West" in the HTML
if 'showdown' in html.lower():
    print("✓ Found 'Showdown' in page")
    showdown_matches = re.findall(
        r'[^<>]{0,50}showdown[^<>]{0,50}', html, re.IGNORECASE)
    for match in showdown_matches[:5]:
        print(f"  {match.strip()}")

if 'east/west' in html.lower() or 'east & west' in html.lower():
    print("✓ Found 'East/West' or 'East & West' in page")
