"""Close the 0.31 m void on the first floor between the slab edge (y 13.39) and the foot of the upper stair flight
(Run 1783378 starts at y 13.08), x 4.94-6.04, with a 150 mm slab infill in the landing floor finish."""
import bpy,os,sys
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from refine_interior_realism import export_and_save
from exterior_stucco import world_uv
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
 assert not any(o.get('stairGapFill') for o in bpy.data.objects),'Already applied'
 x0,x1,y0,y1,z0,z1=4.938,6.042,13.075,13.402,3.0,3.15
 v=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
 me=bpy.data.meshes.new('Stair landing infill');me.from_pydata(v,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.update()
 o=bpy.data.objects.new('Level 1 | stair landing infill',me);bpy.context.collection.objects.link(o);me.materials.append(bpy.data.materials['floor'])
 o['category']='floor';o['finishGroup']='floor';o['floor']=1;o['stairGapFill']=True;world_uv(o)
 export_and_save();print('STAIR GAP FILLED')
