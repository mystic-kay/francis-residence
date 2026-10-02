"""Remove, at the client's request: all nine garden bollards, the wall light over the front door (with the leftover
light bar), the white electrical box beside the gate motor, and the six white full-height downpipe placeholders."""
import bpy,os,sys,json,re
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import remove_faces
from refine_interior_realism import export_and_save
blend=os.path.join(root,'Francis-Web.blend')
SRC=json.load(open(os.path.join(root,'scene-inspection.json')))['objects']
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 boxes=[]
 for s in SRC:
  mn,mx=Vector(s['min']),Vector(s['max'])
  if 'KE Bollard Light' in s['name']:boxes.append(((mn.x-.06,mn.y-.06,-.7),(mx.x+.06,mx.y+.06,.8)))
  if re.search(r'Electrical Equipment Box \[2327055\]',s['name']):boxes.append((tuple(mn),tuple(mx)))
  if 'Generic Model Box' in s['name'] and (mx-mn).z>4 and (mx-mn).x<.3 and (mx-mn).y<.3:boxes.append((tuple(mn),tuple(mx)))
 # Front-door wall light: relocated fitting, lenses, bracket and any remaining light bar at the door head.
 boxes.append(((-.85,8.90,1.95),(.75,9.22,2.45)))
 removed={}
 for o in [o for o in bpy.data.objects if o.type=='MESH' and not o.get('frontDoor') and o.get('category') not in ('metal','lightstrip','walls','render','accent','featurewall','frontdoor','frontdoorframe','frontdoorhardware','glass','doors','floor','paving','lawn','ceiling')]:
  n=remove_faces(o,boxes)
  if n:removed[o.name]=n
 for o in [o for o in bpy.data.objects if o.type=='MESH' and len(o.data.polygons)==0]:bpy.data.objects.remove(o,do_unlink=True)
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 path=os.path.join(root,'public','interior-refinement.json');data=json.load(open(path));data['removedClutter']=removed
 with open(path,'w') as f:json.dump(data,f,indent=2)
 export_and_save();print('CLUTTER REMOVED',json.dumps(removed))
