import os
import csv
import logging
from io import StringIO
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import urllib.parse

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create the database base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key-for-development")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the database
database_url = os.environ.get("DATABASE_URL")
# Fix potential "postgres://" to "postgresql://" for SQLAlchemy 1.4+
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///crawler.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

# Import routes after app initialization to avoid circular imports
from models import CrawlHistory
from crawler import crawl_website, validate_url

@app.route('/')
def index():
    """Render the main page with crawl history"""
    history = CrawlHistory.query.order_by(CrawlHistory.timestamp.desc()).limit(10).all()
    return render_template('index.html', history=history)

@app.route('/crawl', methods=['POST'])
def start_crawl():
    """Handle the crawl request from the form"""
    url = request.form.get('url', '').strip()
    instructions = request.form.get('instructions', '').strip()
    
    # Validate URL
    if not url:
        flash('Please enter a URL to crawl', 'danger')
        return redirect(url_for('index'))
    
    # Check if URL is valid
    if not validate_url(url):
        flash('Invalid URL format. Please provide a valid URL.', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Perform the crawl
        result = crawl_website(url, instructions)
        
        # Save to history with the full result data
        new_crawl = CrawlHistory(
            url=url,
            instructions=instructions,
            result_summary=f"Crawled {len(result['links'])} links, {len(result['text'].split())} words"
        )
        new_crawl.set_result_data(result)  # Store the full result as JSON
        db.session.add(new_crawl)
        db.session.commit()
        
        # Store only the ID in session, not the whole result
        session['crawl_id'] = new_crawl.id
        
        return redirect(url_for('results'))
    
    except Exception as e:
        logging.error(f"Error during crawl: {str(e)}")
        flash(f'Error during crawl: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/results')
def results():
    """Display the results of a crawl"""
    crawl_id = session.get('crawl_id')
    
    if not crawl_id:
        flash('No crawl results available. Please perform a crawl first.', 'warning')
        return redirect(url_for('index'))
    
    # Fetch the crawl history from the database
    crawl = CrawlHistory.query.get(crawl_id)
    
    if not crawl:
        flash('Crawl results not found. Please perform a new crawl.', 'warning')
        return redirect(url_for('index'))
    
    # Get the result data from the crawl history
    result = crawl.get_result_data()
    
    if not result:
        flash('Crawl result data is missing. Please perform a new crawl.', 'warning')
        return redirect(url_for('index'))
    
    return render_template('results.html', result=result, url=crawl.url, instructions=crawl.instructions, crawl_id=crawl_id)

@app.route('/results/<int:crawl_id>')
def view_crawl_result(crawl_id):
    """View a specific crawl result from history"""
    crawl = CrawlHistory.query.get_or_404(crawl_id)
    result = crawl.get_result_data()
    
    if not result:
        flash('Result data for this crawl is not available.', 'warning')
        return redirect(url_for('index'))
    
    return render_template('results.html', result=result, url=crawl.url, instructions=crawl.instructions, crawl_id=crawl_id)

@app.route('/export/<int:crawl_id>/<format>')
def export_crawl_result(crawl_id, format):
    """Export crawl results as CSV or JSON"""
    if format not in ['csv', 'json']:
        flash('Invalid export format. Please choose CSV or JSON.', 'danger')
        return redirect(url_for('index'))
    
    # Get the crawl data
    crawl = CrawlHistory.query.get_or_404(crawl_id)
    result = crawl.get_result_data()
    
    if not result:
        flash('Result data for this crawl is not available.', 'warning')
        return redirect(url_for('index'))
    
    if format == 'json':
        # For JSON, we can directly return the result data
        # Add timestamp and crawl ID to the export
        export_data = {
            'crawl_id': crawl_id,
            'crawl_timestamp': crawl.timestamp.strftime('%Y-%m-%d %H:%M:%S') if crawl.timestamp else datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'export_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'crawl_url': crawl.url,
            'crawl_instructions': crawl.instructions,
            'data': result
        }
        
        response = make_response(jsonify(export_data))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response.headers['Content-Disposition'] = f'attachment; filename=crawl_{crawl_id}_{timestamp}.json'
        response.headers['Content-Type'] = 'application/json'
        return response
    
    elif format == 'csv':
        # For CSV, we need to convert the data structure to a flat format
        csv_data = StringIO()
        writer = csv.writer(csv_data)
        
        # Write crawl information
        writer.writerow(['Crawl Information'])
        writer.writerow(['URL', crawl.url])
        writer.writerow(['Date', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(['Instructions', crawl.instructions or 'None'])
        
        # Site metadata section
        writer.writerow([''])
        writer.writerow(['Site Metadata'])
        writer.writerow(['Title', result.get('metadata', {}).get('title', 'No Title')])
        writer.writerow(['Description', result.get('metadata', {}).get('description', 'No Description')])
        if 'metadata' in result and 'keywords' in result['metadata']:
            writer.writerow(['Keywords', ', '.join(result['metadata'].get('keywords', []))])
        
        # Crawl statistics section
        writer.writerow([''])
        writer.writerow(['Crawl Statistics'])
        writer.writerow(['Pages Crawled', result.get('metadata', {}).get('pages_crawled', 0)])
        writer.writerow(['Total Links', len(result.get('links', []))])
        writer.writerow(['Text Length (characters)', len(result.get('text', ''))])
        writer.writerow(['Text Length (words)', len(result.get('text', '').split())])
        writer.writerow(['Crawl Time (seconds)', result.get('metadata', {}).get('crawl_time', 0)])
        
        # Links section
        writer.writerow([''])
        writer.writerow(['Links Discovered'])
        writer.writerow(['URL', 'Link Text', 'Depth', 'Type', 'Status'])
        
        for link in result.get('links', []):
            writer.writerow([
                link.get('url', ''),
                link.get('text', '').replace('\n', ' ').strip(),
                link.get('depth', ''),
                link.get('type', 'link'),
                link.get('status', '')
            ])
        
        # Page data section if available
        if 'page_data' in result and result['page_data']:
            writer.writerow([''])
            writer.writerow(['Pages Content'])
            writer.writerow(['URL', 'Title', 'Depth', 'Text Sample'])
            
            for page in result.get('page_data', []):
                text_sample = page.get('text_sample', '')
                if text_sample:
                    # Clean up text sample for CSV
                    text_sample = text_sample.replace('\n', ' ').replace('\r', '').strip()
                    if len(text_sample) > 200:
                        text_sample = text_sample[:197] + '...'
                
                writer.writerow([
                    page.get('url', ''),
                    page.get('title', 'No Title'),
                    page.get('depth', 0),
                    text_sample
                ])
        
        # Create response
        response = make_response(csv_data.getvalue())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        response.headers['Content-Disposition'] = f'attachment; filename=crawl_{crawl_id}_{timestamp}.csv'
        response.headers['Content-Type'] = 'text/csv'
        return response

@app.route('/api/check-url', methods=['POST'])
def check_url():
    """API endpoint to validate URL format"""
    data = request.get_json()
    url = data.get('url', '')
    
    is_valid = validate_url(url)
    return jsonify({'valid': is_valid})

# Create or update database tables
with app.app_context():
    # We need to drop and recreate the table to add the new column
    # Only do this in development, in production you'd use migrations
    db.drop_all()
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
