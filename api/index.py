from flask import Flask, render_template, request, jsonify
import asyncio
from eksipy import Eksi
from typing import List

app = Flask(__name__)

from dataclasses import dataclass

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
                print("Failed to find the topics container with the updated selector.")
                return []
            
            topics = topics_container.find("li > a")
            if not topics:
                print("No topics found with the updated selector.")
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
                        print(f"Error parsing topic: {e}")
                        continue
            return basliklar
        except Exception as e:
            print(f"An error occurred while fetching gundem: {e}")
            return []

@app.route('/')
def index():
    async def fetch_gundem():
        eksi = UpdatedEksi()
        topics = await eksi.gundem()
        return topics

    # Handle event loop safely
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    gundem_topics = loop.run_until_complete(fetch_gundem())

    return render_template('index.html', gundem_topics=gundem_topics)


@app.route('/get_entries', methods=['GET'])
def get_entries():
    topic_title = request.args.get('topic_title')
    async def fetch_entries():
        eksi = Eksi()
        topic = await eksi.getTopic(topic_title)
        max_page = topic.max_page
        entries = await eksi.getEntrys(topic, page=max_page)
        
        if entries:
            sorted_entries = sorted(entries, key=lambda entry: entry.date, reverse=True)
            entry_texts = [entry.text() for entry in sorted_entries]
            return entry_texts
        else:
            return []
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        entry_texts = loop.run_until_complete(fetch_entries())
        return jsonify({"entries": entry_texts})
    except Exception as e:
        # Log the exception details (optional)
        print(f"Error fetching entries: {e}")
        # Return a JSON response with the error message and a 404 status code
        return jsonify({"error": str(e)}), 404

if __name__ == '__main__':
    app.run(debug=True)
