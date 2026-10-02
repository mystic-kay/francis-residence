"""Add the web planting assets to the editable Blender scene without enlarging the building GLB."""
import bpy,os,math
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
for asset,positions,height in [('tree_small_02',[(-5,5,1),(19,5,.9),(-5,22,1.1),(19,22,1)],6.5),('shrub_01',[(1,5.8,.9),(3,5.9,.7),(7,6,1),(9,6,.8),(-1.7,8,.8)],.9)]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=os.path.join(root,'public','models',asset+'.glb'));objects=[o for o in bpy.data.objects if o not in before and o.type=='MESH'];bpy.context.view_layer.update()
 pts=[o.matrix_world@Vector(p) for o in objects for p in o.bound_box];lo=Vector([min(p[i] for p in pts) for i in range(3)]);hi=Vector([max(p[i] for p in pts) for i in range(3)]);scale=height/(hi.z-lo.z);center=(lo+hi)/2
 for x,y,variation in positions:
  for original in objects:
   mesh=original.data.copy();o=bpy.data.objects.new(asset,mesh);bpy.context.collection.objects.link(o)
   for v in mesh.vertices:
    p=original.matrix_world@v.co;p-=Vector((center.x,center.y,lo.z));p*=scale*variation;v.co=p
   o.location=(x,y,-.59);o.rotation_euler.z=x*.41
 for o in objects:bpy.data.objects.remove(o,do_unlink=True)
for image in bpy.data.images:
 if image.size[0]>0 and not image.packed_file:
  try:image.pack()
  except RuntimeError:pass
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
print('ASSEMBLED editable residence with landscape')
