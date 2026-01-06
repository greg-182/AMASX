"""Debug script to examine the actual HTML structure"""
import requests
from bs4 import BeautifulSoup

url = "https://mxgpresults.com/sx/2024/salt-lake-city/"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Find all headings
print("="*60)
print("HEADINGS FOUND:")
print("="*60)
headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
for i, h in enumerate(headings[:20]):
    print(f"{i}: <{h.name}> {h.get_text(strip=True)}")

print("\n" + "="*60)
print("LOOKING FOR MAIN EVENT SECTION:")
print("="*60)

for heading in headings:
    text = heading.get_text(strip=True)
    if 'main event' in text.lower() or 'overall' in text.lower():
        print(f"\nFound heading: {text}")
        print(f"Tag: <{heading.name}>")

        # Check next siblings
        next_elem = heading.find_next_sibling()
        if next_elem:
            print(
                f"Next sibling: <{next_elem.name}> {next_elem.get_text(strip=True)[:100]}")

        # Check for ol
        ol = heading.find_next('ol')
        if ol:
            print(f"Found OL after heading")
            items = ol.find_all('li', recursive=False)
            print(f"Number of list items: {len(items)}")
            if items:
                print(f"First 3 items:")
                for i, item in enumerate(items[:3], 1):
                    print(f"  {i}. {item.get_text(strip=True)[:80]}")
