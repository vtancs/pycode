import requests
import re
import time
from pathlib import Path

def extract_arxiv_id(url):
    """Extract arXiv ID from URL, handling various formats."""
    # Remove spaces and normalize URL
    url = url.replace(' ', '')
    
    # Extract the arXiv ID (pattern: YYMM.NNNNN or YYMM.NNNNNvN)
    match = re.search(r'(\d{4}\.\d{5}(?:v\d+)?)', url)
    if match:
        return match.group(1)
    return None

def download_paper(arxiv_id, output_dir='.'):
    """Download a paper from arXiv given its ID."""
    # Construct the PDF URL
    pdf_url = f'https://arxiv.org/pdf/{arxiv_id}.pdf'
    
    # Create filename from arXiv ID
    filename = f'{arxiv_id.replace("/", "_")}.pdf'
    filepath = Path(output_dir) / filename
    
    # Skip if already downloaded
    if filepath.exists():
        print(f'Already exists: {filename}')
        return True
    
    try:
        print(f'Downloading {arxiv_id}...')
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status()
        
        # Save the PDF
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f'✓ Downloaded: {filename}')
        return True
        
    except requests.exceptions.RequestException as e:
        print(f'✗ Failed to download {arxiv_id}: {e}')
        return False

def main():
    input_file = 'papers.txt'
    
    # Read URLs from file
    try:
        with open(input_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f'Error: {input_file} not found!')
        return
    
    print(f'Found {len(urls)} URLs in {input_file}\n')
    
    # Track unique arXiv IDs to avoid duplicates
    seen_ids = set()
    downloaded = 0
    failed = 0
    skipped = 0
    
    for url in urls:
        arxiv_id = extract_arxiv_id(url)
        
        if not arxiv_id:
            print(f'✗ Could not extract arXiv ID from: {url}')
            failed += 1
            continue
        
        if arxiv_id in seen_ids:
            print(f'Skipping duplicate: {arxiv_id}')
            skipped += 1
            continue
        
        seen_ids.add(arxiv_id)
        
        if download_paper(arxiv_id):
            downloaded += 1
        else:
            failed += 1
        
        # Be polite to arXiv servers
        time.sleep(1)
    
    print(f'\n--- Summary ---')
    print(f'Downloaded: {downloaded}')
    print(f'Failed: {failed}')
    print(f'Skipped (duplicates): {skipped}')

if __name__ == '__main__':
    main()