import bpy,json,os
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(root,'FrancisProject-3DView-{3D}.fbx'))
objects=[]
for o in bpy.data.objects:
 if o.type=='MESH':
  pts=[o.matrix_world@Vector(v) for v in o.bound_box]
  objects.append(dict(name=o.name,vertices=len(o.data.vertices),materials=[m.name for m in o.data.materials if m],min=[min(v[i] for v in pts) for i in range(3)],max=[max(v[i] for v in pts) for i in range(3)]))
with open(os.path.join(root,'scene-inspection.json'),'w') as f: json.dump(dict(objects=objects,materials=[m.name for m in bpy.data.materials]),f,indent=2)
print('INSPECTED',len(objects))
