from pydantic import BaseModel
from typing import Optional

class DateOfBirth(BaseModel):
    """
    Structured date of birth with separate components.
    """
    year: int
    month: int
    day: int

class ExtractedInformation(BaseModel):
    """
    Schema for the extracted information from a medical document.
    """
    patient_name: Optional[str] = None
    date_of_birth: Optional[DateOfBirth] = None
    phone_number: Optional[str] = None
    referring_physician_name: Optional[str] = None
    reason_for_referral: Optional[str] = None
