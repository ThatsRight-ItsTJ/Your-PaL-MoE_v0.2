"""
AI API Liaison - Main FastAPI Application
Integrates all components for intelligent AI provider routing
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import our custom components
from config.csv_provider_loader import CSVProviderLoader, ProviderConfig
from ml.task_reasoning_engine import TaskReasoningEngine, ComplexityScore
from selection.dynamic_selector import ProviderSelector
from cost.token_counter import TokenCounter, CostBreakdown
from monitoring.metrics_collector import MetricsCollector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
provider_loader: Optional[CSVProviderLoader] = None
task_engine: Optional[TaskReasoningEngine] = None
provider_selector: Optional[ProviderSelector] = None
token_counter: Optional[TokenCounter] = None
metrics_collector: Optional[MetricsCollector] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global provider_loader, task_engine, provider_selector, token_counter, metrics_collector
    
    # Startup
    logger.info("🚀 Starting AI API Liaison...")
    
    try:
        # Initialize components
        provider_loader = CSVProviderLoader("providers.csv")
        providers = provider_loader.load_providers()
        logger.info(f"✅ Loaded {len(providers)} providers")
        
        task_engine = TaskReasoningEngine()
        logger.info("✅ Task reasoning engine initialized")
        
        provider_selector = ProviderSelector(providers)
        logger.info("✅ Provider selector initialized")
        
        token_counter = TokenCounter()
        logger.info("✅ Token counter initialized")
        
        metrics_collector = MetricsCollector()
        logger.info("✅ Metrics collector initialized")
        
        logger.info("🎉 AI API Liaison started successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize AI API Liaison: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down AI API Liaison...")

# Create FastAPI app
app = FastAPI(
    title="AI API Liaison",
    description="Intelligent AI Provider Routing System with Cost Optimization",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="List of messages")
    model: Optional[str] = Field("auto", description="Model to use (auto for intelligent selection)")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")
    stream: Optional[bool] = Field(False, description="Stream response")
    context: Optional[Dict[str, Any]] = Field({}, description="Additional context for provider selection")

class ProcessRequest(BaseModel):
    content: str = Field(..., description="Content to process")
    context: Optional[Dict[str, Any]] = Field({}, description="Processing context")
    constraints: Optional[Dict[str, Any]] = Field({}, description="Processing constraints")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    uptime: float
    providers: Dict[str, Any]

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        system_metrics = await metrics_collector.get_system_metrics()
        provider_stats = provider_loader.get_provider_stats()
        
        return HealthResponse(
            status="healthy",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            version="1.0.0",
            uptime=system_metrics.get("uptime", 0),
            providers=provider_stats
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Service unhealthy")

# OpenAI-compatible chat completions endpoint
@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    background_tasks: BackgroundTasks,
    req: Request
):
    """OpenAI-compatible chat completions endpoint with intelligent provider routing"""
    start_time = time.time()
    request_id = f"req_{int(start_time * 1000)}"
    
    try:
        # Analyze task complexity
        content = " ".join([msg.content for msg in request.messages])
        complexity_score = task_engine.analyze_complexity(content, request.context)
        
        logger.info(f"Request {request_id}: Complexity={complexity_score.complexity_level} ({complexity_score.total_score:.3f})")
        
        # Select optimal provider
        selected_provider = await provider_selector.select_provider(
            complexity_score, request.context, request.constraints
        )
        
        if not selected_provider:
            raise HTTPException(status_code=503, detail="No available providers")
        
        logger.info(f"Request {request_id}: Selected provider={selected_provider.name}")
        
        # Calculate estimated cost
        messages_dict = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        cost_breakdown = await token_counter.calculate_cost(
            selected_provider.name.lower(),
            messages_dict,
            "",  # No output yet
            request.model if request.model != "auto" else None
        )
        
        # Simulate API call (replace with actual provider integration)
        response_content = f"This is a simulated response from {selected_provider.name} for complexity level {complexity_score.complexity_level}"
        
        # Calculate final cost with response
        final_cost = await token_counter.calculate_cost(
            selected_provider.name.lower(),
            messages_dict,
            response_content,
            request.model if request.model != "auto" else None
        )
        
        # Record metrics
        response_time = time.time() - start_time
        background_tasks.add_task(
            metrics_collector.record_request,
            selected_provider.name,
            final_cost.model,
            True,  # success
            response_time,
            final_cost.total_cost,
            final_cost.input_tokens,
            final_cost.output_tokens,
            complexity_score.complexity_level
        )
        
        # Update provider metrics
        provider_selector.update_provider_metrics(
            selected_provider.name,
            response_time,
            True,  # success
            final_cost.total_cost / (final_cost.input_tokens + final_cost.output_tokens) if (final_cost.input_tokens + final_cost.output_tokens) > 0 else 0
        )
        
        # Return OpenAI-compatible response
        return {
            "id": request_id,
            "object": "chat.completion",
            "created": int(start_time),
            "model": final_cost.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_content
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": final_cost.input_tokens,
                "completion_tokens": final_cost.output_tokens,
                "total_tokens": final_cost.input_tokens + final_cost.output_tokens
            },
            "x_provider": selected_provider.name,
            "x_complexity": complexity_score.complexity_level,
            "x_cost": final_cost.total_cost
        }
        
    except Exception as e:
        # Record failed request
        response_time = time.time() - start_time
        background_tasks.add_task(
            metrics_collector.record_request,
            "unknown",
            "unknown",
            False,  # success
            response_time,
            0.0,  # cost
            0,  # input_tokens
            0,  # output_tokens
            "unknown",  # complexity_level
            str(type(e).__name__)  # error_type
        )
        
        logger.error(f"Request {request_id} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics endpoints
@app.get("/analytics/system")
async def get_system_analytics():
    """Get system-wide analytics"""
    try:
        return await metrics_collector.get_system_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/providers")
async def get_provider_analytics():
    """Get provider-specific analytics"""
    try:
        providers = provider_loader.providers
        analytics = {}
        
        for provider_name in providers.keys():
            analytics[provider_name] = await metrics_collector.get_provider_metrics(provider_name)
        
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/costs")
async def get_cost_analytics():
    """Get cost analytics and recommendations"""
    try:
        system_metrics = await metrics_collector.get_system_metrics()
        
        return {
            "total_cost": system_metrics.get("total_cost", 0),
            "cost_savings": system_metrics.get("cost_savings", 0),
            "cost_savings_percentage": system_metrics.get("cost_savings_percentage", 0),
            "requests_per_hour": system_metrics.get("requests_per_hour", 0),
            "complexity_distribution": system_metrics.get("complexity_distribution", {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Provider management endpoints
@app.get("/providers")
async def list_providers():
    """List all configured providers"""
    try:
        providers = provider_loader.providers
        provider_list = []
        
        for provider in providers.values():
            provider_metrics = await metrics_collector.get_provider_metrics(provider.name)
            provider_list.append({
                "name": provider.name,
                "tier": provider.tier.value,
                "models": provider.models,
                "health_score": provider.health_score,
                "metrics": provider_metrics
            })
        
        return {"providers": provider_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)