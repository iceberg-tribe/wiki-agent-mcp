import os
from typing import Optional

class LLMClient:
    def __init__(self, provider: str = "openai", model: str = None, api_key: str = None, base_url: str = None):
        self.provider = provider.lower()
        self.model = model or self._default_model()
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        self.base_url = base_url

    def _default_model(self):
        if self.provider == "openai":
            return "gpt-4-turbo-preview"
        elif self.provider == "anthropic":
            return "claude-3-opus-20240229"
        elif self.provider == "ollama":
            return "llama3"
        return "gpt-3.5-turbo"

    def generate(self, prompt: str, system: str = None, temperature: float = 0.3) -> str:
        if self.provider == "openai":
            import openai
            client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
            )
            return response.choices[0].message.content
        elif self.provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=self.model,
                max_tokens=4000,
                temperature=temperature,
                system=system or "",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        elif self.provider == "ollama":
            import requests
            full_prompt = f"{system}\n\n{prompt}" if system else prompt
            resp = requests.post(
                f"{self.base_url or 'http://localhost:11434'}/api/generate",
                json={"model": self.model, "prompt": full_prompt, "stream": False}
            )
            return resp.json()["response"]
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
