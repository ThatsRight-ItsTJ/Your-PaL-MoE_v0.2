"""
Provider factory for creating LLM providers
Converts the Go provider creation logic to Python
"""

import os
from typing import Optional, Any
from .config import get_vertexai_config


class MockProvider:
    """Mock provider for testing"""
    
    def __init__(self):
        self.name = "mock"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate a mock response"""
        return f"Mock response to: {prompt[:50]}..."
    
    async def stream_generate(self, prompt: str, **kwargs):
        """Generate a streaming mock response"""
        response = f"Mock streaming response to: {prompt[:50]}..."
        for word in response.split():
            yield word + " "


class OpenAIProvider:
    """OpenAI provider wrapper"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.name = "openai"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenAI API"""
        # This would integrate with the existing OpenAI client
        # For now, return a placeholder
        return f"OpenAI {self.model} response to: {prompt[:50]}..."
    
    async def stream_generate(self, prompt: str, **kwargs):
        """Generate streaming response using OpenAI API"""
        response = f"OpenAI {self.model} streaming response to: {prompt[:50]}..."
        for word in response.split():
            yield word + " "


class AnthropicProvider:
    """Anthropic provider wrapper"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.name = "anthropic"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using Anthropic API"""
        return f"Anthropic {self.model} response to: {prompt[:50]}..."
    
    async def stream_generate(self, prompt: str, **kwargs):
        """Generate streaming response using Anthropic API"""
        response = f"Anthropic {self.model} streaming response to: {prompt[:50]}..."
        for word in response.split():
            yield word + " "


class GeminiProvider:
    """Gemini provider wrapper"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.name = "gemini"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using Gemini API"""
        return f"Gemini {self.model} response to: {prompt[:50]}..."
    
    async def stream_generate(self, prompt: str, **kwargs):
        """Generate streaming response using Gemini API"""
        response = f"Gemini {self.model} streaming response to: {prompt[:50]}..."
        for word in response.split():
            yield word + " "


class OllamaProvider:
    """Ollama provider wrapper"""
    
    def __init__(self, model: str, host: str = "http://localhost:11434"):
        self.model = model
        self.host = host
        self.name = "ollama"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using Ollama API"""
        return f"Ollama {self.model} response to: {prompt[:50]}..."
    
    async def stream_generate(self, prompt: str, **kwargs):
        """Generate streaming response using Ollama API"""
        response = f"Ollama {self.model} streaming response to: {prompt[:50]}..."
        for word in response.split():
            yield word + " "


class OpenRouterProvider:
    """OpenRouter provider wrapper"""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.name = "openrouter"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using OpenRouter API"""
        return f"OpenRouter {self.model} response to: {prompt[:50]}..."
    
    async def stream_generate(self, prompt: str, **kwargs):
        """Generate streaming response using OpenRouter API"""
        response = f"OpenRouter {self.model} streaming response to: {prompt[:50]}..."
        for word in response.split():
            yield word + " "


class VertexAIProvider:
    """Vertex AI provider wrapper"""
    
    def __init__(self, project_id: str, location: str, model: str):
        self.project_id = project_id
        self.location = location
        self.model = model
        self.name = "vertexai"
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response using Vertex AI API"""
        return f"VertexAI {self.model} response to: {prompt[:50]}..."
    
    async def stream_generate(self, prompt: str, **kwargs):
        """Generate streaming response using Vertex AI API"""
        response = f"VertexAI {self.model} streaming response to: {prompt[:50]}..."
        for word in response.split():
            yield word + " "


async def create_provider(provider_name: str, api_key: Optional[str], model_name: str) -> Any:
    """Create an LLM provider based on configuration"""
    
    if provider_name == "openai":
        return OpenAIProvider(api_key, model_name)
    
    elif provider_name == "anthropic":
        return AnthropicProvider(api_key, model_name)
    
    elif provider_name == "gemini":
        return GeminiProvider(api_key, model_name)
    
    elif provider_name == "ollama":
        # Ollama doesn't need an API key
        from .config import Config
        config = Config.get_instance()
        host = config.providers["ollama"].host
        return OllamaProvider(model_name, host)
    
    elif provider_name == "openrouter":
        return OpenRouterProvider(api_key, model_name)
    
    elif provider_name == "vertexai":
        # Vertex AI needs project ID and location from environment
        project_id, location = get_vertexai_config()
        if not project_id:
            raise ValueError("VERTEXAI_PROJECT or GOOGLE_CLOUD_PROJECT environment variable required for Vertex AI")
        return VertexAIProvider(project_id, location, model_name)
    
    elif provider_name == "mock":
        return MockProvider()
    
    else:
        raise ValueError(f"Unsupported provider: {provider_name}")