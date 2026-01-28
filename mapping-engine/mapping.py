import pandas as pd
import os
import sys
from sqlmodel import Session, select
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Add the ayurlink-api project's root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import engine
from app.models.terms import Term

def load_data_from_db():
    """
    Loads data from the DB and correctly separates ICD-11 into Biomedicine and TM-2.
    """
    print("--- Loading Data from Database ---")
    
    with Session(engine) as session:
        # Load NAMASTE terms
        statement_namaste = select(Term).where(Term.system.in_(['Ayurveda', 'Siddha', 'Unani']))
        namaste_df = pd.DataFrame([term.dict() for term in session.exec(statement_namaste).all()])
        namaste_df['search_text'] = namaste_df['display'] + ": " + namaste_df['translation'] + " " + namaste_df['definition']
        print(f"-> Loaded {len(namaste_df)} NAMASTE terms.")

        # Load all ICD-11 terms
        statement_icd11 = select(Term).where(Term.system == 'ICD-11-MMS')
        icd11_df = pd.DataFrame([term.dict() for term in session.exec(statement_icd11).all()])
        icd11_df['search_text'] = icd11_df['display']
        print(f"-> Loaded {len(icd11_df)} total ICD-11 terms.")

        # Correctly separate ICD-11 into TM-2 and Biomedicine
        def is_tm2_code(code):
            if not isinstance(code, str) or len(code) < 2: return False
            prefix = code[:2].upper()
            return ('SA' <= prefix <= 'SJ') or ('SK' <= prefix <= 'ST')

        is_tm2 = icd11_df['code'].apply(is_tm2_code)
        icd11_tm2_df = icd11_df[is_tm2].copy().reset_index(drop=True)
        icd11_mms_df = icd11_df[~is_tm2].copy().reset_index(drop=True)

        print(f"-> Separated into {len(icd11_mms_df)} Biomedicine and {len(icd11_tm2_df)} TM-2 terms.")

    print("--- Datasets Loaded ---")
    return namaste_df, icd11_mms_df, icd11_tm2_df

def build_search_index(df: pd.DataFrame, model: SentenceTransformer):
    """Creates a Faiss index for a given DataFrame."""
    print(f"-> Generating embeddings for {len(df)} terms...")
    embeddings = model.encode(df['search_text'].tolist(), show_progress_bar=True)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings.astype('float32'))
    print("-> Index built successfully.")
    return index

def find_mappings(namaste_df, mms_df, mms_index, tm2_df, tm2_index, model):
    """Performs one-to-many parallel mapping for Biomedicine and TM-2."""
    print("\n--- Starting: Finding Parallel Mappings ---")
    
    mms_lookup = pd.Series(mms_df.code.values, index=mms_df.display.str.lower()).to_dict()
    tm2_lookup = pd.Series(tm2_df.code.values, index=tm2_df.display.str.lower()).to_dict()

    print("-> Generating embeddings for NAMASTE terms...")
    namaste_embeddings = model.encode(namaste_df['search_text'].tolist(), show_progress_bar=True)

    # Search for multiple Biomedicine candidates using a threshold
    search_radius_mms = 0.9  # This value may need tuning
    mms_lims, mms_distances, mms_indices = mms_index.range_search(namaste_embeddings.astype('float32'), search_radius_mms)

    # Search for the single best TM-2 candidate
    tm2_distances, tm2_indices = tm2_index.search(namaste_embeddings.astype('float32'), 1)

    all_mappings = []
    print("-> Processing and combining mappings...")
    for i, row in namaste_df.iterrows():
        namaste_translation = row['translation']

        # --- Process TM-2 Mapping (One-to-One) ---
        tm2_code, tm2_display, tm2_type = None, None, 'semantic_match'
        if namaste_translation.lower() in tm2_lookup:
            tm2_code = tm2_lookup[namaste_translation.lower()]
            tm2_display = namaste_translation
            tm2_type = 'direct_match'
        elif len(tm2_indices) > i:
            match_idx = tm2_indices[i][0]
            tm2_code = tm2_df.iloc[match_idx]['code']
            tm2_display = tm2_df.iloc[match_idx]['display']

        # --- Process Biomedicine Mapping (One-to-Many) ---
        biomed_codes, biomed_displays, biomed_types = set(), set(), set()
        # Direct match first
        if namaste_translation.lower() in mms_lookup:
            biomed_codes.add(mms_lookup[namaste_translation.lower()])
            biomed_displays.add(namaste_translation)
            biomed_types.add('direct_match')
        # Then, add all semantic matches that meet the threshold
        start, end = mms_lims[i], mms_lims[i+1]
        for match_idx in mms_indices[start:end]:
            biomed_codes.add(mms_df.iloc[match_idx]['code'])
            biomed_displays.add(mms_df.iloc[match_idx]['display'])
            biomed_types.add('semantic_match')
            
        all_mappings.append({
            'NAMASTE_code': row['code'],
            'NAMASTE_term': row['display'],
            'Biomedicine_code': ", ".join(sorted(list(biomed_codes))),
            'Biomedicine_term': ", ".join(sorted(list(biomed_displays))),
            'Biomedicine_mapping_type': ", ".join(sorted(list(biomed_types))),
            'TM-2_code': tm2_code,
            'TM-2_term': tm2_display,
            'TM-2_mapping_type': tm2_type
        })
    
    print("--- Finished: Finding Mappings ---")
    return pd.DataFrame(all_mappings)

if __name__ == "__main__":
    # Execute the entire pipeline
    namaste_df, icd11_mms_df, icd11_tm2_df = load_data_from_db()
    
    sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    print("\n--- Building Biomedicine (MMS) Search Index ---")
    mms_search_index = build_search_index(icd11_mms_df, sbert_model)
    
    print("\n--- Building Traditional Medicine (TM-2) Search Index ---")
    tm2_search_index = build_search_index(icd11_tm2_df, sbert_model)

    final_mappings_df = find_mappings(
        namaste_df, 
        icd11_mms_df, mms_search_index, 
        icd11_tm2_df, tm2_search_index, 
        sbert_model
    )

    output_path = 'output/final_mappings.csv'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_mappings_df.to_csv(output_path, index=False)
    
    print(f"\n✅ Success! Final mappings saved to {output_path}")
    print("\nMapping Sample:")
    print(final_mappings_df.head())