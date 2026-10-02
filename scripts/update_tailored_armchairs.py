"""Replace only the two sitting-room chairs with the final tailored chair meshes."""
import bpy,os,sys,json
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
import luxury_interiors as luxe
from tailored_armchairs import add_armchairs
from refine_interior_realism import export_and_save
bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
boxes=[((x-.63,8.20,0),(x+.63,9.52,1.0)) for x in [7.78,9.31]]
for o in list(bpy.data.objects):
 if o.get('chairPart') or o.get('chairSewing'):bpy.data.objects.remove(o,do_unlink=True)
 elif o.type=='MESH' and o.name.startswith('Refined |') and o.get('category') in ['livingfabric','decor']:luxe.remove_faces(o,boxes)
for node in bpy.data.materials['livingfabric'].node_tree.nodes:
 if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=.18
luxe.created.clear();chairs=add_armchairs();report=json.load(open(os.path.join(root,'public','interior-refinement.json')));report['armchairs']=chairs
with open(os.path.join(root,'public','interior-refinement.json'),'w') as f:json.dump(report,f,indent=2)
export_and_save();print('ROUNDED AND TAILORED ARMCHAIRS SAVED')
