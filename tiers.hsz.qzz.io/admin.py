from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, Player
from utils import extract_head, render_body
import os
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hsz_tiers.db'
app.config['SECRET_KEY'] = 'admin-secret-key'
app.config['UPLOAD_FOLDER'] = 'static/skins'

db.init_app(app)

with app.app_context():
    db.create_all()

def process_skin(name, skin_file, model_type="steve"):
    if skin_file and skin_file.filename != '':
        skin_filename = f"{name}.png"
        skin_path = os.path.join(app.config['UPLOAD_FOLDER'], skin_filename)
        skin_file.save(skin_path)
        
        # Legacy head
        head_filename = f"{name}_head.png"
        head_path = os.path.join(app.config['UPLOAD_FOLDER'], head_filename)
        extract_head(skin_path, head_path)
        
        # New Isometric Body
        body_filename = f"{name}_body.png"
        body_path = os.path.join(app.config['UPLOAD_FOLDER'], body_filename)
        render_body(skin_path, body_path, model_type=model_type)
        
        return skin_filename
    return None

# Translations for static export (Defaulting to Spanish)
EXPORT_TRANSLATIONS = {
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
    }
}

@app.route('/save_static')
def save_static():
    players = Player.query.filter_by(is_banned=False).order_by(Player.overall_rank.asc()).all()
    # We render the public template with Spanish context
    rendered_html = render_template('index.html', 
                                    players=players, 
                                    active_tab='home', 
                                    t=EXPORT_TRANSLATIONS['es'],
                                    current_lang='es')
    
    date_str = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    filename = f"html-{date_str}.html"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(rendered_html)
    
    flash(f'State saved to {filename} successfully!')
    return redirect(url_for('index'))

@app.route('/')
def index():
    players = Player.query.all()
    return render_template('admin_index.html', players=players)

@app.route('/add', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        name = request.form['name']
        region = request.form['region']
        tier = request.form['tier']
        overall_rank = request.form['overall_rank']
        is_untested = 'is_untested' in request.form
        note = request.form.get('note', '') if 'has_note' in request.form else None
        model_type = request.form.get('model_type', 'steve')
        
        skin_file = request.files.get('skin')
        skin_filename = process_skin(name, skin_file, model_type=model_type)
            
        new_player = Player(
            name=name,
            skin_path=skin_filename,
            region=region,
            tier=tier,
            overall_rank=int(overall_rank),
            is_untested=is_untested,
            note=note,
            model_type=model_type
        )
        db.session.add(new_player)
        db.session.commit()
        flash('Player added successfully!')
        return redirect(url_for('index'))
            
    return render_template('admin_form.html', player=None)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_player(id):
    player = Player.query.get_or_404(id)
    if request.method == 'POST':
        player.name = request.form['name']
        player.region = request.form['region']
        player.tier = request.form['tier']
        player.overall_rank = int(request.form['overall_rank'])
        player.is_untested = 'is_untested' in request.form
        player.note = request.form.get('note', '') if 'has_note' in request.form else None
        
        old_model_type = player.model_type
        player.model_type = request.form.get('model_type', 'steve')
        
        skin_file = request.files.get('skin')
        
        # If model type changed but skin didn't, we still need to re-render
        if skin_file and skin_file.filename != '':
            skin_filename = process_skin(player.name, skin_file, model_type=player.model_type)
            if skin_filename:
                player.skin_path = skin_filename
        elif old_model_type != player.model_type and player.skin_path:
            # Re-render with existing skin but new model type
            skin_path = os.path.join(app.config['UPLOAD_FOLDER'], player.skin_path)
            body_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{player.name}_body.png")
            if os.path.exists(skin_path):
                render_body(skin_path, body_path, model_type=player.model_type)
            
        db.session.commit()
        flash('Player updated successfully!')
        return redirect(url_for('index'))
    return render_template('admin_form.html', player=player)

@app.route('/delete/<int:id>')
def delete_player(id):
    player = Player.query.get_or_404(id)
    db.session.delete(player)
    db.session.commit()
    flash('Player deleted!')
    return redirect(url_for('index'))

@app.route('/ban/<int:id>', methods=['POST'])
def ban_player(id):
    player = Player.query.get_or_404(id)
    reason = request.form.get('reason', 'No reason provided')
    player.is_banned = True
    player.ban_reason = reason
    db.session.commit()
    flash('Player banned!')
    return redirect(url_for('index'))

@app.route('/unban/<int:id>')
def unban_player(id):
    player = Player.query.get_or_404(id)
    player.is_banned = False
    player.ban_reason = None
    db.session.commit()
    flash('Player unbanned!')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9733, debug=True)
