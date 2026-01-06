"""Check 250SX schedule for 2025"""
import requests
from bs4 import BeautifulSoup

# Check main 2025 page
url = "https://mxgpresults.com/sx/2025/"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

print("="*70)
print("ALL RACE LINKS ON 2025 PAGE:")
print("="*70)

links = soup.find_all('a', href=True)
race_links = []

for link in links:
    href = link.get('href')
    if '/sx/2025/' in href and href.count('/') >= 4:
        text = link.get_text(strip=True)
        if text and 'Statistics' not in text:
            race_links.append((text, href))

# Remove duplicates
seen = set()
unique_links = []
for text, href in race_links:
    if href not in seen:
        unique_links.append((text, href))
        seen.add(href)

for text, href in unique_links[:30]:
    print(f"  {text}: {href}")

print(f"\nTotal unique race links: {len(unique_links)}")

# Check if there's a 250SX East or West specific page
print("\n" + "="*70)
print("CHECKING 250SX EAST PAGE:")
print("="*70)

url_east = "https://mxgpresults.com/sx/2025/250sxe"
response_east = requests.get(url_east)
soup_east = BeautifulSoup(response_east.content, 'html.parser')

links_east = soup_east.find_all('a', href=True)
race_links_east = []

for link in links_east:
    href = link.get('href')
    if '/sx/2025/' in href and href.count('/') >= 4:
        text = link.get_text(strip=True)
        if text and 'Statistics' not in text and '250' not in text:
            race_links_east.append((text, href))

seen = set()
unique_east = []
for text, href in race_links_east:
    if href not in seen:
        unique_east.append((text, href))
        seen.add(href)

for text, href in unique_east[:15]:
    print(f"  {text}: {href}")

print(f"\nTotal 250SX East races: {len(unique_east)}")

print("\n" + "="*70)
print("CHECKING 250SX WEST PAGE:")
print("="*70)

url_west = "https://mxgpresults.com/sx/2025/250sxw"
response_west = requests.get(url_west)
soup_west = BeautifulSoup(response_west.content, 'html.parser')

links_west = soup_west.find_all('a', href=True)
race_links_west = []

for link in links_west:
    href = link.get('href')
    if '/sx/2025/' in href and href.count('/') >= 4:
        text = link.get_text(strip=True)
        if text and 'Statistics' not in text and '250' not in text:
            race_links_west.append((text, href))

seen = set()
unique_west = []
for text, href in race_links_west:
    if href not in seen:
        unique_west.append((text, href))
        seen.add(href)

for text, href in unique_west[:15]:
    print(f"  {text}: {href}")

print(f"\nTotal 250SX West races: {len(unique_west)}")
