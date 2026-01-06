"""Debug Anaheim 1 2025 page structure"""
import requests
from bs4 import BeautifulSoup

url = "https://mxgpresults.com/sx/2025/anaheim-1/"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

print("="*70)
print("ALL HEADINGS ON PAGE:")
print("="*70)

headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
for i, h in enumerate(headings[:30]):
    print(f"{i}: <{h.name}> {h.get_text(strip=True)}")

print("\n" + "="*70)
print("EXAMINING EACH SECTION WITH TABLES:")
print("="*70)

for heading in headings:
    text = heading.get_text(strip=True)

    # Look for result sections
    if any(keyword in text.lower() for keyword in ['qualifying', 'heat', 'main event', 'lcq', 'last chance']):
        print(f"\n{'='*70}")
        print(f"SECTION: {text}")
        print(f"{'='*70}")

        table = heading.find_next('table')
        if table:
            rows = table.find_all('tr')
            print(f"Table has {len(rows)} rows")

            if rows:
                # Show header
                print("\nHEADER:")
                header = rows[0]
                cells = header.find_all(['th', 'td'])
                for i, cell in enumerate(cells):
                    print(f"  Col {i}: '{cell.get_text(strip=True)}'")

                # Show first 3 data rows
                print("\nFIRST 3 DATA ROWS:")
                for row_idx in range(1, min(4, len(rows))):
                    print(f"\n  Row {row_idx}:")
                    cells = rows[row_idx].find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        text = cell.get_text(strip=True)
                        if len(text) > 50:
                            text = text[:50] + "..."
                        print(f"    Col {i}: '{text}'")
        else:
            print("No table found")
