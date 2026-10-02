"""Apply the annotated garden correction without altering a single kerb vertex."""
import bpy,os,sys,json
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from garden_layout import create_marked_lawn,LANDSCAPED_FOOTPRINT,FRONT_WALKWAY_REGIONS
bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
kerbs={o.name:[list(o.matrix_world@v.co) for v in o.data.vertices] for o in bpy.data.objects if o.type=='MESH' and o.get('category')=='kerb'}
converted=[]
for o in list(bpy.data.objects):
 if o.type!='MESH':continue
 if any('['+str(i)+']' in o.name for i in FRONT_WALKWAY_REGIONS):
  o['category']='paving';o['finishGroup']='paving';o.data.materials.clear();o.data.materials.append(bpy.data.materials['paving']);converted.append(o.name)
 elif o.name.startswith('Garden |') and o.get('category')=='lawn':bpy.data.objects.remove(o,do_unlink=True)
assert len(converted)==2,'Both front walkway regions must exist'
o=create_marked_lawn();o.data.materials.append(bpy.data.materials['lawn'])
assert kerbs=={o.name:[list(o.matrix_world@v.co) for v in o.data.vertices] for o in bpy.data.objects if o.type=='MESH' and o.get('category')=='kerb'},'Kerbs must remain untouched'
links=[]
for material in bpy.data.materials:
 if not material.use_nodes:continue
 bs=material.node_tree.nodes.get('Principled BSDF')
 if not bs:continue
 for key in ['Base Color','Roughness','Normal']:
  for link in list(bs.inputs[key].links):links.append((material.node_tree,link.from_socket,link.to_socket));material.node_tree.links.remove(link)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o.type=='MESH' and o.get('category'):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(root,'public','models','francis.glb'),export_format='GLB',export_extras=True,export_yup=True,use_selection=True)
for tree,a,b in links:tree.links.new(a,b)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
with open(os.path.join(root,'public','garden-validation.json'),'w') as f:json.dump({'lawnStatus':'Grass in the user-marked large landscaped area; original tank-side planted strip retained','footprint':LANDSCAPED_FOOTPRINT,'frontWalkway':'Original Subregions 2331126 and 2331133 are paving','kerbStatus':'Original geometry unchanged, exact vertex comparison passed'},f,indent=2)
print('MARKED LANDSCAPE GRASSED; FRONT WALKWAY PAVED; KERBS UNCHANGED')
