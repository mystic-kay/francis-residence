"""The user-marked landscaped area; front-house strips remain paved walkways."""
# Stop inside the original kerb faces; keep the tank/pergola path clear.
LANDSCAPED_FOOTPRINT=[(-2.86,-2.62),(10.55,-2.62),(10.55,5.764),(6.582,5.764),(6.582,4.899),(1.039,4.899),(1.039,1.26),(-2.86,1.26)]
FRONT_WALKWAY_REGIONS=(2331126,2331133)
def create_marked_lawn():
 import bpy
 vertices=[(x,y,-.588) for x,y in LANDSCAPED_FOOTPRINT]
 mesh=bpy.data.meshes.new('User-marked landscaped section');mesh.from_pydata(vertices,[],[tuple(range(len(vertices)))]);mesh.update()
 o=bpy.data.objects.new('Garden | user-marked landscaped section',mesh);bpy.context.collection.objects.link(o);o['finishGroup']='lawn';o['category']='lawn';o['floor']=0
 uv=mesh.uv_layers.new(name='UVMap')
 for f in mesh.polygons:
  for idx in f.loop_indices:
   v=mesh.vertices[mesh.loops[idx].vertex_index].co;uv.data[idx].uv=(v.x,v.y)
 return o
