"""Close the 120 mm slot in the east elevation (y 13.68-13.80, recessed to x 10.40 behind the 10.89 face, from 2.7 m
to the coping), which exposed the bedroom wall and floor edge, with a flush block of white exterior stucco."""
import bpy,os,sys,json
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from refine_interior_realism import export_and_save
from exterior_stucco import world_uv
blend=os.path.join(root,'Francis-Web.blend')
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 assert not any(o.get('eastSlotInfill') for o in bpy.data.objects),'Already applied'
 x0,x1,y0,y1,z0,z1=10.39,10.888,13.672,13.802,2.65,7.05
 v=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
 mesh=bpy.data.meshes.new('East slot infill');mesh.from_pydata(v,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.update()
 o=bpy.data.objects.new('Level 1 | east slot stucco infill',mesh);bpy.context.collection.objects.link(o);mesh.materials.append(bpy.data.materials['render'])
 o['category']='render';o['finishGroup']='render';o['floor']=1;o['exteriorStucco']=True;o['eastSlotInfill']=True;world_uv(o)
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 export_and_save();print('EAST SLOT FILLED')
