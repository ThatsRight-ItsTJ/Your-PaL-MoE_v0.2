"""
Constants for cost calculation
Token costs for different AI models and providers
"""

# Token costs per model (cost per token)
TOKEN_COSTS = {
    # OpenAI models
    "gpt-3.5-turbo": {
        "input_cost_per_token": 0.000002,  # $0.002 per 1K tokens
        "output_cost_per_token": 0.000002,
        "mode": "chat"
    },
    "gpt-4": {
        "input_cost_per_token": 0.00003,  # $0.03 per 1K tokens
        "output_cost_per_token": 0.00006,  # $0.06 per 1K tokens
        "mode": "chat"
    },
    "gpt-4-turbo": {
        "input_cost_per_token": 0.00001,  # $0.01 per 1K tokens
        "output_cost_per_token": 0.00003,  # $0.03 per 1K tokens
        "mode": "chat"
    },
    
    # Anthropic models
    "claude-3-5-sonnet": {
        "input_cost_per_token": 0.000003,  # $0.003 per 1K tokens
        "output_cost_per_token": 0.000015,  # $0.015 per 1K tokens
        "mode": "chat"
    },
    "claude-3-haiku": {
        "input_cost_per_token": 0.00000025,  # $0.00025 per 1K tokens
        "output_cost_per_token": 0.00000125,  # $0.00125 per 1K tokens
        "mode": "chat"
    },
    
    # Cohere models
    "command": {
        "input_cost_per_token": 0.000001,  # $0.001 per 1K tokens
        "output_cost_per_token": 0.000002,  # $0.002 per 1K tokens
        "mode": "chat"
    },
    "command-light": {
        "input_cost_per_token": 0.0000005,  # $0.0005 per 1K tokens
        "output_cost_per_token": 0.000001,  # $0.001 per 1K tokens
        "mode": "chat"
    },
    
    # Together AI models
    "meta-llama/llama-2-7b-chat-hf": {
        "input_cost_per_token": 0.0000002,  # $0.0002 per 1K tokens
        "output_cost_per_token": 0.0000002,
        "mode": "chat"
    },
    "mistralai/mixtral-8x7b-instruct-v0.1": {
        "input_cost_per_token": 0.0000002,  # $0.0002 per 1K tokens
        "output_cost_per_token": 0.0000002,
        "mode": "chat"
    },
    
    # Local models (free)
    "llama2": {
        "input_cost_per_token": 0.0,
        "output_cost_per_token": 0.0,
        "mode": "chat"
    },
    "codellama": {
        "input_cost_per_token": 0.0,
        "output_cost_per_token": 0.0,
        "mode": "chat"
    },
    "mistral": {
        "input_cost_per_token": 0.0,
        "output_cost_per_token": 0.0,
        "mode": "chat"
    }
}