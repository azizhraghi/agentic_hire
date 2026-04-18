import os
import json
import logging
import re
import requests
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class BaseAgent:
    """Core class for AI agents — supports Mistral, HuggingFace, or Gemini."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "mistral-small-latest",
        use_huggingface: bool = False,
        use_mistral: bool = True,
    ):
        self.api_key = (
            api_key
            or os.getenv("MISTRAL_API_KEY")
            or os.getenv("HUGGINGFACE_TOKEN")
            or os.getenv("GOOGLE_API_KEY")
        )
        self.model = model
        self.use_huggingface = use_huggingface
        self.use_mistral = use_mistral
        self.name = "Base Agent"

        # Provider URLs
        self.hf_api_url = f"https://api-inference.huggingface.co/models/{model}"
        self.mistral_api_url = "https://api.mistral.ai/v1/chat/completions"

    def _call_llm(self, prompt: str, system_prompt: str = None, max_tokens: int = 4000) -> str:
        """Call LLM — routes to the correct provider."""
        try:
            if self.use_mistral:
                return self._call_mistral(prompt, system_prompt, max_tokens)
            elif self.use_huggingface:
                return self._call_huggingface(prompt, system_prompt, max_tokens)
            else:
                return self._call_gemini(prompt, system_prompt, max_tokens)
        except Exception as e:
            logger.error(f"[{self.name}] LLM call failed: {e}")
            return "{}"

    def _call_mistral(self, prompt: str, system_prompt: str = None, max_tokens: int = 4000) -> str:
        """Call Mistral AI API."""
        if not self.api_key:
            logger.warning(f"[{self.name}] No Mistral API key provided")
            return "{}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": max_tokens,
        }

        try:
            response = requests.post(self.mistral_api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            logger.error(f"[{self.name}] Mistral API timeout")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"[{self.name}] Mistral API HTTP error: {e.response.status_code}")
            raise
        except Exception as e:
            logger.error(f"[{self.name}] Mistral API error: {e}")
            raise

    def _call_huggingface(self, prompt: str, system_prompt: str = None, max_tokens: int = 4000) -> str:
        """Call HuggingFace Inference API."""
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        full_prompt = "<s>[INST] "
        if system_prompt:
            full_prompt += f"<<SYS>>\n{system_prompt}\n<</SYS>>\n\n"
        full_prompt += f"{prompt} [/INST]"

        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.5,
                "return_full_text": False,
            },
        }

        try:
            response = requests.post(self.hf_api_url, headers=headers, json=payload, timeout=30)
            result = response.json()

            if isinstance(result, list) and "generated_text" in result[0]:
                return result[0]["generated_text"]
            elif isinstance(result, dict) and "error" in result:
                logger.error(f"[{self.name}] HuggingFace error: {result['error']}")
                return "{}"
            return str(result)

        except Exception as e:
            logger.error(f"[{self.name}] HuggingFace API failed: {e}")
            return "{}"

    def _call_gemini(self, prompt: str, system_prompt: str = None, max_tokens: int = 4000) -> str:
        """Call Gemini API."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\nUSER PROMPT:\n{prompt}"

        data = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": max_tokens},
        }

        try:
            response = requests.post(
                url, json=data, headers={"Content-Type": "application/json"}, timeout=30
            )
            if response.status_code != 200:
                logger.error(f"[{self.name}] Gemini API error: {response.status_code}")
                return "{}"

            result = response.json()
            if "candidates" in result and result["candidates"]:
                return result["candidates"][0]["content"]["parts"][0]["text"]
            return "{}"
        except Exception as e:
            logger.error(f"[{self.name}] Gemini call failed: {e}")
            return "{}"

    def _parse_json_response(self, text: str) -> Dict:
        """Extract JSON from LLM response."""
        if not text:
            return {}

        # Clean markdown code blocks
        text = re.sub(r"```json\s*", "", text)
        text = re.sub(r"```\s*", "", text)
        text = text.strip()

        # Try to find JSON object
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1:
            json_str = text[start : end + 1]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            logger.warning(f"[{self.name}] Failed to parse JSON response")
            return {}
