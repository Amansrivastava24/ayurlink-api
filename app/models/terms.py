from sqlmodel import SQLModel, Field, Table, Column, UniqueConstraint
from typing import Optional

class Term(SQLModel, table=True):
    """
    Represents a single terminology entry in the database.
    """
    __tablename__ = "terms" # It's conventional to use singular table names
    
    # Add table arguments for the unique constraint
    __table_args__ = (
        UniqueConstraint("system", "code", name="unique_system_code_constraint"),
    )
    
    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(index=True)
    display: str
    system: str = Field(index=True)
    translation: Optional[str] = Field(default=None)
    definition: Optional[str] = Field(default=None)

        # --- ADD THESE MAPPING FIELDS ---
    icd11_mms_code: Optional[str] = Field(default=None)
    icd11_mms_display: Optional[str] = Field(default=None)
    icd11_tm2_code: Optional[str] = Field(default=None)
    icd11_tm2_display: Optional[str] = Field(default=None)