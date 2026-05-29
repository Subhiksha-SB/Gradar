import json
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Admin(db.Model):
    __tablename__ = "admins"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=True)
    created_at    = db.Column(db.DateTime, default=db.func.current_timestamp())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id":       self.id,
            "username": self.username,
            "email":    self.email,
        }

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
    grade         = db.Column(db.String(50), nullable=False, default="10")
    group         = db.Column(db.String(100), nullable=True)
    board         = db.Column(db.String(50), nullable=True, default="State Board")

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
            "grade":        self.grade,
            "group":        self.group,
            "board":        self.board or "State Board",
        }
