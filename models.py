from datetime import datetime
import json
from app import db

class CrawlHistory(db.Model):
    """Model for storing crawl history."""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    instructions = db.Column(db.Text, nullable=True)
    result_summary = db.Column(db.String(200), nullable=True)
    # Add new column for storing the full result JSON
    result_data = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_result_data(self, result_dict):
        """Store the crawl result as JSON in the database."""
        if result_dict:
            self.result_data = json.dumps(result_dict)
    
    def get_result_data(self):
        """Retrieve the crawl result from JSON in the database."""
        if self.result_data:
            return json.loads(self.result_data)
        return None
    
    def __repr__(self):
        return f'<CrawlHistory {self.url}>'
