"""
Metrics Collection and Monitoring
Enhanced version based on Gracy reporting with AI-specific metrics
"""

import time
import asyncio
from typing import Dict, List, Optional, Any, DefaultDict
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta
import logging
import json

@dataclass
class RequestMetric:
    """Individual request metric"""
    timestamp: float
    provider: str
    model: str
    success: bool
    response_time: float
    cost: float
    input_tokens: int
    output_tokens: int
    complexity_level: str
    error_type: Optional[str] = None

@dataclass
class ProviderMetrics:
    """Aggregated metrics for a provider"""
    name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    total_cost: float = 0.0
    total_tokens: int = 0
    last_request_time: Optional[float] = None
    error_counts: Dict[str, int] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        return self.successful_requests / self.total_requests if self.total_requests > 0 else 0.0
    
    @property
    def avg_response_time(self) -> float:
        return self.total_response_time / self.total_requests if self.total_requests > 0 else 0.0
    
    @property
    def avg_cost_per_request(self) -> float:
        return self.total_cost / self.total_requests if self.total_requests > 0 else 0.0

class MetricsCollector:
    """
    Comprehensive metrics collection for AI API Liaison
    """
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.start_time = time.time()
        
        # Storage for metrics
        self.request_metrics: List[RequestMetric] = []
        self.provider_metrics: Dict[str, ProviderMetrics] = {}
        
        # Aggregated statistics
        self.hourly_stats: DefaultDict[str, Dict[str, Any]] = defaultdict(dict)
        self.complexity_stats: Dict[str, int] = {"low": 0, "medium": 0, "high": 0}
        
        self.logger = logging.getLogger(__name__)
        
        # Start cleanup task
        asyncio.create_task(self._periodic_cleanup())
    
    async def record_request(
        self,
        provider_name: str,
        model: str,
        success: bool,
        response_time: float,
        cost: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        complexity_level: str = "medium",
        error_type: Optional[str] = None
    ):
        """Record a single request metric"""
        
        # Create request metric
        metric = RequestMetric(
            timestamp=time.time(),
            provider=provider_name,
            model=model,
            success=success,
            response_time=response_time,
            cost=cost,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            complexity_level=complexity_level,
            error_type=error_type
        )
        
        # Store metric
        self.request_metrics.append(metric)
        
        # Update provider metrics
        await self._update_provider_metrics(metric)
        
        # Update complexity stats
        self.complexity_stats[complexity_level] += 1
        
        # Update hourly stats
        await self._update_hourly_stats(metric)
        
        self.logger.debug(f"Recorded metric for {provider_name}: success={success}, time={response_time:.3f}s")
    
    async def _update_provider_metrics(self, metric: RequestMetric):
        """Update aggregated provider metrics"""
        provider_name = metric.provider
        
        if provider_name not in self.provider_metrics:
            self.provider_metrics[provider_name] = ProviderMetrics(name=provider_name)
        
        pm = self.provider_metrics[provider_name]
        pm.total_requests += 1
        pm.total_response_time += metric.response_time
        pm.total_cost += metric.cost
        pm.total_tokens += metric.input_tokens + metric.output_tokens
        pm.last_request_time = metric.timestamp
        
        if metric.success:
            pm.successful_requests += 1
        else:
            pm.failed_requests += 1
            if metric.error_type:
                pm.error_counts[metric.error_type] = pm.error_counts.get(metric.error_type, 0) + 1
    
    async def _update_hourly_stats(self, metric: RequestMetric):
        """Update hourly aggregated statistics"""
        hour_key = datetime.fromtimestamp(metric.timestamp).strftime("%Y-%m-%d-%H")
        
        if hour_key not in self.hourly_stats:
            self.hourly_stats[hour_key] = {
                "requests": 0,
                "successes": 0,
                "total_cost": 0.0,
                "total_response_time": 0.0,
                "providers": defaultdict(int),
                "complexity": {"low": 0, "medium": 0, "high": 0}
            }
        
        stats = self.hourly_stats[hour_key]
        stats["requests"] += 1
        stats["total_cost"] += metric.cost
        stats["total_response_time"] += metric.response_time
        stats["providers"][metric.provider] += 1
        stats["complexity"][metric.complexity_level] += 1
        
        if metric.success:
            stats["successes"] += 1
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        total_requests = len(self.request_metrics)
        successful_requests = sum(1 for m in self.request_metrics if m.success)
        failed_requests = total_requests - successful_requests
        
        total_cost = sum(m.cost for m in self.request_metrics)
        total_response_time = sum(m.response_time for m in self.request_metrics)
        
        # Calculate cost savings (compared to using only premium providers)
        estimated_premium_cost = total_requests * 0.002  # Assume $0.002 per request for premium
        cost_savings = max(0, estimated_premium_cost - total_cost)
        
        return {
            "uptime": time.time() - self.start_time,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
            "avg_response_time": total_response_time / total_requests if total_requests > 0 else 0,
            "total_cost": total_cost,
            "cost_savings": cost_savings,
            "cost_savings_percentage": (cost_savings / estimated_premium_cost * 100) if estimated_premium_cost > 0 else 0,
            "active_providers": len(self.provider_metrics),
            "complexity_distribution": self.complexity_stats.copy(),
            "requests_per_hour": self._calculate_requests_per_hour(),
        }
    
    async def get_provider_metrics(self, provider_name: str) -> Dict[str, Any]:
        """Get metrics for a specific provider"""
        if provider_name not in self.provider_metrics:
            return {
                "name": provider_name,
                "total_requests": 0,
                "success_rate": 0,
                "avg_response_time": 0,
                "total_cost": 0,
                "last_used": None
            }
        
        pm = self.provider_metrics[provider_name]
        
        return {
            "name": pm.name,
            "total_requests": pm.total_requests,
            "successful_requests": pm.successful_requests,
            "failed_requests": pm.failed_requests,
            "success_rate": pm.success_rate,
            "avg_response_time": pm.avg_response_time,
            "avg_cost_per_request": pm.avg_cost_per_request,
            "total_cost": pm.total_cost,
            "total_tokens": pm.total_tokens,
            "last_used": datetime.fromtimestamp(pm.last_request_time).isoformat() if pm.last_request_time else None,
            "error_breakdown": pm.error_counts
        }
    
    def _calculate_requests_per_hour(self) -> float:
        """Calculate average requests per hour"""
        if not self.request_metrics:
            return 0.0
        
        # Calculate based on last hour of activity
        one_hour_ago = time.time() - 3600
        recent_requests = [m for m in self.request_metrics if m.timestamp > one_hour_ago]
        
        return len(recent_requests)
    
    async def _periodic_cleanup(self):
        """Periodically clean up old metrics"""
        while True:
            await asyncio.sleep(3600)  # Run every hour
            await self._cleanup_old_metrics()
    
    async def _cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff_time = time.time() - (self.retention_hours * 3600)
        
        # Clean up request metrics
        self.request_metrics = [m for m in self.request_metrics if m.timestamp > cutoff_time]
        
        # Clean up hourly stats
        cutoff_hour = datetime.fromtimestamp(cutoff_time).strftime("%Y-%m-%d-%H")
        old_hours = [h for h in self.hourly_stats.keys() if h < cutoff_hour]
        for hour in old_hours:
            del self.hourly_stats[hour]
        
        self.logger.info(f"Cleaned up metrics older than {self.retention_hours} hours")