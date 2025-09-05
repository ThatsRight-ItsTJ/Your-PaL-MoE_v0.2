#!/usr/bin/env python3
"""
GitHub File Downloader for AI API Liaison Development Plan

This script automatically downloads all GitHub files specified in your development plan.
It handles rate limiting, creates directory structures, and provides progress tracking.
"""

import os
import re
import asyncio
import aiohttp
import aiofiles
from pathlib import Path
from typing import List, Tuple, Dict
from dataclasses import dataclass
import argparse
import sys
from urllib.parse import urlparse

@dataclass
class FileDownload:
    url: str
    local_path: str
    description: str = ""

class GitHubFileDownloader:
    def __init__(self, github_token: str = None):
        self.github_token = github_token
        self.session = None
        self.downloaded_count = 0
        self.failed_count = 0
        
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

    def parse_markdown_downloads(self, md_content: str) -> List[FileDownload]:
        """Parse the markdown content to extract all wget download commands."""
        downloads = []
        
        # Pattern to match wget commands with -O flag
        wget_pattern = r'wget\s+([^\s]+)\s+-O\s+([^\s]+)(?:\s+#\s*(.*))?'
        
        matches = re.findall(wget_pattern, md_content, re.MULTILINE)
        
        for match in matches:
            url = match[0]
            local_path = match[1]
            description = match[2] if len(match) > 2 else ""
            
            downloads.append(FileDownload(
                url=url,
                local_path=local_path,
                description=description
            ))
        
        return downloads
    
    def convert_to_raw_url(self, github_url: str) -> str:
        """Convert GitHub blob URLs to raw URLs for direct download."""
        if 'raw.githubusercontent.com' in github_url:
            return github_url
        
        # Convert github.com/user/repo/blob/branch/file to raw.githubusercontent.com format
        if 'github.com' in github_url and '/blob/' in github_url:
            parts = github_url.replace('https://github.com/', '').split('/')
            if len(parts) >= 4:
                user, repo = parts[0], parts[1]
                branch = parts[3]
                file_path = '/'.join(parts[4:])
                return f'https://raw.githubusercontent.com/{user}/{repo}/{branch}/{file_path}'
        
        return github_url
    
    async def download_file(self, download: FileDownload) -> bool:
        """Download a single file with error handling and retry logic."""
        try:
            # Ensure local directory exists
            local_dir = os.path.dirname(download.local_path)
            if local_dir:
                os.makedirs(local_dir, exist_ok=True)
            
            # Convert to raw URL if needed
            raw_url = self.convert_to_raw_url(download.url)
            
            print(f"📥 Downloading: {download.local_path}")
            print(f"   From: {raw_url}")
            
            async with self.session.get(raw_url) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    async with aiofiles.open(download.local_path, 'wb') as f:
                        await f.write(content)
                    
                    self.downloaded_count += 1
                    print(f"✅ Success: {download.local_path}")
                    return True
                
                elif response.status == 404:
                    print(f"❌ Not Found: {download.local_path} (404)")
                    self.failed_count += 1
                    return False
                
                elif response.status == 403:
                    print(f"⚠️  Rate Limited or Forbidden: {download.local_path} (403)")
                    print("   Consider adding a GitHub token or waiting...")
                    self.failed_count += 1
                    return False
                
                else:
                    print(f"❌ HTTP {response.status}: {download.local_path}")
                    self.failed_count += 1
                    return False
        
        except asyncio.TimeoutError:
            print(f"⏰ Timeout: {download.local_path}")
            self.failed_count += 1
            return False
        
        except Exception as e:
            print(f"❌ Error downloading {download.local_path}: {str(e)}")
            self.failed_count += 1
            return False
    
    async def download_all(self, downloads: List[FileDownload], max_concurrent: int = 5):
        """Download all files with concurrency control."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def download_with_semaphore(download):
            async with semaphore:
                return await self.download_file(download)
        
        print(f"🚀 Starting download of {len(downloads)} files...\n")
        
        # Execute downloads with concurrency limit
        tasks = [download_with_semaphore(download) for download in downloads]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"\n📊 Download Summary:")
        print(f"   ✅ Successful: {self.downloaded_count}")
        print(f"   ❌ Failed: {self.failed_count}")
        print(f"   📁 Total: {len(downloads)}")

def create_project_structure():
    """Create the project directory structure as specified in the plan."""
    directories = [
        "core", "resilience", "selection", "cost", "optimization", 
        "ml", "providers", "monitoring", "config", "api", "storage", 
        "utils", "tests", "examples", "docs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def main():
    parser = argparse.ArgumentParser(description='Download GitHub files for AI API Liaison project')
    parser.add_argument('--token', '-t', help='GitHub personal access token (for rate limiting)', 
                       default=os.getenv('GITHUB_TOKEN'))
    parser.add_argument('--markdown', '-m', help='Path to markdown file', 
                       default='ai-api-liaison-development-plan.md')
    parser.add_argument('--create-dirs', '-d', action='store_true', 
                       help='Create project directory structure')
    parser.add_argument('--concurrent', '-c', type=int, default=5, 
                       help='Maximum concurrent downloads')
    
    args = parser.parse_args()
    
    # Create project structure if requested
    if args.create_dirs:
        print("🏗️  Creating project directory structure...\n")
        create_project_structure()
        print()
    
    # Check if markdown file exists
    if not os.path.exists(args.markdown):
        print(f"❌ Markdown file not found: {args.markdown}")
        print("💡 Make sure the development plan file is in the current directory")
        sys.exit(1)
    
    # Read markdown file
    try:
        with open(args.markdown, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except Exception as e:
        print(f"❌ Error reading markdown file: {e}")
        sys.exit(1)
    
    async def run_downloads():
        async with GitHubFileDownloader(args.token) as downloader:
            downloads = downloader.parse_markdown_downloads(md_content)
            
            if not downloads:
                print("⚠️  No download commands found in markdown file")
                print("💡 Make sure the file contains wget commands with -O flags")
                return
            
            print(f"📋 Found {len(downloads)} files to download")
            if args.token:
                print("🔑 Using GitHub token for authentication")
            else:
                print("⚠️  No GitHub token provided - may hit rate limits")
                print("💡 Set GITHUB_TOKEN environment variable or use --token flag")
            print()
            
            await downloader.download_all(downloads, args.concurrent)
    
    # Run the async downloads
    try:
        asyncio.run(run_downloads())
        print("\n🎉 Download process completed!")
    except KeyboardInterrupt:
        print("\n⚠️  Download interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
