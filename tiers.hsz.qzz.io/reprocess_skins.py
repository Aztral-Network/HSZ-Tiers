import sqlite3
import os
from utils import render_body

# Configuration
DB_PATH = 'instance/hsz_tiers.db' if os.path.exists('instance/hsz_tiers.db') else 'hsz_tiers.db'
SKINS_DIR = 'static/skins'

def reprocess():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Fetch all players who have a skin path
        cursor.execute("SELECT name, skin_path, model_type FROM player WHERE skin_path IS NOT NULL")
        players = cursor.fetchall()
        
        if not players:
            print("No players with skins found in database.")
            return

        for name, skin_filename, model_type in players:
            skin_path = os.path.join(SKINS_DIR, skin_filename)
            body_path = os.path.join(SKINS_DIR, f"{name}_body.png")
            
            if os.path.exists(skin_path):
                print(f"[*] Rendering isometric body for: {name} ({model_type})")
                try:
                    render_body(skin_path, body_path, model_type=model_type)
                    print(f"    [+] Saved to {body_path}")
                except Exception as e:
                    print(f"    [!] Error rendering {name}: {e}")
            else:
                print(f"[-] Skin file missing for {name}: {skin_path}")
                
        conn.close()
        print("\nFinished reprocessing all skins.")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    reprocess()
