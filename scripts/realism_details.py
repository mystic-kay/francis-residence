"""Interior and garden realism, placed by probing the real geometry rather than by hand.
- Bathrooms: around each shower rain head, the walls within reach are tiled floor-to-2.1 m in large-format porcelain
  ('bathtile' finish group), a low stone tray and linear drain go in, and each open side gets a 10 mm fixed glass
  screen with a slim black profile, leaving an entry gap. Each vanity gets a back-lit mirror on the wall behind it, a
  chrome towel rail with a folded towel, a soap dispenser and a bath mat.
- Kitchen: black glass ceramic hob over the source burners, a built-in oven fascia below it, and counter styling
  (coffee machine, kettle, fruit bowl, chopping board with utensils, herb pots) placed only where a probe confirms
  clear worktop.
- Curtains: pleated linen panels and a black ceiling track on the bedroom, study, guest and lounge windows.
- Garden: a charcoal stone water bowl with a still, reflective water surface in the front lawn."""
import bpy,os,sys,json,math
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import material
from refine_interior_realism import export_and_save,pack_surface
blend=os.path.join(root,'Francis-Web.blend')
SRC=json.load(open(os.path.join(root,'scene-inspection.json')))['objects']
PARTS={};REPORT={}
def mat_key(mat,cat):return (mat.name,cat)
def add(mat,cat,verts,faces,uvmode='box',floor=0):
 v,f,meta=PARTS.setdefault(mat_key(mat,cat),([],[],{'mat':mat,'cat':cat,'uv':uvmode,'floor':floor}));o=len(v);v.extend(verts);f.extend(tuple(o+i for i in fc) for fc in faces)
BOXF=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
def box(mat,cat,lo,hi,uv='box',floor=0):
 (x0,y0,z0),(x1,y1,z1)=lo,hi;add(mat,cat,[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)],BOXF,uv,floor)
def cyl(mat,cat,c,r,h,seg=24,r2=None,floor=0):
 r2=r if r2 is None else r2;cx,cy,z=c;v=[(cx+rr*math.cos(2*math.pi*i/seg),cy+rr*math.sin(2*math.pi*i/seg),zz) for rr,zz in ((r,z),(r2,z+h)) for i in range(seg)]
 add(mat,cat,v,[tuple(range(seg-1,-1,-1)),tuple(range(seg,2*seg))]+[(i,(i+1)%seg,(i+1)%seg+seg,i+seg) for i in range(seg)],'box',floor)
def lathe(mat,cat,c,prof,seg=28,floor=0):
 cx,cy,z=c;v=[(cx+r*math.cos(2*math.pi*i/seg),cy+r*math.sin(2*math.pi*i/seg),z+h) for r,h in prof for i in range(seg)]
 add(mat,cat,v,[(j*seg+i,j*seg+(i+1)%seg,(j+1)*seg+(i+1)%seg,(j+1)*seg+i) for j in range(len(prof)-1) for i in range(seg)],'box',floor)
def sphere(mat,cat,c,r,floor=0,sq=1):
 cx,cy,cz=c;n,m=14,8;v=[];fc=[]
 for j in range(m+1):
  ph=-math.pi/2+math.pi*j/m
  for i in range(n):t=2*math.pi*i/n;v.append((cx+r*math.cos(ph)*math.cos(t),cy+r*math.cos(ph)*math.sin(t),cz+r*sq*math.sin(ph)))
 fc=[(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(m) for i in range(n)];add(mat,cat,v,fc,'box',floor)

dg=None
def ray(o,d,dist=3.0):
 ok,loc,n,i,ob,_=bpy.context.scene.ray_cast(dg,Vector(o),Vector(d).normalized(),distance=dist)
 return (loc,n,ob) if ok else None
def floor_at(x,y,z):h=ray((x,y,z),(0,0,-1),3);return h[0].z if h else None
def ceil_at(x,y,z):h=ray((x,y,z),(0,0,1),3.5);return h[0].z if h else None
def src(word):return [(s['name'],Vector(s['min']),Vector(s['max'])) for s in SRC if word in s['name']]
def lvl(z):return 0 if z<3.0 else 1 if z<6.0 else 2

# ---------------- bathrooms ----------------
def showers(m):
 tiles,glass,black,stone,chrome=m['tile'],m['glass'],m['black'],m['stone'],m['chrome'];out=[]
 for name,a,b in src('shower rain head'):
  c=(a+b)/2;fl=floor_at(c.x,c.y,c.z-.3);
  if fl is None:continue
  F=lvl(fl);z=fl+1.2;ext={}
  for k,d in {'-x':(-1,0,0),'+x':(1,0,0),'-y':(0,-1,0),'+y':(0,1,0)}.items():
   h=ray((c.x,c.y,z),d,1.05);ext[k]=(h[0].x if k[1]=='x' else h[0].y) if h else None
  x0=ext['-x'] if ext['-x'] is not None else c.x-.5;x1=ext['+x'] if ext['+x'] is not None else c.x+.5
  y0=ext['-y'] if ext['-y'] is not None else c.y-.5;y1=ext['+y'] if ext['+y'] is not None else c.y+.5
  H=fl+2.1;t=.008
  # Tile the walls that exist; screen the open sides.
  if ext['-x'] is not None:box(tiles,'bathtile',(x0,y0,fl),(x0+t,y1,H),'tile',F)
  if ext['+x'] is not None:box(tiles,'bathtile',(x1-t,y0,fl),(x1,y1,H),'tile',F)
  if ext['-y'] is not None:box(tiles,'bathtile',(x0,y0,fl),(x1,y0+t,H),'tile',F)
  if ext['+y'] is not None:box(tiles,'bathtile',(x0,y1-t,fl),(x1,y1,H),'tile',F)
  box(stone,'bathtile',(x0+.01,y0+.01,fl),(x1-.01,y1-.01,fl+.025),'tile',F)
  drain_y=y0+.08 if ext['-y'] is not None else y1-.08
  box(chrome,'tapware',(x0+.12,drain_y-.025,fl+.025),(x1-.12,drain_y+.025,fl+.028),'box',F)
  opens=[k for k,v in ext.items() if v is None]
  for k in opens[:2]:
   if k[1]=='x':
    xx=x0 if k=='-x' else x1;L=y1-y0;s0,s1=(y0,y0+L*.72) if ext['-y'] is not None else (y1-L*.72,y1)
    box(glass,'decor',(xx-.005,s0,fl+.025),(xx+.005,s1,fl+2.0),'box',F);box(black,'decor',(xx-.012,s0,fl+1.97),(xx+.012,s1,fl+2.0),'box',F)
    box(black,'decor',(xx-.012,s0 if s0>y0 else s1-.012,fl+.025),(xx+.012,(s0+.012) if s0>y0 else s1,fl+2.0),'box',F)
   else:
    yy=y0 if k=='-y' else y1;L=x1-x0;s0,s1=(x0,x0+L*.72) if ext['-x'] is not None else (x1-L*.72,x1)
    box(glass,'decor',(s0,yy-.005,fl+.025),(s1,yy+.005,fl+2.0),'box',F);box(black,'decor',(s0,yy-.012,fl+1.97),(s1,yy+.012,fl+2.0),'box',F)
  out.append({'shower':name.strip()[:30],'extent':[round(x0,2),round(y0,2),round(x1,2),round(y1,2)],'screens':opens[:2]})
 REPORT['showers']=out

def vanities(m):
 out=[]
 for name,a,b in src('Sink Vanity'):
  c=(a+b)/2;fl=floor_at(c.x,c.y,a.z);F=lvl(fl);z=fl+1.6;best=None
  for d in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0)):
   h=ray((c.x,c.y,z),d,.7)
   if h and (best is None or (h[0]-Vector((c.x,c.y,z))).length<best[1]):best=(Vector(d),(h[0]-Vector((c.x,c.y,z))).length,h[0])
  if not best:continue
  d,dist,hit=best;n=-d;side=Vector((-d.y,d.x,0))
  def at(u,v,w):return hit+side*u+n*v+Vector((0,0,w-z))
  def slab(mat,cat,u0,u1,v0,v1,w0,w1):
   pts=[at(u,v,w) for w in (w0,w1) for (u,v) in ((u0,v0),(u1,v0),(u1,v1),(u0,v1))];add(mat,cat,[tuple(p) for p in pts],BOXF,'box',F)
  # Back-lit mirror: warm LED halo plate, then the mirror proud of it.
  slab(m['led'],'interiorlight',-.29,.29,.004,.012,fl+1.18,fl+1.98);slab(m['mirror'],'decor',-.27,.27,.012,.03,fl+1.2,fl+1.96)
  # Towel rail and folded towel 0.55 m along the wall.
  for w in (fl+1.0,fl+1.1):slab(m['chrome'],'tapware',.42,.82,.06,.075,w,w+.015)
  for u in (.42,.805):slab(m['chrome'],'tapware',u,u+.015,0,.075,fl+.99,fl+1.12)
  slab(m['towel'],'decor',.45,.79,.045,.095,fl+.72,fl+1.12)
  slab(m['towel2'],'decor',.47,.77,.093,.105,fl+.80,fl+1.10)
  # Soap dispenser on the basin deck and a mat in front.
  basin_top=b.z-.12;p=at(-.2,.12,0);cyl(m['amber'],'decor',(p.x,p.y,basin_top),.03,.13,16,.026,F);cyl(m['black'],'decor',(p.x,p.y,basin_top+.13),.012,.04,10,.008,F)
  q=at(0,.85,0);box(m['mat'],'decor',(q.x-.3,q.y-.2,fl),(q.x+.3,q.y+.2,fl+.012),'box',F) if abs(n.x)>abs(n.y) else box(m['mat'],'decor',(q.x-.2,q.y-.3,fl),(q.x+.2,q.y+.3,fl+.012),'box',F)
  out.append(name.strip()[:30])
 REPORT['vanities']=out

# ---------------- kitchen ----------------
def kitchen(m):
 burners=[(Vector(s['min'])+Vector(s['max']))/2 for s in SRC if 'Hob burner' in s['name']]
 cx=sum(b.x for b in burners)/len(burners);cy=sum(b.y for b in burners)/len(burners);top=max(s['max'][2] for s in SRC if 'Hob burner' in s['name'])
 box(m['hob'],'decor',(cx-.3,cy-.27,top+.001),(cx+.3,cy+.27,top+.007))
 for b in burners:
  ring=[(b.x+.075*math.cos(t),b.y+.075*math.sin(t),top+.0075) for t in [i*2*math.pi/36 for i in range(36)]]
  add(m['hobmark'],'decor',ring+[(x,y,z+.0004) for x,y,z in ring],[(i,(i+1)%36,(i+1)%36+36,i+36) for i in range(36)])
 # Oven fascia on the cabinet front below the hob.
 h=ray((cx+1.2,cy,.5),(-1,0,0),2.0)
 if h:
  fx=h[0].x;box(m['ovenglass'],'decor',(fx,cy-.29,.14),(fx+.012,cy+.29,.72));box(m['chrome'],'tapware',(fx+.012,cy-.22,.66),(fx+.035,cy+.22,.685))
  box(m['black'],'decor',(fx,cy-.29,.72),(fx+.012,cy+.29,.80))
 REPORT['hob']=[round(cx,2),round(cy,2),round(top,3)]
 placed=[]
 def spot(x,y,need=.45,foot=.18):
  h=ray((x,y,1.35),(0,0,-1),1.0)
  if not h or h[2].get('category')!='counter' or h[1].z<.95 or not(.84<h[0].z<.96):return None
  if ray((x,y,h[0].z+.01),(0,0,1),need):return None
  for dx,dy in ((foot,0),(-foot,0),(0,foot),(0,-foot)):
   g=ray((x+dx,y+dy,1.35),(0,0,-1),1.0)
   if not g or abs(g[0].z-h[0].z)>.01:return None
  return h[0].z
 cands={'coffee':[(5.65,18.38),(5.45,18.38)],'kettle':[(3.25,18.38),(3.4,18.38)],'bowl':[(4.6,16.9),(4.3,16.9),(4.9,16.9)],
  'board':[(5.0,18.38),(4.95,18.4)],'herbs':[(6.9,18.25),(6.9,17.9)],'vase':[(5.1,16.75),(4.2,17.05)]}
 for item,pts in cands.items():
  for x,y in pts:
   z=spot(x,y)
   if z is None:continue
   if item=='coffee':
    box(m['black'],'decor',(x-.14,y-.17,z),(x+.14,y+.17,z+.38));box(m['steel'],'decor',(x-.145,y-.12,z+.06),(x+.145,y+.12,z+.075))
    box(m['steel'],'decor',(x-.06,y-.06,z+.22),(x+.06,y+.06,z+.3));cyl(m['white'],'decor',(x+.0,y,z+.075),.035,.09,14,.042)
   elif item=='kettle':lathe(m['steel'],'decor',(x,y,z),[(0,0),(.085,0),(.095,.04),(.09,.17),(.06,.22),(0,.235)]);cyl(m['black'],'decor',(x,y,z+.235),.018,.02,10)
   elif item=='bowl':
    lathe(m['ceramic'],'decor',(x,y,z),[(0,0),(.08,0),(.15,.06),(.16,.09),(.15,.09),(.07,.02),(0,.015)])
    for k,(dx,dy,col,r) in enumerate([(-.05,.02,'orange',.042),(.05,-.03,'orange',.04),(.0,.06,'green',.038),(.03,.04,'red',.04),(-.03,-.05,'lemon',.036)]):sphere(m[col],'decor',(x+dx,y+dy,z+.07+(.03 if k>2 else 0)),r)
   elif item=='board':
    box(m['oak'],'decor',(x-.2,y-.14,z),(x+.2,y+.14,z+.022));lathe(m['white'],'decor',(x+.28,y,z),[(0,0),(.06,0),(.065,.17),(0,.17)])
    for k in range(4):a=k*1.5;add(m['oak'],'decor',[(x+.28+.02*math.cos(a),y+.02*math.sin(a),z+.15),(x+.28+.025*math.cos(a)+.003,y+.02*math.sin(a),z+.15),(x+.28+.05*math.cos(a)+.003,y+.04*math.sin(a),z+.36),(x+.28+.05*math.cos(a),y+.04*math.sin(a),z+.36)],[(0,1,2,3)])
   elif item=='herbs':
    for k in range(3):
     px=x+(k-1)*.14;cyl(m['terracotta'],'decor',(px,y,z),.05,.11,16,.06)
     for j in range(6):sphere(m['herb'],'decor',(px+.03*math.cos(j*1.1),y+.03*math.sin(j*1.1),z+.15+.02*(j%3)),.035)
   elif item=='vase':
    lathe(m['ceramic'],'decor',(x,y,z),[(0,0),(.05,0),(.07,.08),(.04,.2),(.045,.24),(0,.24)])
    for k in range(5):a=k*1.25;line_pts=[(x,y,z+.22),(x+.09*math.cos(a),y+.09*math.sin(a),z+.42+.04*(k%2))];add(m['herb'],'decor',[line_pts[0],(line_pts[0][0]+.004,line_pts[0][1],line_pts[0][2]),(line_pts[1][0]+.004,line_pts[1][1],line_pts[1][2]),line_pts[1]],[(0,1,2,3)]);sphere(m['herb'],'decor',line_pts[1],.022)
   placed.append(item);break
 REPORT['kitchenStyling']=placed

# ---------------- curtains ----------------
WINDOWS=[('primary',[1781599,1781605,1781609],1),('bed2',[1781615,1781625],1),('bed1',[1781700,1781710],-1),('study',[1781639,1781645],-1),
 ('guest',[1781342,1781352],-1),('lounge',[1781737,1781743],1)]
def curtains(m):
 out=[]
 for room,ids,inward in WINDOWS:
  boxes=[(Vector(s['min']),Vector(s['max'])) for s in SRC if any(f'[{i}]' in s['name'] for i in ids)]
  if not boxes:continue
  x0=min(a.x for a,b in boxes);x1=max(b.x for a,b in boxes);gy=boxes[0][0].y if inward>0 else boxes[0][1].y;zc=sum((a.z+b.z)/2 for a,b in boxes)/len(boxes)
  fl=floor_at((x0+x1)/2,gy+inward*.4,zc);ce=ceil_at((x0+x1)/2,gy+inward*.4,zc)
  if fl is None or ce is None:continue
  F=lvl(fl);ty=gy+inward*.16;top=ce-.04
  box(m['black'],'decor',(x0-.25,ty-.02,top),(x1+.25,ty+.02,ce),'box',F)
  for s0,s1 in ((x0-.24,x0+.16),(x1-.16,x1+.24)):
   nx,nz=28,10;v=[];fc=[]
   for i in range(nx+1):
    u=i/nx
    for j in range(nz+1):
     w=j/nz;v.append((s0+(s1-s0)*u,ty+inward*(.03*math.sin(u*math.pi*10)*(1+.15*(1-w))),fl+.015+(top-fl-.03)*w))
   fc=[(i*(nz+1)+j,(i+1)*(nz+1)+j,(i+1)*(nz+1)+j+1,i*(nz+1)+j+1) for i in range(nx) for j in range(nz)]
   add(m['curtain'],'curtains',v,fc,'wall',F)
  out.append(room)
 REPORT['curtains']=out

def water_feature(m):
 x,y=5.6,3.7;g=floor_at(x,y,1.0) or -.59
 # Charcoal stone bowl on a low plinth, filled almost to the brim.
 box(m['charcoal'],'decor',(x-1.25,y-.38,g),(x+1.25,y+.38,g+.06),'box')
 lo,hi=(x-1.15,y-.3),(x+1.15,y+.3);H=.48;t=.05
 for a,b in (((lo[0],lo[1]),(hi[0],lo[1]+t)),((lo[0],hi[1]-t),(hi[0],hi[1])),((lo[0],lo[1]),(lo[0]+t,hi[1])),((hi[0]-t,lo[1]),(hi[0],hi[1]))):box(m['charcoal'],'decor',(a[0],a[1],g+.06),(b[0],b[1],g+.06+H),'box')
 box(m['charcoal'],'decor',(lo[0]+t,lo[1]+t,g+.06),(hi[0]-t,hi[1]-t,g+.1),'box')
 box(m['water'],'water',(lo[0]+t,lo[1]+t,g+.06+H-.035),(hi[0]-t,hi[1]-t,g+.06+H-.03),'box')
 # Bronze spout plate at the far end.
 box(m['bronze'],'decor',(hi[0]-t-.004,y-.09,g+.06+H-.09),(hi[0]-t,y+.09,g+.06+H-.02),'box')
 REPORT['waterFeature']=[x,y,round(g,2)]

if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 for o in [o for o in bpy.data.objects if o.get('realismDetails')]:bpy.data.objects.remove(o,do_unlink=True)
 dg=bpy.context.evaluated_depsgraph_get()
 cfg=json.load(open(os.path.join(root,'scripts','reference-materials.json')))
 for cat in ['bathtile','curtains','tapware']:pack_surface(cat,cfg)
 M=lambda n,c,r=.6,mt=0,**k:material('Decor | '+n,c,r,mt,**k)
 m={'tile':bpy.data.materials['bathtile'],'curtain':bpy.data.materials['curtains'],'chrome':bpy.data.materials['tapware'],
  'glass':M('shower glass','#d7e3e6',.05,0,coat=1),'black':M('PV frame black','#1b1d20',.4,.6),'stone':M('shower tray stone','#e6e1d7',.45),
  'mirror':M('mirror','#e9eef0',.02,1.0),'led':M('warm LED','#fff0d5',.22,emission=3),'towel':M('towel white','#f1ece2',.98),'towel2':M('towel sage','#8a9a80',.98),
  'amber':M('amber glass','#8a5a2a',.15,0,coat=.8),'mat':M('bath mat','#d9d2c4',.98),'hob':M('hob glass','#0e0f11',.08,0,coat=1),'hobmark':M('hob marking','#5a5f66',.4),
  'ovenglass':M('oven glass','#151719',.1,.2,coat=1),'steel':M('brushed steel sink','#b7bcc0',.32,.9),'white':M('porcelain','#eee6d8',.32),
  'ceramic':M('stoneware','#d9d0bf',.55),'orange':M('orange','#e8892c',.55),'green':M('green apple','#8db04a',.45),'red':M('red apple','#b53a2e',.45),'lemon':M('lemon','#e9cf45',.5),
  'oak':M('chopping board oak','#b98a5a',.6),'terracotta':M('rust','#ad785e',.75),'herb':M('herb green','#4f7a3a',.8),'charcoal':M('charcoal stone','#2c2e30',.75),
  'water':M('still water','#1d3a44',.03,0,coat=1),'bronze':M('bronze spout','#6b5136',.35,.8)}
 showers(m);vanities(m);kitchen(m);curtains(m);water_feature(m)
 for (mname,cat),(v,f,meta) in PARTS.items():
  me=bpy.data.meshes.new('Detail | '+mname);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new('Detail | '+mname.split('| ')[-1]+' | '+cat,me)
  bpy.context.collection.objects.link(o);me.materials.append(meta['mat']);uv=me.uv_layers.new(name='UVMap')
  for p in me.polygons:
   ax=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=ax]
   for li in p.loop_indices:
    co=me.vertices[me.loops[li].vertex_index].co;a,b=co[axes[0]],co[axes[1]]
    # Tiles: rotate 45 degrees so the diamond-laid texture reads as a square grid.
    uv.data[li].uv=((a+b)/math.sqrt(2),(b-a)/math.sqrt(2)) if meta['uv']=='tile' else (a,b)
  z=min(vv[2] for vv in v);o['floor']=lvl(z) if cat!='water' else 0;o['category']=cat;o['finishGroup']=cat;o['realismDetails']=True
  if cat=='water':o['category']='decor';o['finishGroup']='decor'
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 path=os.path.join(root,'public','interior-refinement.json');data=json.load(open(path));data['realismDetails']=REPORT
 with open(path,'w') as fh:json.dump(data,fh,indent=2)
 export_and_save();print('DETAILS SAVED',json.dumps(REPORT))
