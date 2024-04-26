### Eksi Sozluk Live Feed

#### Overview
This Flask application provides a simple web interface to fetch and display the latest entries from Eksi Sozluk topics. It uses the `eksipy` library to interact with Eksi Sozluk's API and displays entries sorted by date in descending order. The application also features a dark mode toggle for user preference.

- **Live Demo:**
  A live demo of the application is available at [Eksi Live Feed Demo on Heroku](https://eksi-live-feed-cf249b9adec7.herokuapp.com/).

#### Prerequisites
- Python 3.6 or higher

#### Installation

1. **Clone the repository:**
   ```bash
   git clone git@github.com:cellamo/EksiLiveFeed.git
   cd EksiLiveFeed
   ```

2. **Set up a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies from `requirements.txt`:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

#### Usage

- **Access the application:**
  Open a web browser and navigate to `http://127.0.0.1:5000/`.

- **Using the interface:**
  - Enter a topic title in the input field.
  - Click the `Submit` button to fetch the latest entries.
  - Entries will be displayed in a list; newer entries appear at the top.
  - Click the `Toggle Dark Mode` button to switch between light and dark themes.

- **Automatic refresh:**
  After the initial fetch, the application will automatically refresh the entries every 3 seconds.

#### Files and Directories

- `app.py`: The main Python file containing Flask routes and logic for fetching Eksi Sozluk entries.
- `templates/`: Directory containing HTML files for the web interface.
- `index.html`: The HTML template for the application's front end.

#### Features

- Fetch and display entries from Eksi Sozluk based on user-specified topics.
- Entries are sorted by date in descending order.
- Automatic refreshing of entries every 3 seconds after the first fetch.
- Dark mode toggle for enhanced user experience.

#### Contributing

Contributions to this project are welcome. Please fork the repository, make your changes, and submit a pull request.

#### License

This project is licensed under the MIT License. See the LICENSE file for more details.
