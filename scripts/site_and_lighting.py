"""Move the kitchen artwork to the corridor, replace the driveway gate with a sliding slatted gate,
and split every light fitting and wall switch into switchable room zones for the website."""
import bpy,bmesh,os,sys,json,math,re
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import created,remove_faces,material,box,sphere,line
from refine_interior_realism import export_and_save,pack_surface
from modern_dining_set import mesh_object,block,box_uv
blend=os.path.join(root,'Francis-Web.blend')

def faces_in(o,a,b,tol=.003):
 mw=o.matrix_world
 return [f.index for f in o.data.polygons if all(all(a[i]-tol<=(mw@o.data.vertices[v].co)[i]<=b[i]+tol for i in range(3)) for v in f.vertices)]
def strip(box_,cats=None,floor=None,prefix=None):
 n=0
 for o in list(bpy.data.objects):
  if o.type!='MESH' or o.get('siteLighting'):continue
  if cats and o.get('category') not in cats:continue
  if floor is not None and o.get('floor')!=floor:continue
  if prefix and not o.name.startswith(prefix):continue
  n+=remove_faces(o,[box_])
 return n

# ---------- Artwork: off the kitchen wall units, onto the corridor wall above the console ----------
def move_art():
 report={'kitchenArtFaces':strip(((4.2,15.09,1.2),(5.0,15.17,2.16)),prefix='Refined |'),
         'placeholderPanelFaces':strip(((10.28,13.77,1.14),(10.345,14.69,1.86)),cats=['details'],floor=0),
         'corridorPlaceholderFaces':strip(((4.59,14.84,1.24),(5.61,14.88,2.01)),cats=['details'],floor=0)}
 paper=material('Decor | mounted art paper','#ede1cc',.96);rust=material('Decor | mounted art rust','#a9755e',.85);olive=material('Decor | mounted art olive','#65765d',.86);ink=material('Decor | mounted art charcoal','#303438',.75)
 # Corridor face of the kitchen wall is at y=14.876; the piece faces -y into the corridor.
 width,height=1.0,.75;center=Vector((5.10,14.876-.014,1.625));u=Vector((1,0,0));n=Vector((0,-1,0));angle=0
 o=box('Corridor art | canvas',tuple(center),(width,.024,height),'decor',.001,paper)
 for side in (-1,1):
  box('Corridor art | frame side',tuple(center+u*side*width/2+n*.017),(.017,.035,height+.035),'interiormetal',.002)
  box('Corridor art | frame rail',tuple(center+n*.017+Vector((0,0,side*height/2))),(width+.035,.035,.017),'interiormetal',.002)
 for du,dz,sx,sz,mat in [(-.18,.10,.28,.42,rust),(.20,-.20,.24,.26,olive),(.02,.24,.12,.16,rust)]:
  sphere('Corridor art | relief',tuple(center+u*(du*width)+n*.026+Vector((0,0,dz*height))),(sx*width,.006,sz*height),'decor',mat)
 line('Corridor art | flowing line',[tuple(center+u*(width*.74*(v-.5))+n*.035+Vector((0,0,math.sin(v*2*math.pi)*height*.2))) for v in [i/60 for i in range(61)]],.0025,'decor',ink)
 report['corridorArt']={'center':list(center),'size':[width,height],'facing':'corridor (-y)'}
 return report

# ---------- Sliding gate ----------
GATE={'x0':10.84,'x1':15.54,'y':-2.50,'bottom':-.55,'top':2.30,'slide':4.80}
def build_gate():
 # The source gate is a single flat Generic Model Box in the driveway opening.
 removed=strip(((10.93,-2.81,-.57),(15.45,-2.74,2.31)),floor=0)
 g=GATE;mid=(g['x0']+g['x1'])/2;w=g['x1']-g['x0'];h=g['top']-g['bottom'];f=.07
 parts=[]
 # Slim perimeter frame and a centre stile, satin metal.
 for z in (g['bottom']+f/2,g['top']-f/2):parts.append(block('Gate | frame rail',(mid,g['y'],z),(w,.06,f),'gateframe',.004))
 for x in (g['x0']+f/2,mid,g['x1']-f/2):parts.append(block('Gate | frame stile',(x,g['y'],(g['bottom']+g['top'])/2),(f,.06,h),'gateframe',.004))
 # Horizontal timber-look aluminium slats with 18 mm shadow gaps.
 inner0,inner1=g['bottom']+f,g['top']-f;slat=.115;gap=.018;z=inner0+gap
 while z+slat<=inner1-gap/2:
  for x0,x1 in ((g['x0']+f,mid-f/2),(mid+f/2,g['x1']-f)):
   parts.append(block('Gate | slat',((x0+x1)/2,g['y'],z+slat/2),(x1-x0,.03,slat),'gate',.004))
  z+=slat+gap
 for o in parts:o['slidingGate']=True
 # Static ground track and a compact motor housing behind the boundary wall.
 track=block('Gate | ground track',((g['x0']-g['slide']+g['x1'])/2,g['y'],-.585),(w+g['slide']+.2,.05,.03),'gateframe',.003)
 motor=block('Gate | motor housing',(g['x0']-.45,g['y']+.22,-.30),(.30,.22,.55),'gateframe',.02)
 track['gateStatic']=motor['gateStatic']=True
 return {'removedFaces':removed,'openingMetres':round(w,2),'slideMetres':g['slide'],'slats':sum(1 for o in parts if o.name.startswith('Gate | slat'))}

# ---------- Lighting zones and switches ----------
# Plan rectangles (x0,y0,x1,y1) from the source ceiling outlines; first match wins, the rest is exterior.
LEVELS={0:(-.7,3.05,2.62),1:(3.05,6.1,5.62),2:(6.1,9.7,8.6)}
ZONES=[('kitchen','Kitchen',0,(2.24,15.08,6.14,18.9)),('dining','Dining room',0,(6.14,15.08,10.45,18.9)),
 ('living','Living room',0,(6.14,7.6,11.0,13.36)),('corridor','Corridor & lobby',0,(-1.2,13.36,10.45,15.08)),
 ('guest','Guest bedroom',0,(-1.2,15.08,2.24,18.9)),('hall','Hall & study',0,(-1.2,9.0,2.34,13.36)),('stair','Stair hall',0,(2.34,9.0,6.14,13.36)),
 ('primary','Primary suite',1,(6.14,7.6,11.6,13.4)),('bed1','Bedroom one',1,(2.34,15.08,6.14,18.9)),('study','Study',1,(6.14,15.08,10.45,18.9)),
 ('bed2','Bedroom two',1,(-1.2,9.0,3.5,13.4)),('upperhall','First-floor hall',1,(3.5,9.0,6.14,13.4)),('landing','Landing',1,(-1.2,13.4,10.45,15.08)),('westsuite','West suite & bath',1,(-1.2,15.08,2.34,18.9)),
 ('roofdining','Top-floor dining',2,(-1.2,13.4,10.45,19.3)),('terrace','Roof terrace & pergola',2,(-1.6,7.0,12.0,13.4))]
def zone_of(p):
 for zid,_,lvl,(x0,y0,x1,y1) in ZONES:
  z0,z1,_=LEVELS[lvl]
  if x0<=p.x<=x1 and y0<=p.y<=y1 and z0<=p.z<z1:return zid
 return 'exterior'
def nearest_zone(p):
 best=None
 for zid,_,lvl,(x0,y0,x1,y1) in ZONES:
  z0,z1,_=LEVELS[lvl]
  if not z0<=p.z<z1:continue
  d=math.hypot(max(x0-p.x,0,p.x-x1),max(y0-p.y,0,p.y-y1))
  if best is None or d<best[0]:best=(d,zid)
 return best[1] if best and best[0]<.6 else 'exterior'

def split_faces(o,assign):
 """Split a merged mesh into new objects keyed by assign(face_centre). Returns {key: object}."""
 mw=o.matrix_world;keys={}
 for f in o.data.polygons:keys.setdefault(assign(mw@f.center,f.index),[]).append(f.index)
 out={}
 for key,idx in keys.items():
  new=o.copy();new.data=o.data.copy();bpy.context.collection.objects.link(new)
  keep=set(idx);bm=bmesh.new();bm.from_mesh(new.data);bm.faces.ensure_lookup_table()
  bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.index not in keep],context='FACES');bm.to_mesh(new.data);bm.free()
  out[key]=new
 bpy.data.objects.remove(o,do_unlink=True);return out

def light_zones():
 source=json.load(open(os.path.join(root,'scene-inspection.json')))['objects']
 switches=[(Vector(s['min']),Vector(s['max'])) for s in source if re.search(r'KE Light Switch',s['name'])]
 plate=material('Decor | switch plate','#f3f1ec',.38)
 counts={};switch_counts={}
 for o in [o for o in bpy.data.objects if o.type=='MESH' and o.get('category') in ('lighting','interiorlight') and not o.get('siteLighting')]:
  cat=o.get('category');floor=o.get('floor')
  def assign(c,_):
   for a,b in switches:
    if all(a[i]-.004<=c[i]<=b[i]+.004 for i in range(3)):return ('switch',nearest_zone(c) if zone_of(c)=='exterior' else zone_of(c))
   return ('light',zone_of(c))
  for (kind,zid),new in split_faces(o,assign).items():
   new['siteLighting']=True;new['floor']=floor
   if kind=='switch':
    new.name=f'Switch | {zid}';new['lightSwitch']=zid;new['category']='details';new['finishGroup']='details';new.data.materials.clear();new.data.materials.append(plate)
    switch_counts[zid]=switch_counts.get(zid,0)+len(new.data.polygons)
   else:
    new.name=f'Lights | {zid} | {cat}';new['lightZone']=zid;counts[zid]=counts.get(zid,0)+len(new.data.polygons)
 zones=[]
 for zid,name,lvl,rect in ZONES+[('exterior','Garden & façade',None,None)]:
  entry={'id':zid,'name':name,'level':lvl,'fixtureFaces':counts.get(zid,0),'switchPlates':switch_counts.get(zid,0)}
  if rect:x0,y0,x1,y1=rect;entry.update(center=[(x0+x1)/2,(y0+y1)/2,LEVELS[lvl][2]],size=[x1-x0,y1-y0])
  zones.append(entry)
 return zones

def tag_new(prefix_map):
 groups={}
 for o in created:groups.setdefault((o['category'],o.data.materials[0].name),[]).append(o)
 joined=[]
 for (cat,mat),objects in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in objects:o.select_set(True)
  bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;joined.append(o)
  o['category']=cat;o['finishGroup']=cat;o['floor']=0;o['siteLighting']=True
 return joined

if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 assert not any(o.get('siteLighting') for o in bpy.data.objects),'Already applied: restore the previous Francis-Web.blend before rerunning'
 cfg=json.load(open(os.path.join(root,'scripts','reference-materials.json')))
 for cat in ['gate','gateframe']:pack_surface(cat,cfg)
 created.clear();report={'art':move_art()}
 bpy.context.view_layer.update();box_uv(created)
 for o in tag_new({}):o.name='Corridor art | '+o.data.materials[0].name
 created.clear();report['gate']=build_gate();bpy.context.view_layer.update();box_uv(created)
 # Slats and frame stay separate objects from the static track so only the leaf animates.
 moving=[o for o in created if o.get('slidingGate')];static=[o for o in created if o.get('gateStatic')]
 by_cat={cat:[o for o in moving if o['category']==cat] for cat in ('gate','gateframe')}
 for cat,objs in by_cat.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in objs:o.select_set(True)
  bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object;o.name=f'Gate | sliding leaf {cat}';o['slidingGate']=True;o['slideMetres']=GATE['slide'];o['category']=cat;o['finishGroup']=cat;o['floor']=0;o['siteLighting']=True
 bpy.ops.object.select_all(action='DESELECT')
 for o in static:o.select_set(True)
 bpy.context.view_layer.objects.active=static[0];bpy.ops.object.join();o=bpy.context.object;o.name='Gate | track and motor';o['category']='gateframe';o['finishGroup']='gateframe';o['floor']=0;o['siteLighting']=True
 report['lighting']=light_zones()
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 with open(os.path.join(root,'public','lighting-zones.json'),'w') as f:json.dump({'zones':report['lighting'],'gate':GATE},f,indent=2)
 path=os.path.join(root,'public','interior-refinement.json');data=json.load(open(path));data['site']={k:v for k,v in report.items() if k!='lighting'}
 with open(path,'w') as f:json.dump(data,f,indent=2)
 export_and_save();print('SITE AND LIGHTING SAVED',json.dumps({k:v for k,v in report.items() if k!='lighting'}),[(z['id'],z['fixtureFaces'],z['switchPlates']) for z in report['lighting']])
