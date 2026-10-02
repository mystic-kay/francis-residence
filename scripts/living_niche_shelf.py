"""Styled built-in for the recess between the living room and dining room (east wall, x 10.338, y 13.59-14.86,
0.40 m deep, floor to 2.70 m): floating fluted walnut credenza with marble top, six-frame photo gallery, two floating
walnut shelves with warm LED strips, and curated decor. Photos are generated Kenyan landscape prints, packed into the
model, intended to be swapped for the client's own photographs."""
import bpy,os,sys,json,math
import numpy as np
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import created,material,box,cylinder,sphere,line,finish
from refine_interior_realism import pack_surface
from modern_dining_set import mesh_object,tube
blend=os.path.join(root,'Francis-Web.blend')
WALL=10.338;Y0,Y1=13.595,14.855;YC=(Y0+Y1)/2

def lathe(name,profile,c,mat,seg=40):
 """Revolve [(radius,z)] about a vertical axis at c=(x,y,z0)."""
 verts=[];faces=[]
 for r,z in profile:
  for k in range(seg):t=2*math.pi*k/seg;verts.append((c[0]+r*math.cos(t),c[1]+r*math.sin(t),c[2]+z))
 for j in range(len(profile)-1):
  for k in range(seg):a=j*seg+k;b=j*seg+(k+1)%seg;faces.append((a,b,b+seg,a+seg))
 faces.append(tuple(range(seg-1,-1,-1)))
 return mesh_object(name,verts,faces,'decor',True,mat)

# ---------- generated prints ----------
def smooth_noise(n,w,seed,oct=4):
 rng=np.random.default_rng(seed);out=np.zeros(w)
 for o in range(oct):
  k=2**(o+2);pts=rng.random(k+1);x=np.linspace(0,k,w);out+=np.interp(x,np.arange(k+1),pts)/(2**o)
 return out/ out.max()
def acacia(img,x,base,s,col):
 h,w,_=img.shape;yy,xx=np.mgrid[0:h,0:w]
 trunk=(abs(xx-x)<s*.035)&(yy<base)&(yy>base-s*.55);img[trunk]=col
 for dx,dy,a in [(-.12,.5,.08),(.10,.47,.07)]:
  br=(abs((xx-x)-(yy-(base-s*.3))*dx/.3*-1)<s*.022)&(yy<base-s*.25)&(yy>base-s*.55);img[br]=col
 can=(((xx-x)/(s*.62))**2+((yy-(base-s*.62))/(s*.11))**2)<1;img[can]=col
def make_print(kind,W=420,H=520):
 yy,xx=np.mgrid[0:H,0:W]/np.array([H,W])[:,None,None]
 img=np.zeros((H,W,3))
 if kind=='sunset':
  top,bot=np.array([.28,.16,.30]),np.array([.98,.62,.30]);img[:]=top+(bot-top)*yy[...,None]**.8
  sun=((xx-.62)**2*1.6+(yy-.62)**2)<.012;img[sun]=[1,.86,.55]
  ground=yy>.80;img[ground]=[.12,.07,.06]
  hill=smooth_noise(4,W,3)*.05+.76
  for i in range(W):img[int(hill[i]*H):,i]=[.15,.09,.07]
  acacia(img,int(W*.32),int(H*.80),H*.55,[.10,.06,.05]);acacia(img,int(W*.80),int(H*.80),H*.30,[.10,.06,.05])
 elif kind=='kili':
  img[:]=(.92-.25*yy)[...,None]
  ridge=.30+.22*np.clip(abs(np.linspace(-1,1,W))*1.3,0,1)+smooth_noise(4,W,8)*.03
  for i in range(W):
   r=int(ridge[i]*H);img[r:,i]=.35;img[r:r+int(.05*H),i]=.95
  plain=yy>.72;img[plain]=(.55-.2*(yy[plain]-.72))[...,None]
  acacia(img,int(W*.25),int(H*.86),H*.22,[.12,.12,.12]);img=img*np.array([1,1,1])
 elif kind=='dhow':
  img[:]=np.array([.86,.76,.60])-np.array([.25,.22,.18])*yy[...,None]
  sea=yy>.62;img[sea]=np.array([.55,.47,.36])-(yy[sea]-.62)[...,None]*.5
  for t in range(0,W,7):img[int(.62*H)+((t*37)%int(.36*H)),t:t+4]=[.80,.70,.54]
  sail=(xx>.38)&(xx<.62)&(yy>.25)&(yy<.58)&((xx-.38)/.24>(yy-.25)/.33*.9)
  img[sail]=[.95,.90,.80];hull=(xx>.34)&(xx<.66)&(yy>.58)&(yy<.63);img[hull]=[.22,.16,.10]
 elif kind=='flamingo':
  img[:]=np.array([.94,.80,.82])-np.array([.15,.18,.10])*yy[...,None]
  water=yy>.55;img[water]=np.array([.86,.70,.74])
  rng=np.random.default_rng(4)
  for _ in range(18):
   cx,cy=rng.uniform(.08,.92),rng.uniform(.58,.9);s=rng.uniform(.6,1.1)
   body=((xx-cx)/(.035*s))**2+((yy-cy)/(.02*s))**2<1;img[body]=[.92,.42,.48]
   neck=(abs(xx-cx-.012*s)<.004*s)&(yy<cy)&(yy>cy-.06*s);img[neck]=[.90,.40,.46]
   leg=(abs(xx-cx)<.0025)&(yy>cy)&(yy<cy+.07*s);img[leg]=[.55,.25,.30]
 elif kind=='leaf':
  img[:]=.93
  for k in range(7):
   a=k/7*math.pi*1.1-.2;cx,cy=.5+.05*math.cos(a),.85
   d=np.stack([xx-cx,yy-cy],-1);u=np.array([math.sin(a)*.6,-math.cos(a)]);u/=np.linalg.norm(u);t=d@u;p=abs(d@np.array([-u[1],u[0]]))
   blade=(t>0)&(t<.62)&(p<.06*np.sin(np.clip(t/.62,0,1)*math.pi));img[blade]=.18+.1*(k%2)
 elif kind=='savanna':
  img[:]=np.array([.78,.86,.92])-np.array([.2,.18,.1])*yy[...,None]
  grass=yy>.6;img[grass]=np.array([.80,.68,.40])-(yy[grass]-.6)[...,None]*np.array([.3,.3,.2])
  for gx in (.30,.40):
   b=((xx-gx)/.05)**2+((yy-.58)/.025)**2<1;img[b]=[.35,.24,.14]
   nk=(abs(xx-gx-.03-(.58-yy)*.25)<.008)&(yy<.58)&(yy>.40);img[nk]=[.35,.24,.14]
   for lx in (-.03,.03):img[(abs(xx-gx-lx)<.006)&(yy>.58)&(yy<.70)]=[.35,.24,.14]
  acacia(img,int(W*.75),int(H*.62),H*.25,[.25,.18,.10])
 img=np.clip(img,0,1);return img
def image_material(name,kind):
 arr=make_print(kind);H,W,_=arr.shape;rgba=np.concatenate([arr,np.ones((H,W,1))],-1)[::-1].astype(np.float32)
 im=bpy.data.images.new('Print | '+kind,W,H);im.pixels[:]=rgba.ravel();im.pack()
 m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;bs=nt.nodes['Principled BSDF']
 tex=nt.nodes.new('ShaderNodeTexImage');tex.image=im;nt.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 bs.inputs['Roughness'].default_value=.35;m['keepTexture']=True;return m

def photo(cy,cz,w,h,frame,kind,frame_w=.018):
 x=WALL-.013
 box('Gallery | frame back',(x,cy,cz),(.022,w,h),'decor',.0015,frame)
 mat=material('Decor | gallery mat','#f4f1ea',.9)
 box('Gallery | mount',(x-.012,cy,cz),(.003,w-2*frame_w,h-2*frame_w),'decor',0,mat)
 pw,ph=(w-2*frame_w)*.72,(h-2*frame_w)*.72
 verts=[(x-.0145,cy+pw/2,cz-ph/2),(x-.0145,cy-pw/2,cz-ph/2),(x-.0145,cy-pw/2,cz+ph/2),(x-.0145,cy+pw/2,cz+ph/2)]
 o=mesh_object('Gallery | print '+kind,verts,[(0,1,2,3)],'decor',False,image_material('Decor | print '+kind,kind))
 uv=o.data.uv_layers.new(name='UVMap')
 for li,(u,v) in zip(o.data.polygons[0].loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[li].uv=(u,v)
 o['photoPrint']=True

def build():
 cfg=json.load(open(os.path.join(root,'scripts','reference-materials.json')))
 for cat in ['diningwood','coffeetop']:pack_surface(cat,cfg)
 created.clear()
 black=material('Decor | PV frame black','#1b1d20',.4,.6);brass=material('Decor | brass fitting','#b48a4a',.32,.9)
 # Credenza: recessed plinth, carcass, fluted doors, marble top.
 d=.38;front=WALL-d;W=Y1-Y0
 box('Credenza | recessed plinth',(WALL-(d-.06)/2,YC,.05),(d-.06,W-.08,.10),'decor',.003,black)
 box('Credenza | carcass',(WALL-d/2,YC,.36),(d,W,.52),'diningwood',.004)
 n=int((W-.03)/.026)
 for k in range(n):
  y=Y0+.015+.013+k*.026
  if abs(y-YC)<.012:continue
  box('Credenza | flute',(front-.006,y,.36),(.012,.020,.48),'diningwood',.004)
 box('Credenza | door shadow gap',(front-.001,YC,.36),(.004,.006,.50),'decor',0,black)
 for y in (YC-.04,YC+.04):box('Credenza | brass pull',(front-.016,y,.53),(.012,.012,.10),'decor',.003,brass)
 box('Credenza | marble top',(WALL-(d+.01)/2,YC,.635),(d+.01,W,.03),'coffeetop',.003)
 # Gallery wall.
 frames=[(YC,1.36,.38,.50,black,'sunset'),(13.845,1.47,.26,.30,material('Decor | walnut frame','#5a3b26',.45),'kili'),
  (13.845,1.165,.26,.19,brass,'leaf'),(14.605,1.525,.26,.19,black,'flamingo'),(14.605,1.22,.26,.30,brass,'dhow'),(YC,1.72,.18,.13,material('Decor | walnut frame','#5a3b26',.45),'savanna')]
 for f in frames:photo(*f)
 # Floating shelves with warm LED under the front edge.
 glow=material('Decor | warm LED','#fff0d5',.22,emission=3)
 for z in (1.90,2.28):
  box('Shelf | floating walnut',(WALL-.13,YC,z),(.26,W-.004,.04),'diningwood',.003)
  box('Shelf | LED strip',(WALL-.235,YC,z-.0215),(.012,W-.06,.003),'interiorlight',0,glow)
 # ---- Decor on the credenza (top at 0.65) ----
 clay=material('Decor | rust','#ad785e',.75);cream=material('Decor | porcelain','#eee6d8',.32);ink=material('Decor | charcoal','#282f32',.6)
 stone=material('Decor | travertine','#d8ccb6',.7);pampas=material('Decor | dried pampas','#e6d5b8',.95);sage=material('Decor | olive','#64715b',.75)
 olive=bpy.data.materials.get('Decor | olive foliage') or material('Decor | olive foliage','#5d6b45',.8)
 t=.65;x=WALL-.19
 lathe('Decor | tall terracotta vase',[(0,0),(.07,0),(.085,.08),(.075,.22),(.04,.32),(.035,.38),(.045,.40),(0,.40)],(x,13.76,t),clay)
 for k,(dy,dz,lean) in enumerate([(-.05,.42,-.10),(0,.48,0),(.05,.44,.12),(.02,.40,.05)]):
  tip=(x+lean*.2,13.76+dy,t+.38+dz);line('Decor | pampas stem',[(x,13.76,t+.36),tip],.003,'decor',pampas)
  sphere('Decor | pampas plume',(tip[0],tip[1],tip[2]-.06),(.025,.025,.11),'decor',pampas)
 for k,(h,c) in enumerate([(.035,'#3c4a5a'),(.03,'#c8b89a'),(.028,'#6b4a3a')]):
  box('Decor | coffee-table book',(x,14.10,t+.015+sum([.035,.03,.028][:k])+h/2-.015),(.24,.30-k*.02,h),'decor',.002,material('Decor | book '+c,c,.8))
 lathe('Decor | stone bowl',[(0,0),(.05,0),(.09,.03),(.10,.06),(.09,.06),(.07,.025),(0,.02)],(x,14.10,t+.093),stone)
 sphere('Decor | sculpture orb',(x+.02,14.50,t+.11),(.06,.06,.06),'decor',ink)
 box('Decor | sculpture plinth',(x+.02,14.50,t+.025),(.10,.10,.05),'decor',.004,stone)
 for dy,h in ((14.68,.16),(14.75,.11)):
  cylinder('Decor | candle',(x-.04,dy,t+h/2),.028,h,'decor',cream)
 # ---- Shelf 1 (top 1.92) ----
 t1=1.92;cols=['#6e7b5c','#b45f3c','#e0d4bf','#2f3a45','#8c6f52','#d9c9a3','#4d5c4a']
 y=13.64
 for k,c in enumerate(cols):
  h=.20+((k*37)%5)*.012;wb=.028+((k*11)%3)*.006
  box('Decor | book',(WALL-.12,y+wb/2,t1+h/2),(.17,wb,h),'decor',.002,material('Decor | book '+c,c,.8));y+=wb+.002
 lathe('Decor | ribbed vase',[(0,0),(.05,0),(.065,.06),(.06,.14),(.03,.20),(.032,.24),(0,.24)],(WALL-.12,14.30,t1),cream)
 lathe('Decor | plant pot',[(0,0),(.055,0),(.065,.11),(.06,.11),(0,.1)],(WALL-.12,14.70,t1),stone)
 for k in range(9):
  a=k*2.4;r=.05+.02*(k%3)
  sphere('Decor | trailing foliage',(WALL-.12+r*math.cos(a)*.6,14.70+r*math.sin(a),t1+.12-(k%4)*.06),(.045,.045,.04),'decor',olive)
 for k in range(4):sphere('Decor | trailing foliage',(WALL-.25,14.68+.02*k,t1-.03-.07*k),(.03,.03,.04),'decor',olive)
 # ---- Shelf 2 (top 2.30) ----
 t2=2.30
 lathe('Decor | stoneware jug',[(0,0),(.045,0),(.06,.05),(.055,.12),(.035,.17),(.04,.19),(0,.19)],(WALL-.12,13.80,t2),sage)
 for k,(h,c) in enumerate([(.03,'#d9c9a3'),(.025,'#2f3a45')]):
  box('Decor | book stack',(WALL-.12,14.22,t2+.015+(.03 if k else 0)),(.17,.24,h),'decor',.002,material('Decor | book '+c,c,.8))
 sphere('Decor | small orb',(WALL-.12,14.22,t2+.085),(.03,.03,.03),'decor',brass)
 lathe('Decor | low bowl',[(0,0),(.04,0),(.08,.035),(.085,.05),(.075,.05),(.035,.018),(0,.015)],(WALL-.12,14.62,t2),clay)

def export():
 links=[]
 for m in bpy.data.materials:
  if not m.use_nodes or m.get('keepTexture'):continue
  bs=m.node_tree.nodes.get('Principled BSDF')
  if not bs:continue
  for key in ['Base Color','Roughness','Normal']:
   for link in list(bs.inputs[key].links):links.append((m.node_tree,link.from_socket,link.to_socket));m.node_tree.links.remove(link)
 bpy.ops.object.select_all(action='DESELECT')
 for o in bpy.data.objects:
  if o.type=='MESH' and o.get('category'):o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=os.path.join(root,'public','models','francis.glb'),export_format='GLB',export_extras=True,export_yup=True,use_selection=True)
 for tree,a,b in links:tree.links.new(a,b)
 bpy.ops.wm.save_as_mainfile(filepath=blend)

if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 for o in [o for o in bpy.data.objects if o.get('livingNiche')]:bpy.data.objects.remove(o,do_unlink=True)
 build();bpy.context.view_layer.update()
 for o in created:
  if o.get('photoPrint'):continue
  uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
  for f in o.data.polygons:
   nrm=o.matrix_world.to_3x3()@f.normal;ax=max(range(3),key=lambda i:abs(nrm[i]));axes=[i for i in range(3) if i!=ax]
   for li in f.loop_indices:p=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(p[axes[0]],p[axes[1]])
 groups={}
 for o in created:groups.setdefault((o['category'],o.data.materials[0].name),[]).append(o)
 for (cat,mat),objs in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in objs:o.select_set(True)
  bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object
  o.name='Living niche | '+mat.split('| ')[-1];o['category']=cat;o['finishGroup']=cat;o['floor']=0;o['livingNiche']=True
  if cat=='interiorlight':o['lightZone']='corridor';o['siteLighting']=True
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 export();print('LIVING NICHE SAVED',len(groups),'objects')
