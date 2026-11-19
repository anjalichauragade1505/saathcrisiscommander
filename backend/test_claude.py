from dotenv import load_dotenv
import os
from anthropic import Anthropic

load_dotenv()

key = os.getenv("ANTHROPIC_API_KEY")

print("API key loaded:", bool(key))

if not key:
    raise ValueError("API key not loaded. Check .env location.")

client = Anthropic(api_key=key)

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "Reply with: Claude API working"}
    ]
)

for block in response.content:
    if hasattr(block, "text"):
        print(block.text)