import os
import base64
from dotenv import load_dotenv

load_dotenv()

from openai import AzureOpenAI

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_key=os.getenv("AZURE_API_KEY"),
    api_version='2024-10-21',
)

# Read and encode the image
with open("sample.jpg", "rb") as image_file:
    image_data = base64.b64encode(image_file.read()).decode('utf-8')

response = client.chat.completions.create(
    messages=[
        {
            "role": "system",
            "content": "You are a helpful assistant that can analyze images.",
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Please describe this image in detail."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]
        }
    ],
    max_tokens=4096,
    temperature=1.0,
    top_p=1.0,
    model='gpt-4'
)

print(response.choices[0].message.content)