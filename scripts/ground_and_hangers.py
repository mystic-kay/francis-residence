"""Seat floating items: bollards (modelled at house floor level 0.0) drop onto the ground beneath them, and
shower rain heads gain a chrome ceiling arm instead of hanging in mid-air."""
import bpy,bmesh,os,sys,json,re
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import created,material
from refine_interior_realism import export_and_save
from modern_dining_set import tube
blend=os.path.join(root,'Francis-Web.blend')
SRC=json.load(open(os.path.join(root,'scene-inspection.json')))['objects']
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 assert not any(o.get('groundedFittings') for o in bpy.data.objects),'Already applied'
 dg=bpy.context.evaluated_depsgraph_get();sc=bpy.context.scene;report={'bollards':[],'rainHeads':[]}
 fittings=[o for o in bpy.data.objects if o.type=='MESH' and o.get('cleanSite')]
 for s in [s for s in SRC if 'KE Bollard Light' in s['name']]:
  c=(Vector(s['min'])+Vector(s['max']))/2
  hide=[o for o in fittings];[o.hide_set(True) for o in hide]
  ok,loc,*_=sc.ray_cast(bpy.context.evaluated_depsgraph_get(),Vector((c.x,c.y,.5)),Vector((0,0,-1)),distance=3)
  [o.hide_set(False) for o in hide]
  ground=loc.z if ok else 0.0;dz=ground-0.0
  for o in fittings:
   bm=bmesh.new();bm.from_mesh(o.data);mw=o.matrix_world;inv=mw.inverted();moved=False
   for v in bm.verts:
    p=mw@v.co
    if (p.x-c.x)**2+(p.y-c.y)**2<.012 and -.01<=p.z<=.76:v.co=inv@(p+Vector((0,0,dz)));moved=True
   if moved:bm.to_mesh(o.data)
   bm.free()
  report['bollards'].append({'at':[round(c.x,2),round(c.y,2)],'ground':round(ground,3)})
 chrome=material('Decor | brushed chrome','#c7ccd0',.22,.95);created.clear()
 for s in [s for s in SRC if 'shower rain head' in s['name']]:
  mn,mx=Vector(s['min']),Vector(s['max']);c=(mn+mx)/2
  ok,loc,*_=sc.ray_cast(dg,Vector((c.x,c.y,mx.z+.01)),Vector((0,0,1)),distance=1.5)
  if not ok:continue
  tube('Shower | ceiling arm',[(c.x,c.y,mx.z),(c.x,c.y,loc.z)],.011,'decor',chrome)
  report['rainHeads'].append({'name':s['name'].strip()[:40],'armMetres':round(loc.z-mx.z,2)})
 if created:
  bpy.ops.object.select_all(action='DESELECT')
  for o in created:o.select_set(True)
  bpy.context.view_layer.objects.active=created[0];bpy.ops.object.join();o=bpy.context.object;o.name='Shower | chrome ceiling arms';o['category']='decor';o['finishGroup']='decor';o['floor']=0;o['groundedFittings']=True
 for o in fittings:o['groundedFittings']=True
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 path=os.path.join(root,'public','interior-refinement.json');data=json.load(open(path));data['groundedFittings']=report
 with open(path,'w') as f:json.dump(data,f,indent=2)
 export_and_save();print('GROUNDED SAVED',json.dumps(report))
