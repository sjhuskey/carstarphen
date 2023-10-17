#!/usr/bin/env python3

'''
Script to scrape OCR text from the Oklahoma Historical
Society's gateway site.

author: Sam Huskey (with help from ChatGPT)
'''

import requests
import csv
import time
import logging
from bs4 import BeautifulSoup

# Logging setup
logging.basicConfig(filename='scraping.log', level=logging.INFO)

def extract_ocr_text(ocr_page_url):
    response = session.get(ocr_page_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    ocr_link = soup.select_one('a#ocr-text')
    
    if ocr_link:
        ocr_response = session.get(f'{ocr_page_url}{ocr_link["href"]}', headers=headers)
        return ocr_response.text.strip()
    else:
        ocr_text = soup.select_one('#ocr-text')
        return ocr_text.get_text(strip=True) if ocr_text else None

def get_metadata_and_ocr(subpage_url):
    try:
        page_response = session.get(subpage_url, headers=headers)
        page_soup = BeautifulSoup(page_response.text, 'html.parser')

        pub_date = page_soup.find('meta', {'name': 'citation_publication_date'})['content']
        volume = page_soup.find('meta', {'name': 'citation_volume'})['content']
        title = page_soup.find('meta', {'name': 'citation_title'})['content']
        
        ocr_text = extract_ocr_text(subpage_url)
        
        return [subpage_url, pub_date, volume, title, ocr_text]
    except Exception as e:
        logging.error(f"Error processing {subpage_url}: {str(e)}")
        return None

# Number of total articles and articles per page
total_articles = 895
articles_per_page = 24

# URLs and headers
base_search_url = 'https://gateway.okhistory.org/search/?q=cherokee+advocate&t=fulltext&fq=untl_collection%3ACHRAD&start={}'
headers = {'User-Agent': 'CherokeeAdvocateScrapter (huskey@ou.edu)'}
session = requests.Session() 

# With statement for CSV writing
with open('cherokee-advocate.csv', 'w', newline='', encoding='utf-8') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Subpage URL', 'Publication Date', 'Volume', 'Title', 'OCR Text'])
    
    logging.info('Script started')
    print('Scraping started')    
    
    for start in range(0, total_articles, articles_per_page):
        search_url = base_search_url.format(start)
        logging.info(f'Processing articles from {search_url}')
        
        try:
            response = session.get(search_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            current_iteration = 0  # Initialize the current iteration counter
            
            # Iterate through each article in the page
            for article in soup.find_all('article'):
                current_iteration += 1  # Increment the current iteration counter
                
                article_link = article.find('a')['href']
                article_url = f"https://gateway.okhistory.org{article_link}"
                
                # Fetch the main article page to find the number of subpages
                article_response = session.get(article_url, headers=headers)
                article_soup = BeautifulSoup(article_response.text, 'html.parser')
                
                # Assumes subpages are listed as `/m1/1/`, `/m1/2/`, etc.
                subpage_links = article_soup.find('div', {'id': 'more-pages'}).find_all('a')
                
                for subpage_link in subpage_links:
                    # Form the subpage URL and fetch data
                    subpage_url = f"https://gateway.okhistory.org{subpage_link['href']}"
                    
                    data = get_metadata_and_ocr(subpage_url)
                    if data:
                        csv_writer.writerow(data)
                    
                    # Respectful sleeping
                    time.sleep(3)
                
                # Print progress message every 5 articles
                if current_iteration % 5 == 0:
                    print(f"Processing {current_iteration} of {total_articles} articles")
                    
        except Exception as e:
            logging.error(f"Error processing search page {search_url}: {str(e)}")
        
        # Sleep between fetching pages of search results
        time.sleep(3)
    
    print('Scraping finished')
    logging.info('Script finished')
