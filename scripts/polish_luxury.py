import bpy,os,sys
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import add_living_curtains
bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
for o in bpy.data.objects:
 if o.name.startswith('Luxury | fabric | Decor |'):o['category']='decor';o['finishGroup']='decor'
assert not any(o.get('category')=='curtains' for o in bpy.data.objects),'Curtains already added'
add_living_curtains()
material=bpy.data.materials['curtains'];nodes=material.node_tree.nodes;links=material.node_tree.links;bs=nodes.get('Principled BSDF');noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=220;bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.002;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
saved=[]
for m in bpy.data.materials:
 if not m.use_nodes:continue
 bs=m.node_tree.nodes.get('Principled BSDF')
 if not bs:continue
 for key in ['Base Color','Roughness','Normal']:
  for link in list(bs.inputs[key].links):saved.append((m.node_tree,link.from_socket,link.to_socket));m.node_tree.links.remove(link)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o.type=='MESH' and o.get('category'):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(root,'public','models','francis.glb'),export_format='GLB',export_extras=True,export_yup=True,use_selection=True)
for tree,a,b in saved:tree.links.new(a,b)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(root,'Francis-Web.blend'));print('CURTAINS AND ACCENT COLORS FINISHED')
