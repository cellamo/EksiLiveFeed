# Eksi Sozluk Live Feed App

A web application that provides a live feed of entries from **Ekşi Sözlük**, allowing users to view the latest posts on trending topics in real-time.

## Features

- **Live Entry Feed**: Fetches and displays the latest entries for a selected topic from Ekşi Sözlük.
- **Trending Topics Sidebar**: Displays a list of current trending topics (Gündem Başlıkları) for quick access.
- **Responsive Design**: Optimized for both desktop and mobile devices.
- **Dark Mode**: Toggle between light and dark themes for better readability.

## Prerequisites

- **Python 3.6 or higher**
- **pip** package manager
- **Virtual Environment** *(recommended)*

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/cellamo/EksiLiveFeed.git
   ```

2. **Navigate to the project directory:**

   ```bash
   cd EksiLiveFeed
   ```

3. **Create a virtual environment** *(optional but recommended):*

   ```bash
   python -m venv venv
   ```

    3.1 **Activate the virtual environment:**
      - On **Windows:**

        ```bash
        venv\Scripts\activate
        ```

      - On **macOS** and **Linux:**

        ```bash
        source venv/bin/activate
        ```

4. **Install required packages:**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Run the application:**

   ```bash
   python api/index.py
   ```

   The server will start on `http://0.0.0.0:8000`.

2. **Access the application:**
   Open your web browser and navigate to `http://localhost:8000`.

3. **Explore Trending Topics**:
   - The sidebar displays the current trending topics (Gündem Başlıkları) from Ekşi Sözlük.
   - Click on any topic to see the live feed of entries related to that topic.

4. **Search for a Topic**:
   - Use the input field at the top to enter a topic title.
   - Click on **Submit** to start fetching live entries for the entered topic.

5. **Toggle Dark Mode**:
   - Click on the **"Toggle Dark Mode"** button to switch between light and dark themes.

## Project Structure

- `api/index.py`: The main Flask application that handles routes and server logic.
- `api/templates/index.html`: The HTML template for rendering the web page.

## Notes

- **Ekşi Sözlük Integration**: The application fetches data from Ekşi Sözlük using the **`eksipy`** library.
- **Updated Selectors**: Due to potential changes in the Ekşi Sözlük website structure, the **`UpdatedEksi`** class in **`index.py`** includes updated selectors to ensure data is fetched correctly.
- **Logging**: The application uses Python's logging module for error tracking and debugging.

## Troubleshooting

- **Fetching Errors**: If you encounter errors related to fetching topics or entries, it might be due to changes in the Ekşi Sözlük website structure or connectivity issues.
- **Error Messages**: Check the console output for any error logs to identify and resolve issues.
- **Dependencies**: Ensure all dependencies are installed correctly and are up to date.

## Disclaimer

This application uses the `eksipy` library to retrieve data from Ekşi Sözlük. I do not employ any scraping techniques or have any affiliation with Ekşi Sözlük. This is an independent project created for personal use only. I created this to read entries on topics during Galatasaray matches.

## License

This project is licensed under the MIT License.

---

Feel free to contribute to this project by submitting issues or pull requests.
