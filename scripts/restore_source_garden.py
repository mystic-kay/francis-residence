"""Keep the original grass regions and kerbs; remove the added lawn footprint."""
import bpy,bmesh,os,json
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(root,'FrancisProject-3DView-{3D}.fbx'))
source={}
for o in bpy.data.objects:
 if o.type!='MESH':continue
 if 'kerb' in o.name.lower() or any('['+str(i)+']' in o.name for i in [2331112,2331126,2331133]):
  verts=[list(o.matrix_world@v.co) for v in o.data.vertices];faces=[list(p.vertices) for p in o.data.polygons]
  source[o.name]={'vertices':verts,'faces':faces,'category':'kerb' if 'kerb' in o.name.lower() else 'lawn'}
assert len(source)==5
bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
# Remove all generated grass, including the extended main polygon.
for o in list(bpy.data.objects):
 if o.type=='MESH' and o.get('category')=='lawn':bpy.data.objects.remove(o,do_unlink=True)
# The original kerbs were joined into details. Extract their faces using the exact source vertices.
kerb_points={tuple(round(c,4) for c in p) for part in source.values() if part['category']=='kerb' for p in part['vertices']}
removed=0
for o in list(bpy.data.objects):
 if o.type!='MESH' or o.get('category')!='details':continue
 bm=bmesh.new();bm.from_mesh(o.data)
 faces=[f for f in bm.faces if all(tuple(round(c,4) for c in o.matrix_world@v.co) in kerb_points for v in f.verts)]
 if faces:removed+=len(faces);bmesh.ops.delete(bm,geom=faces,context='FACES');bm.to_mesh(o.data);o.data.update()
 bm.free()
assert removed>0,'Original kerb extraction failed'
material=bpy.data.materials.new('Original kerb | grey concrete');material.use_nodes=True
bs=material.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.12,.13,.14,1);bs.inputs['Roughness'].default_value=.95
for name,part in source.items():
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(part['vertices'],[],part['faces']);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);category=part['category'];o['category']=category;o['floor']=0;o['sourceName']=name
 o.data.materials.append(material if category=='kerb' else bpy.data.materials['lawn'])
 if category=='lawn':o.location.z=.02
 uv=mesh.uv_layers.new(name='UVMap')
 for f in mesh.polygons:
  for idx in f.loop_indices:
   p=mesh.vertices[mesh.loops[idx].vertex_index].co;uv.data[idx].uv=(p.x,p.y)
# Export building/site meshes only, keeping the editable file's planting and packed maps.
links=[]
for material in bpy.data.materials:
 if not material.use_nodes:continue
 bs=material.node_tree.nodes.get('Principled BSDF')
 if not bs:continue
 for key in ['Base Color','Roughness','Normal']:
  for link in list(bs.inputs[key].links):links.append((material.node_tree,link.from_socket,link.to_socket));material.node_tree.links.remove(link)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o.type=='MESH' and o.get('category'):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=os.path.join(root,'public','models','francis.glb'),export_format='GLB',export_extras=True,export_yup=True,use_selection=True)
for tree,a,b in links:tree.links.new(a,b)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
with open(os.path.join(root,'public','garden-validation.json'),'w') as f:json.dump({'lawnStatus':'Only original planted Subregion geometry; no custom lawn footprint','kerbStatus':'Exact original FBX vertex positions and faces','sourceRegions':list(source),'restoredKerbFaces':removed},f,indent=2)
print('ORIGINAL GARDEN REGIONS AND KERBS RESTORED',list(source))
