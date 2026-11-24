import bpy
import math
import json
import sys
import random
import os
from pathlib import Path
from mathutils import Vector

def arg_config():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args:
        raise RuntimeError("Missing scene_config.json argument")
    with open(args[0], "r", encoding="utf-8") as f:
        return json.load(f)

def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

def principled(name, color, metallic=0.0, roughness=0.45, emission=None):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Metallic"].default_value = metallic
    bs.inputs["Roughness"].default_value = roughness
    if emission:
        bs.inputs["Emission Color"].default_value = (*emission, 1)
        bs.inputs["Emission Strength"].default_value = 1.8
    return mat

def planet_material(name, colors, roughness=0.8):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bs = nodes.get("Principled BSDF")
    bs.inputs["Roughness"].default_value = roughness
    tex = nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 3.2
    tex.inputs["Detail"].default_value = 5.0
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.25
    ramp.color_ramp.elements[0].color = (*colors[0], 1)
    ramp.color_ramp.elements[1].position = 0.72
    ramp.color_ramp.elements[1].color = (*colors[1], 1)
    links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bs.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.18
    bump.inputs["Distance"].default_value = 0.12
    links.new(tex.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    return mat

def add_text(body, location, size, material, name="Label"):
    bpy.ops.object.text_add(location=location, rotation=(math.radians(90), 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj.data.body = body
    obj.data.size = size
    obj.data.extrude = 0.002
    obj.data.materials.append(material)
    return obj

def main():
    cfg = arg_config()
    random.seed(14)
    clear_scene()
    style = cfg.get("style", "")
    topic = cfg.get("topic", "Unknown world")
    planet = cfg.get("planet") or {}
    resolution = cfg.get("resolution", "1280x720")
    width, height = [int(v) for v in resolution.split("x")]
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.eevee.taa_render_samples = 16
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.frame_start = 1
    scene.frame_end = 24 * 16
    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    output_path = Path(cfg["output"]).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    # Blender treats the FFmpeg filepath as a base name and adds the container extension.
    scene.render.filepath = str(output_path.with_suffix(""))
    scene.render.use_file_extension = True
    scene.render.ffmpeg.audio_codec = "AAC"
    scene.render.film_transparent = False
    scene.world.color = (0.001, 0.002, 0.008)
    scene.view_settings.view_transform = "Standard"

    if style == "Animated Facts":
        colors = ((0.025, 0.16, 0.38), (0.05, 0.8, 0.72))
        accent = (0.1, 0.9, 0.8)
        planet_color = (0.025, 0.22, 0.55)
    elif style == "Viral 3D":
        colors = ((0.12, 0.015, 0.28), (0.9, 0.08, 0.48))
        accent = (1.0, 0.12, 0.48)
        planet_color = (0.24, 0.025, 0.28)
    elif style == "Professional Facts":
        colors = ((0.025, 0.08, 0.17), (0.16, 0.52, 0.7))
        accent = (0.2, 0.8, 0.9)
        planet_color = (0.04, 0.2, 0.35)
    elif style == "Real Exoplanet Cinematic Exploration":
        colors = ((0.16, 0.035, 0.02), (0.78, 0.3, 0.08))
        accent = (1.0, 0.55, 0.2)
        planet_color = (0.28, 0.08, 0.025)
    else:
        colors = ((0.025, 0.06, 0.16), (0.1, 0.35, 0.5))
        accent = (0.35, 0.75, 1.0)
        planet_color = (0.025, 0.16, 0.3)

    dark = principled("Deep Space", (0.002, 0.004, 0.012), roughness=1)
    accent_mat = principled("Accent Glow", accent, metallic=0.35, emission=accent)
    star_mat = principled("Star Light", (1.0, 0.72, 0.38), emission=(1.0, 0.6, 0.25))
    planet_mat = planet_material("Procedural Planet Surface", colors)
    ground_mat = principled("Orbit Metal", (0.025, 0.04, 0.07), metallic=0.8, roughness=0.25)

    # Star field made from small low-poly emissive spheres.
    for i in range(260):
        direction = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))).normalized()
        loc = direction * random.uniform(13, 32)
        radius = random.uniform(0.012, 0.035)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=radius, location=loc)
        bpy.context.object.data.materials.append(star_mat)

    # Main world body.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=3.2, location=(0, 0, 0))
    world = bpy.context.object
    world.name = "Animated Exoplanet / World"
    world.data.materials.append(planet_mat)
    for poly in world.data.polygons:
        poly.use_smooth = True
    world.rotation_euler[2] = math.radians(-15)
    world.keyframe_insert(data_path="rotation_euler", frame=1)
    world.rotation_euler[2] = math.radians(28)
    world.keyframe_insert(data_path="rotation_euler", frame=scene.frame_end)

    # Thin atmospheric rim and orbit rings.
    bpy.ops.mesh.primitive_torus_add(major_radius=4.15, minor_radius=0.035, major_segments=96,
                                     minor_segments=8, location=(0, 0, 0), rotation=(math.radians(68), 0, math.radians(18)))
    ring = bpy.context.object
    ring.name = "Orbital Ring"
    ring.data.materials.append(accent_mat)
    bpy.ops.mesh.primitive_torus_add(major_radius=3.34, minor_radius=0.045, major_segments=96,
                                     minor_segments=8, location=(0, 0, 0))
    atmosphere = bpy.context.object
    atmosphere.name = "Atmospheric Rim"
    atmosphere.data.materials.append(accent_mat)

    # Distant host star for exoplanet mode.
    if style == "Real Exoplanet Cinematic Exploration":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.8, location=(-7, 3, 4))
        host = bpy.context.object
        host.name = "Host Star"
        host.data.materials.append(star_mat)
        bpy.ops.object.light_add(type="POINT", location=(-7, -2, 4))
        host_light = bpy.context.object
        host_light.data.energy = 1800
        host_light.data.shadow_soft_size = 3
        add_text(str(planet.get("pl_name", topic)), (-4.5, -4.0, -4.2), 0.48, accent_mat, "Exoplanet Name")
        distance = planet.get("sy_dist")
        dist_text = f"{distance} light-years from Earth" if distance else "Confirmed exoplanet"
        add_text(dist_text, (-4.5, -4.0, -4.85), 0.22, star_mat, "Discovery Distance")

    # Animated orbiting moons / science markers.
    for i in range(4 if style != "Professional Facts" else 6):
        angle = i * (math.tau / 4)
        radius = 5.4 + (i % 2) * 0.6
        bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=0.22 if style != "Viral 3D" else 0.3,
                                             location=(math.cos(angle) * radius, math.sin(angle) * radius, math.sin(angle * 2) * 0.6))
        moon = bpy.context.object
        moon.data.materials.append(accent_mat if i % 2 == 0 else ground_mat)
        start = moon.location.copy()
        moon.location.x += 0.8
        moon.keyframe_insert(data_path="location", frame=1)
        moon.location.x -= 1.6
        moon.keyframe_insert(data_path="location", frame=scene.frame_end)

    # Professional infographic-style orbit grid.
    if style == "Professional Facts":
        for radius in (4.8, 5.8, 6.8):
            bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=0.012,
                                             major_segments=96, minor_segments=6,
                                             location=(0, 0, -0.25))
            bpy.context.object.data.materials.append(ground_mat)
        add_text("PLANETARY SYSTEM / 3D VISUALIZATION", (-5.8, -4.2, 4.2), 0.28, accent_mat, "Section Title")
    elif style == "Animated Facts":
        add_text("DISCOVER • EXPLORE • LEARN", (-4.7, -4.2, 4.3), 0.34, accent_mat, "Animated Title")
    elif style == "Viral 3D":
        add_text("A WORLD BEYOND", (-4.0, -4.2, 4.3), 0.42, accent_mat, "Viral Title")
    else:
        add_text("BEYOND OUR SOLAR SYSTEM", (-4.8, -4.2, 4.3), 0.32, accent_mat, "Cinematic Title")

    # Camera and smooth cinematic push-in.
    bpy.ops.object.camera_add(location=(0, -24, 5.2))
    camera = bpy.context.object
    camera.data.lens = 42
    scene.camera = camera
    target = bpy.data.objects.get("Animated Exoplanet / World")
    constraint = camera.constraints.new(type="TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    camera.location = (0, -24, 5.2)
    camera.keyframe_insert(data_path="location", frame=1)
    camera.location = (0, -9.5, 2.3)
    camera.keyframe_insert(data_path="location", frame=scene.frame_end)
    for fc in camera.animation_data.action.fcurves:
        for key in fc.keyframe_points:
            key.interpolation = "BEZIER"

    # Lighting.
    bpy.ops.object.light_add(type="AREA", location=(-8, -10, 8))
    key = bpy.context.object
    key.data.energy = 1600
    key.data.shape = "DISK"
    key.data.size = 9
    key.rotation_euler = (math.radians(25), 0, math.radians(-35))
    bpy.ops.object.light_add(type="AREA", location=(7, 3, 1))
    rim = bpy.context.object
    rim.data.energy = 950
    rim.data.color = accent
    rim.data.size = 7
    rim.rotation_euler = (math.radians(60), 0, math.radians(135))

    scene.camera.data.dof.use_dof = False
    scene.render.image_settings.color_mode = "RGB"
    scene.render.ffmpeg.gopsize = 12
    scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=cfg["output"].replace(".mp4", ".blend"))
    bpy.ops.render.render(animation=True)

if __name__ == "__main__":
    main()
