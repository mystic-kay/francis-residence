"""Soft tub chairs with rounded arm ends and fitted upholstered panel seams."""
import bpy,math
from mathutils import Vector,Matrix
from luxury_interiors import finish,material,line,cylinder,created

def power(v,e):return math.copysign(abs(v)**e,v)

def cushion(name,loc,size,rotation,body=False):
 # Separate exponents keep the top broad and the perimeter softly rounded.
 rings,segments=48,96;verts=[];faces=[]
 for j in range(rings+1):
  phi=-math.pi/2+math.pi*j/rings
  for i in range(segments):
   t=2*math.pi*i/segments;cp=power(math.cos(phi),.38 if body else .46)
   x=cp*power(math.cos(t),.76)*size[0]/2;y=cp*power(math.sin(t),.76)*size[1]/2;z=power(math.sin(phi),.38 if body else .46)*size[2]/2
   if not body:
    # Softly settled top, with short gathered folds restricted to its edge.
    if z>0:z-=.0045*math.exp(-((x/.24)**2+(y/.24)**2))
    edge=max(abs(x)/(size[0]/2),abs(y)/(size[1]/2));z+=.0012*math.sin(t*19+phi*5)*math.exp(-((edge-.90)/.055)**2)
   verts.append((x,y,z))
 for j in range(rings):
  for i in range(segments):
   k=j*segments+i;k2=j*segments+(i+1)%segments;faces.append((k,k2,k2+segments,k+segments))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler.z=rotation;finish(o,'livingfabric')
 uv=mesh.uv_layers.new(name='UVMap')
 for f in mesh.polygons:
  f.use_smooth=True
  for idx in f.loop_indices:
   vi=mesh.loops[idx].vertex_index;p=mesh.vertices[vi].co
   latitude=-math.pi/2+math.pi*(f.vertices[0]//segments+.5)/rings
   if abs(latitude)<math.pi/6:
    theta=2*math.pi*(vi%segments)/segments
    if vi%segments==0 and any(v%segments==segments-1 for v in f.vertices):theta=2*math.pi
    uv.data[idx].uv=(theta*(size[0]+size[1])/4,p.z)
   else:uv.data[idx].uv=(p.x,p.y)
 o['tailoredUV']=True;o['chairPart']='support' if body else 'seat';o['refinedSeat']=True
 return o

def add_armchairs():
 result=[]
 for x in [7.78,9.31]:
  start=len(created);cy=8.87;origin=Vector((x,cy,0));target=Vector((8.12,11.15,0));forward=(target-origin).normalized();yaw=-math.atan2(forward.x,forward.y);rot=Matrix.Rotation(yaw,3,'Z')
  def point(p):return tuple(origin+rot@Vector(p))
  base=cylinder('Tailored chair | recessed swivel plinth',(x,cy,.08),.32,.10,'interiormetal');base['chairPart']='base'
  cushion('Tailored chair | padded lower body',(x,cy,.22),(.87,.84,.30),yaw,True)
  seat=cushion('Tailored chair | settled removable cushion',point((0,.027,.365)),(.74,.73,.18),yaw)
  # Dense continuous sweep: the terminal caps round off instead of leaving cut faces.
  path_steps,cross_steps=256,48;verts=[];faces=[];uvs=[]
  def profile(t,a,offset=0):
   rear=max(0,-math.sin(t));top=.515+.235*rear**.82;bottom=.155
   deg=math.degrees(t);cap=max(0,(155-deg)/7,(deg-385)/7);envelope=math.sqrt(max(.00001,1-min(1,cap)**2))
   radial=.060*power(math.cos(a),.62)*envelope
   r=.420+radial+offset+.0008*math.sin(t*29+a*3)*abs(math.cos(a))
   z=(bottom+top)/2+(top-bottom)/2*power(math.sin(a),.40)*envelope
   return (r*math.cos(t),r*math.sin(t),z)
  for i in range(path_steps+1):
   t=math.radians(148+244*i/path_steps)
   for j in range(cross_steps):
    a=2*math.pi*j/cross_steps;verts.append(point(profile(t,a)));uvs.append((t*.42,a*.11))
  perimeters=[];across=[0.0]*cross_steps
  for i in range(path_steps+1):
   row=verts[i*cross_steps:(i+1)*cross_steps];along=0.0
   for j in range(cross_steps):
    if j:along+=(Vector(row[j])-Vector(row[j-1])).length
    if i:across[j]+=(Vector(row[j])-Vector(verts[(i-1)*cross_steps+j])).length
    uvs[i*cross_steps+j]=(across[j],along)
   perimeters.append(along+(Vector(row[0])-Vector(row[-1])).length)
  for i in range(path_steps):
   for j in range(cross_steps):
    k=i*cross_steps+j;k2=i*cross_steps+(j+1)%cross_steps;faces.append((k,k+cross_steps,k2+cross_steps,k2))
  faces.extend([tuple(range(cross_steps-1,-1,-1)),tuple(range(path_steps*cross_steps,(path_steps+1)*cross_steps))])
  mesh=bpy.data.meshes.new('Continuous padded arm and back');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('Tailored chair | rounded arms and back',mesh);bpy.context.collection.objects.link(o);finish(o,'livingfabric');o['chairPart']='back';o['refinedSeat']=True;o['tailoredUV']=True;o['roundedArmCaps']=True;o['seatingForward']=list(forward);o['seatingCenter']=list(origin);o['seatingTarget']=list(target)
  uv=mesh.uv_layers.new(name='UVMap')
  for f in mesh.polygons:
   f.use_smooth=True
   for idx in f.loop_indices:
    v=mesh.loops[idx].vertex_index;u,w=uvs[v]
    # Keep the wrap seam outside the visible inner face.
    if v%cross_steps==0 and any(mesh.loops[k].vertex_index%cross_steps==cross_steps-1 for k in f.loop_indices):w=perimeters[v//cross_steps]
    uv.data[idx].uv=(u,w)
  # Fitted arm-end panels have welted joins all around the padded cap shoulders.
  for deg in [156,384]:
   t=math.radians(deg);points=[point(profile(t,2*math.pi*j/144,.0007)) for j in range(145)]
   seam=line('Tailored chair | arm end panel welt',points,.0018,'livingfabric');seam['armSeam']=True
  crown=[point(profile(math.radians(156+228*i/240),math.radians(70),.0004)) for i in range(241)]
  seam=line('Tailored chair | continuous crown seam',crown,.0017,'livingfabric');seam['armSeam']=True
  # An outer side panel seam follows the arm curvature, rather than a flat stripe.
  outer=[point(profile(math.radians(156+228*i/240),0,.001)) for i in range(241)]
  seam=line('Tailored chair | outer panel welt',outer,.0016,'livingfabric');seam['armSeam']=True
  # Small paired stitches sit beside the crown welt and around both end panels.
  stitch=material('Decor | chair upholstery thread','#b6ac9a',.94)
  for i in range(164):
   t0=math.radians(158+224*i/164);t1=t0+math.radians(.70)
   for a in [math.radians(64),math.radians(76)]:
    line('Tailored chair | fine saddle stitch',[point(profile(t0,a,.0015)),point(profile(t1,a,.0015))],.00065,'decor',stitch)
  # Seat welt joins the cushion's upper and lower cloth panels.
  cp=power(math.cos(math.pi/6),.46);weltz=.365+power(.5,.46)*.09
  pts=[point((cp*power(math.cos(t),.76)*.370,.027+cp*power(math.sin(t),.76)*.365,weltz)) for t in [i*2*math.pi/192 for i in range(193)]]
  line('Tailored chair | seat cushion piping',pts,.002,'livingfabric')
  # Keep reviewable cushion and shell parts; consolidate tiny sewing details.
  groups={}
  for obj in created[start:]:
   obj['floor']=0
   if obj.get('chairPart'):continue
   groups.setdefault((obj['category'],obj.data.materials[0].name),[]).append(obj)
  kept=[obj for obj in created[start:] if obj.get('chairPart')]
  joined=[]
  for (cat,mat),objects in groups.items():
   bpy.ops.object.select_all(action='DESELECT')
   for obj in objects:obj.select_set(True)
   bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();obj=bpy.context.object;obj.name='Tailored chair | arm seams' if cat=='livingfabric' else 'Tailored chair | double stitching';obj['category']=cat;obj['finishGroup']=cat;obj['floor']=0;obj['chairSewing']=True;obj['armSeam']=cat=='livingfabric';obj['tailoredUV']=True;joined.append(obj)
   uv=obj.data.uv_layers.get('UVMap') or obj.data.uv_layers.new(name='UVMap')
   for f in obj.data.polygons:
    for idx in f.loop_indices:
     p=obj.matrix_world@obj.data.vertices[obj.data.loops[idx].vertex_index].co;uv.data[idx].uv=(p.x,p.z)
  created[start:]=kept+joined
  result.append({'center':[x,cy],'baseTop':.13,'supportBottom':.07,'supportTop':.37,'cushionBottom':.275,'seatTop':.455,'backTop':.75,'inwardForward':list(forward),'armFinish':'Rounded cap shoulders with fitted end-panel welts, continuous crown and side-panel seams, double stitching','fabricMapping':'Continuous wrap UVs without per-face projection switches'})
 return result
