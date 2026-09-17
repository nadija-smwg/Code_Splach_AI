# backend/ai_pipeline/test_gemini.py
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

# Test with a simple prompt
response = model.generate_content("Hello, test connection")
print(response.text)
