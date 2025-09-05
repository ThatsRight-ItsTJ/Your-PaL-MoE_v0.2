"""
CLI configuration and command-line argument parsing
Handles configuration from files, environment variables, and command-line arguments
"""

import asyncio
import json
import sys
from typing import Optional, Dict, Any, AsyncGenerator
from contextual import Context as BaseContext

from .config import Config, init_optimized_config, get_optimized_api_key, get_optimized_provider
from .provider_factory import create_provider


class Context:
    """Execution context for CLI operations"""
    
    def __init__(self, config: Config):
        self.config = config
    
    async def create_provider(self):
        """Create an LLM provider based on configuration"""
        provider_name = self.config.provider
        
        api_key = await get_optimized_api_key(provider_name)
        _, model_name = await get_optimized_provider()
        
        return await create_provider(provider_name, api_key, model_name)


async def stream_output(stream: AsyncGenerator[str, None], output_file=None) -> None:
    """Handle streaming output"""
    output_file = output_file or sys.stdout
    
    async for chunk in stream:
        output_file.write(chunk)
        output_file.flush()


def format_output(output: str, format_type: str = "text") -> str:
    """Format output based on configuration"""
    if format_type == "json":
        # For JSON format, ensure it's valid JSON
        output = output.strip()
        if not (output.startswith("{") or output.startswith("[")):
            # Wrap in a simple JSON object if it's not already JSON
            return json.dumps({"output": output})
        return output
    return output


async def run_cli_command(prompt: str, config_file: Optional[str] = None) -> str:
    """Run a CLI command with the given prompt"""
    # Initialize configuration
    await init_optimized_config(config_file)
    
    # Create context and provider
    context = Context(Config.get_instance())
    provider = await context.create_provider()
    
    # Generate response
    response = await provider.generate(prompt)
    
    # Format and return output
    return format_output(response, context.config.output)