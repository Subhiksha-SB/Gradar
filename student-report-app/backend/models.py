import json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    __tablename__ = "students"

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    parent_email  = db.Column(db.String(150), nullable=False)
    _marks        = db.Column("marks", db.Text, nullable=False)   # stored as JSON
    total         = db.Column(db.Float, nullable=False)
    average       = db.Column(db.Float, nullable=False)
    rank          = db.Column(db.Integer, nullable=True)
    email_sent    = db.Column(db.Boolean, default=False)

    # ------- marks property (serialize / deserialize) -------
    @property
    def marks(self):
        return json.loads(self._marks)

    @marks.setter
    def marks(self, value):
        self._marks = json.dumps(value)

    def to_dict(self):
        return {
            "id":           self.id,
            "name":         self.name,
            "parent_email": self.parent_email,
            "marks":        self.marks,
            "total":        self.total,
            "average":      round(self.average, 2),
            "rank":         self.rank,
            "email_sent":   self.email_sent,
        }
