import os
from dotenv import load_dotenv
load_dotenv()

from groq import Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
models = client.models.list()
print("Available Groq Models:")
for m in sorted(models.data, key=lambda x: x.id):
    print(f"  - {m.id}")
