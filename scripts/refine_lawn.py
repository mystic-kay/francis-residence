"""Export the original planted regions without reshaping them; preserve packed finishes."""
import bpy,os
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
# Preserve the original planted-region and kerb geometry without alteration.
# Export lean materials; the web app applies the shared external maps.
links=[]
for material in bpy.data.materials:
 if not material.use_nodes:continue
 bs=material.node_tree.nodes.get('Principled BSDF')
 if not bs:continue
 for key in ['Base Color','Roughness','Normal']:
  for link in list(bs.inputs[key].links):links.append((material.node_tree,link.from_socket,link.to_socket));material.node_tree.links.remove(link)
bpy.ops.export_scene.gltf(filepath=os.path.join(root,'public','models','francis.glb'),export_format='GLB',export_extras=True,export_yup=True)
for tree,a,b in links:tree.links.new(a,b)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
print('SOURCE GARDEN EXPORTED AND PACKED FINISHES RETAINED')
