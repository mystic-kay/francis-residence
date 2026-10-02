"""Replace the timber front door (M_Door-Exterior-Single-Two_Lite 900x2500 [1781521]) with a contemporary
black pivot-style entrance door: matte black flush steel leaf with fine horizontal reveals, slim black frame,
and a full-height brushed-brass pull bar."""
import bpy,os,sys,json,math
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import created,remove_faces,material
from refine_interior_realism import export_and_save,pack_surface
from modern_dining_set import block,box_uv,tube
blend=os.path.join(root,'Francis-Web.blend')
# Opening from the source door: x -0.333..0.667, wall y 9.201..9.409 (exterior faces -y), height 2.6 m.
X0,X1,Y0,Y1,H=-.333,.667,9.201,9.409,2.60

def build():
 src=bpy.data.objects.get('M_Door-Exterior-Single-Two_Lite Glazed Door 900x2500 [1781521]')
 assert src or any(o.get('frontDoor') for o in bpy.data.objects),'Source front door not found'
 removed=0
 if src:removed=len(src.data.polygons);bpy.data.objects.remove(src,do_unlink=True)
 # Any glazing or fittings the source door left in merged meshes, entirely within the opening.
 for o in list(bpy.data.objects):
  if o.type=='MESH' and o.get('floor') in (0,None) and o.get('category') in ('glass','metal','details','hardware') and not o.get('frontDoor'):
   removed+=remove_faces(o,[((X0-.005,Y0-.01,-.01),(X1+.005,Y1+.01,H+.01))])
 for o in [o for o in bpy.data.objects if o.get('frontDoor')]:bpy.data.objects.remove(o,do_unlink=True)
 created.clear();f=.06;mid=(Y0+Y1)/2
 # Slim frame lining the whole reveal, so the opening reads as one black element in the stucco.
 block('Front door | frame jamb',(X0+f/2,mid,H/2),(f,Y1-Y0,H),'frontdoorframe',.003)
 block('Front door | frame jamb',(X1-f/2,mid,H/2),(f,Y1-Y0,H),'frontdoorframe',.003)
 block('Front door | frame head',((X0+X1)/2,mid,H-f/2),(X1-X0,Y1-Y0,f),'frontdoorframe',.003)
 # Flush leaf, 62 mm, set towards the outside face of the wall.
 lx0,lx1,lz0,lz1=X0+f+.004,X1-f-.004,.012,H-f-.004;ly0,ly1=Y0+.035,Y0+.097
 leaf=block('Front door | flush leaf',((lx0+lx1)/2,(ly0+ly1)/2,(lz0+lz1)/2),(lx1-lx0,ly1-ly0,lz1-lz0),'frontdoor',.004)
 # Fine horizontal reveals on both faces: near-black gloss strips that catch the light.
 reveal=material('Decor | door reveal','#0c0d0e',.22)
 for i in range(5):
  z=lz0+(lz1-lz0)*(i+1)/6
  for y in (ly0-.0015,ly1+.0015):block('Front door | reveal line',((lx0+lx1)/2,y,z),(lx1-lx0-.12,.003,.008),'frontdoor',.0005)['mat']=1
 for o in created:
  if o.get('mat'):o.data.materials.clear();o.data.materials.append(reveal);o['category']='decor'
 # Full-height brushed-brass pull bar on stand-offs outside, shorter pull inside, and a slim lock escutcheon.
 hx=lx1-.11
 tube('Front door | pull bar',[(hx,ly0-.065,.42),(hx,ly0-.065,1.86)],.0165,'frontdoorhardware')
 for z in (.55,1.73):tube('Front door | pull stand-off',[(hx,ly0-.065,z),(hx,ly0-.001,z)],.009,'frontdoorhardware')
 tube('Front door | inside pull',[(hx,ly1+.06,.80),(hx,ly1+.06,1.30)],.012,'frontdoorhardware')
 for z in (.86,1.24):tube('Front door | inside stand-off',[(hx,ly1+.001,z),(hx,ly1+.06,z)],.007,'frontdoorhardware')
 block('Front door | lock escutcheon',(hx-.002,ly0-.003,1.02),(.026,.006,.12),'frontdoorhardware',.002)
 bpy.context.view_layer.update();box_uv(created)
 groups={}
 for o in created:groups.setdefault(o['category'],[]).append(o)
 names={'frontdoor':'Front door | leaf','frontdoorframe':'Front door | frame','frontdoorhardware':'Front door | pull and lock','decor':'Front door | reveal lines'}
 for cat,objects in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in objects:o.select_set(True)
  bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object
  o.name=names[cat];o['category']=cat;o['finishGroup']=cat;o['floor']=0;o['frontDoor']=True
  # The leaf, its reveals and pulls clear with "Clear doorways"; the frame stays.
  o['doorLeaf']=cat!='frontdoorframe'
 return {'removedSourceFaces':removed,'leaf':'62 mm flush steel, matte black, five horizontal reveals each face','handle':'1.44 m brushed-brass pull bar outside, 0.5 m pull inside, lock escutcheon','frame':'60 mm satin black lining the reveal'}

if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 cfg=json.load(open(os.path.join(root,'scripts','reference-materials.json')))
 for cat in ['frontdoor','frontdoorframe','frontdoorhardware']:pack_surface(cat,cfg)
 report=build()
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 path=os.path.join(root,'public','interior-refinement.json');data=json.load(open(path));data['frontDoor']=report
 with open(path,'w') as f:json.dump(data,f,indent=2)
 export_and_save();print('FRONT DOOR SAVED',report)
