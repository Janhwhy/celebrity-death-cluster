import os
import re
import pandas as pd

def extract_age(description):
    """
    Extracts age at death from description.
    """
    if not isinstance(description, str):
        return None
    # 1. Match age at start: e.g., "59, American..." or ", 59, American..."
    m = re.match(r'^\s*([0-9]{1,3})\b', description)
    if m:
        return int(m.group(1))
    # 2. Match "aged X"
    m = re.search(r'\baged\s+([0-9]{1,3})\b', description, re.IGNORECASE)
    if m:
        return int(m.group(1))
    # 3. Match "X years old"
    m = re.search(r'\b([0-9]{1,3})\s+years?\s+old\b', description, re.IGNORECASE)
    if m:
        return int(m.group(1))
    return None

def classify_profession(description):
    """
    Classifies the profession based on keyword matching in description.
    """
    if not isinstance(description, str):
        return 'Other'
    
    desc_lower = description.lower()
    
    # 1. Actor
    if re.search(r'\b(actor|actress|comedian|filmmaker|screenwriter|thespian|voice-over|voice\s+actor|playwright|dramatist)\b', desc_lower) or \
       re.search(r'\b(film|movie|television|tv|theatre|theater|stage)\s+(director|producer|host|presenter)\b', desc_lower):
        return 'Actor'
        
    # 2. Musician
    if re.search(r'\b(singer|songwriter|musician|composer|conductor|guitarist|pianist|vocalist|drummer|violinist|cellist|soprano|tenor|rapper|dj|lyricist|instrumentalist|organist|flautist|saxophonist|bassist|contralto|mezzo-soprano|baritone|basso|hymnwriter|songsmith|fiddler|trumpeter|trombonist|harpsichordist|lutist|songster)\b', desc_lower) or \
       re.search(r'\b(music|band|orchestra|opera|jazz|rock|pop)\b', desc_lower):
        return 'Musician'
        
    # 3. Politician
    if re.search(r'\b(politician|senator|mayor|governor|minister|mp|congressman|congresswoman|representative|parliamentarian|diplomat|ambassador|activist|statesman|stateswoman|premier|chancellor|alderman|councillor|lobbyist|revolutionary|political)\b', desc_lower) or \
       re.search(r'\b(prime\s+minister|president\s+of|head\s+of\s+state|member\s+of\s+parliament|member\s+of\s+congress|member\s+of\s+senate)\b', desc_lower):
        return 'Politician'
        
    # 4. Athlete
    if re.search(r'\b(athlete|footballer|cricketer|golfer|swimmer|boxer|jockey|cyclist|olympian|wrestler|gymnast|skier|rower|skater|sprinter|marathoner|hurdler|referee|umpire)\b', desc_lower) or \
       re.search(r'\b(baseball|basketball|football|soccer|cricket|tennis|rugby|hockey|lacrosse|volleyball|handball|water\s+polo|bobsleigh|curling|biathlon|triathlon|badminton|squash|motorcycle|racing|formula\s+one|f1|nascar|indycar)\s+(player|coach|manager|driver)\b', desc_lower):
        return 'Athlete'
        
    # 5. Scientist
    if re.search(r'\b(scientist|physicist|chemist|biologist|mathematician|astronomer|geologist|neuroscientist|immunologist|academic|scholar|professor|engineer|inventor|physician|surgeon|historian|economist|sociologist|psychologist|anthropologist|archaeologist|linguist|philosopher|meteorologist|climatologist|seismologist|vulcanologist|botanist|zoologist|geneticist|virologist|bacteriologist|pathologist|anatomist|pharmacologist|toxicologist|epidemiologist|paleontologist|ecologist|microbiologist)\b', desc_lower):
        return 'Scientist'
        
    # 6. Business
    if re.search(r'\b(businessman|businesswoman|ceo|founder|entrepreneur|merchant|banker|investor|industrialist|publisher|magnate|tycoon|executive)\b', desc_lower) or \
       re.search(r'\b(business\s+executive|managing\s+director|venture\s+capitalist|philanthropist)\b', desc_lower):
        return 'Business'
        
    # 7. Royalty
    if re.search(r'\b(prince|princess|king|queen|duke|duchess|emperor|empress|royal|royalty|monarch|sultan|caliph|emir|tsar|czar|grand\s+duke|grand\s+duchess|lord|baron|earl|count|countess|marquess|viscount|baroness)\b', desc_lower):
        return 'Royalty'
        
    return 'Other'

def main():
    raw_path = 'data/raw/deaths_raw.csv'
    cleaned_path = 'data/cleaned/deaths_clean.csv'
    
    if not os.path.exists(raw_path):
        print(f"Error: Raw data file '{raw_path}' not found. Please run the scraper first.")
        return
        
    print(f"Reading raw data from {raw_path}...")
    df = pd.read_csv(raw_path)
    total_before = len(df)
    
    # 1. Parse date column and drop invalid rows
    df['date_parsed'] = pd.to_datetime(df['date'], errors='coerce')
    invalid_dates = df['date_parsed'].isna().sum()
    if invalid_dates > 0:
        print(f"Dropped {invalid_dates} rows with unparseable dates.")
    df = df.dropna(subset=['date_parsed'])
    
    # 2. Extract date components
    df['day'] = df['date_parsed'].dt.day
    df['month'] = df['date_parsed'].dt.month
    df['week_number'] = df['date_parsed'].dt.isocalendar().week
    df['year'] = df['date_parsed'].dt.year  # update year from parsed date
    
    # 3. Classify profession
    print("Classifying professions...")
    df['profession'] = df['description'].apply(classify_profession)
    
    # 4. Filter out 'Other' professions
    print("Filtering out minor/non-celebrity figures...")
    df = df[df['profession'] != 'Other']
    total_after = len(df)
    
    # 5. Extract age at death
    print("Extracting age at death...")
    df['age_at_death'] = df['description'].apply(extract_age)
    
    # Drop the temporary parsing column
    df = df.drop(columns=['date_parsed'])
    
    # Create outputs folder if it doesn't exist
    os.makedirs('data/cleaned', exist_ok=True)
    
    # Save cleaned data
    df.to_csv(cleaned_path, index=False)
    print(f"Cleaned data saved to {cleaned_path}")
    print(f"Total records before filtering: {total_before}")
    print(f"Total records after filtering:  {total_after}")
    print(f"Filtered out {total_before - total_after} records ({(total_before - total_after)/total_before*100:.2f}%)")

if __name__ == "__main__":
    main()
