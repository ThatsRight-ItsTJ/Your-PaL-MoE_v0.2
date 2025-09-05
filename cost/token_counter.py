"""
Token Counter and Cost Calculator
Enhanced version using existing pricing_data.py with additional features
"""

import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from decimal import Decimal

# Import existing cost calculation functions
from cost.pricing_data import (
    calculate_prompt_cost,
    calculate_completion_cost,
    calculate_all_costs_and_tokens,
    count_message_tokens,
    count_string_tokens
)

@dataclass
class CostBreakdown:
    """Detailed cost breakdown for a request"""
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    provider: str = ""

class TokenCounter:
    """
    Enhanced token counting and cost calculation
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Provider-specific model mappings
        self.provider_model_mapping = {
            'openai': {
                'default': 'gpt-3.5-turbo',
                'models': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo']
            },
            'anthropic': {
                'default': 'claude-3-5-sonnet',
                'models': ['claude-3-5-sonnet', 'claude-3-haiku']
            },
            'cohere': {
                'default': 'command',
                'models': ['command', 'command-light']
            },
            'together': {
                'default': 'meta-llama/Llama-2-7b-chat-hf',
                'models': ['meta-llama/Llama-2-7b-chat-hf', 'mistralai/Mixtral-8x7B-Instruct-v0.1']
            },
            'local_ollama': {
                'default': 'llama2',
                'models': ['llama2', 'codellama', 'mistral']
            }
        }
    
    async def calculate_cost(
        self,
        provider: str,
        messages: Union[List[Dict[str, str]], str],
        completion: str = "",
        model: Optional[str] = None
    ) -> CostBreakdown:
        """
        Calculate comprehensive cost breakdown for a request
        
        Args:
            provider: Provider name (e.g., 'openai', 'anthropic')
            messages: Input messages or string
            completion: Completion text (if available)
            model: Specific model name (optional)
            
        Returns:
            CostBreakdown with detailed cost information
        """
        
        # Determine the model to use
        effective_model = self._get_effective_model(provider, model)
        
        try:
            if completion:
                # Calculate both prompt and completion costs
                cost_data = calculate_all_costs_and_tokens(messages, completion, effective_model)
                
                return CostBreakdown(
                    model=effective_model,
                    input_tokens=cost_data['prompt_tokens'],
                    output_tokens=cost_data['completion_tokens'],
                    input_cost=float(cost_data['prompt_cost']),
                    output_cost=float(cost_data['completion_cost']),
                    total_cost=float(cost_data['prompt_cost'] + cost_data['completion_cost']),
                    provider=provider
                )
            else:
                # Calculate only prompt cost
                prompt_cost = calculate_prompt_cost(messages, effective_model)
                
                if isinstance(messages, str):
                    input_tokens = count_string_tokens(messages, effective_model)
                else:
                    input_tokens = count_message_tokens(messages, effective_model)
                
                return CostBreakdown(
                    model=effective_model,
                    input_tokens=input_tokens,
                    output_tokens=0,
                    input_cost=float(prompt_cost),
                    output_cost=0.0,
                    total_cost=float(prompt_cost),
                    provider=provider
                )
                
        except Exception as e:
            self.logger.error(f"Cost calculation failed for {provider}/{effective_model}: {e}")
            
            # Return fallback cost breakdown
            return self._get_fallback_cost_breakdown(provider, messages, completion, effective_model)
    
    def _get_effective_model(self, provider: str, model: Optional[str] = None) -> str:
        """Determine the effective model name for cost calculation"""
        
        provider_key = provider.lower().replace(' ', '_').replace('-', '_')
        
        if model:
            # Use specified model if valid for provider
            if provider_key in self.provider_model_mapping:
                if model in self.provider_model_mapping[provider_key]['models']:
                    return model
            # Otherwise use the model as-is
            return model
        
        # Use default model for provider
        if provider_key in self.provider_model_mapping:
            return self.provider_model_mapping[provider_key]['default']
        
        # Fallback to a common model
        return 'gpt-3.5-turbo'
    
    def _get_fallback_cost_breakdown(
        self,
        provider: str,
        messages: Union[List[Dict[str, str]], str],
        completion: str,
        model: str
    ) -> CostBreakdown:
        """Generate fallback cost breakdown when calculation fails"""
        
        # Estimate token counts
        if isinstance(messages, str):
            input_tokens = len(messages.split()) * 1.3  # Rough estimate
        else:
            total_content = " ".join([msg.get('content', '') for msg in messages])
            input_tokens = len(total_content.split()) * 1.3
        
        output_tokens = len(completion.split()) * 1.3 if completion else 0
        
        # Use fallback pricing (rough estimates)
        fallback_pricing = {
            'openai': 0.002,
            'anthropic': 0.008,
            'cohere': 0.001,
            'together': 0.0002,
            'local_ollama': 0.0
        }
        
        provider_key = provider.lower().replace(' ', '_').replace('-', '_')
        cost_per_1k = fallback_pricing.get(provider_key, 0.002)
        
        input_cost = (input_tokens / 1000) * cost_per_1k
        output_cost = (output_tokens / 1000) * cost_per_1k * 1.5  # Output typically costs more
        
        return CostBreakdown(
            model=model,
            input_tokens=int(input_tokens),
            output_tokens=int(output_tokens),
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost,
            provider=provider
        )
    
    async def estimate_cost(
        self,
        provider: str,
        content_length: int,
        expected_response_length: int = 0,
        model: Optional[str] = None
    ) -> CostBreakdown:
        """
        Estimate cost based on content lengths
        
        Args:
            provider: Provider name
            content_length: Length of input content in characters
            expected_response_length: Expected response length in characters
            model: Specific model name (optional)
            
        Returns:
            Estimated cost breakdown
        """
        
        # Convert character count to rough token estimate
        input_tokens = int(content_length / 4)  # Rough estimate: 4 chars per token
        output_tokens = int(expected_response_length / 4)
        
        effective_model = self._get_effective_model(provider, model)
        
        # Create dummy content for cost calculation
        dummy_messages = [{"role": "user", "content": "x" * content_length}]
        dummy_completion = "x" * expected_response_length
        
        return await self.calculate_cost(provider, dummy_messages, dummy_completion, effective_model)
    
    def get_supported_models(self, provider: str) -> List[str]:
        """Get list of supported models for a provider"""
        
        provider_key = provider.lower().replace(' ', '_').replace('-', '_')
        
        if provider_key in self.provider_model_mapping:
            return self.provider_model_mapping[provider_key]['models']
        
        return []
    
    def get_default_model(self, provider: str) -> str:
        """Get default model for a provider"""
        
        provider_key = provider.lower().replace(' ', '_').replace('-', '_')
        
        if provider_key in self.provider_model_mapping:
            return self.provider_model_mapping[provider_key]['default']
        
        return 'gpt-3.5-turbo'