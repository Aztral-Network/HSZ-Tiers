import sys
import os
import math
import numpy as np
from PIL import Image

OUTPUT_FILE = "output.png"
WIDTH = 256
HEIGHT = 256

# Simple isometric projection
def iso_project(x, y, z, scale=8, angle_y=-45, angle_x=15):
    angle_y = math.radians(angle_y)
    angle_x = math.radians(angle_x)

    # Rotate Y
    xz = x * math.cos(angle_y) - z * math.sin(angle_y)
    zz = x * math.sin(angle_y) + z * math.cos(angle_y)

    # Rotate X
    yz = y * math.cos(angle_x) - zz * math.sin(angle_x)
    zz2 = y * math.sin(angle_x) + zz * math.cos(angle_x)

    screen_x = xz * scale + WIDTH // 2
    screen_y = -yz * scale + HEIGHT // 2 + 40

    return int(screen_x), int(screen_y), zz2


def draw_face(base_img, face_img, cube_origin, face_type, shade):
    face_pixels = face_img.load()
    w, h = face_img.size

    for px in range(w):
        for py in range(h):
            r, g, b, a = face_pixels[px, py]
            if a == 0:
                continue

            if face_type == "front":
                x = cube_origin[0] + px
                y = cube_origin[1] + (h - py)
                z = cube_origin[2] + 8
            elif face_type == "side":
                x = cube_origin[0] + 8
                y = cube_origin[1] + (h - py)
                z = cube_origin[2] + px
            elif face_type == "top":
                x = cube_origin[0] + px
                y = cube_origin[1] + 8
                z = cube_origin[2] + (h - py)

            sx, sy, depth = iso_project(x, y, z)

            r = int(r * shade)
            g = int(g * shade)
            b = int(b * shade)

            base_img.putpixel((sx, sy), (r, g, b, a))


def render_skin(path):
    skin = Image.open(path).convert("RGBA")

    if skin.size != (64, 64):
        raise ValueError("Only 64x64 skins supported")

    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))

    # Extract head
    head_front = skin.crop((8, 8, 16, 16))
    head_side = skin.crop((0, 8, 8, 16))
    head_top = skin.crop((8, 0, 16, 8))

    # Extract body
    body_front = skin.crop((20, 20, 28, 32))
    body_side = skin.crop((16, 20, 20, 32))
    body_top = skin.crop((20, 16, 28, 20))

    # Head position
    head_origin = (0, 20, 0)

    draw_face(canvas, head_top, head_origin, "top", 1.0)
    draw_face(canvas, head_side, head_origin, "side", 0.85)
    draw_face(canvas, head_front, head_origin, "front", 0.95)

    # Body position
    body_origin = (0, 8, 0)

    draw_face(canvas, body_top, body_origin, "top", 1.0)
    draw_face(canvas, body_side, body_origin, "side", 0.85)
    draw_face(canvas, body_front, body_origin, "front", 0.95)

    canvas.save(OUTPUT_FILE)
    print(f"Saved render to {OUTPUT_FILE}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py {skin}")
        sys.exit(1)

    skin_path = sys.argv[1]

    if not os.path.exists(skin_path):
        print("Skin file not found.")
        sys.exit(1)

    render_skin(skin_path)
