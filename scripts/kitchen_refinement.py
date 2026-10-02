"""Kitchen and ground-floor dining: remove ceiling z-fighting, add flush soffits, rebuild skirtings, modern counter stools."""
import bpy,bmesh,os,sys,json,math
from mathutils import Vector,Matrix
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import created,remove_faces,material
from refine_interior_realism import export_and_save,pack_surface
from modern_dining_set import mesh_object,block,pad,box_uv,power
blend=os.path.join(root,'Francis-Web.blend')
CEILING=2.70
REGION=((2.43,14.97),(10.35,18.89))

def edit_faces(o,select,action):
 """Delete or lower the faces of a merged mesh that `select(points,normal)` picks."""
 bm=bmesh.new();bm.from_mesh(o.data);mw=o.matrix_world;nm=mw.to_3x3();faces=[]
 for f in bm.faces:
  pts=[mw@v.co for v in f.verts]
  if select(pts,(nm@f.normal).normalized()):faces.append(f)
 if faces and action=='delete':bmesh.ops.delete(bm,geom=faces,context='FACES')
 elif faces:
  inv=mw.inverted()
  for v in {v for f in faces for v in f.verts}:v.co=inv@(mw@v.co+Vector((0,0,action)))
 if faces:bm.to_mesh(o.data);o.data.update()
 bm.free();return len(faces)
def inside(pts,a,b,tol=.002):return all(all(a[i]-tol<=p[i]<=b[i]+tol for i in range(3)) for p in pts)
def in_region(pts):return all(REGION[0][0]<=p.x<=REGION[1][0] and REGION[0][1]<=p.y<=REGION[1][1] for p in pts)
def mesh(name):return bpy.data.objects[name]

def fix_ceiling():
 report={}
 # Generic Model Box planes duplicate the kitchen gypsum ceiling and the beam soffit at exactly 2.70 m.
 report['duplicateCeilingFaces']=edit_faces(mesh('Level 0 | details'),lambda p,n:inside(p,(2.43,14.97,2.69),(6.26,18.89,2.716)),'delete')
 # Hidden tops resting on the ceiling plane (hood chimney, island panel, fittings) fight the ceiling underside.
 flush=lambda p,n:in_region(p) and n.z>.99 and all(abs(q.z-CEILING)<.0015 for q in p)
 report['hiddenTopFaces']=sum(edit_faces(mesh(f'Level 0 | {c}'),flush,'delete') for c in ('wood','cabinet','lighting'))
 # Downlight trims sit in the ceiling plane; drop them 3 mm so they read in front of it.
 trims=lambda p,n:in_region(p) and n.z<-.99 and all(CEILING-.012<=q.z<=CEILING+.0015 for q in p)
 report['downlightFacesLowered']=edit_faces(mesh('Level 0 | lighting'),trims,-.003)
 return report

def soffit(name,x0,x1,y0,y1,bottom,sides):
 """Plasterboard bulkhead from cabinet top to ceiling. Only visible faces are built, so nothing is coplanar with walls or ceiling."""
 top=CEILING;v=[(x0,y0,bottom),(x1,y0,bottom),(x1,y1,bottom),(x0,y1,bottom),(x0,y0,top),(x1,y0,top),(x1,y1,top),(x0,y1,top)]
 faces=[(0,3,2,1)];quads={'-y':(0,1,5,4),'+x':(1,2,6,5),'+y':(2,3,7,6),'-x':(3,0,4,7)}
 faces+=[quads[s] for s in sides]
 o=mesh_object(name,v,faces,'ceiling',False);o['kitchenRefinement']=True;return o

def add_soffits():
 # Fronts align with the 18 mm door faces; bottoms clear the carcass tops by 3 mm.
 runs=[('west wall units',2.438,2.806,16.276,18.326,2.203,['+x','-y']),
       ('north-west corner units',2.438,3.488,18.326,18.676,2.203,['-y','+x']),
       ('north-east wall units',4.988,6.038,18.326,18.676,2.203,['-y','-x']),
       ('south wall units',3.700,6.038,15.076,15.394,2.203,['+y','-x']),
       ('dining-side wall units',6.238,7.337,15.076,15.394,2.203,['+y','+x']),
       ('peninsula overhead units',6.238,6.618,16.336,18.676,2.253,['+x','-y'])]
 for label,*box,sides in runs:soffit('Kitchen | soffit above '+label,*box,sides)
 return [r[0] for r in runs]

def remove_old_peninsula_bulkhead():
 # Casework Box 2323443 ran from 2.25 m through the ceiling into the slab at 3.0 m.
 box=((6.23,16.33,2.245),(6.63,18.69,3.01))
 return sum(edit_faces(mesh(f'Level 0 | {c}'),lambda p,n:inside(p,*box),'delete') for c in ('cabinet','wood','details'))

# Source skirting runs (Casework Box 2323215-2323220, 2323431): along-run extent and the wall plane behind each.
SKIRTS=[((6.238,8.138),18.676,'y',-1),((9.638,10.338),18.676,'y',-1),((15.076,15.736),10.338,'x',-1),((17.736,18.676),10.338,'x',-1),
        ((9.937,10.338),15.076,'y',1),((15.076,15.436),7.557,'x',-1),((16.336,18.656),6.931,'x',1)]
SKIRT_H,SKIRT_T=.10,.016
def rebuild_skirtings():
 masks=[]
 for (a,b),wall,axis,face in SKIRTS:
  w0,w1=min(wall,wall+face*.021),max(wall,wall+face*.021)
  masks.append(((a,w0,-.01),(b,w1,.095)) if axis=='y' else ((w0,a,-.01),(w1,b,.095)))
 removed=0
 for o in list(bpy.data.objects):
  if o.type=='MESH' and o.get('floor')==0 and o.get('category') in ('details','wood','cabinet') and not o.get('kitchenRefinement'):removed+=remove_faces(o,masks)
 for (a,b),wall,axis,face in SKIRTS:
  back=wall+face*.001;front=back+face*SKIRT_T;chamfer=front-face*.004
  # Profile across the board: back-bottom, front-bottom, front up to a small top chamfer, back-top.
  prof=[(back,0),(front,0),(front,SKIRT_H-.004),(chamfer,SKIRT_H),(back,SKIRT_H)]
  verts=[];n=len(prof)
  for s in (a,b):
   for d,z in prof:verts.append((s,d,z) if axis=='y' else (d,s,z))
  faces=[(i,i+1,n+i+1,n+i) for i in range(n-1)]+[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]
  # The open back (last profile edge) is left out so no face lies on the wall plane.
  o=mesh_object('Kitchen | painted skirting',verts,faces,'skirting',False);o['kitchenRefinement']=True
  if (axis=='y')==(face>0):o.data.flip_normals()
 return removed

def add_stool(cx,cy,yaw):
 rot=Matrix.Rotation(yaw,3,'Z');origin=Vector((cx,cy,0))
 def place(p,lift=0):return tuple(origin+rot@Vector((p[0],p[1],p[2]+lift)))
 pad('Counter stool | upholstered seat',lambda p:place(p,.625),(.46,.44,.07),'diningfabric',.25)
 pad('Counter stool | seat cushion',lambda p:place((p[0],p[1]+.01,p[2]),.67),(.42,.40,.06),'diningfabric',.32,.006)
 # Low wrapped back in the same bouclé, cradling the sitter at the counter.
 path,cross=96,20;verts=[];faces=[]
 def profile(t,a):
  rear=max(0,-math.sin(t));top=.86+.03*rear;bottom=.69
  cap=max(0,(math.radians(212)-t)/math.radians(14),(t-math.radians(328))/math.radians(14));env=math.sqrt(max(.00001,1-min(1,cap)**2))
  r=.035*power(math.cos(a),.5)*env;mid=(top+bottom)/2;half=(top-bottom)/2
  return (math.cos(t)*(.20+r),-.01+math.sin(t)*(.19+r),mid+half*power(math.sin(a),.4)*env)
 for i in range(path+1):
  t=math.radians(198+144*i/path)
  for j in range(cross):verts.append(place(profile(t,2*math.pi*j/cross)))
 for i in range(path):
  for j in range(cross):
   k=i*cross+j;k2=i*cross+(j+1)%cross;faces.append((k,k+cross,k2+cross,k2))
 faces+=[tuple(range(cross-1,-1,-1)),tuple(range(path*cross,(path+1)*cross))]
 mesh_object('Counter stool | wrapped back',verts,faces,'diningfabric')
 # Square walnut legs; the rear pair rise to carry the back. A brass foot bar sits at the front.
 for sx in (-1,1):
  for sy,h in ((.17,.60),(-.17,.80)):
   leg=block('Counter stool | walnut leg',(0,0,0),(.036,.036,h),'diningwood',.003);leg.location=place((sx*.17,sy,h/2));leg.rotation_euler.z=yaw
 for sy in (-.17,):
  rail=block('Counter stool | walnut stretcher',(0,0,0),(.34,.024,.024),'diningwood',.002);rail.location=place((0,sy,.26));rail.rotation_euler.z=yaw
 for sx in (-1,1):
  rail=block('Counter stool | walnut stretcher',(0,0,0),(.024,.34,.024),'diningwood',.002);rail.location=place((sx*.17,0,.26));rail.rotation_euler.z=yaw
 bar=block('Counter stool | brass foot bar',(0,0,0),(.36,.028,.028),'interiormetal',.006);bar.location=place((0,.19,.25));bar.rotation_euler.z=yaw

def replace_stools():
 removed=0
 for o in list(bpy.data.objects):
  if o.type=='MESH' and o.get('floor')==0 and o.get('category') not in ('walls','floor','ceiling') and not o.get('kitchenRefinement') and not o.get('diningSet'):
   removed+=remove_faces(o,[((7.32,16.56,-.01),(7.74,18.63,.68))])
 # Source stool centres, facing the peninsula worktop to the west.
 for y in (16.768,17.615,18.419):add_stool(7.53,y,math.pi/2)
 return removed

def refine_kitchen():
 previous=[o for o in bpy.data.objects if o.get('kitchenRefinement')]
 for o in previous:bpy.data.objects.remove(o,do_unlink=True)
 cfg=json.load(open(os.path.join(root,'scripts','reference-materials.json')))
 for cat in ['ceiling','skirting','diningfabric','diningwood']:pack_surface(cat,cfg)
 report={'ceiling':fix_ceiling(),'oldBulkheadFaces':remove_old_peninsula_bulkhead()}
 assert previous or report['ceiling']['duplicateCeilingFaces']>0,report
 created.clear()
 report['soffits']=add_soffits();report['skirtingSourceFaces']=rebuild_skirtings();report['stoolSourceFaces']=replace_stools()
 assert previous or report['stoolSourceFaces']>0,report
 bpy.context.view_layer.update();box_uv(created)
 groups={}
 for o in created:groups.setdefault(o['category'],[]).append(o)
 names={'ceiling':'Kitchen | ceiling soffits','skirting':'Kitchen | painted skirtings','diningfabric':'Kitchen | counter stool upholstery','diningwood':'Kitchen | walnut counter stool frames','interiormetal':'Kitchen | brass stool foot bars'}
 for cat,objects in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in objects:o.select_set(True)
  bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object
  o.name=names[cat];o['category']=cat;o['finishGroup']=cat;o['floor']=0;o['kitchenRefinement']=True
 report['stools']='Three counter stools: bouclé seat and wrapped back, square walnut legs and stretchers, brass foot bar'
 report['skirting']=f'{SKIRT_H*1000:.0f} mm painted boards with a chamfered top, aligned to the 100 mm kitchen plinths and held 1 mm off the wall'
 return report

if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 report=refine_kitchen()
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 path=os.path.join(root,'public','interior-refinement.json');data=json.load(open(path));data['kitchen']=report
 with open(path,'w') as f:json.dump(data,f,indent=2)
 export_and_save();print('KITCHEN REFINEMENT SAVED',report)
