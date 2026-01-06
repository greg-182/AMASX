"""Check where date and round number are on race pages"""
import requests
from bs4 import BeautifulSoup
import re

urls = [
    "https://mxgpresults.com/sx/2025/anaheim-1/",
    "https://mxgpresults.com/sx/2025/salt-lake-city/",
    "https://mxgpresults.com/sx/2025/denver/250sx"
]

for url in urls:
    print("="*70)
    print(f"URL: {url}")
    print("="*70)

    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Check h1 and h2 tags for race info
    h1 = soup.find('h1')
    if h1:
        print(f"\nH1: {h1.get_text(strip=True)}")

    h2s = soup.find_all('h2')
    for h2 in h2s[:3]:
        print(f"H2: {h2.get_text(strip=True)}")

    # Look for date patterns
    text = soup.get_text()

    # Common date patterns
    date_patterns = [
        r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
        r'(\d{4}-\d{2}-\d{2})',       # YYYY-MM-DD
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}'
    ]

    print("\nDate matches:")
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            print(f"  Pattern {pattern}: {matches[:3]}")

    # Look for round number
    round_patterns = [
        r'Round\s+(\d+)',
        r'Rd\.?\s+(\d+)',
        r'R(\d+)',
        r'#(\d+)'
    ]

    print("\nRound number matches:")
    for pattern in round_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            print(f"  Pattern {pattern}: {matches[:5]}")

    # Check meta tags
    print("\nMeta tags:")
    metas = soup.find_all('meta')
    for meta in metas:
        if 'date' in str(meta).lower() or 'time' in str(meta).lower():
            print(f"  {meta}")

    print("\n")
