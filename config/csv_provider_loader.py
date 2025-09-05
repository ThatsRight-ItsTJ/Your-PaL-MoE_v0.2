"""
CSV Provider Configuration Loader
Custom implementation for loading AI provider configurations from CSV
"""

import csv
import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class ProviderTier(Enum):
    """Provider tier classification"""
    OFFICIAL = "official"
    COMMUNITY = "community"
    UNOFFICIAL = "unofficial"

@dataclass
class ProviderConfig:
    """Configuration for an AI provider"""
    name: str
    tier: ProviderTier
    base_url: str
    api_key: str
    models: List[str]
    timeout: int = 30
    max_requests_per_minute: int = 60
    cost_per_1k_tokens: float = 0.002
    priority: int = 1
    health_score: float = 1.0
    other: str = ""

class CSVProviderLoader:
    """
    Loads provider configurations from CSV file
    """
    
    def __init__(self, csv_file_path: str):
        self.csv_file_path = csv_file_path
        self.providers: Dict[str, ProviderConfig] = {}
        self.logger = logging.getLogger(__name__)
    
    def load_providers(self) -> Dict[str, ProviderConfig]:
        """Load providers from CSV file"""
        if not os.path.exists(self.csv_file_path):
            raise FileNotFoundError(f"Provider CSV file not found: {self.csv_file_path}")
        
        try:
            with open(self.csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                for row in reader:
                    provider = self._parse_provider_row(row)
                    if provider:
                        self.providers[provider.name.lower()] = provider
            
            self.logger.info(f"Loaded {len(self.providers)} providers from {self.csv_file_path}")
            return self.providers
            
        except Exception as e:
            self.logger.error(f"Error loading providers from CSV: {e}")
            raise
    
    def _parse_provider_row(self, row: Dict[str, str]) -> Optional[ProviderConfig]:
        """Parse a single CSV row into ProviderConfig"""
        try:
            # Required fields
            name = row.get('Name', '').strip()
            tier_str = row.get('Tier', '').strip().lower()
            base_url = row.get('Base_URL', '').strip()
            api_key = row.get('APIKey', '').strip()
            models_str = row.get('Model(s)', '').strip()
            
            if not all([name, tier_str, base_url, models_str]):
                self.logger.warning(f"Skipping incomplete provider row: {row}")
                return None
            
            # Parse tier
            try:
                tier = ProviderTier(tier_str)
            except ValueError:
                self.logger.warning(f"Invalid tier '{tier_str}' for provider {name}, defaulting to unofficial")
                tier = ProviderTier.UNOFFICIAL
            
            # Parse models (pipe-separated)
            models = [model.strip() for model in models_str.split('|') if model.strip()]
            
            # Optional fields with defaults
            timeout = int(row.get('Timeout', 30))
            max_requests = int(row.get('Max_Requests_Per_Minute', 60))
            cost_per_1k = float(row.get('Cost_Per_1K_Tokens', 0.002))
            priority = int(row.get('Priority', 1))
            other = row.get('Other', '').strip()
            
            # Handle special API key values
            if api_key.lower() in ['none', 'null', '']:
                api_key = ''
            elif api_key.startswith('${') and api_key.endswith('}'):
                # Environment variable reference
                env_var = api_key[2:-1]
                api_key = os.getenv(env_var, '')
                if not api_key:
                    self.logger.warning(f"Environment variable {env_var} not found for provider {name}")
            
            return ProviderConfig(
                name=name,
                tier=tier,
                base_url=base_url,
                api_key=api_key,
                models=models,
                timeout=timeout,
                max_requests_per_minute=max_requests,
                cost_per_1k_tokens=cost_per_1k,
                priority=priority,
                other=other
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing provider row {row}: {e}")
            return None
    
    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        """Get a specific provider by name"""
        return self.providers.get(name.lower())
    
    def get_providers_by_tier(self, tier: ProviderTier) -> List[ProviderConfig]:
        """Get all providers of a specific tier"""
        return [provider for provider in self.providers.values() if provider.tier == tier]
    
    def get_available_providers(self) -> List[ProviderConfig]:
        """Get providers that have API keys configured"""
        return [provider for provider in self.providers.values() if provider.api_key]
    
    def update_provider_health(self, name: str, health_score: float):
        """Update the health score of a provider"""
        provider = self.get_provider(name)
        if provider:
            provider.health_score = max(0.0, min(1.0, health_score))
    
    def get_providers_by_priority(self) -> List[ProviderConfig]:
        """Get providers sorted by priority (lower number = higher priority)"""
        return sorted(self.providers.values(), key=lambda p: p.priority)
    
    def reload_providers(self) -> Dict[str, ProviderConfig]:
        """Reload providers from CSV file"""
        self.providers.clear()
        return self.load_providers()
    
    def validate_providers(self) -> Dict[str, List[str]]:
        """Validate provider configurations and return issues"""
        issues = {}
        
        for name, provider in self.providers.items():
            provider_issues = []
            
            # Check required fields
            if not provider.base_url:
                provider_issues.append("Missing base URL")
            elif not provider.base_url.startswith(('http://', 'https://')):
                provider_issues.append("Invalid base URL format")
            
            if not provider.models:
                provider_issues.append("No models specified")
            
            if provider.tier == ProviderTier.OFFICIAL and not provider.api_key:
                provider_issues.append("Official provider missing API key")
            
            # Check numeric values
            if provider.timeout <= 0:
                provider_issues.append("Invalid timeout value")
            
            if provider.max_requests_per_minute <= 0:
                provider_issues.append("Invalid max requests per minute")
            
            if provider.cost_per_1k_tokens < 0:
                provider_issues.append("Invalid cost per 1k tokens")
            
            if provider_issues:
                issues[name] = provider_issues
        
        return issues
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics about loaded providers"""
        if not self.providers:
            return {"total": 0}
        
        tier_counts = {}
        for tier in ProviderTier:
            tier_counts[tier.value] = len(self.get_providers_by_tier(tier))
        
        return {
            "total": len(self.providers),
            "by_tier": tier_counts,
            "with_api_keys": len(self.get_available_providers()),
            "average_cost_per_1k": sum(p.cost_per_1k_tokens for p in self.providers.values()) / len(self.providers)
        }