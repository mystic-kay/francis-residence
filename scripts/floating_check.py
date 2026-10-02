"""Report loose parts that touch nothing: no geometry within 3 cm of any face of their bounding box and not
standing on the site ground (z < -0.55). Writes a JSON list for review."""
import bpy,bmesh,json,sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=sys.argv[sys.argv.index('--')+1]
objs=[o for o in bpy.data.objects if o.type=='MESH' and o.get('category') is not None]
verts=[];faces=[];owner=[]
for oi,o in enumerate(objs):
 mw=o.matrix_world;off=len(verts);verts.extend(mw@v.co for v in o.data.vertices)
 for p in o.data.polygons:faces.append(tuple(off+i for i in p.vertices));owner.append((oi,p.index))
tree=BVHTree.FromPolygons(verts,faces);found=[]
for oi,o in enumerate(objs):
 bm=bmesh.new();bm.from_mesh(o.data);bm.faces.ensure_lookup_table();mw=o.matrix_world;seen=set()
 for f in bm.faces:
  if f.index in seen:continue
  comp=[];stack=[f];seen.add(f.index)
  while stack:
   g=stack.pop();comp.append(g)
   for e in g.edges:
    for h in e.link_faces:
     if h.index not in seen:seen.add(h.index);stack.append(h)
  ids={g.index for g in comp};pts=[mw@v.co for g in comp for v in g.verts]
  mn=Vector([min(p[i] for p in pts) for i in range(3)]);mx=Vector([max(p[i] for p in pts) for i in range(3)]);size=mx-mn
  if size.length<.05 or mn.z<-.55:continue
  ok=False
  for axis in range(3):
   for sgn in (-1,1):
    d=Vector((0,0,0));d[axis]=sgn;a,b=[i for i in range(3) if i!=axis]
    for u in (.1,.5,.9):
     for v in (.1,.5,.9):
      q=Vector((0,0,0));q[a]=mn[a]+size[a]*u;q[b]=mn[b]+size[b]*v;q[axis]=(mx if sgn>0 else mn)[axis]+sgn*.001
      h=tree.ray_cast(q,d,.03)
      if h[0] is not None and not(owner[h[2]][0]==oi and owner[h[2]][1] in ids):ok=True;break
      # also probe back into the part's own footprint: contact may be on the inside of the bbox
      h=tree.ray_cast(q-d*.0015,d,.03)
      if h[0] is not None and not(owner[h[2]][0]==oi and owner[h[2]][1] in ids):ok=True;break
     if ok:break
    if ok:break
   if ok:break
  if not ok:found.append({'object':o.name,'category':o.get('category'),'min':[round(x,2) for x in mn],'max':[round(x,2) for x in mx],'faces':len(comp)})
 bm.free()
json.dump(found,open(out,'w'),indent=1);print('FLOATING',len(found))
