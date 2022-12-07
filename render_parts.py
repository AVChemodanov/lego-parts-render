import bpy
import numpy as np
import math
import mathutils
import random
import os


def random_color():
    #r = random.randint(0, 255) / 255.0
    #g = random.randint(0, 255) / 255.0
    #b = random.randint(0, 255) / 255.0
    
    #return (r, g, b, 1.0)
    colors = [  (1.0, 0.0, 0.0, 1.0), # red
                (0.0, 1.0, 0.0, 1.0), # green
                (0.0, 0.0, 1.0, 1.0), # blue
                (1.0, 1.0, 1.0, 1.0), # white
                (0.0, 0.0, 0.0, 1.0), # black 
                (0.5, 0.5, 0.5, 1.0), ] #gray
    index = random.randint(0,5)
    
    #return colors[index]
    return  (1.0, 0.0, 0.0, 1.0) # red color only
    


def create_cube(mat_name, size, location):
    bpy.data.materials.new(mat_name)
    bpy.data.materials[mat_name].diffuse_color = random_color()
    bpy.ops.mesh.primitive_cube_add(size=size, location=location)
    bpy.context.object.data.materials.append(bpy.data.materials[mat_name])


def create_back(): 
    create_cube("bottom", 200, (0, 0, -110))
    
    #create_cube("east", 200, (110, 0, 0))
    #create_cube("south", 200, (110, 110, 0))
    #create_cube("west", 200, (-110, 0, 0))
    #create_cube("north", 200, (-110, -110, 0))
    
    #create_cube("top", 200, (0, 0, 110))
    

def recolor_back():
    white = (1.0, 1.0, 1.0, 1.0)
    bpy.data.materials["bottom"].diffuse_color =  white # random_color()
    #bpy.data.materials["east"].diffuse_color = white # random_color()
    #bpy.data.materials["south"].diffuse_color = white # random_color()
    #bpy.data.materials["west"].diffuse_color = white # random_color()
    #bpy.data.materials["north"].diffuse_color = white # random_color()
    #bpy.data.materials["top"].diffuse_color = random_color()


def prepare_and_load(filename, brick_name):
    # удалим всё
    try:
        if bpy.context.object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
    except AttributeError:
        print('It seems scene is empty')


    # создадим фон
    create_back()
    
    #загрузим деталь 
    bpy.ops.import_scene.importldraw(filepath=filename,useLogoStuds=True)
    brick = bpy.context.active_object
    #brick_name = 'noname'
    for child in bpy.context.scene.objects:
        if ".dat" in child.name:
            brick = child
        if "LegoGroundPlane" in child.name: 
            plane = child;
    #        brick_name = child.name.rpartition('.')[0]

    brick.location[2]+=1

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

    return (brick, plane, light)


def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
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
    scene.render.engine = "BLENDER_EEVEE"
    #scene.render.engine = "CYCLES"
    # Set the device_type
    #bpy.context.preferences.addons[
    #    "cycles"
    #].preferences.compute_device_type = "CUDA" # or "OPENCL"

    # Set the device and feature set
    #bpy.context.scene.cycles.device = "GPU"


    # непосредственно рендер 
    desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') 
    scene.cycles.samples = 150
    scene.render.image_settings.file_format='PNG'
    scene.render.filepath=f'{desktop}\\blend\\{brick_name}.png'

    bpy.ops.render.render(write_still=1)

    radiants = 0.0
    step = 10

    for angle in range(0, 2160, step):
        # enable/disable plane
        #hide = random.randint(0, 100)
        #print(hide)
        #if ( hide > 50 ):
        #    plane.hide_render = True
        #else:
        #    plane.hide_render = False
        
        # colorization
        recolor_back() 

        material_slots = brick.material_slots
        for m in material_slots:
            material = m.material
            material.node_tree.nodes["Group"].inputs[0].default_value = random_color() #(r, g, b, 1.0)


        cam_axis = (0, 0, 1)        
        light_axis = (0, 0, 1)
        #if ( angle < 1920 ):
            #cam_axis = (0, 1, 0)
        #    light_axis = (1, 1, 0)
        #if ( angle < 1440 ):
            #cam_axis = (0, 1, 1)
        #    light_axis = (1, 0, 1)
        #if ( angle < 1080 ):
            #cam_axis = (1, 1, 0)
        #    light_axis = (1, 0, 1)
        #if ( angle < 720 ):
            #cam_axis = (0, 1, 0)
        #    light_axis = (1, 0, 0)
        #if ( angle < 360 ):
        #    cam_axis = (0, 0, 1)
        #    light_axis = (1, 0, 0)
        
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


# пройдемся по каталогам
desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop') 
src_dir=f'{desktop}\\source'


src = []
for (dirpath, dirnames, filenames) in os.walk(src_dir):
    src.extend(filenames)

for filename in src:
    brick_name = filename.rpartition('.')[0]
    
    # загружаем
    (part, plane, light) = prepare_and_load(f'{src_dir}\\{filename}', brick_name)
                  
    # рендерим
    bpy.context.scene.world.use_nodes = False
    render_part(bpy.context.scene, light, part, plane, f'{desktop}\\blend', brick_name)

                     