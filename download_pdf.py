import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import time

SAVE_DIR = "downloaded_pdfs"
VISITED = set()
PDF_FOUND = set()

os.makedirs(SAVE_DIR, exist_ok=True)


def is_same_domain(base, target):
    return urlparse(base).netloc == urlparse(target).netloc


def safe_filename(url):
    name = url.split("/")[-1]
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name.replace("%20", "_")


def download_pdf(pdf_url):
    if pdf_url in PDF_FOUND:
        return
    PDF_FOUND.add(pdf_url)

    try:
        print(f"Downloading PDF: {pdf_url}")

        r = requests.get(pdf_url, stream=True, timeout=20)
        if r.status_code == 200:
            filepath = os.path.join(SAVE_DIR, safe_filename(pdf_url))
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)

            print(f"Saved -> {filepath}\n")
        else:
            print(f"Failed ({r.status_code}) {pdf_url}\n")

    except Exception as e:
        print(f"Error downloading {pdf_url}: {e}")


def crawl(url, base_domain, depth=0, max_depth=3):
    if depth > max_depth or url in VISITED:
        return

    VISITED.add(url)

    try:
        print(f"Crawling: {url}")
        r = requests.get(url, timeout=15)

        if "text/html" not in r.headers.get("Content-Type", ""):
            return

        soup = BeautifulSoup(r.text, "html.parser")

        for link in soup.find_all("a", href=True):
            href = urljoin(url, link["href"])

            if href.lower().endswith(".pdf"):
                download_pdf(href)

            elif is_same_domain(base_domain, href):
                crawl(href, base_domain, depth + 1, max_depth)

        time.sleep(1)  # be polite to server

    except Exception as e:
        print(f"Error crawling {url}: {e}")


def main():
    with open("sites.txt", "r", encoding="utf-8") as f:
        sites = [line.strip() for line in f if line.strip()]

    for site in sites:
        print(f"\n=== Starting site: {site} ===\n")
        crawl(site, site)

    print("\nDone!")
    print(f"Visited pages: {len(VISITED)}")
    print(f"PDFs downloaded: {len(PDF_FOUND)}")


if __name__ == "__main__":
    main()