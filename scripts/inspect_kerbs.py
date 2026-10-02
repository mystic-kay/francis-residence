import bpy,json,os
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(root,'FrancisProject-3DView-{3D}.fbx'))
result={}
for o in bpy.data.objects:
 if 'kerb' in o.name.lower():
  verts=[list(o.matrix_world@v.co) for v in o.data.vertices];result[o.name]=verts
with open(os.path.join(root,'kerb-vertices.json'),'w') as f:json.dump(result,f)
