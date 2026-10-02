"""Make two aluminium glass walls into stacking sliders the website can animate.
- Top floor, dining room to pergola terrace: 4 panels at y 15.0 (System Panel Glazed 1781748/758/774/789).
- First floor, primary suite to its balcony: 3 panels at x 9.47 (1781650/660/674).
Panel 1 of each wall is fixed. Each other panel (its glass, top and bottom rails and leading mullion) becomes its own
object with slideGroup and slideVec (Blender metres): it stacks behind panel 1 on its own track, 70 mm apart."""
import bpy,os,sys,json
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from fixtures_and_lamps import take
from refine_interior_realism import export_and_save
blend=os.path.join(root,'Francis-Web.blend')
SRC={s['name']:s for s in json.load(open(os.path.join(root,'scene-inspection.json')))['objects']}
def panel(i):s=next(v for k,v in SRC.items() if f'[{i}]' in k);return Vector(s['min']),Vector(s['max'])
WALLS=[('terrace','Top-floor dining to terrace',2,'x',(1781748,1781758,1781774,1781789),(14.94,15.04),1),
       ('balcony','Primary suite to balcony',1,'y',(1781650,1781660,1781674),(9.46,9.56),-1)]
SKIP={'walls','render','floor','bedfloor','livingfloor','ceiling','accent','featurewall','coping','roof'}
def inside(pts,a,b):return all(all(a[i]-.004<=p[i]<=b[i]+.004 for i in range(3)) for p in pts)
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 assert not any(o.get('slideGroup') for o in bpy.data.objects),'Already applied'
 report={}
 for gid,label,floor,axis,ids,band,inward in WALLS:
  boxes=[panel(i) for i in ids];a1=boxes[0][0];moved=[]
  for k,(a,b) in enumerate(boxes[1:],start=1):
   if axis=='x':lo=Vector((a.x-.065,band[0],a.z-.07));hi=Vector((b.x+.003,band[1],b.z+.07));vec=[a1.x-a.x,inward*.07*k,0]
   else:lo=Vector((band[0],a.y-.065,a.z-.07));hi=Vector((band[1],b.y+.003,b.z+.07));vec=[inward*.07*k,a1.y-a.y,0]
   objs=[o for o in bpy.data.objects if o.type=='MESH' and o.get('floor')==floor and o.get('category') not in SKIP and not o.get('slideGroup')]
   for o in objs:
    mats=[m.name for m in o.data.materials]
    made=take([o],lambda ob,f,p,lo=lo,hi=hi:inside(p,lo,hi),o.data.materials[0],o.get('category'),f'Slider | {gid} panel {k+1}')
    for n in made:
     n.data.materials.clear()
     for m in mats:n.data.materials.append(bpy.data.materials[m])
     n['slideGroup']=gid;n['slideLabel']=label;n['slideVec']=vec;n['floor']=floor;moved.append(n.name)
  report[gid]=moved
 assert all(report.values()),report
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 export_and_save();print('SLIDERS SAVED',json.dumps(report))
