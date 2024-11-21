# test_openai_api.py

import os
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=".env")  # Adjust the path if your .env file is named differently or located elsewhere

# Get the OpenAI API key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OpenAI API key is missing. Please set the OPENAI_API_KEY environment variable.")

# Set the OpenAI API key
openai.api_key = OPENAI_API_KEY

def test_openai_api():
    try:
        # Make a simple API call to get a completion
        response = openai.Completion.create(
            engine="text-davinci-003",  # You can change the engine if needed
            prompt="Hello, world!",
            max_tokens=5
        )
        print("API call successful. Response:")
        print(response.choices[0].text.strip())
    except openai.error.OpenAIError as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    test_openai_api()
