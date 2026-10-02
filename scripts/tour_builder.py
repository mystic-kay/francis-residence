"""Build the guided walkthrough route (public/tour.json) from the real geometry.

Per floor, a 0.15 m walkability grid is made by ray casting: a cell is free when there is floor under it and nothing
(walls, glass, furniture; doors excluded because the tour opens them) within 0.30 m at knee, chest and eye height.
Each room's view point is its most open cell; routes between rooms are A* on the grid, string-pulled to straight
legs. Stairs follow the real dog-leg flights. Coordinates written are Blender (x, y, z) at eye height."""
import bpy,os,json,math,heapq
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=os.path.dirname(bpy.data.filepath)
CELL=.15;X0,X1,Y0,Y1=-1.3,11.7,7.5,19.0;EYE=1.6;CLEAR=.22
SKIP={'doors','frontdoor','frontdoorhardware','lawn','paving','road','interiorlight'}

def scene_tree(floor=False,skip=SKIP):
 verts=[];faces=[]
 for o in bpy.data.objects:
  if o.type!='MESH' or o.get('category') is None:continue
  if not floor and (o.get('category') in skip or o.get('doorLeaf')):continue
  mw=o.matrix_world;off=len(verts);verts.extend(mw@v.co for v in o.data.vertices);faces.extend(tuple(off+i for i in p.vertices) for p in o.data.polygons)
 return BVHTree.FromPolygons(verts,faces)
TREE=scene_tree();FLOOR_TREE=scene_tree(True);GLASSLESS=scene_tree(skip=SKIP|{'glass','balconyglass','pergolaglass'})
DIRS=[Vector((math.cos(a),math.sin(a),0)) for a in [k*math.pi/4 for k in range(8)]]

def grid(z0,tree=None):
 tree=tree or TREE
 nx,ny=int((X1-X0)/CELL),int((Y1-Y0)/CELL);free=[[False]*ny for _ in range(nx)]
 for i in range(nx):
  for j in range(ny):
   x,y=X0+(i+.5)*CELL,Y0+(j+.5)*CELL
   hit=FLOOR_TREE.ray_cast(Vector((x,y,z0+1.0)),Vector((0,0,-1)),1.15)
   if hit[0] is None or abs(hit[0].z-z0)>.12:continue
   head=tree.ray_cast(Vector((x,y,hit[0].z+.05)),Vector((0,0,1)),2.0)
   if head[0] is not None and head[3]<1.95:continue
   ok=True
   for h,r in ((.45,.12),(1.1,CLEAR),(1.6,.10)):
    p=Vector((x,y,z0+h))
    if any(tree.ray_cast(p,d,r)[0] is not None for d in DIRS):ok=False;break
   free[i][j]=ok
 return free
def cell(x,y):return int((x-X0)/CELL),int((y-Y0)/CELL)
def centre(c):return X0+(c[0]+.5)*CELL,Y0+(c[1]+.5)*CELL
def clearance(free):
 nx,ny=len(free),len(free[0]);INF=10**9;d=[[0 if not free[i][j] else INF for j in range(ny)] for i in range(nx)];q=[]
 for i in range(nx):
  for j in range(ny):
   if not free[i][j]:q.append((i,j))
 k=0
 while k<len(q):
  i,j=q[k];k+=1
  for di,dj in ((1,0),(-1,0),(0,1),(0,-1)):
   a,b=i+di,j+dj
   if 0<=a<nx and 0<=b<ny and d[a][b]>d[i][j]+1:d[a][b]=d[i][j]+1;q.append((a,b))
 return d
def nearest_free(free,x,y):
 c=cell(x,y);best=None
 for r in range(0,30):
  for i in range(c[0]-r,c[0]+r+1):
   for j in range(c[1]-r,c[1]+r+1):
    if 0<=i<len(free) and 0<=j<len(free[0]) and free[i][j]:
     d=(i-c[0])**2+(j-c[1])**2
     if best is None or d<best[0]:best=(d,(i,j))
  if best:return best[1]
 raise RuntimeError(f'no free cell near {x},{y}')
def reach(free,a):
 nx,ny=len(free),len(free[0]);seen={a};st=[a]
 while st:
  c=st.pop()
  for di in (-1,0,1):
   for dj in (-1,0,1):
    n=(c[0]+di,c[1]+dj)
    if n not in seen and 0<=n[0]<nx and 0<=n[1]<ny and free[n[0]][n[1]]:seen.add(n);st.append(n)
 return seen
def astar(free,dist,a,b):
 nx,ny=len(free),len(free[0]);g={a:0};prev={};pq=[(0,a)]
 while pq:
  _,c=heapq.heappop(pq)
  if c==b:break
  for di in (-1,0,1):
   for dj in (-1,0,1):
    if not di and not dj:continue
    n=(c[0]+di,c[1]+dj)
    if not(0<=n[0]<nx and 0<=n[1]<ny) or not free[n[0]][n[1]]:continue
    if di and dj and not(free[c[0]+di][c[1]] and free[c[0]][c[1]+dj]):continue
    # Prefer the middle of corridors and doorways.
    cost=g[c]+math.hypot(di,dj)*(1+1.5/(1+dist[n[0]][n[1]]))
    if cost<g.get(n,1e18):g[n]=cost;prev[n]=c;heapq.heappush(pq,(cost+math.hypot(b[0]-n[0],b[1]-n[1]),n))
 if b not in prev and a!=b:raise RuntimeError(f'no route {centre(a)} -> {centre(b)}')
 path=[b]
 while path[-1]!=a:path.append(prev[path[-1]])
 return path[::-1]
def los(free,a,b):
 n=int(max(abs(b[0]-a[0]),abs(b[1]-a[1]))*2)+1
 for k in range(n+1):
  t=k/n;i=round(a[0]+(b[0]-a[0])*t);j=round(a[1]+(b[1]-a[1])*t)
  if not free[i][j]:return False
 return True
def pull(free,path):
 out=[path[0]];k=0
 while k<len(path)-1:
  m=len(path)-1
  while m>k+1 and not los(free,path[k],path[m]):m-=1
  out.append(path[m]);k=m
 return out

FLOORS={0:0.0,1:3.15,2:6.15}
# Rooms in visiting order: (floor, id, name, plan rectangle x0,y0,x1,y1, caption)
ROOMS=[
 (0,'living','Living room',(6.3,7.9,10.3,13.2),'Welcome in. The living room: tub armchairs, a contemporary sofa and a marble TV wall. Tap any glowing dot or surface to change its finish.'),
 (0,'niche','Gallery shelf',(8.4,13.5,10.2,14.8),'Between living and dining, a walnut credenza, floating shelves and a family photo gallery.'),
 (0,'dining','Dining room',(6.4,15.3,10.2,18.5),'Dining for six: smoked walnut on a sculpted fin base, mustard bouclé chairs, plaster pendants above.'),
 (0,'kitchen','Kitchen',(2.5,15.3,6.0,18.5),'The kitchen: shaker cabinetry, black stone worktops and walnut counter stools. Cabinet, worktop and hardware finishes can all be changed.'),
 (0,'guest','Guest bedroom',(-1.1,15.3,2.1,18.5),'The ground-floor guest bedroom, with its own warm pendant lighting.'),
 (1,'primary','Primary suite',(6.3,7.9,11.4,13.2),'The primary suite opens onto a glass balcony. Use the Lighting tab to dim each room independently.'),
 (1,'study','Study',(6.4,15.3,10.2,18.5),'A quiet study at the back of the first floor.'),
 (1,'bed1','Bedroom one',(2.5,15.3,6.0,18.5),'Bedroom one, with a slim wall-mounted TV and a sage panelled bed wall.'),
 (1,'bed2','Bedroom two',(-1.1,9.4,3.3,13.2),'Bedroom two looks out to the front garden.'),
 (2,'lounge','Top-floor lounge',(-1.0,9.6,3.3,14.7),'The top-floor lounge, with a 65-inch TV.'),
 (2,'roofdining','Top-floor dining',(1.3,15.4,6.0,18.5),'An indoor-outdoor dining room under the sky, with the same walnut and bouclé set.'),
 (2,'terrace','Pergola terrace',(6.4,8.2,10.2,14.6),'The pergola terrace with glass balustrades: the best view in the house. You can change glass tints and pergola frames under Materials.')]
STAIR=lambda z:[(5.49,13.30,z),(5.49,12.98,z),(5.49,10.58,z+1.40),(5.30,10.05,z+1.57),(4.40,10.05,z+1.57),(4.19,10.68,z+1.57),(4.19,13.38,z+3.15 if z<3 else z+3.0),(4.19,13.80,z+(3.15 if z<3 else 3.0))]

def build():
 frames=[]
 def walk(pts,z0,label=None):
  for x,y,*h in pts:frames.append({'p':[round(x,3),round(y,3),round((h[0] if h else z0)+EYE,3)],'k':'walk'})
 # Arrival: street, through the opening gate, up the drive to the front door (explicit exterior route).
 frames.append({'p':[13.2,-11.0,1.0],'k':'start','room':'arrival','name':'Arrival','caption':'Welcome to the Francis Residence. The slatted gate glides open as we arrive.','gate':True})
 # Up the drive to the canopy porch beside the living room, which is where the tour goes in.
 walk([(13.2,-8.0,-.6),(13.2,-3.6,-.6),(13.0,0.5,-.6),(9.0,5.2,-.6),(5.2,6.6,-.6),(5.0,7.5,-.15),(5.0,8.4,0.0)],0)
 floor=0;cur=nearest_free(GRIDS[0],5.0,8.5)
 for f,rid,name,(x0,y0,x1,y1),caption in ROOMS:
  if f!=floor:
   # Walk to the stair foot, then climb the flights.
   foot=nearest_free(GRIDS[floor],5.49,13.6)
   for c in pull(GRIDS[floor],astar(GRIDS[floor],DIST[floor],cur,foot))[1:]:x,y=centre(c);frames.append({'p':[round(x,3),round(y,3),FLOORS[floor]+EYE],'k':'walk'})
   frames.append({'k':'note','caption':'Heading upstairs.' if f==1 else 'Up to the top floor.'})
   walk(STAIR(FLOORS[floor]),0)
   floor=f;cur=nearest_free(GRIDS[floor],4.19,13.9)
  best=None
  for g,d in ((GRIDS[floor],DIST[floor]),(None,None)):
   if g is None:
    # Separated only by fixed glazing (e.g. the pergola terrace): route through it like a sliding door.
    g=grid(FLOORS[floor],GLASSLESS);d=clearance(g);cur=nearest_free(g,*centre(cur))
   r=reach(g,cur)
   mx,my=(x0+x1)/2,(y0+y1)/2
   # Open space matters most, but stay near the middle of the room.
   best=max(((min(d[i][j],8)-math.hypot(centre((i,j))[0]-mx,centre((i,j))[1]-my)/.45,(i,j)) for (i,j) in r if x0<=centre((i,j))[0]<=x1 and y0<=centre((i,j))[1]<=y1),default=None)
   if best:break
  if not best:print('SKIP room unreachable',rid);continue
  tgt=best[1]
  for c in pull(g,astar(g,d,cur,tgt))[1:]:x,y=centre(c);frames.append({'p':[round(x,3),round(y,3),FLOORS[floor]+EYE],'k':'walk'})
  x,y=centre(tgt);eye=Vector((x,y,FLOORS[floor]+EYE))
  # Start the turn facing the longest open view so the room reveals itself.
  # Face into the room: the longest view among directions within 60 degrees of the room's centre.
  mid=math.atan2((y0+y1)/2-y,(x0+x1)/2-x) if math.hypot((x0+x1)/2-x,(y0+y1)/2-y)>.8 else None
  ok=lambda k:mid is None or abs((k*math.pi/36-mid+math.pi)%(2*math.pi)-math.pi)<math.pi/3
  view=max((k for k in range(72) if ok(k)),key=lambda k:(lambda h:h[3] if h[0] is not None else 30)(TREE.ray_cast(eye,Vector((math.cos(k*math.pi/36),math.sin(k*math.pi/36),-.05)).normalized(),30)))
  frames.append({'p':[round(x,3),round(y,3),FLOORS[floor]+EYE],'k':'spin','room':rid,'name':name,'caption':caption,'face':round(view*math.pi/36,4)})
  cur=tgt
 frames.append({'p':[24,-6,17],'k':'fly','room':'finale','name':'The complete residence','caption':'That is the Francis Residence. Explore any room yourself, change materials, or set the lighting mood.','target':[5,13,3]})
 return frames

GRIDS={f:grid(z) for f,z in FLOORS.items()};DIST={f:clearance(g) for f,g in GRIDS.items()}
frames=build()
json.dump({'frames':frames,'note':'Blender coordinates (x,y,z) at eye height; generated by scripts/tour_builder.py'},open(os.path.join(root,'public','tour.json'),'w'),indent=0)
print('TOUR BUILT',len(frames),'frames',sum(1 for f in frames if f['k']=='spin'),'rooms',[sum(sum(r) for r in g) for g in GRIDS.values()],'free cells')
