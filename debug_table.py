"""Debug script to examine table structure in detail"""
import requests
from bs4 import BeautifulSoup

url = "https://mxgpresults.com/sx/2024/salt-lake-city/"
response = requests.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

# Find the main event heading
headings = soup.find_all(['h2', 'h3', 'h4'])
for heading in headings:
    text = heading.get_text(strip=True)
    if 'Main Event' in text or 'Overall Results' in text:
        print(f"\n{'='*60}")
        print(f"Found: {text}")
        print(f"{'='*60}")

        # Find next table
        table = heading.find_next('table')
        if table:
            print("\nTable found!")
            rows = table.find_all('tr')
            print(f"Number of rows: {len(rows)}")

            if rows:
                print("\n--- HEADER ROW ---")
                header = rows[0]
                header_cells = header.find_all(['th', 'td'])
                for i, cell in enumerate(header_cells):
                    print(f"  Col {i}: '{cell.get_text(strip=True)}'")

                print("\n--- FIRST DATA ROW ---")
                if len(rows) > 1:
                    first_row = rows[1]
                    cells = first_row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        print(f"  Col {i}: '{cell.get_text(strip=True)}'")

                print("\n--- SECOND DATA ROW ---")
                if len(rows) > 2:
                    second_row = rows[2]
                    cells = second_row.find_all(['td', 'th'])
                    for i, cell in enumerate(cells):
                        print(f"  Col {i}: '{cell.get_text(strip=True)}'")
        else:
            print("No table found after this heading")

        break
