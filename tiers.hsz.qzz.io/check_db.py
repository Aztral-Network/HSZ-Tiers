from app import app
from models import db, Player

with app.app_context():
    players = Player.query.all()
    for p in players:
        print(f"Name: {p.name}, Tier: {p.tier}, Skin Path: {p.skin_path}")
