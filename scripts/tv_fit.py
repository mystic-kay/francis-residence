"""Fit the new TVs to the existing furniture: bedroom one already has a chest of drawers under its TV, and the
top-floor lounge has a 0.9 m casework cabinet (Casework Box 2323195), so the added floating units are removed and
the lounge TV is lifted to a 1.45 m centre, clear of the cabinet top."""
import bpy,bmesh,os,sys,json
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from refine_interior_realism import export_and_save
blend=os.path.join(root,'Francis-Web.blend')
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend);report={'removedUnits':[],'liftedFaces':0}
 for o in [o for o in bpy.data.objects if o.get('siteRealism') and o.get('category')=='tvunit']:report['removedUnits'].append(o.name);bpy.data.objects.remove(o,do_unlink=True)
 for o in [o for o in bpy.data.objects if o.get('siteRealism') and o.type=='MESH' and o.get('category')=='decor']:
  bm=bmesh.new();bm.from_mesh(o.data);mw=o.matrix_world;inv=mw.inverted();n=0
  for v in bm.verts:
   p=mw@v.co
   if 2.0<p.x<2.2 and 12.7<p.y<14.3 and 6.6<p.z<8.0 and not o.get('tvLifted'):v.co=inv@(p+Vector((0,0,.23)));n+=1
  if n:bm.to_mesh(o.data);o['tvLifted']=True;report['liftedFaces']+=n
  bm.free()
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 path=os.path.join(root,'public','interior-refinement.json');data=json.load(open(path));data['tvFit']=report
 with open(path,'w') as f:json.dump(data,f,indent=2)
 export_and_save();print('TV FIT SAVED',json.dumps(report))
