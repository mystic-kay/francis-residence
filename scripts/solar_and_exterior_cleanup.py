"""Remove remaining white placeholder boxes outside the house, and rebuild the rooftop solar water heater as a
realistic thermosiphon: two 1.0 x 1.8 m flat-plate collectors (anodised frames, dark selective absorber with riser
fins, glass edge) tilted 10 degrees below the existing 250 L cylinder, with insulated flow/return pipes and tank cradles."""
import bpy,os,sys,json,re,math
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import created,remove_faces,material,box
from refine_interior_realism import export_and_save
from modern_dining_set import tube
blend=os.path.join(root,'Francis-Web.blend')
SRC=json.load(open(os.path.join(root,'scene-inspection.json')))['objects']
# Outdoor placeholders: IP66 sockets, CCTV blocks, first-flush diverter, survey pegs, exterior sleeves/ports, a shower
# connection poking through the rear wall.
PATTERNS=[r'Socket Outlet.*IP66',r'KE CCTV Camera',r'FFD-1 first-flush',r'Generic Model Box \[232938[1-6]\]',r'Sleeve DN25 \[2311743\]',r'Sleeve DN50 \[231169[34]\]',r'KD Port',r'Fixture Connection - Sanitary DN50 shower']
LOOSE=('details','metal','lighting','hardware','ceramic','decor','glass','wood')

def clean_exterior():
 boxes=[]
 for s in SRC:
  if any(re.search(p,s['name']) for p in PATTERNS):boxes.append((tuple(v-.01 for v in s['min']),tuple(v+.01 for v in s['max'])))
 n=0
 for o in [o for o in bpy.data.objects if o.type=='MESH' and o.get('category') in LOOSE]:n+=remove_faces(o,boxes)
 return {'sourceItems':len(boxes),'faces':n}

class Frame:
 """Local frame of a panel tilted about x: u along x, v up the slope, n out of the glass."""
 def __init__(s,x0,x1,y_low,y_high,z_low,z_high):
  s.c=Vector(((x0+x1)/2,(y_low+y_high)/2,(z_low+z_high)/2));s.w=x1-x0
  d=Vector((0,y_high-y_low,z_high-z_low));s.l=d.length;s.v=d.normalized();s.n=Vector((1,0,0)).cross(s.v)
  if s.n.z<0:s.n=-s.n
  s.a=math.atan2(s.v.z,s.v.y) if s.v.y>=0 else math.atan2(-s.v.z,-s.v.y)
 def at(s,u,v,w):return s.c+Vector((u,0,0))+s.v*v+s.n*w
 def box(s,name,u,v,w,su,sv,sw,mat,bevel=0):
  o=box(name,tuple(s.at(u,v,w)),(su,sv,sw),'decor',bevel,mat);o.rotation_euler.x=s.a;return o

def source(pattern):return [(Vector(t['min']),Vector(t['max']),t['name']) for t in SRC if re.search(pattern,t['name'])]
def legs(f,alu,x0,x1,feet_z):
 # Two rails under the panel and four legs down to the roof deck.
 for u in (-f.w/2+.12,f.w/2-.12):
  f.box('Solar | mounting rail',u,0,-.06,.04,f.l-.1,.04,alu,.003)
  for v in (-f.l/2+.15,f.l/2-.15):
   p=f.at(u,v,-.08);box('Solar | mounting leg',(p.x,p.y,(feet_z+p.z)/2),(.04,.04,max(.02,p.z-feet_z)),'decor',.003,alu)

def solar():
 # Clear the earlier single collector and its legs.
 old=0
 for o in [o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Site fittings |')]:
  if 'solar collector glass' in o.name:old+=len(o.data.polygons);bpy.data.objects.remove(o,do_unlink=True);continue
  if 'anodised aluminium' in o.name:old+=remove_faces(o,[((4.8,9.9,9.7),(6.5,11.62,10.2))])
 pv=source(r'PV module \d+');sc=source(r'SC-1[ab] solar thermal collector')
 keep={'walls','render','roof','coping','accent','floor','ceiling','paving','lawn'}
 for o in [o for o in bpy.data.objects if o.type=='MESH' and o.get('category') not in keep]:
  old+=remove_faces(o,[(tuple(a-Vector((.01,.01,.01))),tuple(b+Vector((.01,.01,.01)))) for a,b,_ in pv+sc])
 alu=material('Decor | anodised aluminium','#b9bec2',.32,.85);black=material('Decor | PV frame black','#1b1d20',.4,.6)
 cell=material('Decor | PV mono cells','#0a0e14',.16,.1,coat=1);gap=material('Decor | PV cell gap','#a7b0b8',.4,.3)
 absorber=material('Decor | selective absorber','#0b1622',.12,.05,coat=1);fin=material('Decor | absorber riser','#122130',.18,.1,coat=1)
 lag=material('Decor | pipe lagging','#1d1e20',.7);steel=material('Decor | stainless strap','#c9ccce',.25,.95);deck=9.73
 # PV: 1134 x 2252 mono modules, 6 x 12 half-cut cells (mid split), black frames, low tilt rising to +y.
 for a,b,_ in pv:
  f=Frame(a.x,b.x,a.y,b.y,a.z,b.z-.035)
  f.box('PV | frame',0,0,-.0175,f.w,f.l,.035,black,.003)
  f.box('PV | cells',0,0,.0005,f.w-.04,f.l-.04,.002,cell)
  for k in range(1,6):f.box('PV | cell gap',-f.w/2+.02+(f.w-.04)*k/6,0,.002,.004,f.l-.05,.0015,gap)
  for k in range(1,12):f.box('PV | cell gap',0,-f.l/2+.02+(f.l-.04)*k/12,.002,f.w-.05,.004 if k!=6 else .012,.0015,gap)
  legs(f,alu,a.x,b.x,deck)
 # Flat-plate thermal collectors SC-1a/b, glazed, raised side towards the cylinder.
 tank=Vector((5.65,11.89,10.42));r=.30
 for a,b,name in sc:
  low,high=(a.y,b.y) if 'SC-1a' in name else (b.y,a.y)
  f=Frame(a.x,b.x,low,high,a.z,b.z-.04)
  f.box('Solar | collector box',0,0,-.035,f.w,f.l,.07,alu,.004)
  f.box('Solar | absorber plate',0,0,.0005,f.w-.07,f.l-.07,.002,absorber)
  for k in range(9):f.box('Solar | riser fin',-f.w/2+.08+(f.w-.16)*k/8,0,.003,.012,f.l-.12,.003,fin)
  legs(f,alu,a.x,b.x,deck)
  top=f.at(f.w/2-.08,f.l/2-.03,.02);bot=f.at(-f.w/2+.08,-f.l/2+.03,.02)
  side=1 if 'SC-1a' in name else -1
  tube('Solar | hot flow pipe',[tuple(top),(top.x,tank.y-side*.32,tank.z+.18),(6.30,tank.y-side*.32,tank.z+.18),(6.30,tank.y,tank.z+.18)],.026,'decor',lag)
  tube('Solar | cold return pipe',[(5.05,tank.y-side*.30,tank.z-.18),(bot.x,tank.y-side*.30,tank.z-.18),tuple(bot)],.026,'decor',lag)
 for sx in (5.05,6.25):
  box('Solar | tank cradle',(sx,tank.y,tank.z-r-.02),(.06,.50,.06),'decor',.004,alu)
  ring=[(sx,tank.y+(r+.006)*math.cos(t),tank.z+(r+.006)*math.sin(t)) for t in [i*2*math.pi/40 for i in range(41)]]
  tube('Solar | tank strap',ring,.006,'decor',steel)
 cap=material('Decor | cylinder end cap','#3a3d41',.4,.3)
 for ex,d in ((4.86,-1),(6.44,1)):tube('Solar | cylinder end cap',[(ex,tank.y,tank.z),(ex+d*.03,tank.y,tank.z)],r+.004,'decor',cap)
 return {'removedFaces':old,'pv':f'{len(pv)} x 1134 x 2252 mm mono modules, 6 x 12 cells, black frames, rails and legs','collectors':'SC-1a/b flat-plate, glazed absorber with riser fins, lagged flow and return to the 250 L cylinder'}

if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 assert not any(o.get('solarRebuild') for o in bpy.data.objects),'Already applied'
 report={'exterior':clean_exterior()};created.clear();report['solar']=solar()
 bpy.context.view_layer.update()
 for o in created:
  uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
 groups={}
 for o in created:groups.setdefault(o.data.materials[0].name,[]).append(o)
 for mat,objects in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in objects:o.select_set(True)
  bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object
  o.name='Solar | '+mat.split('| ')[-1];o['category']='decor';o['finishGroup']='decor';o['floor']=2;o['solarRebuild']=True
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 path=os.path.join(root,'public','interior-refinement.json');data=json.load(open(path));data['solarAndExterior']=report
 with open(path,'w') as f:json.dump(data,f,indent=2)
 export_and_save();print('SOLAR SAVED',json.dumps(report))
