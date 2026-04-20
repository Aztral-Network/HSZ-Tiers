from flask import Flask, render_template, request, redirect, url_for, session
from models import db, Player
import subprocess
import sys
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hsz_tiers.db'
app.config['SECRET_KEY'] = 'public-secret-key-12345'
app.config['SESSION_TYPE'] = 'filesystem'

db.init_app(app)

with app.app_context():
    db.create_all()

@app.context_processor
def inject_translations():
    lang = session.get('lang', 'es')
    translations = {
        'es': {
            'overall': 'Global',
            'banned': 'Baneados',
            'search': 'Buscar jugadores...',
            'no_players': 'No se encontraron jugadores.',
            'rank': 'Rango',
            'player': 'Jugador',
            'region': 'Región',
            'tier': 'Tier',
            'reason': 'Razón',
            'server_ip': 'IP del Servidor',
            'banned_players': 'JUGADORES BANEADOS',
            'disclaimer': 'Si conoces alguno mas W10, entra a nuestro discord y dilo',
            'untested': 'No testeado'
        },
        'pt': {
            'overall': 'Global',
            'banned': 'Banidos',
            'search': 'Buscar jogadores...',
            'no_players': 'Nenhum jogador encontrado.',
            'rank': 'Rank',
            'player': 'Jogador',
            'region': 'Região',
            'tier': 'Tier',
            'reason': 'Motivo',
            'server_ip': 'IP do Servidor',
            'banned_players': 'JOGADORES BANIDOS',
            'disclaimer': 'Se você conhece mais algum W10, entre no nosso discord e diga-o',
            'untested': 'Não testado'
        }
    }
    return {'t': translations.get(lang, translations['es']), 'current_lang': lang}

@app.route('/set_lang/<lang>')
def set_lang(lang):
    if lang in ['es', 'pt']:
        session['lang'] = lang
        session.modified = True
    return redirect(request.referrer or url_for('index'))

@app.route('/')
def index():
    players = Player.query.filter_by(is_banned=False).order_by(Player.overall_rank.asc()).all()
    return render_template('index.html', players=players, active_tab='home')

@app.route('/banned')
def banned():
    banned_players = Player.query.filter_by(is_banned=True).all()
    return render_template('banned.html', players=banned_players, active_tab='banned')

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print("Starting admin panel (Port 5001)...")
        subprocess.Popen([sys.executable, 'admin.py'])
    
    app.run(host='0.0.0.0',port=9137, debug=True)
