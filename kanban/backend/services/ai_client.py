import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AIClient:
    """
    A client to interact with an Ollama server using the OpenAI-compatible API.
    Enhanced for contextual and multi-project memory support.
    """

    def __init__(self, model: str = "llama3.1:latest", temperature: float = 0.7, num_ctx: int = 4096):
        # Initialize the Ollama-compatible OpenAI client
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",  # Any string works for local Ollama
        )
        self.model = model
        self.temperature = temperature
        self.num_ctx = num_ctx
        print(f"✅ AIClient initialized with model '{self.model}' (ctx={self.num_ctx}, temp={self.temperature})")

    # ----------------------------------------------------------------------
    # 1. Standard chat completion
    # ----------------------------------------------------------------------
    def chat_completion(self, messages: list[dict], temperature: float | None = None) -> str:
        """
        Generates a chat completion using the configured Ollama model.
        """
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.temperature,
                extra_body={
                    # Some Ollama models (e.g., Llama3) respect num_ctx
                    "num_ctx": self.num_ctx
                }
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"❌ Ollama API call failed: {e}")
            print("---")
            print(f"💡 Is the Ollama server running? (ollama serve)")
            print(f"💡 Is '{self.model}' installed? (ollama list)")
            print("---")
            return "Sorry, I can't connect to the local AI service. Please ensure Ollama is running and the model is installed."

    # ----------------------------------------------------------------------
    # 2. Summarization helper
    # ----------------------------------------------------------------------
    def summarize(self, text: str, length: int = 100) -> str:
        """
        Quickly summarize text using the current model.
        """
        messages = [
            {"role": "system", "content": "You are a concise summarization assistant."},
            {"role": "user", "content": f"Summarize the following text in under {length} words:\n{text}"}
        ]
        return self.chat_completion(messages)

# ----------------------------------------------------------------------
# 3. Singleton factory (as before)
# ----------------------------------------------------------------------
def get_ai_client():
    """Factory function to get a singleton AI client instance."""
    if not hasattr(get_ai_client, "instance"):
        get_ai_client.instance = AIClient()
    return get_ai_client.instance
