"""Realistic sanitaryware, tapware and lamps, plus a living-room chandelier.
- Taps are separated from every basin and sink by height and use the 'tapware' finish group (chrome by default);
  shower mixers and rain heads join them. Basins and WCs become glossy vitreous china; the kitchen sink brushed steel.
- Terrace: the white box under the outdoor basin is removed, the basin drops to sit 1 cm proud of the counter
  (rim about 0.9 m above the floor) in a cut-out, and the loose hose tap becomes a brass bib tap fixed to the parapet.
- Pendant and floor-lamp shades become warm linen that glows softly; cords and stems black or brass.
- Chandelier: a two-tier brass ring chandelier with 20 opal globes over the living-room coffee table."""
import bpy,bmesh,os,sys,json,math
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import created,remove_faces,material,cylinder,sphere,box
from refine_interior_realism import export_and_save,pack_surface
from modern_dining_set import tube
blend=os.path.join(root,'Francis-Web.blend')
SRC=json.load(open(os.path.join(root,'scene-inspection.json')))['objects']
def src(word):return [(s['name'],Vector(s['min']),Vector(s['max'])) for s in SRC if word in s['name']]

def inside(pts,a,b,t=.006):return all(all(a[i]-t<=p[i]<=b[i]+t for i in range(3)) for p in pts)
def take(objs,select,mat,cat,name,extra=None):
 """Move faces chosen by select(o,face,points) into a new object; returns it (or None)."""
 made=[]
 for o in objs:
  mw=o.matrix_world;idx=set()
  for f in o.data.polygons:
   pts=[mw@o.data.vertices[v].co for v in f.vertices]
   if select(o,f,pts):idx.add(f.index)
  if not idx:continue
  new=o.copy();new.data=o.data.copy();bpy.context.collection.objects.link(new)
  for target,drop in ((new,lambda f:f.index not in idx),(o,lambda f:f.index in idx)):
   bm=bmesh.new();bm.from_mesh(target.data);bm.faces.ensure_lookup_table()
   bmesh.ops.delete(bm,geom=[f for f in bm.faces if drop(f)],context='FACES');bm.to_mesh(target.data);bm.free()
  new.data.materials.clear();new.data.materials.append(mat)
  for k in [k for k in new.keys()]:del new[k]
  new.name=name;new['category']=cat;new['finishGroup']=cat;new['floor']=o.get('floor');new['fixturesPass']=True
  if extra:
   for k,v in extra(o).items():new[k]=v
  made.append(new)
 return made
meshes=lambda *cats:[o for o in bpy.data.objects if o.type=='MESH' and o.get('category') in cats and not o.get('fixturesPass')]

def sanitary(report):
 china=material('Decor | vitreous china','#f5f4f0',.08,0,coat=.9);steel=material('Decor | brushed steel sink','#b7bcc0',.32,.9)
 tap=bpy.data.materials['tapware']
 basins=src('Sink Vanity')+src('Kitchen Sink')+src('Terrace Sink')
 terrace=[]
 for name,a,b in basins:
  cut=a.z+.68*(b.z-a.z)
  t=take(meshes('ceramic'),lambda o,f,p,a=a,b=b,cut=cut:inside(p,a,b) and min(q.z for q in p)>cut,tap,'tapware','Fixtures | tap')
  bowl=take(meshes('ceramic'),lambda o,f,p,a=a,b=b:inside(p,a,b),steel if 'Kitchen' in name else china,'decor','Fixtures | basin')
  if 'Terrace' in name:terrace=t+bowl
  report['basins']=report.get('basins',0)+1
 for name,a,b in src('Shower Mixer')+src('shower rain head'):
  take(meshes('details','ceramic','lighting'),lambda o,f,p,a=a,b=b:inside(p,a,b),tap,'tapware','Fixtures | shower fitting')
 for name,a,b in src('WC Wall-Hung'):
  take(meshes('walls','ceramic'),lambda o,f,p,a=a,b=b:inside(p,a,b) and f.area<.2,china,'decor','Fixtures | WC')
 report['wcs']=len(src('WC Wall-Hung'))
 return terrace

def terrace_sink(parts,report):
 # Remove the white Plumbing Fixtures Box the basin was standing on.
 _,a,b=src('Plumbing Fixtures Box [2349393]')[0]
 report['plinthFaces']=sum(remove_faces(o,[(tuple(a),tuple(b))]) for o in meshes('ceramic') if o.get('floor')==2)
 pts=[o.matrix_world@v.co for o in parts if o.name.startswith('Fixtures | basin') for v in o.data.vertices]
 rim=max(p.z for p in pts);drop=rim-7.06
 for o in parts:o.location.z-=drop
 x0,x1=min(p.x for p in pts),max(p.x for p in pts);y0,y1=min(p.y for p in pts),max(p.y for p in pts)
 # Cut-out in the 30 mm timber counter top: remove the slab, rebuild it as four strips around the opening.
 n=sum(remove_faces(o,[((-1.07,15.29,7.015),(-.37,18.11,7.055))]) for o in meshes('wood') if o.get('floor')==2)
 hx0,hx1,hy0,hy1=x0+.03,x1-.03,y0+.03,y1-.03;wood=bpy.data.materials['wood']
 for nm,(ax0,ax1,ay0,ay1) in (('w',(-1.06,hx0,15.3,18.1)),('e',(hx1,-.38,15.3,18.1)),('s',(hx0,hx1,15.3,hy0)),('n',(hx0,hx1,hy1,18.1))):
  o=box('Terrace counter | top '+nm,((ax0+ax1)/2,(ay0+ay1)/2,7.035),(ax1-ax0,ay1-ay0,.03),'wood',.002,wood);o['floor']=2
 report['terraceSink']={'loweredMetres':round(drop,3),'rimHeightAboveFloor':round(7.06-6.15,2),'counterFaces':n}

def hose_bib(report):
 _,a,b=src('KD Terrace Tap')[0]
 report['oldHoseTapFaces']=sum(remove_faces(o,[(tuple(a),tuple(b))]) for o in meshes('details') if o.get('floor')==2)
 brass=material('Decor | brass fitting','#b48a4a',.32,.9);x,wall,z=4.57,18.676,6.75
 tube('Hose tap | wall flange',[(x,wall-.002,z),(x,wall-.012,z)],.032,'decor',brass)
 tube('Hose tap | body',[(x,wall-.012,z),(x,wall-.085,z)],.016,'decor',brass)
 tube('Hose tap | spout',[(x,wall-.085,z),(x,wall-.105,z-.02),(x,wall-.11,z-.07)],.012,'decor',brass)
 tube('Hose tap | hose connector',[(x,wall-.11,z-.07),(x,wall-.11,z-.10)],.015,'decor',material('Decor | black flex','#151617',.6))
 tube('Hose tap | headwork',[(x,wall-.06,z+.012),(x,wall-.06,z+.045)],.011,'decor',brass)
 tube('Hose tap | lever',[(x-.045,wall-.06,z+.05),(x+.045,wall-.06,z+.05)],.006,'decor',brass)
 report['hoseTap']='brass bib tap on the parapet face, 0.6 m above the terrace floor'

def lamps(report):
 linen=material('Decor | linen lampshade','#efe6d6',.9,emission=.9);cord=material('Decor | black flex','#151617',.6)
 brass=material('Decor | brass fitting','#b48a4a',.32,.9);zone=lambda o:{'lightZone':o.get('lightZone'),'siteLighting':True}
 shades=src('pendant 1 shade')+src('pendant 2 shade')+src('Floor lamp shade')
 for name,a,b in shades:
  take(meshes('lighting','interiorlight'),lambda o,f,p,a=a,b=b:inside(p,a,b,.02),linen,'lighting','Lamps | linen shade',zone)
 for name,a,b in src('pendant 1 cord')+src('pendant 2 cord'):
  take(meshes('lighting','interiorlight'),lambda o,f,p,a=a,b=b:inside(p,a,b,.01),cord,'decor','Lamps | cord')
 for name,a,b in src('Study floor lamp'):
  take(meshes('lighting','interiorlight','details'),lambda o,f,p,a=a,b=b:inside(p,a,b,.01),brass,'decor','Lamps | floor lamp stem')
  c=(a+b)/2;o=cylinder('Study lamp | drum shade',(c.x,c.y,b.z+.06),.19,.24,'lighting',linen,radius_top=.17);o['lightZone']='study';o['siteLighting']=True
  cylinder('Study lamp | base',(c.x,c.y,a.z+.012),.14,.024,'decor',brass)
 report['shades']=len(shades)+1

def chandelier(report):
 brass=bpy.data.materials['interiormetal'];opal=material('Decor | opal glass','#fbf3e2',.25,emission=2.2)
 cx,cy,ceil=8.05,11.2,2.70
 cylinder('Chandelier | ceiling canopy',(cx,cy,ceil-.02),.075,.04,'interiormetal',brass,radius_top=.06)
 tube('Chandelier | drop rod',[(cx,cy,ceil-.04),(cx,cy,2.02)],.008,'interiormetal',brass)
 sphere('Chandelier | hub',(cx,cy,2.02),(.035,.035,.035),'interiormetal',brass)
 globes=0
 for r,z,n,arm_drop in ((.46,1.93,12,.05),(.27,2.08,8,.04)):
  ring=[(cx+r*math.cos(t),cy+r*math.sin(t),z) for t in [i*2*math.pi/72 for i in range(73)]]
  tube('Chandelier | ring',ring,.009,'interiormetal',brass)
  for k in range(4):
   t=k*math.pi/2+math.pi/4;tube('Chandelier | spoke',[(cx,cy,2.02),(cx+r*math.cos(t),cy+r*math.sin(t),z)],.006,'interiormetal',brass)
  for k in range(n):
   t=k*2*math.pi/n+(.13 if r<.3 else 0);px,py=cx+r*math.cos(t),cy+r*math.sin(t)
   tube('Chandelier | globe stem',[(px,py,z),(px,py,z-arm_drop)],.005,'interiormetal',brass)
   cylinder('Chandelier | lamp holder',(px,py,z-arm_drop-.012),.014,.024,'interiormetal',brass)
   o=sphere('Chandelier | opal globe',(px,py,z-arm_drop-.075),(.06,.06,.06),'lighting',opal);o['lightZone']='living';o['siteLighting']=True;globes+=1
 report['chandelier']=f'two-tier brass ring chandelier, {globes} opal globes, lowest point {1.93-.05-.135:.2f} m above the floor'

if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 assert not any(o.get('fixturesPass') for o in bpy.data.objects),'Already applied'
 cfg=json.load(open(os.path.join(root,'scripts','reference-materials.json')))
 for cat in ['tapware','interiormetal']:pack_surface(cat,cfg)
 report={};created.clear()
 terrace=sanitary(report);terrace_sink(terrace,report);hose_bib(report);lamps(report);chandelier(report)
 bpy.context.view_layer.update()
 for o in created:
  uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
 groups={}
 for o in created:groups.setdefault((o['category'],o.data.materials[0].name,o.get('lightZone')),[]).append(o)
 for (cat,mat,zone),objs in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in objs:o.select_set(True)
  bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object
  z=min((o.matrix_world@v.co).z for v in o.data.vertices);o['floor']=0 if z<2.9 else 1 if z<6.0 else 2
  o.name=f"Fixtures | {mat.split('| ')[-1]}{' | '+zone if zone else ''}";o['category']=cat;o['finishGroup']=cat;o['fixturesPass']=True
  if zone:o['lightZone']=zone;o['siteLighting']=True
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 path=os.path.join(root,'public','interior-refinement.json');data=json.load(open(path));data['fixturesAndLamps']=report
 with open(path,'w') as f:json.dump(data,f,indent=2)
 export_and_save();print('FIXTURES SAVED',json.dumps(report))
