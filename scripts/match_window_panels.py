"""Panels between the stacked front windows (grey Generic Model Boxes) take the stucco of their section:
white for 2328785/2328786 in the white bay, dark for 2328790/2328791 and sill strip 2329148 in the charcoal bay."""
import bpy,os,sys,json
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from refine_interior_realism import export_and_save
from site_realism import take,inside,meshes
blend=os.path.join(root,'Francis-Web.blend')
SRC={s['name']:s for s in json.load(open(os.path.join(root,'scene-inspection.json')))['objects']}
def box(id_):
 s=next(v for k,v in SRC.items() if f'[{id_}]' in k);return Vector(s['min']),Vector(s['max'])
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend);report={}
 for ids,cat in (((2328785,2328786),'render'),((2328790,2328791,2329148),'accent')):
  for i in ids:
   a,b=box(i)
   report[i]=take(meshes(['details']),lambda c,pts,a=a,b=b:inside(pts,a,b,.004),bpy.data.materials[cat],cat,'window panel '+cat)
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 export_and_save();print('PANELS MATCHED',report)
