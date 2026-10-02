"""Correct artwork mounting and build supported, tailored upholstery plus oak flooring."""
import bpy,os,sys,json,math,collections
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
import luxury_interiors as luxe
from luxury_interiors import material,box,cylinder,line,sphere,finish,remove_faces

def signed(v,p):return math.copysign(abs(v)**p,v)
def tailored(name,loc,size,category,exponent=.48,rotation=0,wrinkles=.003):
 """Dense inflated cloth shell with gathered edges and a shallow seat depression."""
 nx,nz=64,32;verts=[];faces=[]
 for j in range(nz+1):
  phi=-math.pi/2+math.pi*j/nz
  for i in range(nx):
   theta=2*math.pi*i/nx
   x=signed(math.cos(phi)*math.cos(theta),exponent)*size[0]/2;y=signed(math.cos(phi)*math.sin(theta),exponent)*size[1]/2;z=signed(math.sin(phi),exponent)*size[2]/2
   edge=max(abs(x)/(size[0]/2),abs(y)/(size[1]/2));ripple=wrinkles*math.sin(theta*17+phi*9)*math.exp(-((edge-.84)/.14)**2)
   z+=ripple
   if size[0]<.3 and size[2]>.3:x+=wrinkles*math.sin(phi*16+theta*3)*math.exp(-((abs(y)/(size[1]/2)-.86)/.15)**2)
   if z>0 and size[2]<.3:z-=.009*math.exp(-((x/(size[0]*.3))**2+(y/(size[1]*.3))**2))
   verts.append((x,y,z))
 for j in range(nz):
  for i in range(nx):
   k=j*nx+i;k2=j*nx+(i+1)%nx;faces.append((k,k2,k2+nx,k+nx))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.location=loc;o.rotation_euler.y=rotation;finish(o,category)
 uv=mesh.uv_layers.new(name='UVMap')
 for face in mesh.polygons:
  face.use_smooth=True
  for idx in face.loop_indices:
   p=mesh.vertices[mesh.loops[idx].vertex_index].co;uv.data[idx].uv=(p.x,p.y if size[2]<.3 else p.z)
 return o

def pack_surface(category,cfg):
 f=cfg[category];m=material(category,f['color'],f['roughness'],f.get('metalness',0),f.get('clearcoat',0));nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes.get('Principled BSDF')
 for key in ['Base Color','Normal','Roughness']:
  for link in list(bs.inputs[key].links):links.remove(link)
 texture=f.get('texture')
 if texture and texture!='woven':
  uv=nodes.new('ShaderNodeTexCoord');mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='SCALE';mapping.inputs[3].default_value=f.get('scale',1);links.new(uv.outputs['UV'],mapping.inputs[0])
  for kind in ['color','normal','roughness']:
   path=os.path.join(root,'public','textures',texture,kind+'.jpg');image=bpy.data.images.load(path,check_existing=True);image.colorspace_settings.name='sRGB' if kind=='color' else 'Non-Color';image.pack();node=nodes.new('ShaderNodeTexImage');node.image=image;links.new(mapping.outputs[0],node.inputs['Vector'])
   if kind=='color':
    mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=bs.inputs['Base Color'].default_value;links.new(node.outputs['Color'],mix.inputs[1]);links.new(mix.outputs[0],bs.inputs['Base Color'])
   elif kind=='normal':
    norm=nodes.new('ShaderNodeNormalMap');norm.inputs['Strength'].default_value=.18 if category in ['livingfabric','livingpillows'] else .35;links.new(node.outputs['Color'],norm.inputs['Color']);links.new(norm.outputs['Normal'],bs.inputs['Normal'])
   else:
    mult=nodes.new('ShaderNodeMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=f['roughness'];links.new(node.outputs['Color'],mult.inputs[1]);mult.inputs[0].default_value=f['roughness'];links.new(mult.outputs[0],bs.inputs['Roughness'])
 bs.inputs['Sheen Weight'].default_value=.18 if category in ['livingfabric','livingpillows'] else 0
 return m

def add_throw_pillows():
 # Filled rectangular throw pillows with sewn edges and small edge creases, resting on the seats.
 pillow_report=[]
 for i,y in enumerate([10.29,10.84,12.23]):
  loc=Vector((9.60,y,.748));angle=.16 if i!=1 else .23;size=(.20,.46,.46);pillow=tailored('Refined | filled throw pillow',loc,size,'livingpillows',.62,angle,.004);pillow['throwPillow']=True
  rot=Matrix.Rotation(angle,3,'Y');points=[]
  for k in range(121):
   t=2*math.pi*k/120;points.append(tuple(loc+rot@Vector((0,signed(math.cos(t),.62)*.23,signed(math.sin(t),.62)*.23))))
  line('Refined | throw pillow sewn edge',points,.0027,'livingpillows');pillow_report.append({'center':list(loc),'size':list(size),'restsOnSeat':True})
 return pillow_report

def refine_interior(pack_finishes=True):
 assert not any(o.get('refinedSeat') for o in bpy.data.objects),'Refinement already applied'
 luxe.created.clear();cfg=json.load(open(os.path.join(root,'scripts','reference-materials.json')))
 for category in ['livingfabric','livingfloor','livingpillows','floor','tvwall']:
  if pack_finishes:pack_surface(category,cfg)
  else:
   f=cfg[category];material(category,f['color'],f['roughness'],f.get('metalness',0),f.get('clearcoat',0))
 # Replace the unsupported original cushion assemblies, keeping the sofa plinth and architecture.
 for o in list(bpy.data.objects):
  if o.get('category')=='livingfabric':bpy.data.objects.remove(o,do_unlink=True)
  elif o.type=='MESH' and o.name.startswith('Luxury |') and o.get('category') in ['decor','fabric']:
   remove_faces(o,[((9.30,9.8,.50),(9.9,12.75,1.05))])
 chair_bases=[((x-.285,8.87-.285,.055),(x+.285,8.87+.285,.185)) for x in [7.78,9.31]]
 for o in list(bpy.data.objects):
  if o.type=='MESH' and o.name.startswith('Luxury |') and o.get('category')=='interiormetal':remove_faces(o,chair_bases)
 # Remove the two original lamp parts that overlap the replacement reading lamp.
 for o in list(bpy.data.objects):
  if o.type=='MESH' and o.get('category')=='details':remove_faces(o,[((9.885,13.035,0),(9.915,13.065,1.60)),((9.680,12.830,1.450),(10.120,13.270,1.700))])
 stitch=material('Decor | tailored stitch','#887b69',.92)
 # The sofa shell has rounded arms; dense cushion meshes carry actual shallow fabric folds.
 box('Refined | sofa foundation',(9.63,11.25,.26),(.9,2.9,.27),'livingfabric',.10)
 box('Refined | sofa upholstered back',(9.96,11.25,.61),(.20,2.9,.58),'livingfabric',.08)
 for y in [9.91,12.59]:box('Refined | upholstered sofa arm',(9.62,y,.49),(.9,.22,.47),'livingfabric',.08)
 for y in [10.39,11.25,12.11]:
  seat=tailored('Refined | softly compressed sofa seat',(9.54,y,.445),(.70,.80,.23),'livingfabric',.42)
  tailored('Refined | plump sofa back cushion',(9.83,y,.71),(.22,.80,.48),'livingfabric',.42,-.12,.002)
  pts=[(9.54+signed(math.cos(t),.40)*.347,y+signed(math.sin(t),.40)*.398,.443) for t in [i*2*math.pi/100 for i in range(101)]];line('Refined | sofa cushion piping',pts,.003,'livingfabric')
 from tailored_armchairs import add_armchairs
 chair_report=add_armchairs()
 pillow_report=add_throw_pillows()
 # Oak overlay follows the existing room footprint. Other ground floors use the same wood finish.
 floor=box('Refined | luxury oak living-room flooring',(8.29,10.675,.006),(4.075,5.36,.01),'livingfloor',0);floor['woodFloor']=True
 # Remove all prior artwork parts, including the piece that crossed the passage opening.
 old_art=[(8.0,13.325,1.56,1.10,1.25),(4.45,18.605,1.58,.65,.95),(5.30,18.605,1.58,.65,.95),(.15,13.405,4.67,.70,.85),(4.35,18.605,4.70,.70,.85)]
 art_boxes=[((x-w/2-.03,y-.055,z-h/2-.035),(x+w/2+.03,y+.025,z+h/2+.035)) for x,y,z,w,h in old_art]
 for o in list(bpy.data.objects):
  if o.type=='MESH' and o.name.startswith('Luxury |') and o.get('category') in ['decor','interiormetal']:remove_faces(o,art_boxes)
 # Mount every new piece against actual solid wall geometry; samples include the full frame perimeter.
 verts=[];faces=[]
 for o in bpy.data.objects:
  if o.type!='MESH' or o.get('category') not in ['walls','accent','featurewall']:continue
  offset=len(verts);verts.extend([o.matrix_world@v.co for v in o.data.vertices]);faces.extend([tuple(offset+i for i in p.vertices) for p in o.data.polygons])
 walls=BVHTree.FromPolygons(verts,faces)
 def mount(origin,direction,tangent,width,height):
  origin=Vector(origin);direction=Vector(direction);tangent=Vector(tangent);hit=walls.ray_cast(origin,direction,.65)[0]
  if hit is None:return None
  normal=-direction;reference=hit
  for u in [-.5,0,.5]:
   for v in [-.5,0,.5]:
    p=origin+tangent*(width*u)+Vector((0,0,height*v));point=walls.ray_cast(p,direction,.65)[0]
    if point is None or abs((point-reference).dot(direction))>.015:return None
  return reference+normal*.018,tangent,normal
 mounts=[]
 plans=[('living',[(10.10,y,1.74) for y in [11.25,10.95,11.65]],(1,0,0),(0,1,0),1.35,.95),('dining',[(x,15.29,1.68) for x in [4.6,5.2,3.4]],(0,-1,0),(1,0,0),.70,.85),('bedroom one',[(5.83,y,4.86) for y in [17.2,16.4]],(1,0,0),(0,1,0),.65,.80),('bedroom two',[(x,13.15,4.84) for x in [.15,.9,1.7]],(0,1,0),(1,0,0),.65,.80)]
 paper=material('Decor | mounted art paper','#ede1cc',.96);rust=material('Decor | mounted art rust','#a9755e',.85);olive=material('Decor | mounted art olive','#65765d',.86);ink=material('Decor | mounted art charcoal','#303438',.75)
 for room,candidates,direction,tangent,width,height in plans:
  found=next((m for m in [mount(p,direction,tangent,width+.04,height+.04) for p in candidates] if m),None)
  if not found:continue
  center,u,n=found;angle=math.atan2(u.y,u.x)
  o=box('Refined | wall-mounted art canvas',center,(width,.024,height),'decor',.001,paper);o.rotation_euler.z=angle;o['artRoom']=room;o['wallMounted']=True
  for side in [-1,1]:
   pos=center+u*side*width/2+n*.017;o=box('Refined | mounted art frame side',pos,(.017,.035,height+.035),'interiormetal',.002);o.rotation_euler.z=angle
   pos=center+n*.017+Vector((0,0,side*height/2));o=box('Refined | mounted art frame rail',pos,(width+.035,.035,.017),'interiormetal',.002);o.rotation_euler.z=angle
  for du,dz,sx,sz,mat in [(-.15,.08,.26,.34,rust),(.19,-.22,.25,.20,olive)]:
   pos=center+u*(du*width)+n*.026+Vector((0,0,dz*height));o=sphere('Refined | wall-art relief',pos,(sx*width,.006,sz*height),'decor',mat);o.rotation_euler.z=angle
  points=[tuple(center+u*(width*.7*(v-.5))+n*.035+Vector((0,0,math.sin(v*2*math.pi)*height*.19))) for v in [i/50 for i in range(51)]];line('Refined | mounted art flowing line',points,.0025,'decor',ink)
  mounts.append({'room':room,'center':list(center),'normal':list(n),'width':width,'height':height,'solidWallSamples':9})
 assert any(m['room']=='living' for m in mounts),'Living artwork must be mounted on a solid wall'
 # Smooth weighted normals on upholstered shells; world-scale UVs on all new objects.
 groups=collections.defaultdict(list)
 for o in list(luxe.created):
  points=[o.matrix_world@Vector(p) for p in o.bound_box];floor=0 if min(p.z for p in points)<3 else 1;o['floor']=floor
  if o.name.startswith('Refined | sofa') or 'upholstered sofa arm' in o.name:
   for p in o.data.polygons:p.use_smooth=True
   mod=o.modifiers.new('Soft upholstery normals','WEIGHTED_NORMAL');mod.keep_sharp=True;bpy.context.view_layer.objects.active=o; o.select_set(True);bpy.ops.object.modifier_apply(modifier=mod.name);o.select_set(False)
  if o.get('tailoredUV'):continue
  uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
  for face in o.data.polygons:
   axis=max(range(3),key=lambda i:abs((o.matrix_world.to_3x3()@face.normal)[i]));axes=[i for i in range(3) if i!=axis]
   for idx in face.loop_indices:
    p=o.matrix_world@o.data.vertices[o.data.loops[idx].vertex_index].co;uv.data[idx].uv=(p[axes[0]],p[axes[1]])
  # Preserve seating and mounted-art tags on individually reviewable pieces.
  if o.get('refinedSeat') or o.get('throwPillow') or o.get('wallMounted') or o.get('woodFloor') or o.get('chairPart'):continue
  groups[(floor,o['category'],o.data.materials[0].name)].append(o)
 for (floor,cat,mat),objects in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in objects:o.select_set(True)
  bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name='Refined | '+cat+' | '+mat;o['floor']=floor
 report={'armchairs':chair_report,'pillows':pillow_report,'artMounts':mounts,'flooring':'Warm European oak boards; marble retained on TV wall','garden':'Unchanged'}
 with open(os.path.join(root,'public','interior-refinement.json'),'w') as f:json.dump(report,f,indent=2)
 return report
def export_and_save():
 links=[]
 for m in bpy.data.materials:
  if not m.use_nodes or m.get('keepTexture'):continue
  bs=m.node_tree.nodes.get('Principled BSDF')
  if not bs:continue
  for key in ['Base Color','Roughness','Normal']:
   for link in list(bs.inputs[key].links):links.append((m.node_tree,link.from_socket,link.to_socket));m.node_tree.links.remove(link)
 bpy.ops.object.select_all(action='DESELECT')
 for o in bpy.data.objects:
  if o.type=='MESH' and o.get('category'):o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=os.path.join(root,'public','models','francis.glb'),export_format='GLB',export_extras=True,export_yup=True,use_selection=True)
 for tree,a,b in links:tree.links.new(a,b)
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))

if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'Francis-Web.blend'));print(refine_interior());export_and_save();print('REFINED INTERIORS EXPORTED AND SAVED')
