"""Replace placeholder site fittings with realistic ones and give utility boxes believable finishes.
- 9 bollards and 5 external wall lights (white emissive boxes) become black aluminium fittings with warm glow,
  switched with the 'exterior' lighting zone. The light that sat on the front door moves to the wall beside it.
- The rooftop solar thermosiphon cylinder gets its flat-plate collector and stand.
- Electric fence posts become black steel, warning plates yellow; kiosk, consumer unit and keypad grey; pump blue."""
import bpy,os,sys,json,re,math
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import created,remove_faces,material,box,cylinder
from refine_interior_realism import export_and_save
from site_realism import take,inside,meshes
blend=os.path.join(root,'Francis-Web.blend')
SRC=json.load(open(os.path.join(root,'scene-inspection.json')))['objects']
def sources(pattern):return [(Vector(s['min']),Vector(s['max'])) for s in SRC if re.search(pattern,s['name'])]

def strip_lights(boxes):
 n=0
 for o in [o for o in bpy.data.objects if o.type=='MESH' and o.get('category') in ('lighting','interiorlight') and not o.get('cleanSite')]:
  n+=remove_faces(o,[(tuple(a-Vector((.02,.02,.02))),tuple(b+Vector((.02,.02,.02)))) for a,b in boxes])
 return n

def fittings():
 body=material('Decor | dark aluminium','#24272a',.42,.55);glow=material('Decor | warm LED','#fff0d5',.22,emission=3)
 bollards=sources(r'KE Bollard Light');walls=sources(r'KE External Wall Light')
 # The door light was already nudged 0.75 m left by site_realism_fixups; include that fragment too.
 removed=strip_lights(bollards+walls+[(Vector((-.70,9.02,2.09)),Vector((-.52,9.16,2.31)))])
 for a,b in bollards:
  c=(a+b)/2;z=a.z
  cylinder('Bollard | body',(c.x,c.y,z+.30),.075,.60,'decor',body)
  cylinder('Bollard | light band',(c.x,c.y,z+.65),.068,.10,'interiorlight',glow)
  cylinder('Bollard | cap',(c.x,c.y,z+.725),.082,.05,'decor',body)
  cylinder('Bollard | base plate',(c.x,c.y,z+.006),.10,.012,'decor',body)
 verts=[];faces=[]
 for o in bpy.data.objects:
  if o.type=='MESH' and o.get('category') in ('walls','render','accent','featurewall','doors','frontdoor','frontdoorframe','glass'):
   off=len(verts);verts.extend(o.matrix_world@v.co for v in o.data.vertices);faces.extend(tuple(off+i for i in p.vertices) for p in o.data.polygons)
 tree=BVHTree.FromPolygons(verts,faces);placed=[]
 for a,b in walls:
  c=(a+b)/2
  if 9.0<c.y<9.2 and -.4<c.x<.7:c=Vector((-.62,c.y,c.z))  # off the front door leaf, onto the wall left of its frame
  axis=0 if (b-a).x<(b-a).y else 1
  # The wall is the side where a short ray finds masonry; the sconce projects to the other side.
  side=None
  for s in (-1,1):
   d=Vector((0,0,0));d[axis]=s;hit=tree.ray_cast(c,d,.35)
   if hit[0] is not None and (side is None or hit[3]<side[1]):side=(s,hit[3],hit[0])
  s,dist,wall=side if side else (1,.06,c+Vector((0,0,0)))
  out=-s;centre=wall.copy();centre[axis]+=out*.075;centre.z=c.z
  cylinder('Wall light | up-down body',tuple(centre),.05,.24,'decor',body)
  for dz in (-.122,.122):cylinder('Wall light | lens',(centre.x,centre.y,centre.z+dz),.036,.004,'interiorlight',glow)
  arm=wall.copy();arm[axis]+=out*.03;arm.z=c.z
  size=[.05,.05,.07];size[axis]=.06;box('Wall light | bracket',tuple(arm),tuple(size),'decor',.004,body)
  placed.append([round(v,2) for v in centre])
 return {'removedPlaceholderFaces':removed,'bollards':len(bollards),'wallLights':placed}

def solar_collector():
 # Cylinder HWC-1 at x 4.87-6.43, y 11.61-12.17, z 10.12-10.72 on its stand; roof deck at about z 9.73.
 glass=material('Decor | solar collector glass','#0f1a24',.08,.15,coat=.9);alu=material('Decor | anodised aluminium','#b9bec2',.32,.85)
 x0,x1,yh,yl,zh,zl=4.90,6.40,11.58,9.98,10.10,9.82
 n=Vector((0,yh-yl,zh-zl)).normalized().cross(Vector((1,0,0)))
 mid=Vector(((x0+x1)/2,(yh+yl)/2,(zh+zl)/2));length=math.hypot(yh-yl,zh-zl);tilt=math.atan2(zh-zl,yh-yl)
 p=box('Solar | collector panel',tuple(mid),(x1-x0,length,.07),'decor',.006,alu);p.rotation_euler.x=tilt
 g=box('Solar | absorber glass',tuple(mid+n*-.036),(x1-x0-.06,length-.06,.004),'decor',0,glass);g.rotation_euler.x=tilt
 for x in (x0+.08,x1-.08):
  for y,top in ((yl+.05,zl-.03),(yh-.05,zh-.03)):
   box('Solar | stand leg',(x,y,(9.74+top)/2),(.04,.04,top-9.74),'decor',.003,alu)
 return {'collector':f'{x1-x0:.2f} x {length:.2f} m flat-plate, {math.degrees(tilt):.0f} degree tilt, aluminium stand'}

def utilities():
 grey=material('Decor | utility enclosure','#6b7075',.6,.2);steel=material('Decor | black steel','#26292c',.45,.6)
 yellow=material('Decor | warning sign','#e3b51c',.5);blue=material('Decor | pump blue','#2f5d8a',.4,.3)
 out={}
 def recolour(label,boxes,mat,cats=('details','metal','walls','render','lighting','hardware')):
  n=0
  for a,b in boxes:n+=take(meshes(list(cats)),lambda c,pts,a=a,b=b:inside(pts,a,b,.004),mat,'decor',label)
  out[label]=n
 fence=[(a,b) for a,b in sources(r'Security Devices Box') if (b-a).z>1.0 or (b-a).x>.9 or (b-a).y>.9]
 signs=[(a,b) for a,b in sources(r'Security Devices Box') if abs((b-a).x-.2)<.02 or abs((b-a).y-.2)<.02]
 recolour('electric fence',fence,steel);recolour('fence warning plates',signs,yellow)
 recolour('utility enclosures',sources(r'Electrical Equipment Box \[2327047|Consumer Unit MDB EDB-1')+[(a,b) for a,b in sources(r'Security Devices Box') if (b-a).z>.2 and (b-a).z<.3],grey)
 recolour('transfer pump',sources(r'Transfer Pump'),blue)
 return out

if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 assert not any(o.get('cleanSite') for o in bpy.data.objects),'Already applied: restore the previous Francis-Web.blend before rerunning'
 report={'utilities':utilities()}
 created.clear();report['fittings']=fittings();report['solar']=solar_collector()
 bpy.context.view_layer.update()
 for o in created:
  uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
 groups={}
 for o in created:groups.setdefault((o['category'],o.data.materials[0].name),[]).append(o)
 for (cat,mat),objects in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in objects:o.select_set(True)
  bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object
  o.name=f'Site fittings | {mat}';o['category']=cat;o['finishGroup']=cat;o['floor']=0;o['cleanSite']=True;o['siteLighting']=True
  if cat=='interiorlight':o['lightZone']='exterior'
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 path=os.path.join(root,'public','interior-refinement.json');data=json.load(open(path));data['cleanSite']=report
 with open(path,'w') as f:json.dump(data,f,indent=2)
 export_and_save();print('CLEAN SITE SAVED',json.dumps(report))
