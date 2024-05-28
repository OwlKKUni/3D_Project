import bpy
import time
import random
import math


# bpy.context.active_object.mode - in interactive console - show what mode the object is in
# Returns "OBJECT"

# On view - select object - press tab - run line of code again - "EDIT"

################################################
# H E L P E R    F U N C T I O N S    S T A R T
################################################

# For animate_360 function variable
class Axis:
    X = 0
    Y = 1
    Z = 2


# Workaround function
# Delete data-blocks associated with thew deleted objects - orphan-data
# So a material linked to an object etc...
def purge_orphans():
    if bpy.app.version >= (3, 0, 0):
        bpy.ops.outliner.orphans_purge(
            do_local_ids=True, do_linked_ids=True, do_recursive=True
        )
    else:
        # call purge_orphans() recursively until there are no more orphan data blocks
        result = bpy.ops.outliner.orphans_purge()
        if result.pop() != "CANCELLED":
            purge_orphans()


def clean_scene():
    """
    Removing all of the objects, collection, materials, particles,
    textures, images, curves, meshes, actions, nodes, and worlds from the scene
    """

    if bpy.context.active_object and bpy.context.active_object.mode == "EDIT":
        bpy.ops.object.editmode_toggle()

    # Ensure all objects are visible for selection
    for obj in bpy.data.objects:
        obj.hide_set(False)
        obj.hide_select = False
        obj.hide_viewport = False

    # Select all objects in the scene and delete them
    # Similar to hitting "A -> X -> D" on the keyboard
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    # Find all of the collections in the scene and delete them all
    collection_names = [col.name for col in bpy.data.collections]
    for name in collection_names:
        bpy.data.collections.remove(bpy.data.collections[name])

    # Delete and replace the world object
    world_names = [world.name for world in bpy.data.worlds]
    for name in world_names:
        bpy.data.worlds.remove(bpy.data.worlds[name])

    # create a new world data block
    # A "world" in Blender is a data structure that contains environment settings like the background color, ambient light etc ...
    bpy.ops.world.new()
    bpy.context.scene.world = bpy.data.worlds["World"]  # assign the world to currenty scene

    purge_orphans()


def time_seed():
    """
    Sets the random seed based on the time
    and copies the seed into the clipboard
    """
    seed = time.time()
    random.seed(seed)

    # add seed value to clipboard
    bpy.context.window_manager.clipboard = str(seed)

    return seed


def add_ctrl_empty(name=None):
    """
    Function to add an empty object for control purposes
    """
    bpy.ops.object.empty_add(type="PLAIN_AXES", align="WORLD")
    empty_ctrl = active_object()  # Get the newly added empty object

    if name:
        empty_ctrl.name = name
    else:
        empty_ctrl.name = "empty.cntrl"

    return empty_ctrl


def make_active(obj):
    """
    Function to make a given object active
    """
    bpy.ops.object.select_all(action="DESELECT")  # Deselect all objects
    obj.select_set(True)  # Select the given object
    bpy.context.view_layer.objects.active = obj  # Set the given object as active


def track_empty(obj):
    """
    create an empty and add a 'Track To' constraint
    """
    empty = add_ctrl_empty(name=f"empty.tracker-target.{obj.name}")

    make_active(obj)
    bpy.ops.object.constraint_add(type="TRACK_TO")
    bpy.context.object.constraints["Track To"].target = empty

    return empty


def set_1080px_square_render_res():
    """
    Set the resolution of the rendered image to 1080 by 1080
    """
    bpy.context.scene.render.resolution_x = 1080
    bpy.context.scene.render.resolution_y = 1080


def set_fcurve_extrapolation_to_linear():
    for fc in bpy.context.active_object.animation_data.action.fcurves:
        fc.extrapolation = "LINEAR"


def hex_color_to_rgb(hex_color):
    """
    Converting from a color in the form of a hex triplet string to a Linear RGB
    """

    if hex_color.startswith("#"):
        hex_color = hex_color[1:]

    assert len(hex_color) == 6

    # extracting the Red component
    red = int(hex_color[:2], 16)
    srgb_red = red / 255
    linear_red = convert_srgb_to_linear_rgb(srgb_red)

    # extracting the Green component
    green = int(hex_color[2:4], 16)
    srgb_green = green / 255
    linear_green = convert_srgb_to_linear_rgb(srgb_green)

    # extracting the Blue component
    blue = int(hex_color[4:6], 16)
    srgb_blue = blue / 255
    linear_blue = convert_srgb_to_linear_rgb(srgb_blue)

    return tuple([linear_red, linear_green, linear_blue])


def hex_color_to_rgba(hex_color, alpha=1.0):
    """
    Converting from a color in the form of a hex triplet string to a Linear RGB with an Alpha passed as a parameter
    Supports: "#RRGGBB" or "RRGGBB"
    """
    linear_red, linear_green, linear_blue = hex_color_to_rgb(hex_color)
    return tuple([linear_red, linear_green, linear_blue, alpha])


def convert_srgb_to_linear_rgb(srgb_color_component):
    """
    Converting from sRGB to Linear RGB
    https://entropymine.com/imageworsener/srgbformula/
    """
    if srgb_color_component <= 0.04045:
        linear_color_component = srgb_color_component / 12.92
    else:
        linear_color_component = math.pow((srgb_color_component + 0.055) / 1.055, 2.4)

    return linear_color_component


def animate_rotation(angle, axis_index, last_frame, obj=None, clockwise=False, linear=True, start_frame=1):
    if not obj:
        obj = active_object()  # Use active object if none provided
    frame = start_frame
    obj.keyframe_insert("rotation_euler", index=axis_index, frame=frame)

    if clockwise:
        angle_offset = -angle
    else:
        angle_offset = angle
    frame = last_frame
    obj.rotation_euler[axis_index] = math.radians(angle_offset) + obj.rotation_euler[axis_index]
    obj.keyframe_insert("rotation_euler", index=axis_index, frame=frame)

    if linear:
        set_fcurve_extrapolation_to_linear()


# Function to animate a full 360-degree rotation
def animate_360_rotation(axis_index, last_frame, obj=None, clockwise=False, linear=True, start_frame=1):
    animate_rotation(360, axis_index, last_frame, obj, clockwise, linear, start_frame)


# Function to apply rotation transformation
def apply_rotation():
    bpy.ops.object.transform_apply(rotation=True)


# random.uniform() - draw samples from uniform distribution
# Function to apply random rotation to an object
def apply_random_rotation():
    obj = active_object()
    obj.rotation_euler.x = math.radians(random.uniform(0, 360))
    obj.rotation_euler.y = math.radians(random.uniform(0, 360))
    obj.rotation_euler.z = math.radians(random.uniform(0, 360))
    apply_rotation()


# Function to apply emission material to an object
def apply_emission_material(color, name=None, energy=1):
    material = create_emission_material(color, name=name, energy=energy)

    obj = active_object()
    obj.data.materials.append(material)


def create_emission_material(color, name=None, energy=30, return_nodes=False):
    if name is None:
        name = ""

    material = bpy.data.materials.new(name=f"material.emission.{name}")
    material.use_nodes = True

    out_node = material.node_tree.nodes.get("Material Output")
    bsdf_node = material.node_tree.nodes.get("Principled BSDF")
    material.node_tree.nodes.remove(bsdf_node)

    node_emission = material.node_tree.nodes.new(type="ShaderNodeEmission")
    node_emission.inputs["Color"].default_value = color
    node_emission.inputs["Strength"].default_value = energy

    node_emission.location = 0, 0

    material.node_tree.links.new(node_emission.outputs["Emission"], out_node.inputs["Surface"])

    if return_nodes:
        return material, material.node_tree.nodes
    else:
        return material


def create_reflective_material(color, name=None, roughness=0.1, specular=0.5, return_nodes=False):
    if name is None:
        name = ""

    material = bpy.data.materials.new(name=f"material.reflective.{name}")
    material.use_nodes = True

    bsdf_node = material.node_tree.nodes.get("Principled BSDF")
    if bsdf_node and "Specular" in bsdf_node.inputs:  # Check for "Specular" input
        bsdf_node.inputs["Base Color"].default_value = color
        bsdf_node.inputs["Roughness"].default_value = roughness
        bsdf_node.inputs["Specular"].default_value = specular  # Set "Specular" value if exists

    if return_nodes:
        return material, material.node_tree.nodes
    else:
        return material


def apply_reflective_material(color, name=None, roughness=0.1, specular=0.5):
    material = create_reflective_material(color, name=name, roughness=roughness, specular=specular)

    obj = active_object()
    obj.data.materials.append(material)


def get_random_color():
    hex_color = random.choice(
        [
            "#FC766A",
            "#5B84B1",
            "#5F4B8B",
            "#E69A8D",
            "#42EADD",
            "#CDB599",
            "#00A4CC",
            "#F95700",
            "#00203F",
            "#ADEFD1",
            "#606060",
            "#D6ED17",
            "#ED2B33",
            "#D85A7F",
        ]
    )

    return hex_color_to_rgba(hex_color)


def setup_camera(loc, rot):
    """
    create and setup the camera
    """
    bpy.ops.object.camera_add(location=loc, rotation=rot)
    camera = active_object()

    # set the camera as the "active camera" in the scene
    bpy.context.scene.camera = camera

    # set Focal Length
    camera.data.lens = 70

    camera.data.passepartout_alpha = 0.9

    empty = track_empty(camera)

    return empty


def set_scene_props(fps, seconds):
    """
    Set scene properties
    """
    frame_count = fps * seconds

    scene = bpy.context.scene
    scene.frame_end = frame_count

    # set the world background to black
    world = bpy.data.worlds["World"]
    if "Background" in world.node_tree.nodes:
        world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)

    scene.render.fps = fps
    scene.frame_current = 1
    scene.frame_start = 1

    scene.render.engine = "CYCLES"

    # Use the GPU to render
    scene.cycles.device = 'GPU'
    scene.cycles.samples = 1024
    scene.view_settings.look = "AgX - Very High Contrast"

    set_1080px_square_render_res()


def scene_setup(i=0):
    fps = 30
    loop_seconds = 12
    frame_count = fps * loop_seconds

    project_name = "ProjecT"
    bpy.context.scene.render.image_settings.file_format = "FFMPEG"
    bpy.context.scene.render.ffmpeg.format = "MPEG4"
    bpy.context.scene.render.filepath = f"/tmp/project_{project_name}/loop_{i}.mp4"

    seed = 0
    if seed:
        random.seed(seed)
    else:
        time_seed()

    # Utility Building Blocks
    use_clean_scene_experimental = False
    if use_clean_scene_experimental:
        clean_scene_experimental()
    else:
        clean_scene()

    set_scene_props(fps, loop_seconds)

    loc = (0, 0, 7)
    rot = (0, 0, 0)
    setup_camera(loc, rot)

    context = {
        "frame_count": frame_count,
    }

    return context


# Setup area lights with parameters
def add_light():
    bpy.ops.object.light_add(type="AREA", radius=1, location=(0, 0, 2))  # Position of the light on the axis
    bpy.context.object.data.energy = 100
    bpy.context.object.data.color = get_random_color()[:3]
    bpy.context.object.data.shape = "DISK"


def apply_glare_composite_effect():
    bpy.context.scene.use_nodes = True

    render_layer_node = bpy.context.scene.node_tree.nodes.get("Render Layers")
    comp_node = bpy.context.scene.node_tree.nodes.get("Composite")

    # remove node_glare from the previous run
    old_node_glare = bpy.context.scene.node_tree.nodes.get("Glare")
    if old_node_glare:
        bpy.context.scene.node_tree.nodes.remove(old_node_glare)

    # create Glare node
    node_glare = bpy.context.scene.node_tree.nodes.new(type="CompositorNodeGlare")
    node_glare.size = 7
    node_glare.glare_type = "FOG_GLOW"
    node_glare.quality = "HIGH"
    node_glare.threshold = 0.2

    # create links
    bpy.context.scene.node_tree.links.new(render_layer_node.outputs["Image"], node_glare.inputs["Image"])
    bpy.context.scene.node_tree.links.new(node_glare.outputs["Image"], comp_node.inputs["Image"])


# Renaming functions for ease of use
# -----------------------------------------------

# Return name of currently active/selected object
def active_object():
    return bpy.context.active_object


# render the animation
def render_loop():
    bpy.ops.render.render(animation=True)


# ------------------------------------------------

################################################
# H E L P E R    F U N C T I O N S    E N D
################################################


def apply_metaball_material():
    color = get_random_color()
    material = create_reflective_material(color, name="metaball", roughness=0.1, specular=0.5)

    primary_metaball = bpy.data.metaballs[0]
    primary_metaball.materials.append(material)


def create_metaball_path(context):
    bpy.ops.curve.primitive_bezier_circle_add()  # Add horizontal circle
    path = active_object()

    bpy.context.object.data.path_duration = context['frame_count']

    # Move the bezier curve "loop" along the X axis
    animate_360_rotation(Axis.X, context['frame_count'], path, clockwise=random.randint(0, 1))

    apply_random_rotation()

    if random.randint(0, 1):
        path.scale.x *= random.uniform(0.05, 0.5)
    else:
        path.scale.y *= random.uniform(0.05, 0.5)

    return path


def create_metaball(path):
    bpy.ops.object.metaball_add()
    ball = active_object()  # Get the newly added metaball

    ball.data.render_resolution = 0.05
    ball.scale *= random.uniform(0.05, 0.5)

    # Move the ball on the bezier curve
    bpy.ops.object.constraint_add(type='FOLLOW_PATH')
    bpy.context.object.constraints["Follow Path"].target = path
    bpy.ops.constraint.followpath_path_animate(constraint="Follow Path", owner='OBJECT')


def create_centerpiece(context):
    metaball_count = 10

    for _ in range(metaball_count):
        path = create_metaball_path(context)

        create_metaball(path)

    apply_metaball_material()


def create_background():
    pass


def main():
    context = scene_setup()
    create_centerpiece(context)
    create_background()
    add_light()


if __name__ == "__main__":
    main()

# View pane commands
# Shift + A - Add objects -> Metaball -> Ball

# Z -> Rendered
# Metaball -> Data -> Render resolution -> lower the better / smoother
# Metaballs are "blobby: objects
