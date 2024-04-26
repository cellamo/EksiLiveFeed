from flask import Flask, render_template, request, jsonify
import asyncio
from eksipy import Eksi

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_entries', methods=['POST'])
def get_entries():
    topic_title = request.form['topic_title']
    
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
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    entry_texts = loop.run_until_complete(fetch_entries())
    
    return jsonify(entry_texts)

if __name__ == '__main__':
    app.run(debug=True)
