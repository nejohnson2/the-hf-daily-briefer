import json
from datetime import datetime, timezone

from extensions import db


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    item_name = db.Column(db.String(500), nullable=False)
    item_type = db.Column(db.String(10), nullable=False)  # "model" or "dataset"
    summary = db.Column(db.Text, nullable=False)
    ideas = db.Column(db.Text, nullable=False)  # JSON array of strings
    metadata_json = db.Column("metadata", db.Text)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    @property
    def ideas_list(self):
        return json.loads(self.ideas)

    def __repr__(self):
        return f"<Report {self.id}: {self.title}>"
