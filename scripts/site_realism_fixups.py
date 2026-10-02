"""Follow-up to site_realism.py: timber on the tank screen's return side, the old door handle and lock removed,
and the entrance wall light moved off the new door leaf onto the wall beside the frame."""
import bpy,bmesh,os,sys,json
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import remove_faces
from refine_interior_realism import export_and_save
from site_realism import take,inside,meshes
blend=os.path.join(root,'Francis-Web.blend')
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 report={}
 # Return side of the tank screen: Generic Model Boxes 2329661 onwards along y 0.44-0.46.
 report['screenReturnFaces']=take(meshes(['details']),lambda c,pts:inside(pts,(-3.50,.43,-.62),(-.85,.47,1.18)),bpy.data.materials['gate'],'gate','tank screen return')
 # Source door's pull and lock, left standing in front of and inside the new leaf.
 report['oldDoorHardwareFaces']=sum(remove_faces(o,[((.55,9.0,1.17),(.67,9.17,1.93)),((.57,9.2,.89),(.61,9.35,1.31))]) for o in meshes(['metal','wood']) if o.get('floor')==0)
 # External wall light (KE WL 10 W, 2200 AFFL) sat on the door leaf; shift it 0.75 m onto the wall left of the frame.
 moved=0
 for o in [o for o in bpy.data.objects if o.type=='MESH' and o.get('lightZone')=='hall']:
  bm=bmesh.new();bm.from_mesh(o.data);mw=o.matrix_world;inv=mw.inverted();verts=set()
  for f in bm.faces:
   if all(.06<=(mw@v.co).x<=.22 and 9.02<=(mw@v.co).y<=9.16 and 2.09<=(mw@v.co).z<=2.31 for v in f.verts):verts|=set(f.verts);moved+=1
  for v in verts:v.co=inv@(mw@v.co+Vector((-.75,0,0)))
  bm.to_mesh(o.data);bm.free()
 report['wallLightFacesMoved']=moved
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 path=os.path.join(root,'public','interior-refinement.json');data=json.load(open(path));data['siteRealismFixups']=report
 with open(path,'w') as f:json.dump(data,f,indent=2)
 export_and_save();print('FIXUPS SAVED',json.dumps(report))
