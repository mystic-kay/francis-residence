"""Kenyan site realism: machine-cut stone boundary walls, stone-clad pillars with precast coping, a ribbed
10,000 L HDPE water tank on its concrete stand behind a timber screen, and slim wall-mounted bedroom TVs."""
import bpy,os,sys,json,math
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import created,remove_faces,material,box
from refine_interior_realism import export_and_save,pack_surface
from modern_dining_set import mesh_object,box_uv,tube
from exterior_stucco import split_exterior,world_uv
blend=os.path.join(root,'Francis-Web.blend')

def take(objects,select,mat,category,label):
 """Move faces chosen by select(centre, points) out of each object into a new object of `category`."""
 moved=0
 for o in objects:
  mw=o.matrix_world;idx=[f.index for f in o.data.polygons if select(mw@f.center,[mw@o.data.vertices[v].co for v in f.vertices])]
  if not idx:continue
  new=split_exterior(o,idx,mat);new.name=f"{o.name.split(' |')[0]} | {label}";new['category']=category;new['finishGroup']=category;new['siteRealism']=True;world_uv(new);moved+=len(idx)
 return moved
inside=lambda pts,a,b,t=.006:all(all(a[i]-t<=p[i]<=b[i]+t for i in range(3)) for p in pts)
meshes=lambda cats:[o for o in bpy.data.objects if o.type=='MESH' and o.get('category') in cats and not o.get('siteRealism')]

def boundary():
 # Wall panels within the perimeter strip (site x -3.86..17.14, y -3.02..21.51) become machine-cut stone.
 strip=lambda c,pts:(c.x<-3.3 or c.x>16.5 or c.y<-2.45 or c.y>20.95) and c.z<2.45
 walls=take(meshes(['render']),strip,bpy.data.materials['boundarywall'],'boundarywall','boundary stone')
 caps=take([o for o in meshes(['accent']) if 'boundary pillars' in o.name],lambda c,pts:c.z>2.395,bpy.data.materials['boundarycoping'],'boundarycoping','precast coping')
 pillars=0
 for o in [o for o in meshes(['accent']) if 'boundary pillars' in o.name]:
  o['category']='boundarypillar';o['finishGroup']='boundarypillar';o.data.materials.clear();o.data.materials.append(bpy.data.materials['boundarypillar']);o['siteRealism']=True;pillars+=len(o.data.polygons)
 return {'stoneWallFaces':walls,'copingFaces':caps,'pillarFaces':pillars}

TANK=Vector((-2.115,-1.025,.38));R=1.19;TOP=3.06
def water_tank():
 # Source: Water Tank 10000L Vertical HDPE on Generic Model Box 2329418 (stand) with slats 2329516-2329660 (screen).
 stand=take(meshes(['details','walls','render']),lambda c,pts:inside(pts,(-3.40,-2.23,-.62),(-1.0,.17,.38)),bpy.data.materials['tankbase'],'tankbase','tank stand')
 screen=take(meshes(['details']),lambda c,pts:inside(pts,(-.915,-2.64,-.62),(-.885,.49,1.18)),bpy.data.materials['gate'],'gate','tank screen slats')
 removed=0
 cats={o.get('category') for o in bpy.data.objects if o.type=='MESH'}-{'paving','lawn','gate','tankbase','boundarywall','boundarypillar','boundarycoping',None}
 for o in meshes(cats):removed+=remove_faces(o,[((-3.40,-2.22,.39),(-.84,.17,3.09))])
 # Ribbed HDPE body: a revolved profile with corrugation bands, a rounded shoulder and moulded lid.
 prof=[(0,0),(R-.04,0),(R,.03)]
 z=.03
 while z<TOP-TANK.z-.42:
  prof+=[(R,z+.08),(R+.022,z+.10),(R+.022,z+.16),(R,z+.18)];z+=.25
 h=TOP-TANK.z
 for i in range(1,9):a=i/9*math.pi/2;prof.append((.34+(R-.34)*math.cos(a),h-.30+.30*math.sin(a)))
 prof+=[(.34,h),(.30,h+.005),(0,h+.005)]
 seg=72;verts=[];faces=[]
 for r,zz in prof:
  for k in range(seg):t=2*math.pi*k/seg;verts.append((TANK.x+r*math.cos(t),TANK.y+r*math.sin(t),TANK.z+zz))
 for j in range(len(prof)-1):
  for k in range(seg):a=j*seg+k;b=j*seg+(k+1)%seg;faces.append((a,b,b+seg,a+seg))
 body=mesh_object('Water tank | ribbed HDPE body',verts,faces,'watertank')
 for f in body.data.polygons:f.use_smooth=True
 lid=[];lf=[];lp=[(0,h+.005),(.27,h+.005),(.28,h+.06),(.26,h+.075),(0,h+.075)]
 for r,zz in lp:
  for k in range(48):t=2*math.pi*k/48;lid.append((TANK.x+r*math.cos(t),TANK.y+r*math.sin(t),TANK.z+zz))
 for j in range(len(lp)-1):
  for k in range(48):a=j*48+k;b=j*48+(k+1)%48;lf.append((a,b,b+48,a+48))
 mesh_object('Water tank | screw lid',lid,lf,'watertank')
 # Brass outlet and overflow towards the house side (+x), on the plumbing face.
 brass=material('Decor | brass fitting','#b48a4a',.32,.9)
 for zz,length,r in ((.16,.22,.028),(h-.42,.16,.022)):
  tube('Water tank | brass fitting',[(TANK.x+R-.01,TANK.y,TANK.z+zz),(TANK.x+R+length,TANK.y,TANK.z+zz)],r,'decor',brass)
 tube('Water tank | outlet pipe',[(TANK.x+R+.22,TANK.y,TANK.z+.16),(TANK.x+R+.22,TANK.y,-.55)],.026,'decor',material('Decor | grey uPVC','#8d9196',.55))
 return {'removedSourceFaces':removed,'standFaces':stand,'screenFaces':screen,'tank':'10,000 L vertical HDPE, 2.38 m diameter, corrugated, screw lid, brass outlet and overflow'}

def tv(name,wall_x,facing,cy,cz,w,hgt,floor_z,console):
 """Slim wall-mounted panel (26 mm) on a 35 mm bracket, with a floating glossy media unit below."""
 frame=material('Decor | TV frame','#111214',.35,.4);screen=material('Decor | large TV screen','#101b27',.19,coat=.7)
 x=wall_x+facing*(.035+.013)
 box(name+' | slim panel',(x,cy,cz),(.026,w,hgt),'decor',.003,frame)
 box(name+' | screen',(x+facing*.0135,cy,cz),(.002,w-.012,hgt-.012),'decor',0,screen)
 box(name+' | wall bracket',(wall_x+facing*.0175,cy,cz),(.035,.40,.30),'decor',.002,frame)
 if console:
  cw,cd,ch,lift=console
  box(name+' | floating media unit',(wall_x+facing*cd/2,cy,floor_z+lift+ch/2),(cd,cw,ch),'tvunit',.006)

def bedroom_tvs():
 removed=0
 for o in meshes(['details','wood','decor','metal','ceramic','hardware','glass']):
  removed+=remove_faces(o,[((2.43,16.74,4.29),(2.54,17.86,4.97)),((2.08,12.89,7.44),(2.19,14.11,8.12))])
 # Bedroom one: 55" (1.23 x 0.71 m), centre 1.18 m above floor, facing the bed; unit clears the TV socket.
 tv('Bedroom one TV',2.44,1,17.30,3.15+1.18,1.228,.708,3.15,(1.60,.36,.24,.30))
 # Top-floor lounge: 65" (1.44 x 0.83 m) on the wall at x 2.18, facing west into the room.
 tv('Top-floor lounge TV',2.18,-1,13.50,6.15+1.22,1.440,.830,6.15,(1.80,.38,.26,.28))
 return {'removedSourceFaces':removed,'bedroomOne':'55-inch slim panel, 1.18 m centre height, floating gloss media unit','topFloorLounge':'65-inch slim panel, 1.22 m centre height, floating gloss media unit'}

if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 assert not any(o.get('siteRealism') for o in bpy.data.objects),'Already applied: restore the previous Francis-Web.blend before rerunning'
 cfg=json.load(open(os.path.join(root,'scripts','reference-materials.json')))
 for cat in ['boundarywall','boundarypillar','boundarycoping','watertank','tankbase','gate','tvunit']:pack_surface(cat,cfg)
 report={'boundary':boundary()}
 created.clear();report['waterTank']=water_tank();report['bedroomTVs']=bedroom_tvs()
 bpy.context.view_layer.update();box_uv(created)
 groups={}
 for o in created:groups.setdefault((o['category'],o.data.materials[0].name,o.location.z>3 or (o.matrix_world@o.data.vertices[0].co).z>3),[]).append(o)
 for (cat,mat,upper),objects in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in objects:o.select_set(True)
  bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object
  z=(o.matrix_world@o.data.vertices[0].co).z;o['floor']=0 if z<3.1 else 1 if z<6.1 else 2
  o.name=f'Site realism | {cat} | {mat}';o['category']=cat;o['finishGroup']=cat;o['siteRealism']=True
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 path=os.path.join(root,'public','interior-refinement.json');data=json.load(open(path));data['siteRealism']=report
 with open(path,'w') as f:json.dump(data,f,indent=2)
 export_and_save();print('SITE REALISM SAVED',json.dumps(report))
