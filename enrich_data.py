import pandas as pd
import requests
from bs4 import BeautifulSoup
import os

def enrich_ayurveda_data():
    """
    Scrapes the NAMASTE portal to get English descriptions (short definitions)
    and merges them into the local ayurveda_codes.xlsx file.
    """
    print("--- Starting Data Enrichment Process ---")
    
    # --- Part 1: Scrape the data from the NAMASTE Portal ---
    url = "https://namaste.ayush.gov.in/ayurveda"
    scraped_data = {}

    print(f"Fetching data from: {url}")
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an error for bad status codes
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the main data table on the page
        table = soup.find('table') 
        if not table:
            print("Error: Could not find the data table on the webpage.")
            return

        # Loop through each row in the table body (skipping the header row)
        for row in table.find('tbody').find_all('tr'):
            columns = row.find_all('td')
            if len(columns) >= 7: # Ensure the row has enough columns
                # Column 4 is 'Namc Term', Column 6 is 'Name English'
                namc_term = columns[3].text.strip()
                name_english = columns[5].text.strip()
                
                if namc_term:
                    scraped_data[namc_term] = name_english

        print(f"-> Successfully scraped definitions for {len(scraped_data)} terms.")

    except requests.exceptions.RequestException as e:
        print(f"Error: Could not fetch the webpage. {e}")
        return
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        return

    # --- Part 2: Read your local Excel file and merge the data ---
    local_file_path = os.path.join('data/source/', 'ayurveda_codes.xlsx')
    output_file_path = os.path.join('data/source/', 'ayurveda_codes_enriched.xlsx')

    print(f"\nReading local file: {local_file_path}")
    try:
        df = pd.read_excel(local_file_path)

        # Use the scraped data to fill the 'Short_definition' column
        # It matches each row's 'NAMC_term' with a key in our scraped_data dictionary
        df['Short_definition'] = df['NAMC_term'].map(scraped_data).fillna(df['Short_definition'])

        # Save the updated DataFrame to a new file
        df.to_excel(output_file_path, index=False)
        
        print(f"\n-> Successfully enriched the data and saved it to:")
        print(f"   {output_file_path}")
        print("--- Enrichment Process Complete ---")

    except FileNotFoundError:
        print(f"Error: The file {local_file_path} was not found.")
    except Exception as e:
        print(f"An error occurred while processing the Excel file: {e}")


if __name__ == "__main__":
    enrich_ayurveda_data()