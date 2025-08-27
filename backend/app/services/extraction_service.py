import os
from openai import OpenAI
from dotenv import load_dotenv
from app.models.schemas import ExtractedInformation


load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)


def extract_information_from_document(document: str) -> ExtractedInformation:
    system_prompt = """
    You are a medical administration assistant.
    Your task is to extract structured information from clinic referral documents, made by a physician to  a specialist.
    You will receive a document in markdown format, and you should extract the following information:
    - Patient's full name
    - Patient's date of birth (year, month, day)
    - Patient's phone number
    - Referring physician's or healthcare provider's full name
    - Reason for referral
    
    The output should be in JSON format, following the schema provided.
    
    For reason for referral, provide a brief summary (1-4 sentences) based on the document content.
    
    The user will provide the document in markdown format. 
    Documents come from various clinics and may have different formats, but they should always contain the required information.
    If any piece of information is not found, return null for that field.
    """
    user_prompt = document

    response = client.responses.parse(
        model="gpt-4o-2024-08-06",
        instructions=system_prompt,
        input=user_prompt,
        text_format= ExtractedInformation
    )

    print(response.output_parsed)
    return response.output_parsed
