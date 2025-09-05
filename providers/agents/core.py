"""
Core agent functionality
Python conversion of the Go agent core system
"""

import asyncio
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field

from ..provider_factory import create_provider
from ..config import Config, init_optimized_config


@dataclass
class State:
    """Agent state management"""
    data: Dict[str, Any] = field(default_factory=dict)
    
    def set(self, key: str, value: Any) -> None:
        """Set a value in the state"""
        self.data[key] = value
    
    def get(self, key: str) -> tuple[Any, bool]:
        """Get a value from the state"""
        if key in self.data:
            return self.data[key], True
        return None, False
    
    def has(self, key: str) -> bool:
        """Check if key exists in state"""
        return key in self.data
    
    def delete(self, key: str) -> bool:
        """Delete a key from state"""
        if key in self.data:
            del self.data[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all state data"""
        self.data.clear()


class Agent:
    """AI Agent with LLM provider integration"""
    
    def __init__(self, name: str, provider: Any):
        self._name = name
        self._provider = provider
    
    def name(self) -> str:
        """Get agent name"""
        return self._name
    
    async def run(self, state: State) -> State:
        """Run the agent with given state"""
        # Get user input from state
        user_input, exists = state.get("user_input")
        if not exists:
            raise ValueError("No user_input found in state")
        
        # Generate response using provider
        response = await self._provider.generate(str(user_input))
        
        # Set output in result state
        result_state = State()
        result_state.data = state.data.copy()  # Copy input state
        result_state.set("output", response)
        
        return result_state
    
    async def stream_run(self, state: State):
        """Run the agent with streaming output"""
        user_input, exists = state.get("user_input")
        if not exists:
            raise ValueError("No user_input found in state")
        
        # Stream response using provider
        async for chunk in self._provider.stream_generate(str(user_input)):
            yield chunk


def new_state() -> State:
    """Create a new state instance"""
    return State()


async def new_agent_from_string(name: str, provider_spec: str) -> Agent:
    """
    Create agent with ultra-simple provider specification
    
    Examples:
    - "gpt-4" -> OpenAI GPT-4
    - "claude" -> Anthropic Claude (latest)
    - "gemini" -> Google Gemini
    - "openai/gpt-4o-mini" -> OpenAI GPT-4o-mini
    - "anthropic/claude-3-opus-latest" -> Anthropic Claude Opus
    - "mock" -> Mock provider for testing
    """
    
    # Initialize config if not already done
    if Config._instance is None:
        await init_optimized_config()
    
    # Parse provider specification
    provider_name, model_name = _parse_provider_spec(provider_spec)
    
    # Get API key for provider
    from ..config import get_optimized_api_key
    try:
        api_key = await get_optimized_api_key(provider_name)
    except ValueError as e:
        raise ValueError(f"Failed to create {provider_name} agent: {e}")
    
    # Create provider
    provider = await create_provider(provider_name, api_key, model_name)
    
    # Create and return agent
    return Agent(name, provider)


def _parse_provider_spec(spec: str) -> tuple[str, str]:
    """Parse provider specification into provider and model"""
    
    # Handle simple aliases
    aliases = {
        "gpt-4": ("openai", "gpt-4"),
        "gpt-4o": ("openai", "gpt-4o"),
        "gpt-4o-mini": ("openai", "gpt-4o-mini"),
        "claude": ("anthropic", "claude-3-5-sonnet-latest"),
        "claude-3": ("anthropic", "claude-3-5-sonnet-latest"),
        "gemini": ("gemini", "gemini-2.0-flash-lite"),
        "gemini-2.0-flash": ("gemini", "gemini-2.0-flash"),
        "mock": ("mock", "mock-model"),
    }
    
    if spec in aliases:
        return aliases[spec]
    
    # Handle provider/model format
    if "/" in spec:
        provider, model = spec.split("/", 1)
        return provider, model
    
    # Handle model name inference
    model_to_provider = {
        "gpt-3.5-turbo": "openai",
        "gpt-4": "openai", 
        "gpt-4o": "openai",
        "gpt-4o-mini": "openai",
        "claude-3-opus-latest": "anthropic",
        "claude-3-5-sonnet-latest": "anthropic",
        "claude-3-haiku-latest": "anthropic",
        "gemini-1.5-pro": "gemini",
        "gemini-1.5-flash": "gemini",
        "gemini-2.0-flash": "gemini",
        "gemini-2.0-flash-lite": "gemini",
    }
    
    if spec in model_to_provider:
        return model_to_provider[spec], spec
    
    # Default to treating as provider name with default model
    config = Config.get_instance()
    if spec in config.providers:
        default_model = config.providers[spec].default_model
        return spec, default_model
    
    raise ValueError(f"Unable to parse provider specification: {spec}")


# Convenience functions matching Go API
NewState = new_state
NewAgentFromString = new_agent_from_string