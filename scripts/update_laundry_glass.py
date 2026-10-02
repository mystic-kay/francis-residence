"""Update only the rear laundry glass infill and its rail in the prepared Blender scene."""
import bpy,bmesh,os,ast,math
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
assert not any(o.name.startswith('Laundry |') for o in bpy.data.objects),'Laundry update already applied'
removed=0
for o in list(bpy.data.objects):
 if o.type!='MESH' or o.get('category')!='details':continue
 bm=bmesh.new();bm.from_mesh(o.data)
 faces=[]
 for face in bm.faces:
  points=[o.matrix_world@v.co for v in face.verts]
  panel=all(-1.063<=p.x<=2.239 and 18.769<=p.y<=18.783 and 3.674<=p.z<=4.251 for p in points)
  rail=all(-1.063<=p.x<=2.239 and 18.755<=p.y<=18.797 and 4.249<=p.z<=4.291 for p in points)
  if panel or rail:faces.append(face)
 if faces:
  removed+=len(faces);bmesh.ops.delete(bm,geom=faces,context='FACES');bm.to_mesh(o.data);o.data.update()
 bm.free()
assert 0<removed<=24,f'Unexpected laundry face count: {removed}'
# Reuse the exact hardware geometry used by the other selected balcony panels.
source=open(os.path.join(root,'scripts','prepare_scene.py')).read();tree=ast.parse(source)
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='guard_run')
exec(compile(ast.Module(body=[function],type_ignores=[]),'guard_run','exec'))
before=set(bpy.data.objects);guard_run((-1.062,18.776),(2.238,18.776),3.675,.575)
created=[o for o in bpy.data.objects if o not in before]
groups={cat:[o for o in created if o.get('finishGroup')==cat] for cat in ['balconyglass','balconyrail']}
for cat,objects in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.data.materials.append(bpy.data.materials[cat]);o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name='Laundry | '+cat;o['category']=cat;o['floor']=1;o['sourcePanel']='KD Box - Generic Model Box [2328756]'
# Keep planting in the Blender file; export only the building with lean web materials.
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
print('LAUNDRY GLASS UPDATED; removed source faces:',removed)
