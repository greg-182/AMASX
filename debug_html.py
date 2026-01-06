"""Check raw HTML structure of table"""
import requests
from bs4 import BeautifulSoup

url = "https://mxgpresults.com/sx/2025/anaheim-1/"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Find main event section
headings = soup.find_all(['h3'])
for heading in headings:
    if 'Main Event' in heading.get_text():
        print("Found Main Event heading")
        table = heading.find_next('table')

        if table:
            print("\nTable HTML (first 2000 chars):")
            print(str(table)[:2000])

            print("\n\n" + "="*70)
            print("ANALYZING TABLE STRUCTURE:")
            print("="*70)

            # Check if table has proper structure
            rows = table.find_all('tr')
            print(f"\nTotal rows: {len(rows)}")

            if rows:
                first_row = rows[0]
                print(f"\nFirst row tag: {first_row.name}")
                print(f"First row HTML: {str(first_row)[:500]}")

                # Check cells
                cells = first_row.find_all(['td', 'th'])
                print(f"\nNumber of cells in first row: {len(cells)}")

                if cells:
                    print("\nFirst cell:")
                    print(f"  Tag: {cells[0].name}")
                    print(f"  Text: {cells[0].get_text(strip=True)[:100]}")
                    print(f"  HTML: {str(cells[0])[:200]}")

                    # Check if cell has nested elements
                    nested = cells[0].find_all()
                    print(f"  Nested elements: {len(nested)}")
                    if nested:
                        for elem in nested[:5]:
                            print(
                                f"    - {elem.name}: {elem.get_text(strip=True)[:50]}")
        break
