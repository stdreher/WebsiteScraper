import requests
from bs4 import BeautifulSoup
import urllib.parse
import logging
import trafilatura
from urllib.parse import urlparse, urljoin
import time
import re

def validate_url(url):
    """
    Validate if the provided URL has a valid format.
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if valid URL format, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except Exception as e:
        logging.error(f"URL validation error: {str(e)}")
        return False

def normalize_url(url, base_url):
    """
    Normalize relative URLs to absolute URLs.
    
    Args:
        url (str): URL to normalize
        base_url (str): Base URL for relative URLs
        
    Returns:
        str: Normalized URL
    """
    try:
        return urljoin(base_url, url)
    except Exception:
        return None

def crawl_website(url, instructions=None, max_pages=20, max_depth=2):
    """
    Crawl a website and extract information based on user instructions.
    
    Args:
        url (str): The URL to crawl
        instructions (str, optional): Custom instructions for crawling
        max_pages (int): Maximum number of pages to crawl
        max_depth (int): Maximum depth of crawling
        
    Returns:
        dict: Crawl results including links, text content, and metadata
    """
    if not validate_url(url):
        raise ValueError("Invalid URL format")
    
    # Parse custom instructions
    depth_match = re.search(r'depth[:\s]+(\d+)', instructions or '', re.IGNORECASE)
    if depth_match:
        max_depth = min(int(depth_match.group(1)), 5)  # Limit to 5 for safety
    
    pages_match = re.search(r'pages[:\s]+(\d+)', instructions or '', re.IGNORECASE)
    if pages_match:
        max_pages = min(int(pages_match.group(1)), 50)  # Limit to 50 for safety
    
    # Initialize the crawl results
    visited = set()
    to_visit = [(url, 0)]  # (url, depth)
    results = {
        'links': [],
        'text': '',
        'metadata': {
            'title': '',
            'description': '',
            'base_url': url,
            'pages_crawled': 0,
            'crawl_time': 0
        },
        'page_data': []
    }
    
    # Track specific patterns based on instructions
    track_images = 'images' in (instructions or '').lower()
    track_headings = 'headings' in (instructions or '').lower()
    
    start_time = time.time()
    
    while to_visit and len(visited) < max_pages:
        current_url, current_depth = to_visit.pop(0)
        
        if current_url in visited or current_depth > max_depth:
            continue
            
        try:
            # Add to visited set
            visited.add(current_url)
            
            # Fetch the page content
            logging.info(f"Crawling: {current_url}")
            headers = {'User-Agent': 'Mozilla/5.0 WebsiteCrawler/1.0'}
            response = requests.get(current_url, headers=headers, timeout=10)
            response.raise_for_status()  # Raise exception for bad status codes
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get metadata
            page_title = soup.title.string if soup.title else "No Title"
            page_description = ''
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and 'content' in meta_desc.attrs:
                page_description = meta_desc['content']
            
            # Extract text content using trafilatura for better text extraction
            downloaded = trafilatura.fetch_url(current_url)
            page_text = trafilatura.extract(downloaded) or "No text content extracted"
            
            # Add to results
            page_data = {
                'url': current_url,
                'title': page_title,
                'description': page_description,
                'text_sample': page_text[:200] + "..." if len(page_text) > 200 else page_text,
                'depth': current_depth
            }
            
            # Track additional elements based on instructions
            if track_images:
                page_data['images'] = [img.get('src', '') for img in soup.find_all('img') if img.get('src')]
                
            if track_headings:
                page_data['headings'] = []
                for i in range(1, 7):
                    for heading in soup.find_all(f'h{i}'):
                        page_data['headings'].append({
                            'level': i,
                            'text': heading.get_text(strip=True)
                        })
            
            results['page_data'].append(page_data)
            results['text'] += f"\n\n--- {page_title} ---\n{page_text}"
            
            # If this is the first page, update metadata
            if len(results['page_data']) == 1:
                results['metadata']['title'] = page_title
                results['metadata']['description'] = page_description
            
            # Extract links if we haven't reached max depth
            if current_depth < max_depth:
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('#') or href.startswith('javascript:'):
                        continue
                        
                    absolute_url = normalize_url(href, current_url)
                    if absolute_url and validate_url(absolute_url):
                        # Only follow links to the same domain
                        if urlparse(absolute_url).netloc == urlparse(url).netloc:
                            if absolute_url not in visited:
                                to_visit.append((absolute_url, current_depth + 1))
                                results['links'].append({
                                    'url': absolute_url,
                                    'text': link.get_text(strip=True),
                                    'depth': current_depth + 1
                                })
            
        except Exception as e:
            logging.error(f"Error crawling {current_url}: {str(e)}")
            continue
    
    # Update metadata
    results['metadata']['pages_crawled'] = len(visited)
    results['metadata']['crawl_time'] = round(time.time() - start_time, 2)
    
    return results
