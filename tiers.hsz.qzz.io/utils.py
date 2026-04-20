from PIL import Image, ImageDraw
import numpy as np
import os

def extract_head(skin_path, output_path):
    """Fallback or legacy head extractor"""
    with Image.open(skin_path) as img:
        img = img.convert("RGBA")
        head_base = img.crop((8, 8, 16, 16))
        head_outer = img.crop((40, 8, 48, 16))
        head_combined = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
        head_combined.paste(head_base, (0, 0))
        head_combined.paste(head_outer, (0, 0), head_outer)
        head_final = head_combined.resize((128, 128), Image.NEAREST)
        head_final.save(output_path)

class SkinRenderer:
    def __init__(self, skin_path, model_type=None):
        self.skin = Image.open(skin_path).convert("RGBA")
        self.width, self.height = self.skin.size
        
        if model_type:
            self.is_slim = (model_type == "alex")
        else:
            self.is_slim = self._check_slim()
        
        # Camera Settings (User Requirements)
        self.y_rot = np.radians(-45)
        self.x_rot = np.radians(15)
        self.scale = 16
        self.canvas_size = (300, 400)
        self.offset = (150, 180) # Centered upper body

    def _check_slim(self):
        """Detect if the skin uses the slim (Alex) model"""
        if self.height == 32: return False
        # Check alpha of the 4th column of the right arm (Steve has 4px, Alex has 3px)
        # Right arm area in 64x64 is (40, 16, 56, 32)
        # The 4th column of the front face would be at index 54-55
        pixel = self.skin.getpixel((54, 20))
        return pixel[3] == 0

    def get_uv(self, part, face, layer="base"):
        """Returns (x1, y1, x2, y2) for the given face"""
        # simplified UV mapping for upper body
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
        # Rotate around Y (horizontal)
        x_rot = x * np.cos(self.y_rot) + z * np.sin(self.y_rot)
        z_rot = -x * np.sin(self.y_rot) + z * np.cos(self.y_rot)
        
        # Rotate around X (tilt)
        y_rot = y * np.cos(self.x_rot) - z_rot * np.sin(self.x_rot)
        z_final = y * np.sin(self.x_rot) + z_rot * np.cos(self.x_rot)
        
        return (x_rot * self.scale + self.offset[0], 
                y_rot * self.scale + self.offset[1], 
                z_final)

    def render(self, output_path):
        canvas = Image.new("RGBA", self.canvas_size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        
        # Parts list: (part_name, offset_x, offset_y, offset_z, angle)
        arm_w = 4 if not self.is_slim else 3
        # Back-to-front rendering order for -45, 15 perspective:
        parts = [
            ("right_arm", -4 - arm_w, 0, -2, 5),
            ("head", -4, -8, -4, 0),
            ("torso", -4, 0, -2, 0),
            ("left_arm", 4, 0, -2, -5)
        ]
        
        # We'll render base then outer for each face to ensure correct layering
        for part, ox, oy, oz, angle in parts:
            info = {"head": (8, 8, 8), "torso": (8, 12, 4), "right_arm": (arm_w, 12, 4), "left_arm": (arm_w, 12, 4)}[part]
            w, h, d = info
            
            active_faces = ["top", "bottom", "front", "right"]
            
            for layer in ["base", "outer"]:
                for face in active_faces:
                    uv = self.get_uv(part, face, layer)
                    face_img = self.skin.crop(uv)
                    
                    # Shading
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
                            
                            def get_v(vrx, vry, vrz):
                                # 1. Expansion (Relief)
                                if expansion > 0:
                                    if face == "top": vry -= expansion
                                    elif face == "bottom": vry += expansion
                                    elif face == "front": vrz += expansion
                                    elif face == "right": vrx += expansion
                                    elif face == "left": vrx -= expansion
                                
                                # 2. Rotation (Open Arms)
                                if angle != 0:
                                    px, py = (0, 0) if part == "left_arm" else (w, 0)
                                    rad = np.radians(angle)
                                    nx = (vrx - px) * np.cos(rad) - (vry - py) * np.sin(rad) + px
                                    ny = (vrx - px) * np.sin(rad) + (vry - py) * np.cos(rad) + py
                                    vrx, vry = nx, ny
                                
                                return self.project(ox + vrx, oy + vry, oz + vrz)

                            # Face-specific vertex mapping
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

        # Final save with high quality pixels (already achieved by drawing polygons)
        canvas.save(output_path)

def render_body(skin_path, output_path, model_type=None):
    renderer = SkinRenderer(skin_path, model_type=model_type)
    renderer.render(output_path)
