"""Remove the white canopy slab over the main entrance (Generic Model Box at x 4.94-6.14, y 7.88-9.28, z 2.65-2.80)."""
import bpy,os,sys
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import remove_faces
from refine_interior_realism import export_and_save
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
 n={o.name:c for o in bpy.data.objects if o.type=='MESH' and o.get('category') in ('details','lighting','interiorlight','decor') for c in [remove_faces(o,[((4.93,7.87,2.64),(6.145,9.285,2.81))])] if c}
 export_and_save();print('CANOPY REMOVED',n)
