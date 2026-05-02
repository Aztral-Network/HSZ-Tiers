#!/usr/bin/env python3
"""Simple skin renderer - renders Minecraft skins to head or 3D views"""
import sys
from PIL import Image, ImageDraw
import numpy as np

def extract_head(skin_path, output_path):
    """Extract head from skin and save as PNG"""
    with Image.open(skin_path) as img:
        img = img.convert("RGBA")
        head_base = img.crop((8, 8, 16, 16))
        head_outer = img.crop((40, 8, 48, 16))
        head_combined = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        head_combined.paste(head_base, (0, 0))
        head_combined.paste(head_outer, (0, 0), head_outer)
        head_final = head_combined.resize((128, 128), Image.NEAREST)
        head_final.save(output_path)
        print(f"Head saved to {output_path}")

class SkinRenderer:
    def __init__(self, skin_path, model_type=None):
        self.skin = Image.open(skin_path).convert("RGBA")
        self.width, self.height = self.skin.size
        
        if model_type:
            self.is_slim = (model_type == "alex")
        else:
            self.is_slim = self._check_slim()
        
        self.y_rot = np.radians(-45)
        self.x_rot = np.radians(15)
        self.scale = 16
        self.canvas_size = (300, 400)
        self.offset = (150, 180)

    def _check_slim(self):
        """Detect if the skin uses the slim (Alex) model"""
        if self.height == 32: return False
        pixel = self.skin.getpixel((54, 20))
        return pixel[3] == 0

    def get_uv(self, part, face, layer="base"):
        """Returns (x1, y1, x2, y2) for the given face"""
        mapping = {
            "head": {"base": (8, 8), "outer": (40, 8), "size": (8, 8, 8)},
            "torso": {"base": (20, 20), "outer": (20, 36), "size": (8, 12, 4)},
            "right_arm": {"base": (44, 20), "outer": (44, 36), "size": (4 if not self.is_slim else 3, 12, 4)},
            "left_arm": {"base": (36, 52), "outer": (52, 52), "size": (4 if not self.is_slim else 3, 12, 4)}
        }
        
        info = mapping[part]
        start_x, start_y = info[layer]
        w, h, d = info["size"]
        
        faces = {
            "top": (start_x, start_y - d, start_x + w, start_y),
            "bottom": (start_x + w, start_y - d, start_x + 2*w, start_y),
            "right": (start_x - d, start_y, start_x, start_y + h),
            "front": (start_x, start_y, start_x + w, start_y + h),
            "left": (start_x + w, start_y, start_x + w + d, start_y + h),
            "back": (start_x + w + d, start_y, start_x + 2*w + d, start_y + h)
        }
        return faces[face]

    def project(self, x, y, z):
        """Project 3D point to 2D screen coordinates"""
        x_rot = x * np.cos(self.y_rot) + z * np.sin(self.y_rot)
        z_rot = -x * np.sin(self.y_rot) + z * np.cos(self.y_rot)
        y_rot = y * np.cos(self.x_rot) - z_rot * np.sin(self.x_rot)
        z_final = y * np.sin(self.x_rot) + z_rot * np.cos(self.x_rot)
        
        return (x_rot * self.scale + self.offset[0], 
                y_rot * self.scale + self.offset[1], 
                z_final)

    def render(self, output_path):
        canvas = Image.new("RGBA", self.canvas_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        
        arm_w = 4 if not self.is_slim else 3
        parts = [
            ("right_arm", -4 - arm_w, 0, -2, 5),
            ("head", -4, -8, -4, 0),
            ("torso", -4, 0, -2, 0),
            ("left_arm", 4, 0, -2, -5)
        ]
        
        for part, ox, oy, oz, angle in parts:
            info = {"head": (8, 8, 8), "torso": (8, 12, 4), "right_arm": (arm_w, 12, 4), "left_arm": (arm_w, 12, 4)}[part]
            w, h, d = info
            active_faces = ["top", "bottom", "front", "right"]
            
            for layer in ["base", "outer"]:
                for face in active_faces:
                    uv = self.get_uv(part, face, layer)
                    face_img = self.skin.crop(uv)
                    
                    shading = 1.0
                    if face == "front": shading = 0.85
                    elif face in ["left", "right"]: shading = 0.7
                    elif face == "bottom": shading = 0.5
                    
                    expansion = 0.35 if layer == "outer" else 0.0
                    
                    fw, fh = face_img.size
                    for fx in range(fw):
                        for fy in range(fh):
                            color = face_img.getpixel((fx, fy))
                            if color[3] == 0: continue
                            
                            color = (int(color[0]*shading), int(color[1]*shading), int(color[2]*shading), color[3])
                            
                            def get_v(vrx, vry, vrz, face=face, expansion=expansion, angle=angle, part=part, w=w, ox=ox, oy=oy, oz=oz):
                                if expansion > 0:
                                    if face == "top": vry -= expansion
                                    elif face == "bottom": vry += expansion
                                    elif face == "front": vrz += expansion
                                    elif face == "right": vrx += expansion
                                    elif face == "left": vrx -= expansion
                                
                                if angle != 0:
                                    px, py = (0, 0) if part == "left_arm" else (w, 0)
                                    rad = np.radians(angle)
                                    nx = (vrx - px) * np.cos(rad) - (vry - py) * np.sin(rad) + px
                                    ny = (vrx - px) * np.sin(rad) + (vry - py) * np.cos(rad) + py
                                    vrx, vry = nx, ny
                                
                                return self.project(ox + vrx, oy + vry, oz + vrz)
                            
                            if face in ["top", "bottom"]:
                                ry_val = 0 if face == "top" else h
                                p1 = get_v(fx, ry_val, fy)
                                p2 = get_v(fx + 1, ry_val, fy)
                                p3 = get_v(fx + 1, ry_val, fy + 1)
                                p4 = get_v(fx, ry_val, fy + 1)
                            elif face == "front":
                                p1 = get_v(fx, fy, d)
                                p2 = get_v(fx + 1, fy, d)
                                p3 = get_v(fx + 1, fy + 1, d)
                                p4 = get_v(fx, fy + 1, d)
                            elif face in ["left", "right"]:
                                rx_val = w if face == "right" else 0
                                p1 = get_v(rx_val, fy, fx)
                                p2 = get_v(rx_val, fy, fx + 1)
                                p3 = get_v(rx_val, fy + 1, fx + 1)
                                p4 = get_v(rx_val, fy + 1, fx)
                            
                            draw.polygon([(p1[0], p1[1]), (p2[0], p2[1]), (p3[0], p3[1]), (p4[0], p4[1])], fill=color)
        
        canvas.save(output_path)
        print(f"3D render saved to {output_path}")

def main():
    if len(sys.argv) not in (4, 5):
        print("Usage: SkinRenderer.py {type} {skin png} {output png} [model]")
        print("Types: head, 3d")
        print("Model (optional): alex, steve (default: auto-detect)")
        sys.exit(1)
    
    render_type = sys.argv[1].lower()
    skin_path = sys.argv[2]
    output_path = sys.argv[3]
    model_type = None
    
    if len(sys.argv) == 5:
        model_type = sys.argv[4].lower()
        if model_type not in ("alex", "steve"):
            print("Error: Model type must be 'alex' or 'steve'")
            sys.exit(1)
    
    if render_type == "head":
        extract_head(skin_path, output_path)
    elif render_type == "3d":
        renderer = SkinRenderer(skin_path, model_type=model_type)
        renderer.render(output_path)
    else:
        print(f"Unknown type: {render_type}")
        print("Valid types: head, 3d")
        sys.exit(1)

if __name__ == "__main__":
    main()
