"""Give the staircase its own finishes and keep only the central railing.
- Treads, risers and landings (Monolithic Run/Landing boxes) move from the floor groups to 'stairs'.
- Railing parts in the stairwell (x 3.6-6.1, y 9.3-13.45) are split by loose part: the run between the two flights
  (x 4.6-5.1, y >= 10.5) becomes 'stairrail'; wall-side and landing railings are removed. Guarding that starts on the
  top floor (z >= 6.1) is left alone."""
import bpy,bmesh,os,sys,json
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from refine_interior_realism import export_and_save,pack_surface
from fixtures_and_lamps import take
blend=os.path.join(root,'Francis-Web.blend')
SRC=json.load(open(os.path.join(root,'scene-inspection.json')))['objects']
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 assert not any(o.get('category')=='stairs' for o in bpy.data.objects),'Already applied'
 cfg=json.load(open(os.path.join(root,'scripts','reference-materials.json')))
 for cat in ['stairs','stairrail']:pack_surface(cat,cfg)
 boxes=[(Vector(s['min'])-Vector((.004,)*3),Vector(s['max'])+Vector((.004,)*3)) for s in SRC if 'Monolithic' in s['name']]
 made=take([o for o in bpy.data.objects if o.type=='MESH' and o.get('category') in ('floor','bedfloor')],
  lambda ob,f,p:any(all(all(a[i]<=q[i]<=b[i] for i in range(3)) for q in p) for a,b in boxes),bpy.data.materials['stairs'],'stairs','Stairs | treads and landings')
 stairs=sum(len(o.data.polygons) for o in made);kept=removed=0
 for o in [o for o in bpy.data.objects if o.type=='MESH' and o.get('category')=='pergolaframe' and o.get('floor') in (0,1,2)]:
  bm=bmesh.new();bm.from_mesh(o.data);bm.faces.ensure_lookup_table();mw=o.matrix_world;seen=set();keep=[];drop=[]
  for f in bm.faces:
   if f.index in seen:continue
   comp=[];st=[f];seen.add(f.index)
   while st:
    g=st.pop();comp.append(g)
    for e in g.edges:
     for h in e.link_faces:
      if h.index not in seen:seen.add(h.index);st.append(h)
   pts=[mw@v.co for g in comp for v in g.verts];mn=[min(p[i] for p in pts) for i in range(3)];mx=[max(p[i] for p in pts) for i in range(3)]
   if not(mn[0]>=3.6 and mx[0]<=6.1 and mn[1]>=9.3 and mx[1]<=13.45 and mn[2]<6.1 and mx[2]<7.2):continue
   (keep if mn[0]>=4.6 and mx[0]<=5.1 and mn[1]>=10.5 else drop).extend(g.index for g in comp)
  bm.free()
  if drop:
   bm=bmesh.new();bm.from_mesh(o.data);bm.faces.ensure_lookup_table();d=set(drop);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.index in d],context='FACES');bm.to_mesh(o.data);bm.free();removed+=len(drop)
   # indices shift after deletion; recompute the kept set by position
  if keep:
   new=take([o],lambda ob,f,p:all(4.6-.002<=q.x<=5.1+.002 and 10.5-.002<=q.y<=13.45 and q.z<7.2 for q in p),bpy.data.materials['stairrail'],'stairrail','Stairs | central railing');kept+=sum(len(n.data.polygons) for n in new)
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 export_and_save();print('STAIRS SAVED',{'stairFaces':stairs,'railKept':kept,'railRemoved':removed})
