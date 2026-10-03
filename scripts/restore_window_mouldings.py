"""Restore the two vertical mouldings framing the stacked windows of the charcoal bay (Generic Model Boxes 2328787 and
2328788), removed in error by remove_site_clutter.py as downpipe placeholders. They now run to the paving (-0.6 m)."""
import bpy,os,sys
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from refine_interior_realism import export_and_save
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
 for o in [o for o in bpy.data.objects if o.get('windowMoulding')]:bpy.data.objects.remove(o,do_unlink=True)
 for x0,x1 in ((6.5,6.69),(9.91,10.11)):
  y0,y1,z0,z1=7.65,7.85,-.6,5.9;v=[(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
  me=bpy.data.meshes.new('Window moulding');me.from_pydata(v,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.update();me.uv_layers.new(name='UVMap')
  o=bpy.data.objects.new('Level 0 | window moulding',me);bpy.context.collection.objects.link(o);me.materials.append(bpy.data.materials['details'])
  o['category']='details';o['finishGroup']='details';o['floor']=-1;o['windowMoulding']=True
 export_and_save();print('MOULDINGS RESTORED')
