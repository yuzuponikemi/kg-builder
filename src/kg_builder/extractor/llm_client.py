"""LLM client with support for Ollama, OpenAI, Anthropic, and Gemini."""

import json
from typing import Any, Literal

from kg_builder.config import get_settings


class LLMClient:
    """Universal LLM client that supports multiple providers."""

    def __init__(self, provider: str | None = None):
        """Initialize LLM client.

        Args:
            provider: LLM provider to use (ollama, openai, anthropic, gemini).
                     If None, uses value from settings.
        """
        self.settings = get_settings()
        self.provider = provider or self.settings.llm_provider

        # Initialize provider-specific client
        if self.provider == "ollama":
            import ollama

            self.client = ollama.Client(host=self.settings.ollama_base_url)
            self.model = self.settings.ollama_model
        elif self.provider == "openai":
            from openai import OpenAI

            self.client = OpenAI(api_key=self.settings.openai_api_key)
            self.model = self.settings.openai_model
        elif self.provider == "anthropic":
            from anthropic import Anthropic

            self.client = Anthropic(api_key=self.settings.anthropic_api_key)
            self.model = self.settings.anthropic_model
        elif self.provider == "gemini":
            import google.generativeai as genai

            genai.configure(api_key=self.settings.gemini_api_key)
            self.client = genai.GenerativeModel(self.settings.gemini_model)
            self.model = self.settings.gemini_model
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")

    def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: Literal["text", "json"] = "text",
    ) -> str:
        """Generate text completion.

        Args:
            prompt: User prompt
            system: System prompt (optional)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            response_format: Response format (text or json)

        Returns:
            Generated text
        """
        temp = temperature if temperature is not None else self.settings.default_temperature
        max_tok = max_tokens if max_tokens is not None else self.settings.max_tokens

        if self.provider == "ollama":
            return self._generate_ollama(prompt, system, temp, max_tok, response_format)
        elif self.provider == "openai":
            return self._generate_openai(prompt, system, temp, max_tok, response_format)
        elif self.provider == "anthropic":
            return self._generate_anthropic(prompt, system, temp, max_tok, response_format)
        elif self.provider == "gemini":
            return self._generate_gemini(prompt, system, temp, max_tok, response_format)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _generate_ollama(
        self,
        prompt: str,
        system: str | None,
        temperature: float,
        max_tokens: int,
        response_format: str,
    ) -> str:
        """Generate using Ollama."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        options = {
            "temperature": temperature,
            "num_predict": max_tokens,
            "num_ctx": self.settings.ollama_num_ctx,
        }

        if response_format == "json":
            # Add JSON format instruction
            if system:
                messages[0]["content"] += "\n\nYou must respond with valid JSON only."
            else:
                messages.insert(
                    0, {"role": "system", "content": "You must respond with valid JSON only."}
                )
            options["format"] = "json"

        response = self.client.chat(model=self.model, messages=messages, options=options)

        return response["message"]["content"]

    def _generate_openai(
        self,
        prompt: str,
        system: str | None,
        temperature: float,
        max_tokens: int,
        response_format: str,
    ) -> str:
        """Generate using OpenAI."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}

        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    def _generate_anthropic(
        self,
        prompt: str,
        system: str | None,
        temperature: float,
        max_tokens: int,
        response_format: str,
    ) -> str:
        """Generate using Anthropic."""
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if system:
            kwargs["system"] = system

        if response_format == "json":
            # Add JSON instruction to prompt
            kwargs["messages"][0]["content"] += "\n\nRespond with valid JSON only."

        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def _generate_gemini(
        self,
        prompt: str,
        system: str | None,
        temperature: float,
        max_tokens: int,
        response_format: str,
    ) -> str:
        """Generate using Gemini."""
        # Combine system and user prompt for Gemini
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}"

        if response_format == "json":
            full_prompt += "\n\nRespond with valid JSON only."

        # Configure generation
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }

        if response_format == "json":
            generation_config["response_mime_type"] = "application/json"

        response = self.client.generate_content(
            full_prompt,
            generation_config=generation_config
        )

        return response.text

    def extract_json(self, response: str) -> dict[str, Any]:
        """Extract JSON from response, handling markdown code blocks.

        Args:
            response: LLM response that may contain JSON

        Returns:
            Parsed JSON object
        """
        # Remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]  # Remove ```json
        elif response.startswith("```"):
            response = response[3:]  # Remove ```

        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}\nResponse: {response}")


def get_llm_client(provider: str | None = None) -> LLMClient:
    """Get LLM client instance.

    Args:
        provider: LLM provider to use. If None, uses settings default.

    Returns:
        LLM client instance
    """
    return LLMClient(provider=provider)
