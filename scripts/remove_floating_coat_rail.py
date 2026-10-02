"""Remove the coat-hook rail (Casework Boxes 2322919-2322923) that floats across the open passage from the
entrance vestibule to the corridor, with no wall behind it."""
import bpy,os,sys
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import remove_faces
from refine_interior_realism import export_and_save
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
 n=sum(remove_faces(o,[((2.49,13.28,1.54),(3.39,13.39,1.71))]) for o in bpy.data.objects if o.type=='MESH' and o.get('floor')==0 and o.get('category') in ('wood','details','cabinet','hardware'))
 export_and_save();print('COAT RAIL REMOVED',n)

def move_consumer_unit():
 """KE Consumer Unit MDB ELB-1 [2295077] is mounted across the hall-to-vestibule doorway; slide it 2.88 m along
 the same wall onto solid masonry (y 9.60-10.05)."""
 import bmesh
 from mathutils import Vector
 n=0
 for o in [o for o in bpy.data.objects if o.type=='MESH' and o.get('floor')==0]:
  bm=bmesh.new();bm.from_mesh(o.data);mw=o.matrix_world;inv=mw.inverted();vs=set()
  for f in bm.faces:
   if all(2.12<=(mw@v.co).x<=2.245 and 12.47<=(mw@v.co).y<=12.94 and 1.19<=(mw@v.co).z<=1.81 for v in f.verts):vs|=set(f.verts);n+=1
  for v in vs:v.co=inv@(mw@v.co+Vector((0,-2.88,0)))
  if vs:bm.to_mesh(o.data)
  bm.free()
 return n
