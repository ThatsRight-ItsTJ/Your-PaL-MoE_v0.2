#!/usr/bin/env python3
"""
Fixed GitHub File Downloader for AI API Liaison Development Plan

This script handles missing files by providing alternative URLs or similar files.
Updated to work around 404 errors from the original development plan.
"""

import os
import re
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import argparse
import sys
from urllib.parse import urlparse

@dataclass
class FileDownload:
    url: str
    local_path: str
    description: str = ""
    alternatives: List[str] = None
    is_critical: bool = True

class FixedGitHubDownloader:
    def __init__(self, github_token: str = None):
        self.github_token = github_token
        self.session = None
        self.downloaded_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
    async def __aenter__(self):
        headers = {
            'User-Agent': 'AI-API-Liaison-Downloader/1.0'
        }
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def get_fixed_downloads(self) -> List[FileDownload]:
        """Return the corrected list of downloads with working URLs and alternatives."""
        downloads = []
        
        # ✅ GRACY FRAMEWORK FILES (Working)
        downloads.extend([
            FileDownload(
                "https://raw.githubusercontent.com/guilatrova/gracy/main/src/gracy/__init__.py",
                "resilience/gracy_init.py",
                "Gracy core init"
            ),
            FileDownload(
                "https://raw.githubusercontent.com/guilatrova/gracy/main/src/gracy/_core.py",
                "resilience/gracy_client.py",
                "Gracy core client"
            ),
            FileDownload(
                "https://raw.githubusercontent.com/guilatrova/gracy/main/src/gracy/_models.py",
                "resilience/gracy_models.py",
                "Gracy models"
            ),
            FileDownload(
                "https://raw.githubusercontent.com/guilatrova/gracy/main/src/gracy/common_hooks.py",
                "resilience/hooks_manager.py",
                "Gracy hooks"
            ),
            FileDownload(
                "https://raw.githubusercontent.com/guilatrova/gracy/main/src/gracy/_reports/_builders.py",
                "monitoring/metrics_collector.py",
                "Metrics collector"
            ),
            FileDownload(
                "https://raw.githubusercontent.com/guilatrova/gracy/main/examples/pokeapi_retry.py",
                "examples/gracy_retry_example.py",
                "Retry example"
            ),
            FileDownload(
                "https://raw.githubusercontent.com/guilatrova/gracy/main/examples/pokeapi_throttle.py",
                "examples/gracy_throttle_example.py",
                "Throttle example"
            ),
        ])
        
        # ❌ ZUKIJOURNEY API-OSS FILES (Fixed with alternatives)
        downloads.extend([
            FileDownload(
                "https://raw.githubusercontent.com/zukijourney/example-api/main/index.js",
                "core/routing_engine_base.ts",
                "Routing engine base (alternative from example-api)",
                alternatives=[
                    "https://raw.githubusercontent.com/hlohaus/g4f/main/g4f/api.py",
                    "https://raw.githubusercontent.com/xtekky/gpt4free/main/g4f/api.py"
                ],
                is_critical=False
            ),
            FileDownload(
                "https://raw.githubusercontent.com/hlohaus/g4f/main/g4f/Provider/OpenaiChat.py",
                "api/openai_compatible_base.py",
                "OpenAI compatible base (alternative from g4f)",
                alternatives=[
                    "https://raw.githubusercontent.com/openai/openai-python/main/src/openai/_client.py"
                ],
                is_critical=False
            ),
            FileDownload(
                "https://raw.githubusercontent.com/hlohaus/g4f/main/g4f/api.py",
                "core/auth_middleware_base.py",
                "Auth middleware base (alternative)",
                is_critical=False
            ),
            FileDownload(
                "https://raw.githubusercontent.com/hlohaus/g4f/main/g4f/Provider/__init__.py",
                "core/provider_manager_base.py",
                "Provider manager base (alternative)",
                is_critical=False
            ),
        ])
        
        # ✅ DESLIB SELECTION ALGORITHMS (Working)
        downloads.extend([
            FileDownload(
                "https://raw.githubusercontent.com/scikit-learn-contrib/DESlib/master/deslib/des/knora_e.py",
                "selection/knora_selector.py",
                "KNORA selector"
            ),
            FileDownload(
                "https://raw.githubusercontent.com/scikit-learn-contrib/DESlib/master/deslib/des/des_clustering.py",
                "selection/clustering_engine.py",
                "Clustering engine"
            ),
            FileDownload(
                "https://raw.githubusercontent.com/scikit-learn-contrib/DESlib/master/deslib/util/instance_hardness.py",
                "selection/performance_metrics.py",
                "Performance metrics"
            ),
            FileDownload(
                "https://raw.githubusercontent.com/scikit-learn-contrib/DESlib/master/deslib/base.py",
                "selection/base_selector.py",
                "Base selector"
            ),
        ])
        
        # ❌ RETRY MECHANISMS (Fixed with alternatives)
        downloads.extend([
            FileDownload(
                "https://raw.githubusercontent.com/jd/tenacity/main/tenacity/__init__.py",
                "resilience/retry_base.py",
                "Tenacity retry library (better alternative to uplink.retry)",
                alternatives=[
                    "https://raw.githubusercontent.com/urllib3/urllib3/main/src/urllib3/util/retry.py"
                ]
            ),
            FileDownload(
                "https://raw.githubusercontent.com/litl/backoff/master/backoff/_wait_gen.py",
                "resilience/wait_strategies.py",
                "Wait strategies"
            ),
        ])
        
        # ❌ PROVIDER ADAPTERS (Fixed with alternatives)
        downloads.extend([
            FileDownload(
                "https://raw.githubusercontent.com/openai/openai-python/main/src/openai/_client.py",
                "providers/openai_adapter_base.py",
                "OpenAI adapter (official Python client)",
                alternatives=[
                    "https://raw.githubusercontent.com/tmc/langchaingo/main/llms/openai/openaillm.go"
                ]
            ),
            FileDownload(
                "https://raw.githubusercontent.com/anthropics/anthropic-sdk-python/main/src/anthropic/_client.py",
                "providers/anthropic_adapter_base.py",
                "Anthropic adapter (official Python client)",
                alternatives=[
                    "https://raw.githubusercontent.com/tmc/langchaingo/main/llms/anthropic/anthropic.go"
                ]
            ),
        ])
        
        # ✅ COST ESTIMATION COMPONENTS (Working)
        downloads.extend([
            FileDownload(
                "https://raw.githubusercontent.com/AgentOps-AI/tokencost/main/tokencost/costs.py",
                "cost/pricing_data.py",
                "Pricing data"
            ),
            FileDownload(
                "https://raw.githubusercontent.com/AgentOps-AI/tokencost/main/tokencost/model_prices.json",
                "cost/model_prices.json",
                "Model prices"
            ),
            FileDownload(
                "https://raw.githubusercontent.com/oneirocom/ai-api-cost-estimator/main/src/index.ts",
                "cost/cost_estimator_base.ts",
                "Cost estimator base"
            ),
            FileDownload(
                "https://raw.githubusercontent.com/oneirocom/ai-api-cost-estimator/main/src/models.ts",
                "cost/models_config.ts",
                "Models config"
            ),
        ])
        
        # ❌ PROMPT OPTIMIZATION COMPONENTS (Fixed with alternatives)
        downloads.extend([
            FileDownload(
                "https://raw.githubusercontent.com/microsoft/promptflow/main/src/promptflow/core/_flow.py",
                "optimization/prompt_optimizer_base.py",
                "Prompt optimizer base (alternative file from promptflow)",
                alternatives=[
                    "https://raw.githubusercontent.com/microsoft/guidance/main/guidance/_guidance.py"
                ],
                is_critical=False
            ),
            FileDownload(
                "https://raw.githubusercontent.com/microsoft/FLAML/main/flaml/automl/automl.py",
                "optimization/genetic_algorithm_base.py",
                "AutoML optimization base (alternative to optuna_searcher)",
                alternatives=[
                    "https://raw.githubusercontent.com/optuna/optuna/master/optuna/samplers/_base.py"
                ],
                is_critical=False
            ),
        ])
        
        return downloads
    
    async def download_file(self, download: FileDownload) -> bool:
        """Download a single file with fallback to alternatives."""
        urls_to_try = [download.url] + (download.alternatives or [])
        
        for i, url in enumerate(urls_to_try):
            try:
                # Ensure local directory exists
                local_dir = os.path.dirname(download.local_path)
                if local_dir:
                    os.makedirs(local_dir, exist_ok=True)
                
                is_alternative = i > 0
                status_prefix = "🔄 Alt" if is_alternative else "📥"
                
                print(f"{status_prefix} Downloading: {download.local_path}")
                print(f"   From: {url}")
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        
                        # Add comment to file if it's an alternative
                        if is_alternative and download.local_path.endswith(('.py', '.ts', '.js')):
                            comment_char = '#' if download.local_path.endswith('.py') else '//'
                            comment = f"{comment_char} Alternative file from {url}\n{comment_char} Original file was not available\n\n"
                            if isinstance(content, bytes):
                                content = comment.encode() + content
                        
                        async with aiofiles.open(download.local_path, 'wb') as f:
                            await f.write(content if isinstance(content, bytes) else content.encode())
                        
                        self.downloaded_count += 1
                        success_msg = "✅ Success (Alt)" if is_alternative else "✅ Success"
                        print(f"{success_msg}: {download.local_path}")
                        return True
                    
                    elif response.status == 404:
                        if is_alternative or not download.alternatives:
                            print(f"❌ Not Found: {download.local_path} (404)")
                        else:
                            print(f"⚠️  Original not found, trying alternatives...")
                            continue
                    
                    elif response.status == 403:
                        print(f"⚠️  Rate Limited or Forbidden: {download.local_path} (403)")
                        if not is_alternative and download.alternatives:
                            continue
                    
                    else:
                        print(f"❌ HTTP {response.status}: {download.local_path}")
                        if not is_alternative and download.alternatives:
                            continue
            
            except Exception as e:
                print(f"❌ Error downloading {download.local_path}: {str(e)}")
                if not is_alternative and download.alternatives:
                    continue
        
        # If we get here, all URLs failed
        if download.is_critical:
            self.failed_count += 1
        else:
            self.skipped_count += 1
            print(f"⏭️  Skipped (non-critical): {download.local_path}")
        
        return False
    
    async def download_all(self, downloads: List[FileDownload], max_concurrent: int = 3):
        """Download all files with concurrency control."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_with_semaphore(download):
            async with semaphore:
                return await self.download_file(download)
        
        print(f"🚀 Starting download of {len(downloads)} files...\n")
        print("Legend:")
        print("  ✅ = Successfully downloaded")
        print("  🔄 = Using alternative URL")
        print("  ⏭️  = Skipped (non-critical)")
        print("  ❌ = Failed (critical)")
        print()
        
        # Execute downloads with concurrency limit
        tasks = [download_with_semaphore(download) for download in downloads]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"\n📊 Download Summary:")
        print(f"   ✅ Successful: {self.downloaded_count}")
        print(f"   ⏭️  Skipped (non-critical): {self.skipped_count}")
        print(f"   ❌ Failed (critical): {self.failed_count}")
        print(f"   📁 Total: {len(downloads)}")
        
        if self.failed_count > 0:
            print(f"\n⚠️  {self.failed_count} critical files failed to download.")
            print("💡 You may need to find these files manually or implement alternatives.")
        
        if self.skipped_count > 0:
            print(f"\n📝 {self.skipped_count} non-critical files were skipped.")
            print("💡 These can be implemented from scratch or found later.")

def create_project_structure():
    """Create the project directory structure."""
    directories = [
        "core", "resilience", "selection", "cost", "optimization", 
        "ml", "providers", "monitoring", "config", "api", "storage", 
        "utils", "tests", "examples", "docs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def create_missing_file_guide():
    """Create a guide for the missing files."""
    guide_content = """# Missing Files Guide

## Files That Failed to Download

Some files from the original development plan were not available. Here's what you can do:

### ZukiJourney API-OSS Files (404 Errors)
The original repository structure has changed. Alternatives downloaded:
- `core/routing_engine_base.ts` - Use g4f routing logic instead
- `api/openai_compatible_base.py` - Use official OpenAI Python client
- `core/auth_middleware_base.py` - Implement basic FastAPI middleware
- `core/provider_manager_base.py` - Use g4f provider patterns

### Uplink Retry Files (404 Errors)
- `resilience/retry_base.py` - Replaced with Tenacity library (better alternative)

### Microsoft Prompt/FLAML Files (404 Errors)
- `optimization/prompt_optimizer_base.py` - Use Guidance library instead
- `optimization/genetic_algorithm_base.py` - Use Optuna for optimization

## Recommended Implementations

1. **For routing logic**: Implement a simple FastAPI-based router
2. **For retries**: Use Tenacity library (already downloaded)
3. **For prompt optimization**: Implement basic A/B testing
4. **For provider management**: Use the g4f patterns as reference

## Next Steps

1. Review downloaded alternatives
2. Implement missing critical components
3. Focus on core functionality first
4. Add advanced features incrementally
"""
    
    with open("MISSING_FILES_GUIDE.md", "w") as f:
        f.write(guide_content)
    print("📝 Created MISSING_FILES_GUIDE.md")

def main():
    parser = argparse.ArgumentParser(description='Fixed GitHub file downloader')
    parser.add_argument('--token', '-t', help='GitHub personal access token', 
                       default=os.getenv('GITHUB_TOKEN'))
    parser.add_argument('--create-dirs', '-d', action='store_true', 
                       help='Create project directory structure')
    parser.add_argument('--concurrent', '-c', type=int, default=3, 
                       help='Maximum concurrent downloads (reduced for stability)')
    parser.add_argument('--create-guide', '-g', action='store_true',
                       help='Create guide for missing files')
    
    args = parser.parse_args()
    
    # Create project structure if requested
    if args.create_dirs:
        print("🏗️  Creating project directory structure...\n")
        create_project_structure()
        print()
    
    # Create missing files guide if requested
    if args.create_guide:
        create_missing_file_guide()
        print()
    
    async def run_downloads():
        async with FixedGitHubDownloader(args.token) as downloader:
            downloads = downloader.get_fixed_downloads()
            
            print(f"📋 Found {len(downloads)} files to download")
            if args.token:
                print("🔑 Using GitHub token for authentication")
            else:
                print("⚠️  No GitHub token - may hit rate limits")
                print("💡 Set GITHUB_TOKEN environment variable or use --token flag")
            print()
            
            await downloader.download_all(downloads, args.concurrent)
    
    # Run the async downloads
    try:
        asyncio.run(run_downloads())
        print("\n🎉 Download process completed!")
        print("\n💡 Next steps:")
        print("   1. Review downloaded files")
        print("   2. Check MISSING_FILES_GUIDE.md if created")  
        print("   3. Install dependencies: pip install -r requirements.txt")
        print("   4. Start implementing core functionality")
    except KeyboardInterrupt:
        print("\n⚠️  Download interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
