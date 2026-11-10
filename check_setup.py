import os
import sys
from dotenv import load_dotenv

load_dotenv()

print("Python version:", sys.version.split()[0])

import anthropic, feedparser, requests
print("Packages imported OK")

key = os.getenv("ANTHROPIC_API_KEY")
print("API key found:", bool(key))