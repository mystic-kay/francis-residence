"""Replace both dining sets (top floor and beside the ground-floor kitchen) with walnut and bouclé."""
import bpy,os,sys,json,math
from mathutils import Vector,Matrix
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
import luxury_interiors as luxe
from luxury_interiors import finish,created,remove_faces,material
from refine_interior_realism import export_and_save,pack_surface
blend=os.path.join(root,'Francis-Web.blend')
TOP=.75

# Each room keeps the source table's centre line; masks are the exact source footprints.
ROOMS=[
 {'id':'roof','name':'Terrace dining','floor':2,'z':6.15,'center':(3.60,16.80),'size':(2.40,1.00),'axis':'x',
  'chairs':[(x,16.80+s*.80,0 if s<0 else math.pi) for x in (2.80,3.60,4.40) for s in (-1,1)],
  'masks':{'wood':[((2.40,16.30,6.14),(4.80,17.30,6.72))],'fabric':[((2.53,15.72,6.14),(4.67,17.88,6.97))]},'pendants':None},
 # Ground floor: Casework Box table 900 x 1800 and six box-frame chairs, between the island stools and the east wall.
 # The table moves 0.5 m north so both end chairs clear the walls; the pendants are re-centred over it.
 {'id':'kitchen','name':'Dining beside the kitchen','floor':0,'z':0.0,'center':(9.27,16.87),'size':(.90,1.70),'axis':'y',
  'chairs':[(9.27+s*.67,16.87+d,s*math.pi/2) for s in (-1,1) for d in (-.42,.42)]+[(9.27,15.47,0),(9.27,18.27,math.pi)],
  'masks':{'wood':[((8.81,15.46,-.01),(9.73,17.28,.76)),((8.41,15.69,-.01),(8.88,17.06,.91)),((9.66,15.69,-.01),(10.13,17.06,.91)),((9.03,15.08,-.01),(9.50,15.56,.91)),((9.03,17.19,-.01),(9.50,17.66,.91)),((9.10,16.20,1.94),(9.44,16.54,3.01))],
           'lighting':[((9.10,16.20,1.94),(9.44,16.54,3.01))]},
  'pendants':{'ceiling':2.70,'bottom':1.58,'spacing':.56,'count':3}},
]

def power(v,e):return math.copysign(abs(v)**e,v)
def mesh_object(name,verts,faces,cat,smooth=True,mat=None):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o)
 for f in mesh.polygons:f.use_smooth=smooth
 return finish(o,cat,mat)
def bevel(o,width,segments=4):
 mod=o.modifiers.new('Soft finished edges','BEVEL');mod.width=width;mod.segments=segments;mod.limit_method='ANGLE'
 bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=mod.name);o.select_set(False);return o
def slab(name,center,size,radius,cat,n=96,e=.18,mat=None):
 """Rounded-rectangle slab (superellipse plan)."""
 cx,cy,cz=center;a,b,h=size[0]/2,size[1]/2,size[2]/2;verts=[]
 for z in (-h,h):
  for i in range(n):
   t=2*math.pi*i/n;verts.append((cx+power(math.cos(t),e)*a,cy+power(math.sin(t),e)*b,cz+z))
 faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 o=mesh_object(name,verts,faces,cat,False,mat);return bevel(o,radius)
def block(name,center,size,cat,radius=.005):
 x,y,z=[v/2 for v in size];cx,cy,cz=center;verts=[(cx+a*x,cy+b*y,cz+c*z) for c in (-1,1) for a,b in ((-1,-1),(1,-1),(1,1),(-1,1))]
 o=mesh_object(name,verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],cat,False);return bevel(o,radius)
def tube(name,points,radius,cat,mat=None):
 curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.bevel_depth=radius;curve.bevel_resolution=2;curve.use_fill_caps=True
 sp=curve.splines.new('POLY');sp.points.add(len(points)-1)
 for p,co in zip(sp.points,points):p.co=(*co,1)
 o=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
 return finish(o,cat,mat)
def pad(name,place,size,cat,e=.30,dish=0,mat=None):
 """Superellipsoid cushion; `dish` settles the top where a sitter would rest."""
 rings,segments=24,48;verts=[];faces=[]
 for j in range(rings+1):
  phi=-math.pi/2+math.pi*j/rings
  for i in range(segments):
   t=2*math.pi*i/segments;cp=power(math.cos(phi),e)
   x=cp*power(math.cos(t),e)*size[0]/2;y=cp*power(math.sin(t),e)*size[1]/2;z=power(math.sin(phi),e)*size[2]/2
   if z>0 and dish:z-=dish*math.exp(-((x/(size[0]*.32))**2+(y/(size[1]*.32))**2))
   verts.append(place((x,y,z)))
 for j in range(rings):
  for i in range(segments):
   k=j*segments+i;k2=j*segments+(i+1)%segments;faces.append((k,k2,k2+segments,k+segments))
 return mesh_object(name,verts,faces,cat,True,mat)

def slatted_base(x,y,z,length,axis):
 """Sculptural base of vertical walnut fins whose depths rise and fall along the table."""
 count=max(9,round(length/.058)+1)
 for k in range(count):
  depth=.30+.16*(.5+.5*math.cos(2*math.pi*k/6.5));shift=.03*math.sin(2*math.pi*k/4.3);along=-length/2+length*k/(count-1)
  center=(x+along,y+shift,z+(TOP-.05)/2) if axis=='x' else (x+shift,y+along,z+(TOP-.05)/2)
  size=(.032,depth,TOP-.05) if axis=='x' else (depth,.032,TOP-.05)
  block('Dining | walnut base fin',center,size,'diningwood')

def add_chair(cx,cy,z,yaw):
 rot=Matrix.Rotation(yaw,3,'Z');origin=Vector((cx,cy,z))
 def place(p,lift=0):return tuple(origin+rot@Vector((p[0],p[1],p[2]+lift)))
 # Deep upholstered deck and a plump, softly settled seat cushion.
 pad('Dining chair | upholstered deck',lambda p:place(p,.335),(.60,.56,.15),'diningfabric',.25)
 pad('Dining chair | seat cushion',lambda p:place((p[0],p[1]+.03,p[2]),.445),(.46,.42,.11),'diningfabric',.32,.008)
 # Chunky barrel shell: one continuous squared curve forming back and arms.
 # Arms stay below the 0.70 m table underside so the chairs can draw in.
 path,cross=144,28;verts=[];faces=[];a0,b0=.26,.25
 def profile(t,a):
  rear=max(0,-math.sin(t));top=.66+.06*rear;bottom=.27
  cap=max(0,(math.radians(162)-t)/math.radians(12),(t-math.radians(378))/math.radians(12));env=math.sqrt(max(.00001,1-min(1,cap)**2))
  r=.065*power(math.cos(a),.5)*env;mid=(top+bottom)/2;half=(top-bottom)/2
  return (power(math.cos(t),.6)*(a0+r),-.02+power(math.sin(t),.6)*(b0+r),mid+half*power(math.sin(a),.35)*env)
 for i in range(path+1):
  t=math.radians(150+240*i/path)
  for j in range(cross):verts.append(place(profile(t,2*math.pi*j/cross)))
 for i in range(path):
  for j in range(cross):
   k=i*cross+j;k2=i*cross+(j+1)%cross;faces.append((k,k+cross,k2+cross,k2))
 faces+=[tuple(range(cross-1,-1,-1)),tuple(range(path*cross,(path+1)*cross))]
 mesh_object('Dining chair | barrel back and arms',verts,faces,'diningfabric')
 # Square walnut posts clasp the upholstered body at each corner.
 for sx in (-1,1):
  for sy in (.12,-.24):
   leg=block('Dining chair | walnut post',(0,0,0),(.05,.05,.58),'diningwood',.004);leg.location=place((sx*.31,sy,.29));leg.rotation_euler.z=yaw

def add_pendants(x,y,cfg,axis):
 """Organic plaster pebble shades in a row along the table, each with a warm glowing lens."""
 plaster=material('Decor | plaster pendant','#ece6da',.88);cord=material('Decor | charcoal','#282f32',.6);glow=material('Decor | warm LED','#fff0d5',.22,emission=3)
 n=cfg['count']
 for k in range(n):
  along=(k-(n-1)/2)*cfg['spacing'];px,py=(x+along,y) if axis=='x' else (x,y+along);seed=k*1.7
  def place(p,px=px,py=py,seed=seed):
   # A gently irregular rim keeps the shades from reading as perfect domes.
   wobble=1+.05*math.sin(math.atan2(p[1],p[0])*3+seed)+.03*math.sin(math.atan2(p[1],p[0])*5-seed)
   return (px+p[0]*wobble,py+p[1]*wobble,cfg['bottom']+.10+p[2])
  pad('Dining pendant | plaster shade',place,(.40,.37,.20),'decor',.55,mat=plaster)
  slab('Dining pendant | warm lens',(px,py,cfg['bottom']-.003),(.20,.20,.006),.002,'interiorlight',48,1,glow)
  tube('Dining pendant | suspension cord',[(px,py,cfg['bottom']+.19),(px,py,cfg['ceiling'])],.004,'decor',cord)
  slab('Dining pendant | ceiling rose',(px,py,cfg['ceiling']-.008),(.09,.09,.016),.003,'decor',32,1,cord)

def box_uv(objects):
 for o in objects:
  uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
  for f in o.data.polygons:
   normal=o.matrix_world.to_3x3()@f.normal;axis=max(range(3),key=lambda i:abs(normal[i]));axes=[i for i in range(3) if i!=axis]
   for idx in f.loop_indices:
    p=o.matrix_world@o.data.vertices[o.data.loops[idx].vertex_index].co;uv.data[idx].uv=(p[axes[0]],p[axes[1]])

def build_room(room,rebuilt):
 removed={}
 for o in list(bpy.data.objects):
  cat=o.get('category')
  if o.type=='MESH' and not o.get('diningSet') and o.get('floor')==room['floor'] and cat in room['masks']:removed[cat]=removed.get(cat,0)+remove_faces(o,room['masks'][cat])
 assert rebuilt or all(removed.get(cat,0)>0 for cat in room['masks']),(room['id'],removed)
 created.clear();(x,y),z,(w,d)=room['center'],room['z'],room['size']
 slab('Dining | walnut table top',(x,y,z+TOP-.025),(w,d,.05),.008,'diningwood',96,.07)
 length=(w if room['axis']=='x' else d)-.84
 slatted_base(x,y,z,length,room['axis'])
 for cx,cy,yaw in room['chairs']:add_chair(cx,cy,z,yaw)
 if room['pendants']:add_pendants(x,y,room['pendants'],room['axis'])
 bpy.context.view_layer.update();box_uv([o for o in created if o.get('category') in ('diningwood','diningfabric')])
 groups={}
 for o in created:groups.setdefault((o['category'],o.data.materials[0].name),[]).append(o)
 names={'diningwood':'walnut table and chair posts','diningfabric':'bouclé barrel chairs','decor':'pendant shades and cords','interiorlight':'pendant lenses'}
 for (cat,_),objects in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in objects:o.select_set(True)
  bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object
  o.name=f"Dining {room['id']} | {names[cat]}";o['category']=cat;o['finishGroup']=cat;o['floor']=room['floor'];o['diningSet']=room['id']
 return {'room':room['name'],'table':f"{max(w,d):.2f} x {min(w,d):.2f} m smoked walnut top, 0.75 m high, on a sculptural base of vertical walnut fins",'chairs':f"{len(room['chairs'])} chunky mustard bouclé barrel chairs with deep seat cushions and square walnut corner posts",'pendants':f"{room['pendants']['count']} organic plaster pebble pendants" if room['pendants'] else None,'removedFaces':removed}

def add_dining_sets():
 rebuilt={o.get('diningSet') for o in bpy.data.objects if o.get('diningSet')}
 for o in [o for o in bpy.data.objects if o.get('diningSet')]:bpy.data.objects.remove(o,do_unlink=True)
 cfg=json.load(open(os.path.join(root,'scripts','reference-materials.json')))
 for cat in ['diningfabric','diningwood']:pack_surface(cat,cfg)
 # Sets from the first single-room version were tagged True rather than by room.
 return {room['id']:build_room(room,room['id'] in rebuilt or (room['id']=='roof' and True in rebuilt)) for room in ROOMS}

if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 report=add_dining_sets()
 # Another tool may be editing the same scene; never overwrite a newer save.
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 path=os.path.join(root,'public','interior-refinement.json');data=json.load(open(path));data['dining']=report
 with open(path,'w') as f:json.dump(data,f,indent=2)
 export_and_save();print('MODERN DINING SETS SAVED',report)
