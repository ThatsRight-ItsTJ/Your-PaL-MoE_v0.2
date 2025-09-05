"""
Dynamic Provider Selection
Intelligent provider selection based on task complexity and provider performance
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from config.csv_provider_loader import ProviderConfig, ProviderTier
from ml.task_reasoning_engine import ComplexityScore

@dataclass
class ProviderPerformance:
    """Track provider performance metrics"""
    name: str
    success_rate: float = 1.0
    avg_response_time: float = 1.0
    avg_cost_efficiency: float = 1.0
    last_updated: datetime = field(default_factory=datetime.now)
    request_count: int = 0

class ProviderSelector:
    """
    Intelligent provider selection based on multiple factors
    """
    
    def __init__(self, providers: Dict[str, ProviderConfig]):
        self.providers = providers
        self.performance_metrics: Dict[str, ProviderPerformance] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize performance metrics for all providers
        for provider_name in providers.keys():
            self.performance_metrics[provider_name] = ProviderPerformance(name=provider_name)
    
    async def select_provider(
        self,
        complexity_score: ComplexityScore,
        context: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Optional[ProviderConfig]:
        """
        Select the best provider based on task complexity and constraints
        
        Args:
            complexity_score: Task complexity analysis
            context: Additional context for selection
            constraints: Selection constraints (budget, latency, etc.)
            
        Returns:
            Selected provider configuration or None if no suitable provider
        """
        
        # Filter available providers
        available_providers = self._filter_available_providers(constraints)
        
        if not available_providers:
            self.logger.warning("No available providers found")
            return None
        
        # Calculate scores for each provider
        provider_scores = []
        for provider in available_providers:
            score = await self._calculate_provider_score(
                provider, complexity_score, context, constraints
            )
            provider_scores.append((provider, score))
        
        # Sort by score (highest first)
        provider_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Select the best provider
        selected_provider = provider_scores[0][0]
        
        self.logger.info(f"Selected provider: {selected_provider.name} (score: {provider_scores[0][1]:.3f})")
        
        return selected_provider
    
    def _filter_available_providers(self, constraints: Optional[Dict[str, Any]] = None) -> List[ProviderConfig]:
        """Filter providers based on availability and constraints"""
        available = []
        
        for provider in self.providers.values():
            # Check if provider has API key (unless it's local/unofficial)
            if provider.tier != ProviderTier.UNOFFICIAL and not provider.api_key:
                continue
            
            # Check health score
            if provider.health_score < 0.1:
                continue
            
            # Apply constraints
            if constraints:
                # Budget constraint
                if constraints.get('max_cost_per_1k') and provider.cost_per_1k_tokens > constraints['max_cost_per_1k']:
                    continue
                
                # Latency constraint
                if constraints.get('max_timeout') and provider.timeout > constraints['max_timeout']:
                    continue
                
                # Tier constraint
                if constraints.get('allowed_tiers'):
                    allowed_tiers = [ProviderTier(tier) for tier in constraints['allowed_tiers']]
                    if provider.tier not in allowed_tiers:
                        continue
                
                # Model constraint
                if constraints.get('required_model'):
                    if constraints['required_model'] not in provider.models:
                        continue
            
            available.append(provider)
        
        return available
    
    async def _calculate_provider_score(
        self,
        provider: ProviderConfig,
        complexity_score: ComplexityScore,
        context: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate a comprehensive score for provider selection"""
        
        # Base score components
        capability_score = self._calculate_capability_score(provider, complexity_score)
        performance_score = self._calculate_performance_score(provider)
        cost_score = self._calculate_cost_score(provider, constraints)
        reliability_score = self._calculate_reliability_score(provider)
        
        # Weights for different factors
        weights = {
            'capability': 0.35,
            'performance': 0.25,
            'cost': 0.25,
            'reliability': 0.15
        }
        
        # Apply context-based weight adjustments
        if context:
            if context.get('priority') == 'cost':
                weights['cost'] = 0.4
                weights['capability'] = 0.25
            elif context.get('priority') == 'performance':
                weights['performance'] = 0.4
                weights['cost'] = 0.15
            elif context.get('priority') == 'quality':
                weights['capability'] = 0.5
                weights['cost'] = 0.15
        
        # Calculate weighted score
        total_score = (
            capability_score * weights['capability'] +
            performance_score * weights['performance'] +
            cost_score * weights['cost'] +
            reliability_score * weights['reliability']
        )
        
        return total_score
    
    def _calculate_capability_score(self, provider: ProviderConfig, complexity_score: ComplexityScore) -> float:
        """Calculate how well the provider matches the task complexity"""
        
        # Tier-based capability mapping
        tier_capabilities = {
            ProviderTier.OFFICIAL: {
                'reasoning': 0.9,
                'knowledge': 0.95,
                'computation': 0.85,
                'coordination': 0.8
            },
            ProviderTier.COMMUNITY: {
                'reasoning': 0.7,
                'knowledge': 0.75,
                'computation': 0.8,
                'coordination': 0.6
            },
            ProviderTier.UNOFFICIAL: {
                'reasoning': 0.5,
                'knowledge': 0.6,
                'computation': 0.7,
                'coordination': 0.4
            }
        }
        
        capabilities = tier_capabilities[provider.tier]
        
        # Calculate match score for each dimension
        reasoning_match = min(1.0, capabilities['reasoning'] / max(0.1, complexity_score.reasoning))
        knowledge_match = min(1.0, capabilities['knowledge'] / max(0.1, complexity_score.knowledge))
        computation_match = min(1.0, capabilities['computation'] / max(0.1, complexity_score.computation))
        coordination_match = min(1.0, capabilities['coordination'] / max(0.1, complexity_score.coordination))
        
        # Weighted average
        capability_score = (
            reasoning_match * 0.3 +
            knowledge_match * 0.3 +
            computation_match * 0.25 +
            coordination_match * 0.15
        )
        
        return capability_score
    
    def _calculate_performance_score(self, provider: ProviderConfig) -> float:
        """Calculate performance score based on historical metrics"""
        
        if provider.name not in self.performance_metrics:
            return 0.5  # Default score for new providers
        
        metrics = self.performance_metrics[provider.name]
        
        # Normalize response time (lower is better)
        response_time_score = max(0.0, 1.0 - (metrics.avg_response_time / 10.0))
        
        # Success rate score
        success_rate_score = metrics.success_rate
        
        # Cost efficiency score
        cost_efficiency_score = metrics.avg_cost_efficiency
        
        # Combine scores
        performance_score = (
            response_time_score * 0.4 +
            success_rate_score * 0.4 +
            cost_efficiency_score * 0.2
        )
        
        return performance_score
    
    def _calculate_cost_score(self, provider: ProviderConfig, constraints: Optional[Dict[str, Any]] = None) -> float:
        """Calculate cost efficiency score (lower cost = higher score)"""
        
        # Base cost score (inverse relationship)
        max_cost = 0.01  # Assume max reasonable cost per 1k tokens
        cost_score = max(0.0, 1.0 - (provider.cost_per_1k_tokens / max_cost))
        
        # Apply budget constraints
        if constraints and constraints.get('budget_weight'):
            cost_score *= constraints['budget_weight']
        
        return cost_score
    
    def _calculate_reliability_score(self, provider: ProviderConfig) -> float:
        """Calculate reliability score based on provider characteristics"""
        
        # Base reliability by tier
        tier_reliability = {
            ProviderTier.OFFICIAL: 0.95,
            ProviderTier.COMMUNITY: 0.8,
            ProviderTier.UNOFFICIAL: 0.6
        }
        
        base_score = tier_reliability[provider.tier]
        
        # Adjust by health score
        reliability_score = base_score * provider.health_score
        
        # Adjust by rate limits (higher limits = more reliable)
        rate_limit_factor = min(1.0, provider.max_requests_per_minute / 1000.0)
        reliability_score *= (0.8 + 0.2 * rate_limit_factor)
        
        return reliability_score
    
    def update_provider_metrics(self, provider_name: str, response_time: float, success: bool, cost_efficiency: float = 1.0):
        """Update provider performance metrics"""
        
        if provider_name not in self.performance_metrics:
            self.performance_metrics[provider_name] = ProviderPerformance(name=provider_name)
        
        metrics = self.performance_metrics[provider_name]
        
        # Update with exponential moving average
        alpha = 0.1  # Learning rate
        
        metrics.avg_response_time = (1 - alpha) * metrics.avg_response_time + alpha * response_time
        metrics.avg_cost_efficiency = (1 - alpha) * metrics.avg_cost_efficiency + alpha * cost_efficiency
        
        # Update success rate
        metrics.request_count += 1
        if success:
            metrics.success_rate = (1 - alpha) * metrics.success_rate + alpha * 1.0
        else:
            metrics.success_rate = (1 - alpha) * metrics.success_rate + alpha * 0.0
        
        metrics.last_updated = datetime.now()
        
        self.logger.debug(f"Updated metrics for {provider_name}: success_rate={metrics.success_rate:.3f}, response_time={metrics.avg_response_time:.3f}")
    
    def get_provider_rankings(self, complexity_score: ComplexityScore) -> List[Tuple[str, float]]:
        """Get current provider rankings for given complexity"""
        
        rankings = []
        for provider in self.providers.values():
            score = asyncio.run(self._calculate_provider_score(provider, complexity_score))
            rankings.append((provider.name, score))
        
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings