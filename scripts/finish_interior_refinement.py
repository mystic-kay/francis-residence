"""Final fit checks: remove overlapping source lamp and seat the new throw cushions."""
import bpy,os,sys,json,collections
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
import luxury_interiors as luxe
from refine_interior_realism import add_throw_pillows,export_and_save
bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
for o in list(bpy.data.objects):
 if o.type=='MESH' and o.get('category')=='details':luxe.remove_faces(o,[((9.885,13.035,0),(9.915,13.065,1.60)),((9.680,12.830,1.450),(10.120,13.270,1.700))])
 if o.type=='MESH' and o.name.startswith('Luxury |') and o.get('category') in ['decor','fabric']:luxe.remove_faces(o,[((9.30,9.8,.50),(9.9,12.75,1.05))])
 if o.get('category')=='livingpillows':bpy.data.objects.remove(o,do_unlink=True)
luxe.created.clear();pillows=add_throw_pillows();bpy.context.view_layer.update();edges=[]
for o in luxe.created:
 uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
 for f in o.data.polygons:
  normal=o.matrix_world.to_3x3()@f.normal;axis=max(range(3),key=lambda i:abs(normal[i]));axes=[i for i in range(3) if i!=axis]
  for idx in f.loop_indices:
   p=o.matrix_world@o.data.vertices[o.data.loops[idx].vertex_index].co;uv.data[idx].uv=(p[axes[0]],p[axes[1]])
 if not o.get('throwPillow'):edges.append(o)
bpy.ops.object.select_all(action='DESELECT')
for o in edges:o.select_set(True)
bpy.context.view_layer.objects.active=edges[0];bpy.ops.object.join();bpy.context.object.name='Refined | throw pillow sewn edges'
report=json.load(open(os.path.join(root,'public','interior-refinement.json')));report['pillows']=pillows
with open(os.path.join(root,'public','interior-refinement.json'),'w') as f:json.dump(report,f,indent=2)
export_and_save();print('FINAL CUSHION FIT AND LAMP CLEANUP SAVED')
