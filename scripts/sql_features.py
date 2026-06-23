"""
SQL Features Script

This script performs the following tasks:
1. Loads data/cleaned/deaths_clean.csv into a local SQLite database (deaths.db).
2. Executes SQL queries to create summary tables:
   - weekly_summary: aggregated death counts and average age by year, week, and profession.
   - monthly_summary: aggregated death counts and average age by year, month, and profession.
   - death_gaps: gap in days between consecutive deaths within each profession.
3. Exports these summary tables as CSV files in data/outputs/.
4. Prints the first 5 rows of each generated table.

Only pandas and sqlite3 (built-in) are used.
"""

import os
import sqlite3
import pandas as pd

# Define paths relative to the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(PROJECT_ROOT, 'data', 'cleaned', 'deaths_clean.csv')
DB_PATH = os.path.join(PROJECT_ROOT, 'deaths.db')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'outputs')

def main():
    print("=" * 60)
    print("SQL Feature Extraction and Data Summarization")
    print("=" * 60)

    # Verify input file exists
    if not os.path.exists(CSV_PATH):
        print(f"Error: Cleaned deaths file not found at: {CSV_PATH}")
        print("Please run the cleaner script first.")
        return

    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output directory verified: {OUTPUT_DIR}")

    # 1. Connect to SQLite database
    print(f"Connecting to SQLite database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Load CSV data into SQLite database
        print(f"Loading data from {CSV_PATH} into 'deaths' table...")
        df = pd.read_csv(CSV_PATH)
        
        # Load the DataFrame to SQLite
        df.to_sql('deaths', conn, if_exists='replace', index=False)
        print(f"Successfully loaded {len(df)} records into 'deaths' table.")

        # 2. Write and execute SQL queries to create tables
        
        # Query 2.1: Create weekly_summary
        print("\nCreating 'weekly_summary' table...")
        cursor.execute("DROP TABLE IF EXISTS weekly_summary;")
        create_weekly_summary_sql = """
        CREATE TABLE weekly_summary AS
        SELECT 
            year,
            week_number AS week,
            profession,
            COUNT(*) AS death_count,
            AVG(age_at_death) AS avg_age_at_death
        FROM 
            deaths
        GROUP BY 
            year,
            week_number,
            profession;
        """
        cursor.execute(create_weekly_summary_sql)
        print("Table 'weekly_summary' created.")

        # Query 2.2: Create monthly_summary
        print("\nCreating 'monthly_summary' table...")
        cursor.execute("DROP TABLE IF EXISTS monthly_summary;")
        create_monthly_summary_sql = """
        CREATE TABLE monthly_summary AS
        SELECT 
            year,
            month,
            profession,
            COUNT(*) AS death_count,
            AVG(age_at_death) AS avg_age_at_death
        FROM 
            deaths
        GROUP BY 
            year,
            month,
            profession;
        """
        cursor.execute(create_monthly_summary_sql)
        print("Table 'monthly_summary' created.")

        # Query 2.3: Create death_gaps
        print("\nCreating 'death_gaps' table...")
        cursor.execute("DROP TABLE IF EXISTS death_gaps;")
        create_death_gaps_sql = """
        CREATE TABLE death_gaps AS
        WITH ordered_deaths AS (
            SELECT 
                name,
                date,
                profession,
                age_at_death,
                LAG(date) OVER (
                    PARTITION BY profession 
                    ORDER BY date ASC, name ASC
                ) AS prev_death_date
            FROM 
                deaths
        )
        SELECT 
            name,
            date,
            profession,
            age_at_death,
            prev_death_date,
            CASE 
                WHEN prev_death_date IS NULL THEN NULL
                ELSE CAST(julianday(date) - julianday(prev_death_date) AS INTEGER)
            END AS gap_in_days
        FROM 
            ordered_deaths;
        """
        cursor.execute(create_death_gaps_sql)
        print("Table 'death_gaps' created.")

        # Commit changes
        conn.commit()

        # 3. Export tables to CSV
        print("\n" + "=" * 40)
        print("Exporting tables to CSV...")
        print("=" * 40)

        # Helper to export and display
        tables_to_export = {
            'weekly_summary': 'weekly_summary.csv',
            'monthly_summary': 'monthly_summary.csv',
            'death_gaps': 'death_gaps.csv'
        }

        for table_name, file_name in tables_to_export.items():
            export_path = os.path.join(OUTPUT_DIR, file_name)
            print(f"Exporting '{table_name}' to {export_path}...")
            
            # Read from sqlite table
            table_df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
            
            # Save to CSV
            table_df.to_csv(export_path, index=False)
            print(f"Saved {len(table_df)} rows.")

            # 4. Print first 5 rows
            print(f"\n--- First 5 rows of '{table_name}' ---")
            print(table_df.head(5))
            print("-" * 50)

    except Exception as e:
        print(f"An error occurred during database operations: {e}")
        conn.rollback()
    finally:
        # Close connection
        conn.close()
        print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()
