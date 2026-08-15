from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

print("=== MODELOS GEMINI DISPONIBLES ===")

for model in client.models.list():
    if model.supported_actions and "generateContent" in model.supported_actions:
        print(model.name)

print("\n=== PRUEBA DE GEMINI 3.5 FLASH ===")

response = client.models.generate_content(
    model="gemini-3.5-flash",
    contents="Hola, soy Leo"
)

print("\nRESPUESTA DE GEMINI:")
print(response.text)