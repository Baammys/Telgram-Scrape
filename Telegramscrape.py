import requests
from bs4 import BeautifulSoup
import newspaper
import telegram
import asyncio
import time

bot_token = 'your bot token'
channel_id = '@yourchannel'

websites = [
    
    
]

keywords = [


    "struggle"
]

bot = telegram.Bot(token=bot_token)

posted_urls_file = 'posted_urls.txt'

posted_urls = {}

def load_posted_urls():
    try:
        with open(posted_urls_file, 'r') as file:
            lines = file.read().splitlines()
            for line in lines:
                parts = line.split(',')
                if len(parts) == 2:
                    url, timestamp = parts
                    posted_urls[url] = float(timestamp)
    except FileNotFoundError:
        pass

def save_posted_urls():
    with open(posted_urls_file, 'w') as file:
        for url, timestamp in posted_urls.items():
            file.write(f"{url},{timestamp}\n")

load_posted_urls()

def extract_summary_and_date(website_url):
    try:
        article = newspaper.Article(website_url)
        article.download()
        article.parse()
        summary = article.text[:500] 
        date = article.publish_date.strftime('%d %b, %Y') if article.publish_date else ''

        return summary, date
    except Exception as e:
        print(f"Error extracting summary: {str(e)}")
        return "", ""

async def scrape_webpage(website_url):
    try:
        response = await asyncio.to_thread(requests.get, website_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        links = soup.find_all('a', href=True)

        current_time = time.time()

        for link in links:
            href = link['href']
            text = link.text.strip()

            for keyword in keywords:
                if keyword.lower() in text.lower():
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            href = website_url + href[1:]
                        else:
                            href = website_url + href

                    if href not in posted_urls or (current_time - posted_urls[href]) >= 60:
                        summary, date_posted = extract_summary_and_date(href)

                        if "grants" in keyword:
                            message = f"What to apply for\nSummary: '{summary}'\nDate: {date_posted}\n{href}"
                        elif "funding" in keyword:
                            message = f"Looking\nSummary: '{summary}'\nDate: {date_posted}\n{href}"
                        elif "fellowship" in keyword:
                            message = f"What do you wish for\nSummary: '{summary}'\nDate: {date_posted}\n{href}"

                        try:
                            await bot.send_message(chat_id=channel_id, text=message)
                            posted_urls[href] = current_time
                            time.sleep(60)
                        except Exception as e:
                            print(f"Error sending message to Telegram: {str(e)}")

    except Exception as e:
        print(f"Error scraping webpage {website_url}: {str(e)}")

import atexit
atexit.register(save_posted_urls)

async def main():
    for website_url in websites:
        await scrape_webpage(website_url)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
