import math
import os
import sys
from typing import Any, List, Tuple

import bpy

"""
This file is part of blitz.

HOBAK is free software: you can redistribute it and/or modify it under the terms of
the GNU General Public License as published by the Free Software Foundation, either
version 3 of the License, or (at your option) any later version.

HOBAK is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with HOBAK.
If not, see <https://www.gnu.org/licenses/>.
"""


"""
NOTE: This file CANNOT BE TESTED LOCALLY. bpy is a nightmare to work with, so you just
need to copy this into the blender scripts folder, change the root_dir, and it should work.

If you just need to run this, please see the README in this folder for detailed instructions.
"""


def dbg_print(data: Any):
    """Debug print from within blender. Useful for debugging scripts.

    Args:
        data (Any): Blender data type, fits anything
    """
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == "CONSOLE":
                override = {"window": window, "screen": screen, "area": area}
                bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")


def make_hair_material(obj: bpy.types.Object):
    """Sets the material for the collection from the FIRST object. The material can be
    changed in the blender UI from here and apply to everyone.

    Args:
        all_obj_objects (List[bpy.types.Object]): The list of obj objects.
            If you are re-running this from the script it will not work since it won't
            have the objects. Never fear! This code will fetch the objects from the
            collection for you, so just pass "None" when calling and it'll do the rest.
    """
    # This is the selected global material to apply to everyone
    hair_mat = bpy.data.materials.get("Hair")

    # Delete the hair material
    if hair_mat is not None:
        bpy.data.materials.remove(hair_mat)

    # Set up a new hair material
    hair_mat = bpy.data.materials.new(name="Hair")
    hair_mat.use_nodes = True

    # Remove all tree nodes so we get a fresh start
    for n in hair_mat.node_tree.nodes:
        hair_mat.node_tree.nodes.remove(n)

    # Make an output material
    output_shader = hair_mat.node_tree.nodes.new("ShaderNodeOutputMaterial")

    # Make the hair BSDF
    hair_shader = hair_mat.node_tree.nodes.new("ShaderNodeBsdfHairPrincipled")

    # Set the connections
    hair_mat.node_tree.links.new(hair_shader.outputs[0], output_shader.inputs[0])

    if "simulation_output" in obj.name:
        for slot in obj.material_slots:
            slot.material = hair_mat


def load_obj_file(path: str) -> bpy.types.Object:
    """Loads the obj files into memory as blender obj objects.

    Args:
        obj_file_paths (List[str]): The list of paths to obj files

    Returns:
        List[bpy.types.Object]: The loaded obj files as blender objects
    """
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.import_scene.obj(
        filepath=path,
        filter_glob="*.obj;*.mtl",
        use_edges=True,
        use_smooth_groups=True,
        use_split_objects=True,
        use_split_groups=True,
        use_groups_as_vgroups=False,
        use_image_search=True,
        split_mode="ON",
        axis_forward="Z",
        axis_up="Y",
    )

    # Selected object is the first one, append to our cache
    obj = bpy.context.selected_objects[0]
    name = path.split(".obj")[0]
    obj.name = name
    obj.data.name = name
    return obj


def load_obj_files(paths: List[str]) -> List[bpy.types.Object]:
    return [load_obj_file(p) for p in paths]


def scale_assets(oobj: bpy.types.Object, asset_objs: List[bpy.types.Object]):
    xpts = []
    ypts = []
    zpts = []
    for bb in oobj.bound_box:
        xpts.append(bb[0])
        ypts.append(bb[1])
        zpts.append(bb[2])

    x = max(xpts) - min(xpts)
    y = max(ypts) - min(ypts)
    z = max(zpts) - min(zpts)

    for aobj in asset_objs:
        print("scaling", aobj.data.name)

        # Increase the size of the backdrop to match the dims
        if "assets/backdrop" in aobj.data.name:
            aobj.dimensions = (x * 3, y * 2.5, z * 1.5)

        # Increase the size of the light
        if "assets/light" in aobj.data.name:
            scale = 0.5
            _, y, _ = oobj.dimensions
            aobj.dimensions = (x * scale, y, z * scale)


def position_assets(oobj: bpy.types.Object, asset_objs: List[bpy.types.Object]):
    xpts = []
    ypts = []
    zpts = []
    for bb in oobj.bound_box:
        xpts.append(bb[0])
        ypts.append(bb[1])
        zpts.append(bb[2])

    x = max(xpts) - min(xpts)
    y = max(ypts) - min(ypts)
    z = max(zpts) - min(zpts)

    for obj in asset_objs:
        print("positioning", obj.data.name)
        if "assets/backdrop" in obj.data.name:
            obj.location = (-x * 0.5, y, z * 0.1)

        if "assets/light" in obj.data.name:
            obj.location = (-x * 0.5, y, z * 1.2)


def place_camera(loc: Tuple[float, float, float], rot: Tuple[float, float, float]):
    cam_data = bpy.data.cameras.new("Camera")
    cam_obj = bpy.data.objects.new("Camera", object_data=cam_data)
    bpy.context.view_layer.active_layer_collection.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    cam_obj.location = loc
    cam_obj.rotation_euler = rot


## UNUSED
def build_animation_from_obj_files(all_obj_objects: List[bpy.types.Object]):
    """Loads a sequence of loaded blender objects and adds them to a given animation

    Args:
        all_obj_objects (List[bpy.types.Object]): The obj objects loaded from memory
    """
    # Set the starting frame to 0
    obj_frame_start = 0
    obj_frame_end = len(all_obj_objects) - 1

    # Set the scene frames in the UI.
    bpy.context.scene.frame_start = obj_frame_start
    bpy.context.scene.frame_end = obj_frame_end

    # Now, the high level idea here is simple. For each frame, we need to set EVERY object
    # as "invisible" on render except "frame". So if we have 500 frames worth of objects
    # we would then iterate through all the frames, set every object's "hide_render" field
    # to "True" and then just this frame's "hide_render" is set to "False", showing ONLY
    # this frame on the render.
    for frame in range(obj_frame_end):
        # VERY IMPORTANT. We need to set the frame here to ensure that the proper frame
        # is active when we set the frame states
        bpy.context.scene.frame_set(frame)

        # Now, we have to iterate through ALL frames to add the keyframe for this scene
        # frame.
        for i, ob in enumerate(all_obj_objects):
            # If our iteration has reached our designated frame, mark it as visible
            if i == frame:
                ob.hide_viewport = ob.hide_render = False
                ob.keyframe_insert(data_path="hide_viewport")
                ob.keyframe_insert(data_path="hide_render")
            # Otherwise, set it to invisible
            else:
                ob.hide_viewport = ob.hide_render = True
                ob.keyframe_insert(data_path="hide_viewport")
                ob.keyframe_insert(data_path="hide_render")

    # Now, set the material for all of the obj files to be the first one. From here, you
    # can edit just one material to make everything look the same.
    print("setting materials")
    make_hair_material(all_obj_objects)


def make_emission_material(asset_objs: List[bpy.types.Object]):
    mat_light = bpy.data.materials.get("Light")

    if mat_light is not None:
        # Delete the material so we can re-make it
        bpy.data.materials.remove(mat_light)

    # Setup a new material with the name
    mat_light = bpy.data.materials.new(name="Light")
    mat_light.use_nodes = True

    # Remove all tree nodes so we get a fresh start
    for n in mat_light.node_tree.nodes:
        mat_light.node_tree.nodes.remove(n)

    # Make an output material
    output_shader = mat_light.node_tree.nodes.new("ShaderNodeOutputMaterial")

    # Make an emission input material
    emission_shader = mat_light.node_tree.nodes.new("ShaderNodeEmission")

    # Set the emission strength to 5
    emission_shader.inputs[1].default_value = 5

    # Set up the tree node links and link the output emission to the input material
    # output
    mat_light.node_tree.links.new(emission_shader.outputs[0], output_shader.inputs[0])

    # This is a bit brittle, but for now find the assets/light and assign the material
    for obj in asset_objs:
        if "assets/light" in obj.name:
            for slot in obj.material_slots:
                slot.material = mat_light


def help():
    print(
        "usage: blender -b sim.blend -P main.py -- root_dir_name [optional] --cam_loc=x,y,z, --cam_rot=x,y,z (deg) file1 file2 file3"
    )


class args:
    def __init__(self):
        self.cam_loc: Tuple[float, float]
        self.cam_rot: Tuple[float, float]
        self.obj_file: str = ""

    def __repr__(self):
        items = ("%s = %r" % (k, v) for k, v in self.__dict__.items())
        return "<%s: {%s}>" % (self.__class__.__name__, ", ".join(items))


def parse_args(argv: List[str]):
    if "--" not in sys.argv:
        help()
        exit(1)

    a = args()
    for opt in argv:
        # Assumed to be an obj file
        if opt.endswith(".obj"):
            a.obj_file = opt
        if "--cam_loc" in opt:
            cam_loc_str = opt.split("=")[1]
            cam_loc = tuple(map(float, cam_loc_str.split(",")))
            a.cam_loc = cam_loc

        if "--cam_rot" in opt:
            cam_rot_str = opt.split("=")[1]
            cam_rot = tuple(map(math.radians, map(float, cam_rot_str.split(","))))
            a.cam_rot = cam_rot
    return a


if __name__ == "__main__":
    cam_loc = (-32, 161.5, 73)
    cam_rot = (math.radians(75), 0, math.radians(180))
    a = parse_args(sys.argv)

    bpy.ops.scene.new()
    print(f"Loading animation on file {a.obj_file}")

    root_dir_obj = load_obj_file(a.obj_file)

    # Put the backdrop and light in the scene
    # build_animation_from_obj_files(root_dir_objs)

    print("loading other assets")

    assets_directory_path = os.path.join(os.path.dirname(__file__), "assets")
    print("looking in assets dir", assets_directory_path)

    # Path to the assets dir obj files
    asset_file_paths = list(
        map(
            lambda x: os.path.join(assets_directory_path, x),
            filter(lambda x: x.endswith(".obj"), os.listdir(assets_directory_path)),
        )
    )
    print(f"[dbg]: Asset files found {asset_file_paths}")
    asset_objs = load_obj_files(asset_file_paths)
    bpy.ops.object.select_all(action="DESELECT")

    # Move the assets and make them fit the mesh
    scale_assets(root_dir_obj, asset_objs)
    position_assets(root_dir_obj, asset_objs)

    # Now that the assets are in, make the light source
    print("making the emission material")
    make_emission_material(asset_objs)

    # Toss the camera in there
    place_camera(cam_loc, cam_rot)
    bpy.ops.object.select_all(action="DESELECT")

    # Always use cycles
    bpy.context.scene.render.engine = "CYCLES"

    # Always use GPU
    bpy.context.scene.cycles.device = "GPU"

    # Save when the background flag is set
    if "-b" in sys.argv:
        bpy.ops.wm.save_as_mainfile(
            filepath=os.path.join(
                os.path.dirname(__file__), a.obj_file.split(".obj")[0] + ".blend"
            )
        )

    print("done loading animation")
