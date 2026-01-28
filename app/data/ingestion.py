import pandas as pd
import os
import sys
import httpx
from sqlmodel import Session, select, SQLModel, text

# Add the project root to the Python path to allow imports from 'app'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.core.database import engine
from app.models.terms import Term

def find_column(df, options):
    """Helper to find the first matching column from a list of options, case-insensitively."""
    df_columns_lower = [str(col).lower() for col in df.columns]
    for option in options:
        if option.lower() in df_columns_lower:
            original_col_index = df_columns_lower.index(option.lower())
            return df.columns[original_col_index]
    return None

def ingest_namaste_data():
    """Reads NAMASTE Excel files, cleans them, and saves the base terms to the database."""
    print("--- Starting NAMASTE Data Ingestion ---")
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    base_path = os.path.join(project_root, 'data', 'source')
    files = {
        'Ayurveda': os.path.join(base_path, 'ayurveda_codes.xlsx'),
        'Siddha': os.path.join(base_path, 'siddha_codes.xlsx'),
        'Unani': os.path.join(base_path, 'unani_codes.xlsx')
    }
    
    with Session(engine) as session:
        # Efficiently clear all existing data from the term table
        print("-> Clearing existing data from the 'term' table...")
        session.execute(text("DELETE FROM terms"))
        
        for system, path in files.items():
            try:
                df = pd.read_excel(path, dtype=str).fillna("")
                df.replace("--", "", inplace=True)
                
                code_col = find_column(df, ['NAMC_CODE', 'NUMC_CODE', 'NAMD_CODE', 'CODE'])
                display_col = find_column(df, ['NAMC_term', 'NAMC_TERM', 'NUMC_TERM', 'TERM'])
                translation_col = find_column(df, ['Short_definition', 'Short Definition'])
                definition_col = find_column(df, ['Long_definition', 'Long Definition'])

                if not code_col or not display_col:
                    print(f"Warning: Skipping {path} due to missing columns.")
                    continue

                # Clean and filter data before insertion
                df[code_col] = df[code_col].str.strip().str.replace(r'\s+', ' ', regex=True)
                df.dropna(subset=[code_col, display_col], inplace=True)
                df = df[(df[code_col] != '') & (df[display_col] != '')]
                df.drop_duplicates(subset=[code_col], keep='first', inplace=True)

                for _, row in df.iterrows():
                    session.add(Term(
                        code=row.get(code_col), display=row.get(display_col),
                        system=system, translation=row.get(translation_col, ""),
                        definition=row.get(definition_col, "")
                    ))
                print(f"-> Prepared {len(df)} unique, valid terms from {system}.")
            except Exception as e:
                print(f"Warning: Could not process {path}. Error: {e}")
        
        session.commit()
    print("--- NAMASTE Data Ingestion Complete ---")


def fetch_and_save_icd_codes():
    """
    Fetches all MMS codes from the local Docker API and saves them to the database.
    """
    print("\n--- Starting ICD-11 Data Fetch ---")
    local_base_url = "http://localhost:8000"
    headers = {"API-Version": "v2", "Accept-Language": "en", "Accept": "application/json"}

    with httpx.Client(headers=headers, timeout=30.0) as client:
        with Session(engine) as session:
            system_name = "ICD-11-MMS"
            linearization_url = f"{local_base_url}/icd/release/11/mms"
            
            print(f"Fetching {system_name} codes from {linearization_url}...")
            try:
                # Step 1: Get the latest release URI from the local container
                response = client.get(linearization_url)
                response.raise_for_status()
                latest_release_uri = response.json().get('latestRelease').replace("https://id.who.int", local_base_url)
                
                # Step 2: Use the release URI to get the list of chapters
                response = client.get(latest_release_uri)
                response.raise_for_status()
                chapters = [uri.replace("https://id.who.int", local_base_url) for uri in response.json().get('child', [])]
                
                print(f"-> Found {len(chapters)} chapters. Fetching all codes...")
                all_codes_to_add = []
                
                # Step 3: Loop through chapters and get all leaf nodes
                for i, chapter_uri in enumerate(chapters, 1):
                    res = client.get(chapter_uri)
                    entity = res.json()
                    if "leaf" in entity and entity["leaf"]:
                        for leaf_node in entity["leaf"]:
                            if len(leaf_node) == 2:
                                all_codes_to_add.append(Term(code=leaf_node[0], display=leaf_node[1], system=system_name))
                    print(f"  -> Processed chapter {i}/{len(chapters)}. Total codes found so far: {len(all_codes_to_add)}")

                session.add_all(all_codes_to_add)
                session.commit()
                print(f"-> Successfully saved {len(all_codes_to_add)} {system_name} codes to the database.")
            except Exception as e:
                print(f"Process failed for {system_name}: {e}")
                session.rollback()

def update_mappings_from_csv():
    """
    Reads the final_mappings.csv and updates the Term table with the ICD-11 mappings.
    """
    print("\n--- Starting: Updating Mappings in Database ---")
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    mappings_file = os.path.join(project_root, 'mapping-engine', 'output', 'final_mappings.csv')
    
    try:
        mappings_df = pd.read_csv(mappings_file).fillna('')
    except FileNotFoundError:
        print(f"Error: Mapping file not found at {mappings_file}")
        return

    with Session(engine) as session:
        update_count = 0
        for _, row in mappings_df.iterrows():
            statement = select(Term).where(Term.code == row['NAMASTE_code'])
            term_to_update = session.exec(statement).first()
            
            if term_to_update:
                term_to_update.icd11_mms_code = str(row.get('Biomedicine_code', '')).split(',')[0].strip()
                term_to_update.icd11_mms_display = str(row.get('Biomedicine_term', '')).split(',')[0].strip()
                term_to_update.icd11_tm2_code = row.get('TM-2_code', '')
                term_to_update.icd11_tm2_display = row.get('TM-2_term', '')
                session.add(term_to_update)
                update_count += 1
        
        session.commit()
        print(f"-> Successfully updated {update_count} mappings in the database.")
    
    print("--- Finished: Updating Mappings ---")


if __name__ == "__main__":
    # Create tables if they don't exist
    SQLModel.metadata.create_all(engine)
    
    # Run the full pipeline
    ingest_namaste_data()
    fetch_and_save_icd_codes()
    update_mappings_from_csv()