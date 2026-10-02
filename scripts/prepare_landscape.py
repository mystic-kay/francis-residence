import bpy,os
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for asset in ['tree_small_02','shrub_01']:
 directory=os.path.join(root,'assets',asset)
 bpy.ops.wm.open_mainfile(filepath=os.path.join(directory,asset+'.blend'))
 chosen=asset+'_LOD1' if asset=='tree_small_02' else 'shrub_01_h_LOD2'
 for o in list(bpy.data.objects):
  if o.name!=chosen:bpy.data.objects.remove(o,do_unlink=True)
 optimized=os.path.join(directory,'optimized');os.makedirs(optimized,exist_ok=True)
 for image in bpy.data.images:
  candidate=os.path.join(directory,'textures',os.path.basename(bpy.path.abspath(image.filepath)))
  if os.path.exists(candidate):image.filepath=candidate;image.reload()
  if image.size[0]>512:image.scale(512,512)
  if image.size[0]>0:
   out=os.path.join(optimized,image.name.split('.')[0]+'.png');bpy.context.scene.render.image_settings.file_format='PNG';bpy.context.scene.render.image_settings.color_depth='8';bpy.context.scene.view_settings.view_transform='Standard' if image.colorspace_settings.name=='sRGB' else 'Raw';image.save_render(out,scene=bpy.context.scene);image.filepath=out;image.reload();image.pack()
 total=0
 for o in list(bpy.data.objects):
  if o.type!='MESH':bpy.data.objects.remove(o,do_unlink=True);continue
  count=len(o.data.polygons)
  if count>60000:
   mod=o.modifiers.new('Web polygon budget','DECIMATE');mod.ratio=60000/count;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
  total+=len(o.data.polygons)
 bpy.ops.export_scene.gltf(filepath=os.path.join(root,'public','models',asset+'.glb'),export_format='GLB',export_yup=True)
 print('LANDSCAPE',asset,total,'faces')
