import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print('No GEMINI_API_KEY found')
    exit(1)

url = f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'
try:
    response = requests.get(url)
    data = response.json()
    print('Available Models:')
    for model in data.get('models', []):
        if 'generateContent' in model.get('supportedGenerationMethods', []):
            print(f"- {model['name']}")
except Exception as e:
    print(e)
