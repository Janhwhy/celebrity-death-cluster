import os
import re
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_month_links(year_url, year, headers):
    """
    Fetches the year page and extracts the links for each month's death list.
    If no links are found, falls back to programmatically generating them.
    """
    months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    try:
        response = requests.get(year_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Warning: Year page {year} returned status code {response.status_code}. Falling back to programmatically generated month links.")
            return [f"https://en.wikipedia.org/wiki/Deaths_in_{month}_{year}" for month in months]
        
        soup = BeautifulSoup(response.text, 'html.parser')
        month_urls = []
        seen = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Match href starting with /wiki/Deaths_in_ and ending with _year
            if href.startswith('/wiki/Deaths_in_') and href.endswith(f'_{year}'):
                url = 'https://en.wikipedia.org' + href
                if url not in seen:
                    seen.add(url)
                    month_urls.append(url)
                    
        # If we failed to find any month links, generate them programmatically
        if not month_urls:
            return [f"https://en.wikipedia.org/wiki/Deaths_in_{month}_{year}" for month in months]
            
        return month_urls
    except Exception as e:
        print(f"Error fetching year page for {year}: {e}. Falling back to programmatically generated month links.")
        return [f"https://en.wikipedia.org/wiki/Deaths_in_{month}_{year}" for month in months]

def scrape_month_deaths(month_url, year, headers, month_num):
    """
    Scrapes the list of deaths from a monthly Wikipedia page.
    """
    records = []
    try:
        response = requests.get(month_url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Warning: Failed to fetch {month_url} (Status code: {response.status_code})")
            return records
            
        soup = BeautifulSoup(response.text, 'html.parser')
        content_div = soup.find(class_='mw-parser-output')
        if not content_div:
            return records
            
        current_day = None
        for child in content_div.children:
            if child.name in ['h2', 'h3', 'h4', 'div']:
                text = child.get_text().strip()
                # Remove edit links (e.g. "[edit]" or "1[edit]")
                text = re.sub(r'\[edit\]', '', text).strip()
                if text.isdigit():
                    val = int(text)
                    if 1 <= val <= 31:
                        current_day = val
                # Stop parsing if we reach references, see also or similar sections
                elif text in ['References', 'See also', 'Notes', 'External links', 'Navigation menu']:
                    current_day = None
                    
            elif child.name == 'ul' and current_day is not None:
                for li in child.find_all('li', recursive=False):
                    first_a = li.find('a')
                    full_text = li.text.strip()
                    if first_a:
                        name = first_a.text.strip()
                        # Extract description next to the name
                        description = full_text[len(name):].strip()
                    else:
                        parts = full_text.split(',', 1)
                        name = parts[0].strip()
                        description = parts[1].strip() if len(parts) > 1 else ''
                        
                    # Skip if name is empty or it's a metadata list item
                    if not name or len(name) > 100:
                        continue
                        
                    # Clean up description (remove citations and leading commas/spaces)
                    description = re.sub(r'\[\d+\]', '', description)
                    description = re.sub(r'\[[a-zA-Z\s]+\]', '', description)
                    description = description.strip(', ').strip()
                    
                    # Format date as YYYY-MM-DD
                    date_str = f"{year}-{month_num:02d}-{current_day:02d}"
                    
                    records.append({
                        'name': name,
                        'date': date_str,
                        'description': description,
                        'year': year
                    })
    except Exception as e:
        print(f"Error scraping month {month_url}: {e}")
        
    return records

def main():
    headers = {
        'User-Agent': 'CelebrityDeathScraper/1.0 (contact: scraper@example.com) Mozilla/5.0'
    }
    
    months = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    month_map = {month: i for i, month in enumerate(months, 1)}
    
    all_records = []
    
    print("Starting Wikipedia death data scraping (Years 2000 to 2025)...")
    
    for year in range(2000, 2026):
        year_url = f"https://en.wikipedia.org/wiki/Deaths_in_{year}"
        print(f"Scraping year {year}...")
        
        # 1. Get monthly URLs for this year
        month_urls = get_month_links(year_url, year, headers)
        
        year_record_count = 0
        
        # 2. Scrape each month
        for month_url in month_urls:
            # Determine the month number
            month_num = 1
            for m in months:
                if f"_{m}_" in month_url or month_url.endswith(f"_{m}"):
                    month_num = month_map[m]
                    break
            
            # Scrape month page
            month_records = scrape_month_deaths(month_url, year, headers, month_num)
            all_records.extend(month_records)
            year_record_count += len(month_records)
            
            # Respect rate limits between month page requests
            time.sleep(1.0)
            
        print(f"Completed scraping year {year}. Found {year_record_count} records.")
        
        # Add 5 second delay between years as requested
        time.sleep(5.0)
        
    # Create output directory if it doesn't exist
    os.makedirs('data/raw', exist_ok=True)
    
    # Save to CSV
    df = pd.DataFrame(all_records)
    csv_path = 'data/raw/deaths_raw.csv'
    df.to_csv(csv_path, index=False)
    print(f"Scraping completed. Saved {len(df)} records to {csv_path}")

if __name__ == "__main__":
    main()
