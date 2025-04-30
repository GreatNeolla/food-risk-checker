from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()  # <- MUST come before reading the env

api_key = os.getenv("OPENAI_API_KEY")
print("🔑 Loaded Key:", "Yes" if api_key else "No")

client = OpenAI(api_key=api_key)

# Test a simple call
try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say hi"}],
        max_tokens=10
    )
    print("✅ GPT response:", response.choices[0].message.content)
except Exception as e:
    print("❌ API failed:", e)
