# blitz
🫥 Blender Animation Engine Supporting Huge Meshes

## Working with this tool
This system allows you to import meshes of arbitrary size (assuming you have the RAM and the patience) and sets up a scene with backdrop.

### Setting Up Your First Render
First, you need to invoke the setup script over your obj folder, below is an example
```bash
# Spin up the script and point it to your obj folder, optionall setting the camera
$ blender -b -P main.py -- obj_folder_name_here --cam_loc=-32,161.5,73 --cam_rot=75,0,180

# Now you should have a "sim.blend" file
$ blender -b sim.blend -E CYCLES -o //render -a

# Now you should have a rendered image. You can customize this depending on how many frames that you have etc
```
