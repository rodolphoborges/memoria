import os
import asyncio
import argparse
from datetime import datetime
from crawl4ai import AsyncWebCrawler
from vectorize import prepare_chunks, upsert_to_pinecone

async def crawl_and_ingest(url: str, context: str):
    """
    Scrapes a URL using Crawl4AI and ingests it into the knowledge base.
    """
    print(f"🚀 Starting crawl for: {url}")
    
    # Determine namespace
    namespace = "work-context" if context == "pro" else "home-context"
    
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
        
        if not result.success:
            print(f"❌ Failed to crawl {url}: {result.error_message}")
            return

        print(f"✅ Successfully scraped: {url}")
        markdown_content = result.markdown
        
        # Metadata enrichment
        source_name = url.split("//")[-1].split("/")[0] # Basic domain extraction
        scrape_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Prepare content for vectorization
        # We prepend URL and Date to the content for better RAG context
        enriched_content = f"Source URL: {url}\nScraped at: {scrape_date}\n\n{markdown_content}"
        
        print(f"📦 Vectorizing and upserting to {namespace}...")
        
        try:
            processed_data = prepare_chunks(
                content=enriched_content,
                source=url,
                file_type="web-page",
                namespace=namespace,
                file_path=url
            )
            
            if processed_data:
                upsert_to_pinecone(processed_data, namespace)
                print(f"✨ Successfully indexed {len(processed_data)} chunks from {url}")
            else:
                print("⚠️ No chunks were generated from the content.")
                
        except Exception as e:
            print(f"❌ Error during vectorization: {e}")

def main():
    parser = argparse.ArgumentParser(description="Ingest web content using Crawl4AI.")
    parser.add_argument("url", type=str, help="The URL to scrape and ingest")
    parser.add_argument("--context", type=str, choices=["pro", "personal"], default="personal",
                        help="Context to ingest into (pro -> work-context, personal -> home-context)")
    
    args = parser.parse_args()
    
    asyncio.run(crawl_and_ingest(args.url, args.context))

if __name__ == "__main__":
    main()
