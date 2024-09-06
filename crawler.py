import csv
import os
import re
from urllib.parse import urljoin

import chardet
import requests
from bs4 import BeautifulSoup

# Output file name
filename = "Company2Fulltext.csv"
# Increase the field size limit to avoid field size limit error (due to the web data being very big)
csv.field_size_limit(100000000)


# Function to check if the link is invalid (e.g., a link to a PDF file)
def check_if_invalid_link(url):
    invalid_extensions = ('.pdf', '.jpg', '.png', '.jpeg', '.gif', '.svg', '.mp4', '.mp3',
                          '.avi', '.mov', '.flv', '.wmv', '.wav', '.flac', '.aac', '.wma',
                          '.ogg', '.zip', '.tar', '.gz', '.rar', '.exe')
    return any(url.lower().endswith(ext) for ext in invalid_extensions)


# Function to get the text from a webpage
def get_page_text(url):
    try:
        # Check if the link is invalid
        if check_if_invalid_link(url):
            return None
        # Get the page content
        response = requests.get(url, timeout=20)
        # Check if the response is successful
        if response.status_code == 200:
            # Detect encoding, to mitigate corrupted output
            if 'charset' not in response.headers.get('content-type', '').lower():
                # If the encoding is not specified in the response headers, detect it
                encoding = chardet.detect(response.content)['encoding']
            else:
                # If the encoding is specified in the response headers, use it
                encoding = response.encoding

            # Parse the content using BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser', from_encoding=encoding)
            # Find all <p> tags and extract the text
            all_p = soup.find_all('p')
            # Join the text from all <p> tags
            page_text = ' '.join(p.get_text(separator=' | ', strip=True) for p in all_p)
            print('Page text:', page_text[:100])
            return page_text
        return None
    # Handle exceptions
    except Exception as e:
        print('Error getting page text:', e)
        return None


# Function to crawl the web and extract the text from the webpages
def crawl_web(url, visited_urls=None, seen_strings=None, max_depth=3, current_depth=1):
    # Initialize the visited_urls and seen_strings sets
    if visited_urls is None:
        visited_urls = set()
    if seen_strings is None:
        seen_strings = set()
    # Check if the current depth is greater than the maximum depth or if the URL has already been visited
    if current_depth > max_depth or url in visited_urls:
        return ''

    try:
        # Add the URL to the visited_urls set
        visited_urls.add(url)
        # Get the text from the webpage
        page_text = get_page_text(url)
        if page_text:
            # Remove extra whitespace
            cleaned = re.sub(r'\s+', ' ', page_text).strip()
            # Check if the text has already been seen
            if cleaned not in seen_strings:
                seen_strings.add(cleaned)
            else:
                # If the text has already been seen, return an empty string to avoid duplicate content
                cleaned = ''
            # Crawl child links
            if not check_if_invalid_link(url):
                # Get the webpage content
                response = requests.get(url, timeout=20)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    # Extract all links from the webpage
                    links = [urljoin(url, link['href']) for link in soup.find_all('a', href=True)]
                    for next_url in links:
                        # Recursively crawl the child links if they are not already visited
                        if not next_url.startswith('http') or next_url in visited_urls:
                            continue
                        cleaned += crawl_web(next_url, visited_urls, seen_strings, max_depth, current_depth + 1)
            return cleaned
        return ''
    except Exception as e:
        print(f'Error crawling {url}: {e}')
        return ''


# Checks if there is already data for the company
def check_file_for_company(filename, company_name):
    if os.path.isfile(filename):
        try:
            with open(filename, 'rb') as file:
                # Remove NUL (encoded as '\x00') characters
                content = file.read().replace(b'\x00', b'')
            # Decode the content to a string
            content = content.decode('utf-8', errors='ignore')
            # Read the CSV content
            reader = csv.reader(content.splitlines(), delimiter=';')
            for r in reader:
                # Check if the company name is in the first column of the CSV
                if r[0] == company_name.replace(' ', '_'):
                    print('Data already exists for:', company_name)
                    return True
        except Exception as e:
            print('Error reading file:', e)
            return False
    return False


def crawl(homepage_url, name):
    # Only crawl if file doesn't contain the company data yet
    has_data = check_file_for_company("Company2Fulltext.csv", name.replace(' ', '_'))
    if has_data:
        return
    # Crawl the website
    fulltext = crawl_web(homepage_url)

    # Check if the file exists
    file_exists = os.path.isfile(filename)

    print('Writing to file')
    # Open the file in append mode
    try:
        with open(filename, mode='a', newline='', encoding='utf8', errors='ignore') as file:
            writer = csv.writer(file, delimiter=';')
            # If the file does not exist, write the header
            if not file_exists:
                writer.writerow(['name', 'fulltext'])
            # Write the new data
            if len(fulltext) > 1:
                # Remove NUL (encoded as '\x00') characters and the ";" which acts as the delimiter for the csv.
                writer.writerow([name.replace(' ', '_'), fulltext.replace(';', ',').replace('\x00', '')])
        print("Data appended.")
    except Exception as e:
        print('Error writing to file:', e)
        return


with open('companies2links.csv', 'r', errors='ignore') as company2LinkFile:
    # Initialize the index to keep track of the progress
    ind = 0
    # Read the company links from the file
    company2Link = csv.reader(company2LinkFile, delimiter=';')

    for row in company2Link:
        # Skip the header row and rows with missing data
        if not row[1] or row[1] == 'URL':
            print('Skipping row:', row)
            continue

        # Keep track of the progress through the loop index
        ind += 1
        print('---------------------------------------------------------')
        print('Progress: ', ind)
        print(row)
        # Crawl the company website
        crawl(row[1], row[0])
