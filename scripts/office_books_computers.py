"""Books on every office and study shelf, and realistic computers on the desks.
Shelves (from the source casework): ground-floor hall bookcases on the west wall (x -1.06..-0.56) and north wall
(y 9.38..9.88), and the first-floor study wall unit (x 6.25..6.59). Desks: the study's long desk (top 3.91 m, wall
at x 8.44, knee spaces y 15.95-16.88 and 17.33-18.23) and bedroom two's desk (top 3.90 m, wall at y 9.38).
Screens carry generated images (an architect's floor plan, a spreadsheet, a project dashboard) packed in the model."""
import bpy,os,sys,json,math,random
import numpy as np
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import material
from living_niche_shelf import export
blend=os.path.join(root,'Francis-Web.blend')
rng=random.Random(2024)
PARTS={}
def add_box(mat,center,size,frame=None):
 """Accumulate an axis-aligned (or framed) box into the per-material mesh buffer."""
 v,f=PARTS.setdefault(mat,([],[]));o=len(v);cx,cy,cz=center or (0,0,0);sx,sy,sz=[s/2 for s in size]
 for dz in (-1,1):
  for dx,dy in ((-1,-1),(1,-1),(1,1),(-1,1)):
   p=(dx*sx,dy*sy,dz*sz)
   v.append(frame(p) if frame else (cx+p[0],cy+p[1],cz+p[2]))
 f.extend([(o,o+3,o+2,o+1),(o+4,o+5,o+6,o+7),(o,o+1,o+5,o+4),(o+1,o+2,o+6,o+5),(o+2,o+3,o+7,o+6),(o+3,o,o+4,o+7)])

PALETTE=['#2f3a4a','#7a3b2e','#55603f','#d8cdb4','#2b2b2d','#b7905a','#6b2f3a','#3f5a52','#c9b79a','#8a8f94','#e9e2d2','#a4552f']
def init_materials():
 global BOOK,GOLD,CREAM,STONE,BLACK
 BOOK={c:material('Decor | book '+c,c,.75) for c in PALETTE}
 GOLD=material('Decor | spine gilt','#c9a55a',.35,.7);CREAM=material('Decor | spine label','#efe7d6',.8)
 STONE=material('Decor | travertine','#d8ccb6',.7);BLACK=material('Decor | PV frame black','#1b1d20',.4,.6)

def shelf(along,lo,hi,base,clear,back,out,depth_max):
 """Fill one shelf. along: 'x' or 'y' axis the shelf runs on; back: wall-side coordinate; out: +1/-1 towards room."""
 pos=lo+.02;count=0
 def put(mat,a0,a1,d0,d1,z0,z1):
  ca,cd=(a0+a1)/2,back+out*(d0+d1)/2;size_a,size_d=a1-a0,d1-d0
  c=(cd,ca,(z0+z1)/2) if along=='y' else (ca,cd,(z0+z1)/2);s=(size_d,size_a,z1-z0) if along=='y' else (size_a,size_d,z1-z0)
  add_box(mat,c,s)
 while pos<hi-.05:
  r=rng.random()
  if r<.74:
   for _ in range(rng.randint(5,13)):
    w=rng.uniform(.018,.048);h=min(clear-.025,rng.uniform(.17,.31));d=min(depth_max,rng.uniform(.14,.23))
    if pos+w>hi-.02:break
    col=rng.choice(PALETTE);put(BOOK[col],pos,pos+w-.002,.015,.015+d,base,base+h)
    if rng.random()<.38:
     band=GOLD if col in ('#2f3a4a','#7a3b2e','#2b2b2d','#6b2f3a','#3f5a52','#55603f') else CREAM
     for zb in ((h*.82,h*.86),) if rng.random()<.6 else ((h*.12,h*.2),(h*.8,h*.84)):
      put(band,pos+.002,pos+w-.004,.015+d,.015+d+.0015,base+zb[0],base+zb[1])
    pos+=w;count+=1
  elif r<.88:
   w=rng.uniform(.15,.22);z=base
   for _ in range(rng.randint(2,5)):
    t=rng.uniform(.02,.04);col=rng.choice(PALETTE);put(BOOK[col],pos+.005,pos+.005+w-rng.uniform(0,.02),.02,.02+min(depth_max,rng.uniform(.15,.21)),z,z+t);z+=t;count+=1
   if rng.random()<.5 and z+.08<base+clear:put(STONE,pos+w/2-.035,pos+w/2+.035,.06,.13,z,z+.07)
   pos+=w+.015
  else:
   g=rng.uniform(.07,.16)
   if rng.random()<.5:put(BLACK,pos+.01,pos+.022,.03,.15,base,base+min(.15,clear-.03))
   pos+=g
 return count

def screen_image(kind,W=640,H=400):
 img=np.zeros((H,W,3));yy,xx=np.mgrid[0:H,0:W]/np.array([H,W])[:,None,None]
 if kind=='plan':
  img[:]=np.array([.13,.16,.2]);img[:int(.06*H)]=[.22,.25,.3]
  img[int(.06*H):,:int(.16*W)]=[.17,.2,.25]
  def rect(x0,y0,x1,y1,t=2):
   X0,X1,Y0,Y1=int(x0*W),int(x1*W),int(y0*H),int(y1*H)
   img[Y0:Y0+t,X0:X1]=img[Y1-t:Y1,X0:X1]=img[Y0:Y1,X0:X0+t]=img[Y0:Y1,X1-t:X1]=[.88,.91,.95]
  rect(.24,.14,.92,.9,3)
  for r in ((.24,.14,.5,.5),(.5,.14,.92,.42),(.5,.42,.72,.9),(.72,.42,.92,.9),(.24,.5,.5,.9)):rect(*r)
  for k in range(9):img[int((.2+k*.075)*H),int(.02*W):int(.13*W)]=[.55,.6,.68]
  img[int(.62*H):int(.64*H),int(.3*W):int(.44*W)]=[.85,.62,.3]
 elif kind=='sheet':
  img[:]=1.0;img[:int(.09*H)]=[.13,.45,.29]
  for r in range(int(.15*H),H,int(.045*H)):img[r,:]=[.85,.85,.85]
  for c in range(0,W,int(.12*W)):img[int(.12*H):,c]=[.85,.85,.85]
  img[int(.12*H):int(.165*H)]=[.9,.94,.91]
  for k in range(8):
   h=.2+.5*abs(math.sin(k*1.3));x0=int((.58+k*.045)*W);img[int((.92-h*.5)*H):int(.92*H),x0:x0+int(.03*W)]=[.2,.55,.75]
 else:
  img[:]=np.array([.95,.94,.92]);img[:,:int(.18*W)]=[.16,.2,.26]
  for k,(c,v) in enumerate(((.25,.62),(.47,.38),(.69,.84))):
   x0=int(c*W);img[int(.12*H):int(.36*H),x0:x0+int(.19*W)]=[1,1,1];img[int(.3*H):int(.33*H),x0+8:x0+8+int(.17*W*v)]=[.84,.55,.24]
  t=np.linspace(0,1,W-int(.24*W));curve=(.82-.25*t-.06*np.sin(t*14))*H
  for i,yv in enumerate(curve):img[int(yv):int(yv)+3,int(.22*W)+i]=[.24,.48,.7]
 return np.clip(img,0,1)
def screen_mat(kind):
 arr=screen_image(kind);H,W,_=arr.shape;rgba=np.concatenate([arr,np.ones((H,W,1))],-1)[::-1].astype(np.float32)
 im=bpy.data.images.new('Screen | '+kind,W,H);im.pixels[:]=rgba.ravel();im.pack()
 m=bpy.data.materials.new('Decor | screen '+kind);m.use_nodes=True;nt=m.node_tree;bs=nt.nodes['Principled BSDF']
 tex=nt.nodes.new('ShaderNodeTexImage');tex.image=im;nt.links.new(tex.outputs['Color'],bs.inputs['Base Color']);nt.links.new(tex.outputs['Color'],bs.inputs['Emission Color'])
 bs.inputs['Emission Strength'].default_value=.55;bs.inputs['Roughness'].default_value=.15;m['keepTexture']=True;return m

SCREENS=[]
def frame_of(origin,toward):
 f=Vector((toward[0],toward[1],0)).normalized();r=Vector((-f.y,f.x,0));o=Vector((origin[0],origin[1],0))
 return lambda p:tuple(o+r*p[0]+f*p[1]+Vector((0,0,p[2])))
def quad(mat,corners):
 SCREENS.append((mat,corners))
def monitor(origin,toward,top,kind):
 F=frame_of(origin,toward);alu=material('Decor | anodised aluminium','#b9bec2',.32,.85);black=material('Decor | monitor black','#141518',.35,.3)
 add_box(alu,None,(.17,.14,.006),lambda p:F((p[0],p[1]-.02,p[2]+top+.003)))
 add_box(alu,None,(.045,.018,.15),lambda p:F((p[0],p[1]-.075,p[2]+top+.075)))
 cz=top+.10+.16;add_box(black,None,(.545,.012,.32),lambda p:F((p[0],p[1]-.06,p[2]+cz)))
 w,h=.525,.295;quad(screen_mat(kind),[F((-w/2,-.0535,cz-h/2)),F((w/2,-.0535,cz-h/2)),F((w/2,-.0535,cz+h/2)),F((-w/2,-.0535,cz+h/2))])
 # Keyboard and mouse in front.
 add_box(alu,None,(.42,.13,.009),lambda p:F((p[0]-.03,p[1]+.17,p[2]+top+.0045)))
 key=material('Decor | keycaps','#e9e9e6',.5)
 for row in range(4):
  for k in range(14):add_box(key,None,(.024,.022,.004),lambda p,row=row,k=k:F((p[0]-.03-.195+k*.0295,p[1]+.17-.045+row*.029,p[2]+top+.011)))
 v,fc=PARTS.setdefault(material('Decor | mouse white','#f1f1ef',.35),([],[]))
 o=len(v);seg=16
 for j in range(5):
  for i in range(seg):
   t=2*math.pi*i/seg;a=math.sin(j/4*math.pi/2);hgt=.016*math.cos(j/4*math.pi/2)
   v.append(F((.24+.032*a*math.cos(t)*(1-.0*j),.17+.058*a*math.sin(t)/1.0,top+hgt+.0005)))
 for j in range(4):
  for i in range(seg):a=o+j*seg+i;b=o+j*seg+(i+1)%seg;fc.append((a,b,b+seg,a+seg))
def laptop(origin,toward,top,kind,open_deg=108):
 F=frame_of(origin,toward);alu=material('Decor | laptop aluminium','#c4c6c8',.3,.85);black=material('Decor | monitor black','#141518',.35,.3)
 add_box(alu,None,(.31,.215,.013),lambda p:F((p[0],p[1],p[2]+top+.0065)))
 add_box(black,None,(.27,.09,.001),lambda p:F((p[0],p[1]-.025,p[2]+top+.0135)))
 a=math.radians(open_deg-90);hinge=Vector((0,-.1075,top+.013));up=Vector((0,-math.sin(a),math.cos(a)));n=Vector((0,math.cos(a),math.sin(a)))
 def lid(p):q=hinge+Vector((p[0],0,0))+up*(p[2]+.1)+n*p[1];return F((q.x,q.y,q.z))
 add_box(alu,None,(.31,.006,.205),lid)
 w,h=.285,.18;c=lambda x,z:(lambda q:F((q.x,q.y,q.z)))(hinge+Vector((x,0,0))+up*(z+.1)+n*.0035)
 quad(screen_mat(kind),[c(-w/2,-h/2),c(w/2,-h/2),c(w/2,h/2),c(-w/2,h/2)])

def build():
 init_materials();counts={}
 # The ground-floor hall shelving is a general store, so it stays empty.
 tops=[.03,.50,.98,1.45,1.93];under=[.48,.95,1.42,1.90,2.38]
 # First-floor study wall unit (spines face +x).
 counts['study']=sum(shelf('y',16.02,18.65,t,u-t,6.25,1,.30) for t,u in ((3.98,4.34),(4.37,4.74),(4.76,5.13),(5.16,5.53)))
 # Floating shelves above the study desk (spines face -x).
 counts['studyFloating']=sum(shelf('y',15.62,18.58,t,u-t,8.44,-1,.22) for t,u in ((4.43,4.80),(4.83,5.30)))
 # Two grey placeholder monitor boxes (Generic Model Boxes 2329044/2329045) stand on the study desk; remove them.
 from luxury_interiors import remove_faces
 counts['placeholderFaces']=sum(remove_faces(o,[((8.09,16.09,4.04),(8.14,16.71,4.41)),((8.09,17.54,4.04),(8.14,18.16,4.41))]) for o in bpy.data.objects if o.type=='MESH' and o.get('category')=='details' and o.get('floor')==1)
 monitor((8.30,16.41),(-1,0),3.91,'plan')
 laptop((8.12,17.78),(-1,0),3.91,'dash')
 laptop((1.0,9.62),(0,1),3.90,'sheet')
 return counts

if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 for o in [o for o in bpy.data.objects if o.get('officePass')]:bpy.data.objects.remove(o,do_unlink=True)
 counts=build()
 for mat,(v,f) in PARTS.items():
  me=bpy.data.meshes.new('Office | '+mat.name);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new('Office | '+mat.name.split('| ')[-1],me)
  bpy.context.collection.objects.link(o);me.materials.append(mat)
  uv=me.uv_layers.new(name='UVMap')
  for p in me.polygons:
   ax=max(range(3),key=lambda i:abs(p.normal[i]));axes=[i for i in range(3) if i!=ax]
   for li in p.loop_indices:co=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]]*2,co[axes[1]]*2)
  z=min(vv[2] for vv in v);o['category']='decor';o['finishGroup']='decor';o['floor']=0 if z<3 else 1;o['officePass']=True
 for k,(mat,c) in enumerate(SCREENS):
  me=bpy.data.meshes.new('Screen');me.from_pydata(c,[],[(0,1,2,3)]);me.update();o=bpy.data.objects.new(f'Office | screen {k}',me);bpy.context.collection.objects.link(o);me.materials.append(mat)
  uv=me.uv_layers.new(name='UVMap')
  for li,uvv in zip(me.polygons[0].loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[li].uv=uvv
  o['category']='decor';o['finishGroup']='decor';o['floor']=1;o['officePass']=True
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 export();print('OFFICE SAVED',json.dumps(counts),len(SCREENS),'screens')
