# Web Crawler Application

A powerful Flask-based website crawler that allows you to extract and analyze content from websites with custom instructions.

## Features

- **Website Crawling**: Input any URL and extract structured content including text, links, and metadata
- **Custom Instructions**: Provide specific instructions to tailor the crawling process to your needs
- **Depth Control**: Configure how deep the crawler should go into linked pages
- **Crawl History**: Keep track of your previous crawls and easily access results
- **Structured Results**: View and analyze crawled content in a clean, structured format
- **Export Options**: Download crawl results as CSV or JSON for further analysis or integration

## Tech Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **UI**: Bootstrap CSS with dark theme
- **Text Extraction**: Trafilatura
- **HTML Parsing**: BeautifulSoup4

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd web-crawler
   ```

2. Install dependencies:
   ```
   pip install beautifulsoup4 email-validator flask flask-sqlalchemy gunicorn psycopg2-binary requests sqlalchemy trafilatura werkzeug
   ```

3. Set up environment variables:
   ```
   export DATABASE_URL=postgresql://username:password@localhost/dbname
   export FLASK_SECRET_KEY=your_secret_key
   ```

4. Initialize the database:
   ```
   flask db upgrade
   ```

5. Run the application:
   ```
   python main.py
   ```

6. Visit `http://localhost:5000` in your browser

## Using the Crawler

1. **Enter a URL**: Provide the website URL you want to crawl
2. **Add Instructions** (Optional): Specify any custom instructions for the crawl
3. **Submit**: Click "Start Crawling" to begin the process
4. **View Results**: Analyze the structured results including extracted text, links, and metadata
5. **Access History**: View and revisit previous crawls from the history section
6. **Export Data**: Download crawl results in CSV or JSON format for further analysis

### Export Formats

- **CSV Export**: Provides a well-structured, human-readable format with multiple sections:
  - Crawl Information (URL, Date, Instructions)
  - Site Metadata (Title, Description, Keywords)
  - Crawl Statistics (Pages, Links, Text Length, Crawl Time)
  - Links Discovered (URL, Text, Depth, Type, Status)
  - Pages Content (URL, Title, Depth, Text Sample)

- **JSON Export**: Provides the complete raw data structure with all crawled information, ideal for programmatic access and integration with other systems

## Project Structure

- `main.py`: Entry point for the application
- `app.py`: Core Flask application setup with routes and database initialization
- `models.py`: Database models for storing crawl data
- `crawler.py`: Implementation of the web crawling functionality
- `templates/`: HTML templates for the web interface
  - `layout.html`: Base template with common elements
  - `index.html`: Main page with crawl form and history
  - `results.html`: Detailed results display
- `static/`: Static assets like CSS and JavaScript
  - `css/custom.css`: Custom styling for the application
  - `js/main.js`: Client-side functionality

## API Endpoints

- `GET /`: Main page with crawl form and history
- `POST /crawl`: Submit a URL and instructions for crawling
- `GET /results`: View results of the most recent crawl
- `GET /results/<crawl_id>`: View results of a specific crawl by ID
- `GET /export/<crawl_id>/json`: Download crawl results as JSON file
- `GET /export/<crawl_id>/csv`: Download crawl results as CSV file
- `POST /api/check-url`: API endpoint to validate URL format

## Tips for Effective Crawling

- Be specific with your URLs - include the full path for more targeted results
- Use custom instructions to tailor the crawl to your needs
- For large websites, limit the depth and number of pages
- Some websites may block or limit crawling - respect their terms of service
- For better text extraction, include specific instructions

## Responsible Crawling

The crawler implements several features to ensure responsible web crawling:
- Respects robots.txt rules
- Implements rate limiting to avoid overloading target websites
- Keeps track of visited URLs to avoid duplicate requests
- Properly identifies itself with user-agent headers

## Database Structure

The application uses a PostgreSQL database with the following main table:

- `crawl_history`: Stores information about crawls with the following columns:
  - `id`: Unique identifier for each crawl
  - `url`: The URL that was crawled
  - `instructions`: Custom instructions provided for the crawl
  - `result_summary`: Brief summary of crawl results (number of links, word count)
  - `result_data`: Complete crawl results stored as JSON
  - `timestamp`: When the crawl was performed

The application uses database storage instead of session cookies for crawl results, which allows for:
- Persistence of large crawl results
- History tracking
- Sharing of results via URLs
- Improved performance with large datasets

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.