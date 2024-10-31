from datetime import datetime, timezone
import hashlib
from flask import Flask, render_template, request, jsonify
import asyncio
from eksipy import Eksi, Entry, User, Topic
from typing import List
from dataclasses import dataclass
import logging
from waitress import serve  # Import Waitress
from flask_caching import Cache
import time
from functools import wraps
import psutil
import os
from datetime import datetime

app = Flask(__name__)

# Configure caching
app.config['CACHE_TYPE'] = 'simple'  # Simple in-memory cache
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes
cache = Cache(app)

# Initialize cache metrics
cache_hits = 0
cache_misses = 0

def generate_cache_key(func, args, kwargs):
    key = func.__name__
    key += ":" + ",".join(map(str, args))
    key += ":" + ",".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    # Use hashlib to ensure the key is a valid format
    return hashlib.md5(key.encode('utf-8')).hexdigest()

def cache_metrics(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        global cache_hits, cache_misses
        cache_key = generate_cache_key(func, args, kwargs)
        cached_response = cache.get(cache_key)
        if cached_response is not None:
            cache_hits += 1
            total = cache_hits + cache_misses
            hit_rate = (cache_hits / total) * 100 if total > 0 else 0
            cache_logger.info(f"Cache hit - Key: {cache_key}, Hit Rate: {hit_rate:.2f}%")
            return cached_response
        else:
            cache_misses += 1
            total = cache_hits + cache_misses
            miss_rate = (cache_misses / total) * 100 if total > 0 else 0
            cache_logger.info(f"Cache miss - Key: {cache_key}, Miss Rate: {miss_rate:.2f}%")
            response = func(*args, **kwargs)
            cache.set(cache_key, response, timeout=300)
            return response
    return wrapper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

cache_logger = logging.getLogger('cache_metrics')
cache_logger.setLevel(logging.INFO)

os.makedirs('logs', exist_ok=True)

cache_handler = logging.FileHandler('logs/cache_metrics.log')
cache_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
cache_logger.addHandler(cache_handler)

def time_ago(date):
    now = datetime.now(timezone.utc)
    diff = now - date
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        return f"{int(seconds / 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds / 3600)} hours ago"
    else:
        return f"{int(seconds / 86400)} days ago"

@dataclass
class Topic:
    id: int
    title: str

class UpdatedEksi(Eksi):
    async def gundem(self, page=1) -> List[Topic]:
        """Fetch the Gündem feed with updated selectors."""
        try:
            gundem_response = await self.session.get(
                f'{self.eksi}basliklar/gundem?p={page}'
            )
            # Update the CSS selector based on the current website structure
            # The `ul` with class `topic-list partial` contains the topics
            topics_container = gundem_response.html.find('ul.topic-list.partial', first=True)
            
            if not topics_container:
                logger.error("Failed to find the topics container with the updated selector.")
                return []
            
            topics = topics_container.find("li > a")
            if not topics:
                logger.error("No topics found with the updated selector.")
                return []
            
            basliklar = []
            for topic in topics:
                href = topic.attrs.get("href", "")
                if "?a=" in href:
                    try:
                        # Extract topic ID from the href
                        topic_id = int(href.split('?a=')[0].split('--')[1])
                        baslik = topic.text.strip()
                        
                        # Remove the last word after the final whitespace
                        if ' ' in baslik:
                            baslik = ' '.join(baslik.split(' ')[:-1])
                        
                        basliklar.append(Topic(id=topic_id, title=baslik))
                    except (IndexError, ValueError) as e:
                        logger.warning(f"Error parsing topic: {e}")
                        continue
            return basliklar
        except Exception as e:
            logger.error(f"An error occurred while fetching gundem: {e}")
            return []
        
    async def getEntrys(self, baslik: Topic, page=1, day=None, sukela=None) -> List[Entry]:
        url = await baslik.getUrl()
        url = self.addParamsToUrl(url, {"p": page})
        if day is not None:
            url = self.addParamsToUrl(url, {"day": day})
        if sukela is not None:
            url = self.addParamsToUrl(url, {"a": sukela})

        topic = await self.session.get(url)
        topic = topic.html.find("#topic", first=True)
        entrys = topic.find("#entry-item-list", first=True).find("li")
        giriler = []

        for entry in entrys:
            # Ensure you correctly select the date element
            date_element = entry.find("footer div.info a.entry-date.permalink", first=True)
            date_str = date_element.text.strip() if date_element else ""

            # Convert the date string if it exists
            duzenleme, tarih = self.convertToDate(date_str) if date_str else (None, None)

            giriler.append(
                Entry(
                    self,
                    id=entry.attrs['data-id'],
                    author=User(
                        self,
                        id=entry.attrs['data-author-id'], 
                        nick=entry.attrs['data-author']
                    ),
                    entry=entry.pq(".content"),
                    topic=baslik,
                    date=tarih,
                    edited=duzenleme,
                    fav_count=entry.attrs['data-favorite-count'],
                    comment=entry.attrs['data-comment-count'],
                )
            )
        
        return giriler

@cache_metrics
def get_gundem(page=1):
    logger.info("Fetching gundem_topics from cache or source.")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    eksi = UpdatedEksi()
    topics = loop.run_until_complete(eksi.gundem(page))
    loop.close()
    logger.info("Successfully fetched gundem_topics.")
    return topics

@cache_metrics
def get_entries(topic_title):
    logger.info(f"Fetching entries for topic: {topic_title}")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    eksi = UpdatedEksi()
    try:
        topic = loop.run_until_complete(eksi.getTopic(topic_title))
        max_page = topic.max_page
        entries = loop.run_until_complete(eksi.getEntrys(topic, page=max_page))
        
        if entries:
            sorted_entries = sorted(entries, key=lambda entry: entry.date or 0, reverse=True)
            entry_data = [
                {
                    'text': entry.text(),
                    'author': entry.author.nick,
                    'timestamp': datetime.fromtimestamp(entry.date, timezone.utc).isoformat() if entry.date else None
                }
                for entry in sorted_entries
            ]
            logger.info(f"Fetched {len(entry_data)} entries for topic: {topic_title}")
            return entry_data
        else:
            return []
    except Exception as e:
        logger.error(f"Error fetching entries for topic '{topic_title}': {e}")
        raise e
    finally:
        loop.close()

@app.route('/')
def index():
    try:
        gundem_topics = get_gundem()
        return render_template('index.html', gundem_topics=gundem_topics)
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return render_template('index.html', gundem_topics=[])

@app.route('/get_entries', methods=['GET'])
def get_entries_route():
    start_time = time.time()
    topic_title = request.args.get('topic_title', '').strip()
    if not topic_title:
        logger.warning("No topic_title provided in /get_entries request.")
        return jsonify({"error": "No topic_title provided."}), 400
    
    try:
        entry_data = get_entries(topic_title)
        if entry_data:
            response = jsonify({"entries": entry_data})
        else:
            response = jsonify({"entries": []})
    
    except Exception as e:
        logger.error(f"Error fetching entries for topic '{topic_title}': {e}")
        response = jsonify({"error": "Failed to fetch entries."}), 500

    duration = time.time() - start_time
    logger.info(f"/get_entries processed in {duration:.2f} seconds.")
    return response

@app.route('/cache_metrics')
def cache_metrics_route():
    total = cache_hits + cache_misses
    hit_rate = (cache_hits / total) * 100 if total > 0 else 0
    miss_rate = (cache_misses / total) * 100 if total > 0 else 0
    logger.info(f"Cache Metrics - Hits: {cache_hits}, Misses: {cache_misses}, Hit Rate: {hit_rate:.2f}%, Miss Rate: {miss_rate:.2f}%")
    return jsonify({
        'cache_hits': cache_hits,
        'cache_misses': cache_misses,
        'hit_rate_percent': hit_rate,
        'miss_rate_percent': miss_rate
    })

@app.route('/resource_metrics')
def resource_metrics_route():
    process = psutil.Process()
    mem = process.memory_info().rss / (1024 * 1024)  # Memory usage in MB
    cpu = process.cpu_percent(interval=1)  # CPU usage percentage
    return jsonify({
        'cpu_percent': cpu,
        'memory_mb': mem
    })

if __name__ == '__main__':
    # Use Waitress to serve the app
    serve(app, host='0.0.0.0', port=8000)
