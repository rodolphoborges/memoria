import os
import asyncio
import argparse
from datetime import datetime
from urllib.parse import urljoin, urlparse
from typing import Set, List
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from vectorize import prepare_chunks, upsert_to_pinecone

def is_internal_link(base_url: str, link: str) -> bool:
    """Checks if a link is internal and relevant (same domain and path)."""
    base_domain = urlparse(base_url).netloc
    link_domain = urlparse(link).netloc
    # Stay within the same domain
    if link_domain and link_domain != base_domain:
        return False
    # Avoid anchors and non-html files
    if "#" in link or any(ext in link.lower() for ext in [".pdf", ".jpg", ".png", ".zip", ".exe"]):
        return False
    return True

async def crawl_and_ingest(url: str, context: str, depth: int = 1, max_pages: int = 50):
    """
    Scrapes URL(s) using Crawl4AI and ingests them into the knowledge base.
    Supports recursive crawling within the same domain up to specified depth.
    """
    namespace = "work-context" if context == "pro" else "home-context"
    to_visit: Set[str] = {url}
    visited: Set[str] = set()
    all_results = []
    
    # Model/Index initialization happens lazily in vectorize.py inside prepare_chunks/upsert
    
    async with AsyncWebCrawler() as crawler:
        for current_depth in range(depth):
            if not to_visit or len(visited) >= max_pages:
                break
            
            queue = list(to_visit - visited)[:max_pages - len(visited)]
            if not queue:
                break
                
            print(f"📊 Depth {current_depth + 1}/{depth} | Crawling {len(queue)} pages...")
            
            # RUN MANY for parallel fetching
            results = await crawler.arun_many(
                urls=queue,
                config=CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
            )
            
            new_links = set()
            for res in results:
                visited.add(res.url)
                if not res.success:
                    print(f"❌ Failed: {res.url} ({res.error_message})")
                    continue
                
                print(f"✅ Scraped: {res.url}")
                all_results.append(res)
                
                # Discover more links for next depth
                if current_depth < depth - 1:
                    # Accessing internal links safely
                    # results.links usually contains a dict of internal/external
                    raw_links = res.links.get("internal", [])
                    for link_data in raw_links:
                        link_url = link_data.get("href")
                        if link_url:
                            absolute_url = urljoin(res.url, link_url)
                            if is_internal_link(url, absolute_url) and absolute_url not in visited:
                                new_links.add(absolute_url)
            
            to_visit = new_links

    # Batch process all collected results
    print(f"\n📦 Finalizing: Vectorizing {len(all_results)} pages...")
    total_chunks = 0
    scrape_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for res in all_results:
        try:
            enriched_content = f"Source URL: {res.url}\nScraped at: {scrape_date}\n\n{res.markdown}"
            processed_data = prepare_chunks(
                content=enriched_content,
                source=res.url,
                file_type="web-page",
                namespace=namespace,
                file_path=res.url
            )
            if processed_data:
                upsert_to_pinecone(processed_data, namespace)
                total_chunks += len(processed_data)
        except Exception as e:
            print(f"❌ Error indexing {res.url}: {e}")

    print(f"\n✨ DONE: Indexed {total_chunks} chunks from {len(visited)} pages into {namespace}.")

def main():
    parser = argparse.ArgumentParser(description="Ingest web content deeply using Crawl4AI.")
    parser.add_argument("url", type=str, help="The seed URL to scrape and ingest")
    parser.add_argument("--context", type=str, choices=["pro", "personal"], default="personal",
                        help="Context (pro -> work-context, personal -> home-context)")
    parser.add_argument("--depth", type=int, default=1, help="Crawl depth (1 = single page)")
    parser.add_argument("--limit", type=int, default=30, help="Max total pages to ingest")
    
    args = parser.parse_args()
    
    asyncio.run(crawl_and_ingest(args.url, args.context, args.depth, args.limit))

if __name__ == "__main__":
    main()
