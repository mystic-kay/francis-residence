"""Front entrance steps and porch finishes, plus two floating service items removed from the east wall.
- The grey step boxes (Generic Model Boxes 2329355-57 and 2329359-60) are replaced by three-riser stone flights at
  both entrances: 150 mm risers, 320 mm treads with a 30 mm nosing over a recessed riser and a warm LED strip under
  each nosing (Garden & facade lighting zone). Finish group 'steps'.
- The porch deck surfaces become their own finish group 'porch'.
- A floor gully and two pipe sleeves floating 0.1-0.6 m above the paving on the east wall are removed."""
import bpy,os,sys,json
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import created,remove_faces,material
from refine_interior_realism import export_and_save,pack_surface
from modern_dining_set import block,box_uv
from fixtures_and_lamps import take
blend=os.path.join(root,'Francis-Web.blend')
G=-.6
def flight(x0,x1,y_house):
 for i,top in enumerate((-.15,-.30,-.45)):
  yb=y_house-.32*i;ya=yb-.32
  block('Steps | riser block',((x0+x1)/2,(ya+.02+yb+.01)/2,(G+top-.04)/2),(x1-x0,yb+.01-ya-.02,top-.04-G),'steps',.002)
  block('Steps | tread',((x0+x1)/2,(ya-.01+yb+.012)/2,top-.02),(x1-x0+.04,yb+.012-ya+.01,.04),'steps',.006)
  led=block('Steps | nosing light',((x0+x1)/2,ya+.006,top-.045),(x1-x0-.06,.016,.008),'steps',.001)
  led.data.materials.clear();led.data.materials.append(bpy.data.materials['Decor | warm LED']);led['category']='interiorlight'
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 for o in [o for o in bpy.data.objects if o.get('frontSteps')]:bpy.data.objects.remove(o,do_unlink=True)
 cfg=json.load(open(os.path.join(root,'scripts','reference-materials.json')))
 for cat in ['steps','porch']:pack_surface(cat,cfg)
 material('Decor | warm LED','#fff0d5',.22,emission=3)
 old=[((3.82,6.88,-.6),(6.04,7.78,-.15)),((-.82,7.68,-.6),(1.18,8.28,-.3)),
      ((10.30,12.37,-.49),(10.69,12.44,-.42)),((10.96,13.10,-.27),(11.20,13.29,.0))]
 removed=sum(remove_faces(o,old) for o in bpy.data.objects if o.type=='MESH' and o.get('category') in ('details','metal','ceramic','lighting'))
 porch=0
 if not any(o.get('category')=='porch' for o in bpy.data.objects):
  decks=[((-1.27,8.57,-.16),(3.58,9.19,.005)),((3.56,7.77,-.16),(6.05,9.19,.005)),((4.63,7.87,-.18),(6.15,9.29,-.01))]
  made=take([o for o in bpy.data.objects if o.type=='MESH' and o.get('category') in ('floor','details') and o.get('floor') in (0,-1)],
   lambda ob,f,p:any(all(all(a[i]-.004<=q[i]<=b[i]+.004 for i in range(3)) for q in p) for a,b in decks),bpy.data.materials['porch'],'porch','Level 0 | porch deck')
  porch=sum(len(o.data.polygons) for o in made)
 # The side entrance sits behind a 0.7 m podium at -0.2 m (ground slab edge, y 7.88-8.58): a stone landing level
 # with the deck covers it in front of the door, and the flight starts at the podium edge.
 created.clear();block('Steps | landing',(.17,8.23,-.1),(2.44,.70,.2),'steps',.006);flight(-1.03,1.37,7.88);flight(3.86,6.02,7.78)
 bpy.context.view_layer.update();box_uv(created);groups={}
 for o in created:groups.setdefault(o['category'],[]).append(o)
 for cat,objs in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in objs:o.select_set(True)
  bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object
  o.name='Front steps | '+('stone flights' if cat=='steps' else 'nosing lights');o['category']=cat;o['finishGroup']=cat;o['floor']=0;o['frontSteps']=True
  if cat=='interiorlight':o['lightZone']='exterior';o['siteLighting']=True
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 export_and_save();print('FRONT STEPS SAVED removed',removed,'porch faces',porch)
