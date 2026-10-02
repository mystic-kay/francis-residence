import bpy,os,json
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
with open(os.path.join(root,'scripts','reference-materials.json')) as f:finishes=json.load(f)
for category,finish in finishes.items():
 material=bpy.data.materials.get(category)
 if not material or not finish.get('texture') or finish['texture']=='woven':continue
 for node in material.node_tree.nodes:
  if node.type!='TEX_IMAGE':continue
  kind=os.path.basename(node.image.filepath)
  if kind not in ['color.jpg','normal.jpg','roughness.jpg']:continue
  path=os.path.join(root,'public','textures',finish['texture'],kind)
  image=bpy.data.images.load(path,check_existing=True);image.colorspace_settings.name='sRGB' if kind=='color.jpg' else 'Non-Color';image.pack();node.image=image
 for node in material.node_tree.nodes:
  if node.type=='VECT_MATH' and node.operation=='SCALE':node.inputs[3].default_value=finish.get('scale',1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
print('Updated packed reference finishes')
