"""Replace the clear glass main-entrance panel (System Panel Glazed 1781488, x 6.09-6.11, y 8.04-8.91, z 0.06-2.10)
with an executive door: 60 mm smoked-walnut leaf, vertical flutes outside (porch side, -x), a full-height brass inlay,
a 1.6 m brass pull outside and a short pull inside. The narrow sidelight stays glazed. Safe to rerun."""
import bpy,os,sys,json
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import created,remove_faces
from refine_interior_realism import export_and_save,pack_surface
from modern_dining_set import block,tube,box_uv
blend=os.path.join(root,'Francis-Web.blend')
Y0,Y1,Z0,Z1,XC=8.036,8.906,.06,2.10,6.10
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 for o in [o for o in bpy.data.objects if o.get('entryDoor')]:bpy.data.objects.remove(o,do_unlink=True)
 removed=sum(remove_faces(o,[((6.085,Y0-.001,Z0-.001),(6.115,Y1+.001,Z1+.001))]) for o in bpy.data.objects if o.type=='MESH' and o.get('category')=='glass' and o.get('floor')==0)
 cfg=json.load(open(os.path.join(root,'scripts','reference-materials.json')))
 for cat in ['entrydoor','frontdoorhardware']:pack_surface(cat,cfg)
 created.clear();out=XC-.03;inn=XC+.03;H=Z1-Z0;zc=(Z0+Z1)/2
 block('Entry door | walnut leaf',(XC,(Y0+Y1)/2,zc),(.06,Y1-Y0-.008,H-.006),'entrydoor',.003)
 # Flutes across the outer face, leaving a plain stile on the handle side for the inlay and pull.
 fy0,fy1=Y0+.03,Y1-.19;n=14;w=(fy1-fy0)/n
 for k in range(n):block('Entry door | flute',(out-.007,fy0+w*(k+.5),zc),(.014,w-.012,H-.12),'entrydoor',.005)
 block('Entry door | brass inlay',(out-.0015,Y1-.165,zc),(.003,.006,H-.03),'frontdoorhardware',.0005)
 for y in (Y0+.004,Y1-.004):block('Entry door | edge trim',(XC,y,zc),(.062,.004,H-.006),'frontdoorhardware',.0005)
 hy=Y1-.095
 tube('Entry door | pull bar',[(out-.06,hy,Z0+.28),(out-.06,hy,Z0+1.88)],.016,'frontdoorhardware')
 for z in (Z0+.45,Z0+1.71):tube('Entry door | pull stand-off',[(out-.06,hy,z),(out,hy,z)],.009,'frontdoorhardware')
 tube('Entry door | inside pull',[(inn+.055,hy,Z0+.78),(inn+.055,hy,Z0+1.28)],.012,'frontdoorhardware')
 for z in (Z0+.84,Z0+1.22):tube('Entry door | inside stand-off',[(inn,hy,z),(inn+.055,hy,z)],.007,'frontdoorhardware')
 block('Entry door | lock plate',(out-.002,hy+.045,Z0+1.0),(.004,.03,.12),'frontdoorhardware',.001)
 bpy.context.view_layer.update();box_uv(created);groups={}
 for o in created:groups.setdefault(o['category'],[]).append(o)
 for cat,objs in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in objs:o.select_set(True)
  bpy.context.view_layer.objects.active=objs[0];bpy.ops.object.join();o=bpy.context.object
  o.name='Entry door | '+('walnut leaf' if cat=='entrydoor' else 'brass hardware');o['category']=cat;o['finishGroup']=cat;o['floor']=0;o['entryDoor']=True;o['doorLeaf']=True
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 export_and_save();print('ENTRY DOOR SAVED glass faces removed',removed)
