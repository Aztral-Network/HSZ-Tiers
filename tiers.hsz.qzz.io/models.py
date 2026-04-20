from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    skin_path = db.Column(db.String(255), nullable=True)
    region = db.Column(db.String(10), nullable=False)
    tier = db.Column(db.String(10), default="None")
    overall_rank = db.Column(db.Integer, default=0)
    is_untested = db.Column(db.Boolean, default=False)
    note = db.Column(db.String(255), nullable=True)
    model_type = db.Column(db.String(10), default="steve") # steve or alex
    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<Player {self.name}>'
