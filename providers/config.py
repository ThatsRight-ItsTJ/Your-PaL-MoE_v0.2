"""
Configuration management for the AI API Liaison system
Handles loading settings from YAML files and environment variables
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, field


@dataclass
class ProviderConfig:
    """Configuration for a specific provider"""
    api_key: str = ""
    default_model: str = ""
    host: str = ""  # For Ollama
    project_id: str = ""  # For Vertex AI
    location: str = ""  # For Vertex AI


@dataclass
class Config:
    """Application configuration"""
    provider: str = "openai"
    model: str = ""
    verbose: bool = False
    output: str = "text"
    
    providers: Dict[str, ProviderConfig] = field(default_factory=lambda: {
        "openai": ProviderConfig(default_model="gpt-4o"),
        "anthropic": ProviderConfig(default_model="claude-3-5-sonnet-latest"),
        "gemini": ProviderConfig(default_model="gemini-2.0-flash-lite"),
        "ollama": ProviderConfig(default_model="llama3.2:3b", host="http://localhost:11434"),
        "openrouter": ProviderConfig(default_model="huggingface/zephyr-7b-beta:free"),
        "vertexai": ProviderConfig(default_model="gemini-1.5-flash", location="us-central1"),
    })
    
    _instance: Optional['Config'] = None
    
    @classmethod
    def get_instance(cls) -> 'Config':
        """Get the global config instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def set_instance(cls, config: 'Config'):
        """Set the global config instance"""
        cls._instance = config


async def init_optimized_config(config_file: Optional[str] = None) -> Config:
    """Load configuration from file and environment"""
    config = Config()
    
    # Load from config file
    if config_file and os.path.exists(config_file):
        await load_yaml_file(config, config_file)
        print(f"Using config file: {config_file}")
    else:
        # Try standard locations
        home = Path.home()
        config_paths = [
            home / ".ai-api-liaison.yaml",
            Path(".ai-api-liaison.yaml"),
            home / ".config" / "ai-api-liaison" / "config.yaml",
        ]
        
        for path in config_paths:
            if path.exists():
                await load_yaml_file(config, str(path))
                print(f"Using config file: {path}")
                break
    
    # Override with environment variables
    load_env_vars(config)
    
    # Set as global instance
    Config.set_instance(config)
    return config


async def load_yaml_file(config: Config, path: str) -> None:
    """Load configuration from a YAML file"""
    try:
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            
        if data:
            # Update config with YAML data
            if 'provider' in data:
                config.provider = data['provider']
            if 'model' in data:
                config.model = data['model']
            if 'verbose' in data:
                config.verbose = data['verbose']
            if 'output' in data:
                config.output = data['output']
            
            # Load provider configurations
            if 'providers' in data:
                for provider_name, provider_data in data['providers'].items():
                    if provider_name in config.providers:
                        provider_config = config.providers[provider_name]
                        if 'api_key' in provider_data:
                            provider_config.api_key = provider_data['api_key']
                        if 'default_model' in provider_data:
                            provider_config.default_model = provider_data['default_model']
                        if 'host' in provider_data:
                            provider_config.host = provider_data['host']
                        if 'project_id' in provider_data:
                            provider_config.project_id = provider_data['project_id']
                        if 'location' in provider_data:
                            provider_config.location = provider_data['location']
                            
    except Exception as e:
        print(f"Warning: Could not load config file {path}: {e}")


def load_env_vars(config: Config) -> None:
    """Load configuration from environment variables"""
    # Standard format: AI_API_LIAISON_PROVIDER, AI_API_LIAISON_MODEL, etc.
    if val := os.getenv("AI_API_LIAISON_PROVIDER"):
        config.provider = val
    if val := os.getenv("AI_API_LIAISON_MODEL"):
        config.model = val
    if val := os.getenv("AI_API_LIAISON_VERBOSE"):
        config.verbose = val.lower() == "true"
    if val := os.getenv("AI_API_LIAISON_OUTPUT"):
        config.output = val
    
    # Provider-specific settings
    load_provider_env_vars(config, "openai", "OPENAI")
    load_provider_env_vars(config, "anthropic", "ANTHROPIC")
    load_provider_env_vars(config, "gemini", "GEMINI")
    load_provider_env_vars(config, "ollama", "OLLAMA")
    load_provider_env_vars(config, "openrouter", "OPENROUTER")
    load_provider_env_vars(config, "vertexai", "VERTEXAI")
    
    # Standard API key environment variables (backward compatibility)
    standard_env_vars = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }
    
    for provider, env_var in standard_env_vars.items():
        if val := os.getenv(env_var):
            if not config.providers[provider].api_key:
                config.providers[provider].api_key = val
    
    # Special handling for Ollama
    if val := os.getenv("OLLAMA_HOST"):
        if not config.providers["ollama"].host:
            config.providers["ollama"].host = val
    if val := os.getenv("OLLAMA_MODEL"):
        if not config.providers["ollama"].default_model:
            config.providers["ollama"].default_model = val
    
    # Special handling for Vertex AI
    if val := os.getenv("VERTEXAI_PROJECT"):
        if not config.providers["vertexai"].project_id:
            config.providers["vertexai"].project_id = val
    if val := os.getenv("GOOGLE_CLOUD_PROJECT"):
        if not config.providers["vertexai"].project_id:
            config.providers["vertexai"].project_id = val
    if val := os.getenv("VERTEXAI_LOCATION"):
        if not config.providers["vertexai"].location:
            config.providers["vertexai"].location = val


def load_provider_env_vars(config: Config, provider: str, env_prefix: str) -> None:
    """Load provider-specific environment variables"""
    provider_config = config.providers.get(provider)
    if not provider_config:
        return
    
    # API Key
    env_var = f"AI_API_LIAISON_PROVIDERS_{env_prefix}_API_KEY"
    if val := os.getenv(env_var):
        provider_config.api_key = val
    
    # Default Model
    env_var = f"AI_API_LIAISON_PROVIDERS_{env_prefix}_DEFAULT_MODEL"
    if val := os.getenv(env_var):
        provider_config.default_model = val
    
    # Ollama Host
    if provider == "ollama":
        env_var = f"AI_API_LIAISON_PROVIDERS_{env_prefix}_HOST"
        if val := os.getenv(env_var):
            provider_config.host = val
    
    # Vertex AI Project ID and Location
    if provider == "vertexai":
        env_var = f"AI_API_LIAISON_PROVIDERS_{env_prefix}_PROJECT_ID"
        if val := os.getenv(env_var):
            provider_config.project_id = val
        env_var = f"AI_API_LIAISON_PROVIDERS_{env_prefix}_LOCATION"
        if val := os.getenv(env_var):
            provider_config.location = val


async def get_optimized_api_key(provider: str) -> Optional[str]:
    """Retrieve the API key for a provider"""
    config = Config.get_instance()
    provider_config = config.providers.get(provider)
    
    if not provider_config:
        raise ValueError(f"Unknown provider: {provider}")
    
    if provider in ["ollama", "vertexai", "mock"]:
        # These providers don't require API keys
        return None
    
    key = provider_config.api_key
    if not key:
        # Try environment variable as fallback
        env_var = f"{provider.upper()}_API_KEY"
        key = os.getenv(env_var)
        if not key:
            raise ValueError(f"No API key configured for provider {provider}. "
                           f"Set it in config file or {env_var} environment variable")
    
    return key


async def get_optimized_provider() -> Tuple[str, str]:
    """Return the configured provider and model"""
    config = Config.get_instance()
    provider = config.provider
    model = config.model
    
    # If no model specified, get the default for the provider
    if not model:
        provider_config = config.providers.get(provider)
        if provider_config:
            model = provider_config.default_model
        
        if not model:
            raise ValueError(f"No model specified and no default model configured for provider {provider}")
    
    return provider, model


def get_vertexai_config() -> Tuple[str, str]:
    """Return the configured Vertex AI project ID and location"""
    config = Config.get_instance()
    provider_config = config.providers["vertexai"]
    
    project_id = provider_config.project_id
    location = provider_config.location or "us-central1"
    
    return project_id, location