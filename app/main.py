from fastapi import FastAPI, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from typing import List, Optional

from app.core.database import init_db, get_session
from app.models.terms import Term

from fhir.resources.valueset import ValueSet, ValueSetExpansion, ValueSetExpansionContains
from fhir.resources.coding import Coding
from fhir.resources.codesystem import CodeSystem, CodeSystemConcept
from fhir.resources.extension import Extension

from datetime import datetime, timezone

from fhir.resources.conceptmap import ConceptMap, ConceptMapGroup, ConceptMapGroupElement, ConceptMapGroupElementTarget
from fhir.resources.parameters import Parameters, ParametersParameter

NAMASTE_SYSTEM_URL = "https://namaste.ayush.gov.in/"
ICD11_MMS_URL = "https://icd.who.int/browse/2025-01/mms/en"
ICD11_TM2_URL = "https://icd.who.int/browse/2025-01/mms/en"


# --- App Setup ---
app = FastAPI(
    title="AyurLink API",
    description="A FHIR-compliant terminology service for NAMASTE and ICD-11."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Initialization ---
@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def read_root():
    return {"message": "Welcome to the AyurLink API. Go to /docs for documentation."}

@app.get("/api/search", response_model=dict, summary="Unified Terminology Search")
def unified_search(
    *,
    session: Session = Depends(get_session),
    query: str = Query(..., min_length=2, description="Search for a clinical term."),
    system: Optional[str] = Query("all", description="Filter by system (e.g., all, Ayurveda, ICD-11-MMS)")
):
    """
    Performs a case-insensitive search across both NAMASTE and ICD-11 terms
    and returns the results as a FHIR ValueSet.
    """
    statement = select(Term)
    
    # --- THIS IS THE UPDATED LOGIC ---
    # Filter by the specific system if provided
    if system and system.lower() != "all":
        # Use ilike to handle variations like "icd-11-mms" or "ICD-11-MMS"
        statement = statement.where(Term.system.ilike(f"%{system}%"))
    # ---------------------------------
        
    # Add a case-insensitive search filter for the display text
    statement = statement.where(Term.display.ilike(f"%{query}%"))
    
    # Limit the results
    statement = statement.limit(50)
    
    term_results = session.exec(statement).all()
    
    # Structure the results as a FHIR ValueSet expansion
    expansion_contains = [
        ValueSetExpansionContains(
            system=term.system, # Use the system value directly from the database
            code=term.code,
            display=term.display
        ) for term in term_results
    ]

    # Create a valid ValueSet object
    valueset = ValueSet(
        status="active",
        expansion=ValueSetExpansion(
            timestamp=datetime.now(timezone.utc),
            total=len(expansion_contains),
            contains=expansion_contains
        )
    )
    
    return valueset.dict(exclude_none=True)


@app.get("/fhir/CodeSystem", response_model=dict, summary="Get the NAMASTE CodeSystem")
def get_namaste_codesystem(session: Session = Depends(get_session)):
    """
    Dynamically generates the FHIR CodeSystem resource for all NAMASTE terms.
    """
    # --- THIS IS THE FIX ---
    # Add a filter to fetch only terms from the three NAMASTE systems
    statement = select(Term).where(
        (Term.system == 'Ayurveda') | 
        (Term.system == 'Siddha') | 
        (Term.system == 'Unani')
    )
    terms = session.exec(statement).all()
    # -----------------------
    
    concept_list = [
        CodeSystemConcept(
            code=term.code,
            display=term.display,
            extension=[
                Extension(
                    url="https://namaste.ayush.gov.in/fhir/StructureDefinition/tradition",
                    valueString=term.system
                )
            ]
        ) for term in terms
    ]
    
    codesystem = CodeSystem(
        id="namaste-codes",
        url="https://namaste.ayush.gov.in/fhir/CodeSystem/namaste-codes",
        name="NAMASTE_Codes",
        title="National AYUSH Morbidity & Standardized Terminologies",
        status="active",
        content="complete",
        concept=concept_list
    )
    
    return codesystem.dict(exclude_none=True)
    # -----------------------------------------------------------------
    
    # The .dict() method serializes the FHIR object to a dictionary
    return codesystem_resource.dict()


@app.get("/fhir/ConceptMap", response_model=dict, summary="Get the NAMASTE to ICD-11 ConceptMap")
def get_concept_map(session: Session = Depends(get_session)):
    """
    Dynamically generates the FHIR ConceptMap from the database mappings.
    """
    statement = select(Term).where(Term.system.in_(['Ayurveda', 'Siddha', 'Unani']))
    mapped_terms = session.exec(statement).all()

    map_elements = []
    for term in mapped_terms:
        targets = []
        # Add TM-2 mapping if it exists
        if term.icd11_tm2_code:
            targets.append(ConceptMapGroupElementTarget(
                code=term.icd11_tm2_code, 
                display=term.icd11_tm2_display, 
                relationship="related-to"
            ))
        # Add all Biomedicine mappings if they exist
        if term.icd11_mms_code:
            codes = term.icd11_mms_code.split(', ')
            displays = term.icd11_mms_display.split(', ')
            for i in range(len(codes)):
                targets.append(ConceptMapGroupElementTarget(
                    code=codes[i], 
                    display=displays[i], 
                    relationship="related-to"
                ))
        
        if targets:
            element = ConceptMapGroupElement(
                code=term.code, 
                display=term.display, 
                target=targets
            )
            map_elements.append(element)

    # Remove sourceUri and targetUri - they're causing the error
    concept_map = ConceptMap(
        id="namaste-to-icd11",
        url="https://namaste.ayush.gov.in/fhir/ConceptMap/namaste-to-icd11",
        name="NAMASTE_to_ICD11_Map",
        title="NAMASTE to ICD-11 Concept Map",
        status="draft",
        experimental=True,
        description="Mapping from NAMASTE codes to ICD-11 codes",
        # Removed sourceUri and targetUri
        group=[ConceptMapGroup(
            source=NAMASTE_SYSTEM_URL,
            target=ICD11_MMS_URL,
            element=map_elements
        )]
    )
    
    return concept_map.dict(exclude_none=True)


@app.get("/fhir/ConceptMap/$translate", response_model=dict, summary="Translate a NAMASTE code")
def translate_code(
    *, 
    session: Session = Depends(get_session),
    code: str = Query(..., description="The source NAMASTE code to translate."),
    system: str = Query(..., description="The source system URL.")
):
    """
    Translates a NAMASTE code to all its equivalent ICD-11 codes.
    """
    statement = select(Term).where(Term.code == code).where(Term.system.in_(['Ayurveda', 'Siddha', 'Unani']))
    term = session.exec(statement).first()

    if not term or (not term.icd11_mms_code and not term.icd11_tm2_code):
        return Parameters(
            parameter=[
                ParametersParameter(name="result", valueBoolean=False)
            ]
        ).dict()

    matches = []
    # Add TM-2 mapping
    if term.icd11_tm2_code:
        matches.append(ParametersParameter(
            name="match", 
            part=[
                ParametersParameter(name="equivalence", valueCode="related-to"),
                ParametersParameter(
                    name="concept", 
                    valueCoding={
                        "system": ICD11_TM2_URL, 
                        "code": term.icd11_tm2_code, 
                        "display": term.icd11_tm2_display
                    }
                )
            ]
        ))
    
    # Add Biomedicine mappings
    if term.icd11_mms_code:
        codes = term.icd11_mms_code.split(', ')
        displays = term.icd11_mms_display.split(', ')
        for i in range(len(codes)):
            matches.append(ParametersParameter(
                name="match", 
                part=[
                    ParametersParameter(name="equivalence", valueCode="related-to"),
                    ParametersParameter(
                        name="concept", 
                        valueCoding={
                            "system": ICD11_MMS_URL, 
                            "code": codes[i], 
                            "display": displays[i]
                        }
                    )
                ]
            ))
            
    result_params = [ParametersParameter(name="result", valueBoolean=True)] + matches
    return Parameters(parameter=result_params).dict()


# @app.post("/fhir/Bundle", status_code=200, summary="Upload a FHIR Encounter Bundle")
# def upload_encounter_bundle(bundle: Bundle):
#     """
#     Receives a FHIR Bundle, validates the dual-coding in the Condition resource,
#     and returns a success message.
#     """
#     namaste_code_found = False
#     icd11_code_found = False

#     # Loop through the resources in the Bundle
#     for entry in bundle.entry:
#         if entry.resource.resource_type == "Condition":
#             condition: Condition = entry.resource
#             if condition.code and condition.code.coding:
#                 # Check the codings for both a NAMASTE and an ICD-11 code
#                 for coding in condition.code.coding:
#                     if coding.system and "namaste" in coding.system:
#                         namaste_code_found = True
#                     if coding.system and "icd.who.int" in coding.system:
#                         icd11_code_found = True

#     # Enforce the dual-coding rule
#     if not (namaste_code_found and icd11_code_found):
#         raise HTTPException(
#             status_code=400,
#             detail="Validation Error: Condition resource must contain at least one NAMASTE code and one ICD-11 code."
#         )

#     # In a real application, you would save the bundle to a database here.
#     # For now, we just return a success message.
#     return {"status": "success", "message": "Bundle received and validated successfully."}