from datetime import datetime
from app import db

class CrawlHistory(db.Model):
    """Model for storing crawl history."""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    instructions = db.Column(db.Text, nullable=True)
    result_summary = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CrawlHistory {self.url}>'
