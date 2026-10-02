"""Exterior walls as textured stucco (Kenyan Wallmaster-style coating): white render and dark charcoal render.

Source walls carry both faces in one object ("render off-white both faces"), so each wall face is classified
by sampling rays over its hemisphere: faces that see open sky are exterior render, the rest stay interior paint.
Exterior faces get continuous world-space UVs in metres so the 2 m stucco tile has a true, unstretched scale."""
import bpy,bmesh,os,sys,json,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from refine_interior_realism import export_and_save,pack_surface
blend=os.path.join(root,'Francis-Web.blend')
# Terrain and see-through canopies do not count as cover; window glass does.
TRANSPARENT={'paving','lawn','pergolaglass','decor'}

def occluders():
 verts=[];faces=[]
 for o in bpy.data.objects:
  if o.type!='MESH' or o.get('category') in TRANSPARENT or o.get('category') is None:continue
  mw=o.matrix_world;off=len(verts);verts.extend(mw@v.co for v in o.data.vertices);faces.extend(tuple(off+i for i in p.vertices) for p in o.data.polygons)
 return BVHTree.FromPolygons(verts,faces)

def hemisphere(n,count=48):
 """Fixed, evenly spread directions over the hemisphere around normal n (golden-angle spiral)."""
 t=Vector((0,0,1)) if abs(n.z)<.9 else Vector((1,0,0));a=n.cross(t).normalized();b=n.cross(a)
 out=[]
 for i in range(count):
  z=.15+.85*(i+.5)/count;r=math.sqrt(1-z*z);phi=i*2.39996
  out.append((n*z+a*(r*math.cos(phi))+b*(r*math.sin(phi))).normalized())
 return out

def sky(q,n,tree):
 """Hemisphere rays reaching open sky from point q. Where the source normal points into the wall (the first hit is
 the wall's own opposite face, under 0.45 m, while the other side is open), the reversed normal is used."""
 ahead=tree.ray_cast(q+n*.012,n,120)[3];behind=tree.ray_cast(q-n*.012,-n,120)[3]
 if ahead is not None and ahead<.45 and (behind is None or behind>.45):n=-n
 return sum(1 for d in hemisphere(n) if tree.ray_cast(q+n*.012,d,120)[0] is None)

def classify(o,tree):
 """Return exterior face indices, grown across flat connected wall planes."""
 mw=o.matrix_world;nm=mw.to_3x3();ext=[]
 for f in o.data.polygons:
  if f.area<1e-6:continue
  n=(nm@f.normal).normalized();centre=mw@f.center
  # Sample the centre and points towards each corner: a long wall triangle's centroid can sit inside a pillar.
  corners=[mw@o.data.vertices[v].co for v in f.vertices];samples=[centre]+[centre.lerp(p,.7) for p in corners]
  if any(sky(q,n,tree)>=2 for q in samples):ext.append(f.index)
 return grow_planes(o,ext)

def grow_planes(o,ext):
 """Treat each flat, edge-connected wall plane as one surface: exterior when a quarter of its area sees sky.
 This stops corner or overhang triangles of an exterior wall staying as interior paint."""
 bm=bmesh.new();bm.from_mesh(o.data);bm.faces.ensure_lookup_table();mark=set(ext);seen=set();out=[]
 for f in bm.faces:
  if f.index in seen:continue
  region=[f];seen.add(f.index);stack=[f];n0=f.normal.copy();d0=n0.dot(f.calc_center_median())
  while stack:
   g=stack.pop()
   for e in g.edges:
    for h in e.link_faces:
     if h.index in seen or h.normal.dot(n0)<.999 or abs(n0.dot(h.calc_center_median())-d0)>.002:continue
     seen.add(h.index);region.append(h);stack.append(h)
  area=sum(h.calc_area() for h in region);hit=sum(h.calc_area() for h in region if h.index in mark)
  if area and hit/area>=.25:out.extend(h.index for h in region)
 bm.free();return out

def world_uv(o,indices=None):
 """Planar projection per face in metres: walls use (along-wall, height), horizontal faces use plan XY."""
 # Write into the layer glTF exports (source meshes keep the FBX 'UVChannel_1' active, not 'UVMap').
 mesh=o.data;uv=mesh.uv_layers.active or mesh.uv_layers.new(name='UVMap');mw=o.matrix_world;nm=mw.to_3x3()
 pick=set(indices) if indices is not None else None
 for f in mesh.polygons:
  if pick is not None and f.index not in pick:continue
  n=(nm@f.normal).normalized()
  for li in f.loop_indices:
   p=mw@mesh.vertices[mesh.loops[li].vertex_index].co
   if abs(n.z)>.7:uv.data[li].uv=(p.x,p.y)
   elif abs(n.x)>abs(n.y):uv.data[li].uv=(p.y*(1 if n.x>0 else -1),p.z)
   else:uv.data[li].uv=(p.x*(-1 if n.y>0 else 1),p.z)

def split_exterior(o,indices,mat):
 """Move the given faces of o into a new 'render' object with its own material."""
 new=o.copy();new.data=o.data.copy();bpy.context.collection.objects.link(new)
 keep=set(indices)
 for target,drop in ((new,lambda f:f.index not in keep),(o,lambda f:f.index in keep)):
  bm=bmesh.new();bm.from_mesh(target.data);bm.faces.ensure_lookup_table()
  bmesh.ops.delete(bm,geom=[f for f in bm.faces if drop(f)],context='FACES');bm.to_mesh(target.data);bm.free()
 new.data.materials.clear();new.data.materials.append(mat)
 new.name=o.name.replace('| walls','| exterior render');new['category']='render';new['finishGroup']='render';new['exteriorStucco']=True
 return new

def continuous_entrance_band():
 """The charcoal fin beside the living-room entrance (x 6.02-6.25) breaks between 2.70 m and 3.15 m, where the beam,
 slab edge and oak floor finish show through. Those faces become dark stucco and a 15 mm charcoal cladding plate
 brings the front and door-side faces flush with the fin above and below."""
 lo,hi=Vector((6.015,7.75,2.69)),Vector((6.26,9.2,3.165));moved=0
 for o in [o for o in bpy.data.objects if o.type=='MESH' and o.get('category') in ('walls','render','floor','ceiling')]:
  mw=o.matrix_world;nm=mw.to_3x3();idx=[]
  for f in o.data.polygons:
   c=mw@f.center;n=(nm@f.normal).normalized()
   if all(lo[i]<=c[i]<=hi[i] for i in range(3)) and (n.x<-.9 or n.y<-.9):idx.append(f.index)
  if idx:
   new=split_exterior(o,idx,bpy.data.materials['accent']);new.name=o.name.split(' |')[0]+' | entrance band';new['category']='accent';new['finishGroup']='accent';world_uv(new);moved+=len(idx)
 v=lambda x0,x1,y0,y1,z0,z1:[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
 faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
 plates=[]
 for name,box in (('front',(6.023,6.253,7.761,7.776,2.70,3.15)),('door side',(6.023,6.038,7.776,9.176,2.70,3.15))):
  mesh=bpy.data.meshes.new('Entrance band cladding '+name);mesh.from_pydata(v(*box),[],faces);mesh.update()
  o=bpy.data.objects.new('Level 0 | entrance band cladding '+name,mesh);bpy.context.collection.objects.link(o);mesh.materials.append(bpy.data.materials['accent'])
  o['category']='accent';o['finishGroup']='accent';o['floor']=0;o['exteriorStucco']=True;world_uv(o);plates.append(name)
 return {'recolouredFaces':moved,'claddingPlates':plates}

if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 assert not any(o.get('exteriorStucco') for o in bpy.data.objects),'Already applied: restore the previous Francis-Web.blend before rerunning'
 cfg=json.load(open(os.path.join(root,'scripts','reference-materials.json')))
 for cat in ['render','accent','featurewall']:pack_surface(cat,cfg)
 tree=occluders();report={'split':{},'darkFaces':0}
 for o in [o for o in bpy.data.objects if o.type=='MESH' and o.get('category')=='walls']:
  ext=classify(o,tree);report['split'][o.name]=[len(ext),len(o.data.polygons)]
  if ext:new=split_exterior(o,ext,bpy.data.materials['render']);world_uv(new)
 # Boundary-wall pillars and their caps (Generic Model Boxes on the site perimeter) become dark stucco.
 source=json.load(open(os.path.join(root,'scene-inspection.json')))['objects']
 def perimeter(b):
  mn,mx=b['min'],b['max'];near=lambda v,lo,hi:min(abs(v-lo),abs(v-hi))<.7
  return 'Generic Model Box' in b['name'] and mx[2]>=2.0 and mn[2]<2.6 and (mx[0]-mn[0]<.6 or mx[1]-mn[1]<.6) and (near(mn[0],-3.86,17.14) or near(mx[0],-3.86,17.14) or near(mn[1],-3.02,21.51) or near(mx[1],-3.02,21.51)) and (mx[2]-mn[2]>1.5 or mn[2]>2.3)
 pillars=[(Vector(b['min']),Vector(b['max'])) for b in source if perimeter(b)]
 for o in [o for o in bpy.data.objects if o.type=='MESH' and o.get('category')=='details' and o.get('floor') in (-1,0)]:
  mw=o.matrix_world;idx=[f.index for f in o.data.polygons if any(all(all(a[i]-.004<=(mw@o.data.vertices[v].co)[i]<=b[i]+.004 for i in range(3)) for v in f.vertices) for a,b in pillars)]
  if idx:
   new=split_exterior(o,idx,bpy.data.materials['accent']);new.name=o.name.replace('| details','| boundary pillars');new['category']='accent';new['finishGroup']='accent';world_uv(new);report['pillarFaces']=report.get('pillarFaces',0)+len(idx)
 report['pillarBoxes']=len(pillars)
 report['entranceBand']=continuous_entrance_band()
 # Charcoal façade and the entrance feature wall are exterior throughout: same stucco, dark tint.
 for o in [o for o in bpy.data.objects if o.type=='MESH' and o.get('category') in ('accent','featurewall')]:
  world_uv(o);o['exteriorStucco']=True;report['darkFaces']+=len(o.data.polygons)
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 path=os.path.join(root,'public','interior-refinement.json');data=json.load(open(path));data['exteriorStucco']=report
 with open(path,'w') as f:json.dump(data,f,indent=2)
 export_and_save();print('EXTERIOR STUCCO SAVED',json.dumps(report))
