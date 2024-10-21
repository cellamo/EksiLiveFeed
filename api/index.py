from flask import Flask, render_template, request, jsonify
import asyncio
from eksipy import Eksi
from typing import List
from dataclasses import dataclass
from functools import lru_cache
import logging
from waitress import serve  # Import Waitress

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Caching fetched Gundem topics for 60 seconds
@lru_cache(maxsize=1)
def get_cached_gundem(page=1):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    eksi = UpdatedEksi()
    topics = loop.run_until_complete(eksi.gundem(page))
    loop.close()
    return topics

# Caching fetched entries for each topic_title for 60 seconds
@lru_cache(maxsize=128)
def get_cached_entries(topic_title):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    eksi = Eksi()
    try:
        topic = loop.run_until_complete(eksi.getTopic(topic_title))
        max_page = topic.max_page
        entries = loop.run_until_complete(eksi.getEntrys(topic, page=max_page))
        
        if entries:
            sorted_entries = sorted(entries, key=lambda entry: entry.date, reverse=True)
            entry_texts = [entry.text() for entry in sorted_entries]
            return entry_texts
        else:
            return []
    except Exception as e:
        logger.error(f"Error fetching entries for topic '{topic_title}': {e}")
        raise e  # Re-raise the exception to be handled in the route
    finally:
        loop.close()

@app.route('/')
def index():
    try:
        gundem_topics = get_cached_gundem()
        return render_template('index.html', gundem_topics=gundem_topics)
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return render_template('index.html', gundem_topics=[])

@app.route('/get_entries', methods=['GET'])
def get_entries():
    topic_title = request.args.get('topic_title')
    if not topic_title:
        logger.warning("No topic_title provided in /get_entries request.")
        return jsonify({"error": "No topic_title provided."}), 400
    
    try:
        entry_texts = get_cached_entries(topic_title)
        if entry_texts:
            return jsonify({"entries": entry_texts})
        else:
            return jsonify({"entries": []})

    except Exception as e:
        logger.error(f"Error fetching entries for topic '{topic_title}': {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Use Waitress to serve the app
    serve(app, host='0.0.0.0', port=8000)
