# blitz
🫥 Blender Animation Engine Supporting Huge Meshes

## Working with this tool
This system allows you to import meshes of arbitrary size (assuming you have the RAM and the patience) and sets up a scene with backdrop.

### Setting Up Your First Render
This system operates similarly to something like ffmpeg, meaning that if you have a giant sequence of files in obj format then you need to apply the command one at a time to load them and make a file which works in blender. For example, say we have a bunch of files in a test folder, we can list them all and load them in parallel as:
```bash
# The -- at the end is important
$ find . test/ | xargs -n1 -P10 blender -b -P main.py --
```
This will generate all of your files in whatever directory that you have. To render them, simply do the following:
```bash
$ for i in $(find .blend test/) | xargs -n1 -P10 blender -b $i -E CYCLES -o //$i -a
```
