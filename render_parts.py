import sys
import bpy
import numpy as np
import math
import mathutils
import random
import os
import shutil
from time import sleep
from math import sqrt


RED   = (1.0, 0.0, 0.0, 1.0)  # red
GREEN = (0.0, 1.0, 0.0, 1.0)  # green
BLUE  = (0.0, 0.0, 1.0, 1.0)  # blue
WHITE = (1.0, 1.0, 1.0, 1.0)  # white
BLACK = (0.0, 0.0, 0.0, 1.0)  # black
GREY  = (0.5, 0.5, 0.5, 1.0)  # gray

src_dir = 'new' #'E:\\Projects\\lego-parts-render\\new'
image_cnt = 288
render_engine = "BLENDER_EEVEE" # "CYCLES" 
mode = "M"
brick_level = 2
camera_distance = 4


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

    brick.location[2]+=brick_level
    brick.visible_shadow = False

    # создадим свет 
    # основной
    light_data = bpy.data.lights.new('light', type='SPOT')
    light_data.use_shadow = False
    light_data.energy = 1500
    light_data.spot_size = 1.74533
    light_data.shadow_soft_size = 0.5
        
    light = bpy.data.objects.new('light', light_data)
    bpy.context.collection.objects.link(light)
    light.location = (0, 5, 3)
    light.rotation_euler[0] = -1.5708
    light.rotation_euler[1] = 0
    light.rotation_euler[2] = 0

    # фоновый
    light_data = bpy.data.lights.new('back_light', type='SPOT')
    light_data.use_shadow = False
    light_data.energy = 10000
    light_data.spot_size = 3.1363
    light_data.shadow_soft_size = 3

        
    back_light = bpy.data.objects.new('back_light', light_data)
    bpy.context.collection.objects.link(back_light)
    back_light.location = brick.location
    back_light.location[1]=-1
    back_light.location[2]-=1

    # создадим камеру
    cam_data = bpy.data.cameras.new('camera')
    cam = bpy.data.objects.new('camera', cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera=cam
    cam.location=(0, 1.4, brick_level + camera_distance)
    cam.rotation_euler[0] = -0.35
    
    # направим камеру на объект
    #constraint = cam.constraints.new(type='TRACK_TO')
    #constraint.target=brick

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
    return rotated_point0

def render_part(scene, light, brick, plane, target_dir, brick_name, mode):

    cam = bpy.context.scene.camera
    # настроим рендеринг
    scene.render.engine = render_engine

    # Set the device_type
    bpy.context.preferences.addons[
        "cycles"
    ].preferences.compute_device_type = "CUDA" # or "OPENCL"

    # Set the device and feature set
    bpy.context.scene.cycles.device = "GPU"


    # непосредственно рендер
    scene.cycles.samples = 150
    scene.cycles.diffuse_bounces = 10
    scene.cycles.glossy_bounces = 0
    scene.render.image_settings.file_format='PNG'

    #step = round(360 / sqrt(image_cnt))
    step = image_cnt / 24
    step = round (360 / step) 

    print(step)

    for angle_z in range(-10, 10, 20):
        for angle_x in range(0, 360, 45):
            for angle_y in range(0, 360, step):        
                #brick render
                if angle_x == 0 and angle_y == 0 and angle_z == 0: 
                    scene.render.filepath=f'{target_dir}\\{brick_name}.png'
                    scene.render.resolution_x = 224
                    scene.render.resolution_y = 224
                    bpy.ops.render.render(write_still=1)
                
                scene.render.resolution_x = 224
                scene.render.resolution_y = 224
                scene.render.filepath=f'{target_dir}\\{brick_name}\\{brick_name}_{angle_x}_{angle_y}_{angle_z}R.png'
                bpy.ops.render.render(write_still=1)

                if mode == "S":
                    cam_location_x = cam.location.x
                    cam.location.x += 0.2
                    scene.render.filepath = f'{target_dir}\\{brick_name}\\{brick_name}_{angle_x}_{angle_y}_{angle_z}L.png'
                    bpy.ops.render.render(write_still=1)
                    cam.location.x = cam_location_x

                # brick rotation
                eul = mathutils.Euler((math.radians(angle_x), math.radians(angle_y), math.radians(angle_z)), 'XYZ')

                if brick.rotation_mode == "QUATERNION":
                    brick.rotation_quaternion = eul.to_quaternion()
                elif brick.rotation_mode == "AXIS_ANGLE":
                    q = eul.to_quaternion()
                    brick.rotation_axis_angle[0]  = q.angle
                    brick.rotation_axis_angle[1:] = q.axis
                else:
                    brick.rotation_euler = eul if eul.order == brick.rotation_mode else(
                        eul.to_quaternion().to_euler(obj.rotation_mode))
                    
            


def progress(name, percent):
    cnt = round(percent / 2)
    sys.stdout.write('\r')
    sys.stdout.write("%s: [%-50s] %d%%" % (name, '=' * cnt, percent))
    sys.stdout.flush()


print("Start from " + os.getcwd())

argv = sys.argv
try:
    argv = argv[argv.index("--") + 1:]  # get all args after "--"
except ValueError:
    argv = ''

print(argv)
if len(argv) > 0:
    src_dir = argv[0]
if len(argv) > 1:
    image_cnt = int(argv[1])
if len(argv) > 2:
    # Allowed values
    # BLENDER_WORKBENCH
    # BLENDER_EEVEE
    # CYCLES
    render_engine = argv[2]
if len(argv) > 3:
    # Allowed values
    # M # MONO
    # S # STEREO
    mode = argv[3]

wdir = ""
# пройдемся по каталогам
src = []
print("Walk trhough " + src_dir)
for (dirpath, dirnames, filenames) in os.walk(src_dir):
    print(dirpath + ":" )
    for filename in filenames:
        print( "\\" + filename)
        src.append(dirpath + "\\" + filename)
        wdir = dirpath

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
    render_part(bpy.context.scene, light, part, plane, directory + "\\blended", brick_name, mode)

    shutil.move(filename, target + "\\" + brick_name + ".dat")

if wdir != "":
    os.rmdir(wdir)

