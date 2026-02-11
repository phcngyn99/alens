"""
AI adapter for communicating with AI providers.
Supports OpenAI, Anthropic, Azure OpenAI, and Azure Anthropic APIs.
"""

from dataclasses import dataclass
from typing import Literal, Optional

from app.config import get_settings
from app.core.ai.prompt_builder import PromptBuilder, PromptPayload

settings = get_settings()

# Supported provider types
ProviderType = Literal["openai", "anthropic", "azure_openai", "azure_anthropic"]


@dataclass
class AIResponse:
    """Response from AI provider."""

    content: str
    provider: str
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class AIAdapter:
    """
    Adapter for AI providers (OpenAI, Anthropic, Azure OpenAI, Azure Anthropic).

    Handles API communication and response parsing.
    Credentials are stored securely and retrieved at runtime.

    For Azure providers, additional parameters are required:
    - endpoint_url: Azure endpoint URL (e.g., https://your-resource.openai.azure.com)
    - deployment_name: Azure deployment name
    - api_version: API version string
    """

    def __init__(
        self,
        provider: ProviderType,
        api_key: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
        # Azure-specific parameters
        endpoint_url: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: Optional[str] = None,
    ):
        self.provider = provider
        self.api_key = api_key
        self.model = model or self._get_default_model()
        self.max_tokens = max_tokens
        self.temperature = temperature
        # Azure-specific
        self.endpoint_url = endpoint_url
        self.deployment_name = deployment_name or self.model
        self.api_version = api_version

    def _get_default_model(self) -> str:
        """Get default model for provider."""
        if self.provider == "openai":
            return "gpt-4-turbo-preview"
        elif self.provider == "anthropic":
            return "claude-3-opus-20240229"
        elif self.provider == "azure_openai":
            return "gpt-4"  # Deployment name
        elif self.provider == "azure_anthropic":
            return "claude-opus-4-5"  # Azure model name
        return "gpt-4-turbo-preview"

    async def generate_dimensional_model(self, payload: PromptPayload) -> AIResponse:
        """
        Generate a dimensional model proposal from the payload.

        Args:
            payload: Structured prompt payload

        Returns:
            AIResponse with the generated content
        """
        system_prompt = PromptBuilder.get_system_prompt()
        user_prompt = payload.to_prompt()

        if self.provider == "openai":
            return await self._call_openai(system_prompt, user_prompt)
        elif self.provider == "anthropic":
            return await self._call_anthropic(system_prompt, user_prompt)
        elif self.provider == "azure_openai":
            return await self._call_azure_openai(system_prompt, user_prompt)
        elif self.provider == "azure_anthropic":
            return await self._call_azure_anthropic(system_prompt, user_prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def _call_openai(self, system_prompt: str, user_prompt: str) -> AIResponse:
        """Call OpenAI API."""
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)

        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        return AIResponse(
            content=response.choices[0].message.content,
            provider="openai",
            model=self.model,
            prompt_tokens=response.usage.prompt_tokens if response.usage else None,
            completion_tokens=(
                response.usage.completion_tokens if response.usage else None
            ),
            total_tokens=response.usage.total_tokens if response.usage else None,
        )

    async def _call_anthropic(self, system_prompt: str, user_prompt: str) -> AIResponse:
        """Call Anthropic API."""
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.api_key)

        response = await client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )

        # Extract text from response
        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        return AIResponse(
            content=content,
            provider="anthropic",
            model=self.model,
            prompt_tokens=response.usage.input_tokens if response.usage else None,
            completion_tokens=response.usage.output_tokens if response.usage else None,
            total_tokens=(
                (response.usage.input_tokens + response.usage.output_tokens)
                if response.usage
                else None
            ),
        )

    async def _call_azure_openai(
        self, system_prompt: str, user_prompt: str
    ) -> AIResponse:
        """
        Call Azure OpenAI API.

        Uses the Azure OpenAI endpoint with api-key header authentication.
        """
        from openai import AsyncAzureOpenAI

        client = AsyncAzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint_url,
        )

        response = await client.chat.completions.create(
            model=self.deployment_name,  # Azure uses deployment name
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )

        return AIResponse(
            content=response.choices[0].message.content,
            provider="azure_openai",
            model=self.deployment_name,
            prompt_tokens=response.usage.prompt_tokens if response.usage else None,
            completion_tokens=(
                response.usage.completion_tokens if response.usage else None
            ),
            total_tokens=response.usage.total_tokens if response.usage else None,
        )

    async def _call_azure_anthropic(
        self, system_prompt: str, user_prompt: str
    ) -> AIResponse:
        """
        Call Azure Anthropic API.

        Azure Anthropic uses different headers than standard Anthropic:
        - x-api-key: Azure API key
        - anthropic-version: Required version header

        The endpoint URL points to the Azure-hosted Anthropic service.
        """
        import httpx

        # Build the request URL for Azure Anthropic
        # Format: {endpoint_url}/messages
        url = f"{self.endpoint_url.rstrip('/')}/messages"

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version or "2023-06-01",
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt},
            ],
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        # Extract content from response
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        usage = data.get("usage", {})
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")

        return AIResponse(
            content=content,
            provider="azure_anthropic",
            model=self.model,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            total_tokens=(
                (input_tokens + output_tokens)
                if input_tokens and output_tokens
                else None
            ),
        )
