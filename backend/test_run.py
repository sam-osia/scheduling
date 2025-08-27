import os
import sys
import io
import contextlib
import re
import threading

import marker.services.azure_openai
from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered
from marker.config.parser import ConfigParser
from dotenv import load_dotenv
from marker.services.openai import OpenAIService

load_dotenv()

openai_config = {
    'output_format': 'html',
    'use_llm': True,
    'llm_service': 'marker.services.openai.OpenAIService',
    'openai_api_key': os.getenv('OPENAI_API_KEY')
}

azure_config = {
    'output_format': 'html',
    'use_llm': True,
    'pdftext_workers': 4,
    'llm_service': "marker.services.azure_openai.AzureOpenAIService",
    'azure_endpoint': os.getenv('AZURE_ENDPOINT'),
    'azure_api_key': os.getenv('AZURE_API_KEY'),
    'azure_api_version': '2024-12-01-preview',
    'deployment_name': 'gpt-4o',
}

config_parser = ConfigParser(azure_config)
artifact_dict = create_model_dict()

converter = PdfConverter(
    config=config_parser.generate_config_dict(),
    artifact_dict=artifact_dict,
    processor_list=config_parser.get_processors(),
    renderer=config_parser.get_renderer(),
    llm_service=config_parser.get_llm_service()
)
    
rendered = converter('tmp/sample2.pdf')

print(rendered)
llm_tokens_used = sum(page['block_metadata']['llm_tokens_used'] for page in rendered.metadata['page_stats'])
print(f"LLM tokens used: {llm_tokens_used}")

print("Processing complete!")
text, _, images = text_from_rendered(rendered)

# save the text as an HTML file
with open('tmp/sample_parsed.html', 'w') as f:
    f.write(text)

print('done')
