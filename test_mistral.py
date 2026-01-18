#!/usr/bin/env python3
"""Test Mistral API integration"""

from mistralai import Mistral
import sys

api_key = "DpFNZqWztH9lqbbSzqY1ZkQgvKPZvPGs"

try:
    client = Mistral(api_key=api_key)
    
    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "user", "content": "Say hello in exactly 5 words"}
        ],
    )
    
    print(f"✓ Mistral API working!")
    print(f"Response: {response.choices[0].message.content}")
    sys.exit(0)
    
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
