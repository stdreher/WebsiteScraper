import os
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
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
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///crawler.db")
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
        
        # Save to history
        new_crawl = CrawlHistory(
            url=url,
            instructions=instructions,
            result_summary=f"Crawled {len(result['links'])} links, {len(result['text'].split())} words"
        )
        db.session.add(new_crawl)
        db.session.commit()
        
        # Store result in session for display
        session['crawl_result'] = result
        session['crawled_url'] = url
        session['crawl_instructions'] = instructions
        
        return redirect(url_for('results'))
    
    except Exception as e:
        logging.error(f"Error during crawl: {str(e)}")
        flash(f'Error during crawl: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/results')
def results():
    """Display the results of a crawl"""
    result = session.get('crawl_result')
    url = session.get('crawled_url')
    instructions = session.get('crawl_instructions')
    
    if not result:
        flash('No crawl results available. Please perform a crawl first.', 'warning')
        return redirect(url_for('index'))
    
    return render_template('results.html', result=result, url=url, instructions=instructions)

@app.route('/api/check-url', methods=['POST'])
def check_url():
    """API endpoint to validate URL format"""
    data = request.get_json()
    url = data.get('url', '')
    
    is_valid = validate_url(url)
    return jsonify({'valid': is_valid})

# Create database tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
