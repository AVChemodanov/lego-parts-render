import sys
import bpy
import numpy as np
import math
import mathutils
import random
import os
import shutil
from time import sleep


RED   = (1.0, 0.0, 0.0, 1.0)  # red
GREEN = (0.0, 1.0, 0.0, 1.0)  # green
BLUE  = (0.0, 0.0, 1.0, 1.0)  # blue
WHITE = (1.0, 1.0, 1.0, 1.0)  # white
BLACK = (0.0, 0.0, 0.0, 1.0)  # black
GREY  = (0.5, 0.5, 0.5, 1.0)  #gray

image_cnt = 10
render_engine = "BLENDER_EEVEE"

def create_cube(mat_name, size, location):
    bpy.data.materials.new(mat_name)
    bpy.data.materials[mat_name].diffuse_color = WHITE
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    bpy.context.object.data.materials.append(bpy.data.materials[mat_name])

def prepare_and_load(filename, brick_name):
    # удалим всё
    try:
        if bpy.context.object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
    except AttributeError:
        print('It seems scene is empty')


    #загрузим деталь 
    bpy.ops.import_scene.importldraw(filepath=filename,useLogoStuds=True)
    brick = bpy.context.active_object
    for child in bpy.context.scene.objects:
        if ".dat" in child.name:
            brick = child
        if "LegoGroundPlane" in child.name: 
            plane = child;

    brick.location[2]+=1
    brick.visible_shadow = False

    # создадим свет 
    light_data = bpy.data.lights.new('light', type='SUN')
    light_data.use_shadow = False
    light = bpy.data.objects.new('light', light_data)
    bpy.context.collection.objects.link(light)
    light.location = (25, -3, 20)

    # создадим камеру
    cam_data = bpy.data.cameras.new('camera')
    cam = bpy.data.objects.new('camera', cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera=cam
    cam.location=(2, 2, 3)

    # направим камеру на объект
    constraint = cam.constraints.new(type='TRACK_TO')
    constraint.target=brick

    return brick, plane, light


def rotation_matrix(axis, theta):
    axis = np.asarray(axis)
    axis = axis / math.sqrt(np.dot(axis, axis))
    a = math.cos(theta / 2.0)
    b, c, d = -axis * math.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return np.array([[aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
                     [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                     [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]])

def rotate(point, angle_degrees, axis=(0,1,0)):
    theta_degrees = angle_degrees
    theta_radians = math.radians(theta_degrees)
    
    rotated_point = np.dot(rotation_matrix(axis, theta_radians), point)
    return rotated_point

def render_part(scene, light, brick, plane, target_dir, brick_name):

    cam = bpy.context.scene.camera
    # настроим рендеринг 
    #scene.render.engine = "BLENDER_WORKBENCH"
    #scene.render.engine = "BLENDER_EEVEE"
    #scene.render.engine = "CYCLES"
    scene.render.engine = render_engine

    # Set the device_type
    bpy.context.preferences.addons[
        "cycles"
    ].preferences.compute_device_type = "CUDA" # or "OPENCL"

    # Set the device and feature set
    bpy.context.scene.cycles.device = "GPU"


    # непосредственно рендер 
    #desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    scene.cycles.samples = 150
    scene.cycles.diffuse_bounces = 10
    scene.cycles.glossy_bounces = 0
    scene.render.image_settings.file_format='PNG'
    #scene.render.filepath=f'{desktop}\\blend\\{brick_name}.png'
    scene.render.filepath=f'{target_dir}\\{brick_name}.png'

    scene.render.resolution_x = 1024
    scene.render.resolution_y = 768
    bpy.ops.render.render(write_still=1)

    radiants = 0.0
    step = 10
    total_radiants = image_cnt * step

    print(step)
    print(total_radiants)

    for angle in range(0, total_radiants, step):
        #progress(brick_name, angle / total_radiants * 100)

        cam_axis = (0, 0, 1)
        light_axis = (0, 0, 1)

        # camera rotation
        cam_location = cam.location    
        new_cam_location = rotate(cam_location, step, axis=cam_axis)    
        cam.location = new_cam_location
        print(f"{angle} at {new_cam_location}" )
        
        # light location
        light_location = light.location
        new_light_location = rotate(light_location, step, axis=light_axis)
        #light.location = new_light_location
        
        
        # brick rotation 
        radiants += 15.0
        axis_selector = random.randint(0, 100)
        if axis_selector < 33:
            eul = mathutils.Euler((math.radians(radiants), 0.0, 0.0), 'XYZ')
        else: 
            if axis_selector < 66: 
                eul = mathutils.Euler((0.0, math.radians(radiants), 0.0), 'XYZ')
            else:
                eul = mathutils.Euler((0.0, 0.0, math.radians(radiants)), 'XYZ')

        if brick.rotation_mode == "QUATERNION":
            brick.rotation_quaternion = eul.to_quaternion()
        elif brick.rotation_mode == "AXIS_ANGLE":
            q = eul.to_quaternion()
            brick.rotation_axis_angle[0]  = q.angle
            brick.rotation_axis_angle[1:] = q.axis
        else:
            brick.rotation_euler = eul if eul.order == brick.rotation_mode else(
                eul.to_quaternion().to_euler(obj.rotation_mode))
                
        scene.render.resolution_x = 640
        scene.render.resolution_y = 480
        scene.render.filepath=f'{target_dir}\\{brick_name}\\{brick_name}_{angle}.png'
        bpy.ops.render.render(write_still=1)


def progress(name, percent):
    cnt = round(percent / 2)
    sys.stdout.write('\r')
    sys.stdout.write("%s: [%-50s] %d%%" % (name, '=' * cnt, percent))
    sys.stdout.flush()


argv = sys.argv
argv = argv[argv.index("--") + 1:]  # get all args after "--"

print(argv)
if len(argv) > 0:
    src_dir = argv[0]
if len(argv) > 1:
    image_cnt = int(argv[1])
if len(argv) > 2:
    render_engine = argv[2]

# пройдемся по каталогам
src = []
for (dirpath, dirnames, filenames) in os.walk(src_dir):
    for filename in filenames:
        src.append(dirpath + "\\" + filename)

for filename in src:
    package =  filename.rpartition('\\')[0].rpartition('\\')[-1]
    brick_name = filename.rpartition('.')[0].rpartition('\\')[-1]
    # создадим выходной каталог
    target = "done\\"+package
    os.makedirs(target, exist_ok=True)
    # загружаем
    (part, plane, light) = prepare_and_load(filename, brick_name)

    # рендерим
    directory = os.getcwd()
    bpy.context.scene.world.use_nodes = False
    render_part(bpy.context.scene, light, part, plane, directory + "\\blended", brick_name)

    shutil.move(filename, target + "\\" + brick_name + ".dat")

