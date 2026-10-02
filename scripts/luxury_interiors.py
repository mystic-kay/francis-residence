"""Upgrade the existing sitting room and add restrained interior styling in Blender."""
import bpy,bmesh,os,json,math,collections,sys
from mathutils import Vector,Matrix
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def lin(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def material(name,color,rough=.6,metal=0,coat=0,emission=0):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');rgb=tuple(lin(int(color[i:i+2],16)/255) for i in (1,3,5))+(1,);m.diffuse_color=rgb;b.inputs['Base Color'].default_value=rgb;b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal;b.inputs['Coat Weight'].default_value=coat;b.inputs['Coat Roughness'].default_value=.14
 if emission:b.inputs['Emission Color'].default_value=rgb;b.inputs['Emission Strength'].default_value=emission
 return m
created=[]
def finish(o,cat,mat=None):
 o['category']=cat;o['finishGroup']=cat;o['floor']=0 if o.location.z<3 else 1;o.data.materials.append(mat or bpy.data.materials[cat]);created.append(o);return o
def box(name,loc,size,cat,bevel=.015,mat=None):
 x,y,z=[v/2 for v in size];verts=[(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)];mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.location=loc;finish(o,cat,mat)
 if bevel:
  mod=o.modifiers.new('Soft finished edges','BEVEL');mod.width=bevel;mod.segments=4;bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.modifier_apply(modifier=mod.name);o.select_set(False)
 return o
def cylinder(name,loc,radius,depth,cat,mat=None,radius_top=None):
 n=40;rt=radius if radius_top is None else radius_top;verts=[(r*math.cos(i*2*math.pi/n),r*math.sin(i*2*math.pi/n),h) for r,h in [(radius,-depth/2),(rt,depth/2)] for i in range(n)];faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.location=loc
 for p in mesh.polygons:p.use_smooth=len(p.vertices)==4
 return finish(o,cat,mat)
def line(name,points,radius,cat,mat=None):
 curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.bevel_depth=radius;curve.bevel_resolution=3;sp=curve.splines.new('POLY');sp.points.add(len(points)-1)
 for p,co in zip(sp.points,points):p.co=(*co,1)
 o=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False);return finish(o,cat,mat)
def sphere(name,loc,size,cat,mat=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc);o=bpy.context.object;o.name=name;o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for p in o.data.polygons:p.use_smooth=True
 o.select_set(False);return finish(o,cat,mat)
def remove_faces(o,boxes):
 bm=bmesh.new();bm.from_mesh(o.data);faces=[]
 for f in bm.faces:
  points=[o.matrix_world@v.co for v in f.verts]
  if any(all(all(a[i]-.015<=p[i]<=b[i]+.015 for i in range(3)) for p in points) for a,b in boxes):faces.append(f)
 count=len(faces)
 if faces:bmesh.ops.delete(bm,geom=faces,context='FACES');bm.to_mesh(o.data);o.data.update()
 bm.free();return count

def add_living_curtains():
 for o in list(bpy.data.objects):
  if o.type=='MESH' and o.get('category')=='details':remove_faces(o,[((6.538,8.036,.015),(6.888,8.156,2.62)),((9.688,8.036,.015),(10.038,8.156,2.62))])
 f=json.load(open(os.path.join(root,'scripts','reference-materials.json')))['curtains'];material('curtains',f['color'],f['roughness'])
 for x0,x1 in [(6.55,6.99),(9.53,10.02)]:
  nx,nz=56,12;verts=[];faces=[]
  for i in range(nx+1):
   u=i/nx
   for j in range(nz+1):
    v=j/nz;verts.append((x0+(x1-x0)*u,8.11+.030*math.sin(u*math.pi*14)*(1+.12*(1-v)),.055+2.50*v))
  for i in range(nx):
   for j in range(nz):
    k=i*(nz+1)+j;faces.append((k,k+nz+1,k+nz+2,k+1))
  mesh=bpy.data.meshes.new('Soft pleated linen curtain');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('Luxury | pleated living curtains',mesh);bpy.context.collection.objects.link(o);finish(o,'curtains')
  for face in mesh.polygons:face.use_smooth=True
  uv=mesh.uv_layers.new(name='UVMap')
  for face in mesh.polygons:
   for idx in face.loop_indices:
    v=mesh.vertices[mesh.loops[idx].vertex_index].co;uv.data[idx].uv=(v.x,v.z)

def add_luxury_interior(pack_finishes=True):
 assert not any(o.name.startswith('Luxury |') for o in bpy.data.objects),'Interior upgrade already applied'
 # Work from the exact original footprints, removing only the sitting-room pieces.
 masks={
 'fabric':[((7.261,8.452,0),(8.299,9.223,.81)),((8.791,8.452,0),(9.829,9.223,.81)),((9.39,9.8,0),(10.05,12.7,.83))],
 'wood':[((7.55,10.65,0),(8.55,11.75,.61)),((8.35,8.65,0),(8.75,9.05,.762)),((6.238,9.5,0),(6.72,13.1,2.56))],
 'details':[((6.275,10.58,.95),(6.367,12.03,1.61)),((7.2,9.6,0),(9.95,12.9,.013))],
 'lighting':[((9.75,12.9,1.94),(10.05,13.2,2.56))]}
 removed=collections.Counter()
 for o in list(bpy.data.objects):
  if o.type=='MESH' and o.get('category') in masks:removed[o.get('category')]+=remove_faces(o,masks[o.get('category')])
 assert removed['fabric']>100 and removed['wood']>0 and removed['details']>0,dict(removed)
 cfg=json.load(open(os.path.join(root,'scripts','reference-materials.json')))
 for cat in ['livingfabric','livingrug','tvunit','tvwall','coffeetop','interiormetal','curtains']:
  f=cfg[cat];material(cat,f['color'],f['roughness'],f.get('metalness',0),f.get('clearcoat',0))
 cream=material('Decor | porcelain','#eee6d8',.32);ink=material('Decor | charcoal','#282f32',.6);terracotta=material('Decor | rust','#ad785e',.75);sage=material('Decor | olive','#64715b',.75);paper=material('Decor | art paper','#eee3d0',.95);glow=material('Decor | warm LED','#fff0d5',.22,emission=3);screen=material('Decor | large TV screen','#101b27',.19,coat=.7)
 add_living_curtains()
 # Contemporary sofa, oriented toward the TV wall (+X wall normal; sofa faces -X).
 box('Luxury | sofa recessed base',(9.64,11.25,.10),(.70,2.65,.16),'interiormetal',.035)
 box('Luxury | sofa base',(9.63,11.25,.27),(.90,2.9,.28),'livingfabric',.10)
 box('Luxury | sofa back',(9.96,11.25,.63),(.19,2.9,.58),'livingfabric',.08)
 for y in [9.91,12.59]:box('Luxury | sofa soft arm',(9.62,y,.49),(.90,.22,.48),'livingfabric',.075)
 for y in [10.39,11.25,12.11]:
  box('Luxury | sofa seat cushion',(9.55,y,.48),(.69,.80,.20),'livingfabric',.085)
  o=box('Luxury | sofa back cushion',(9.84,y,.72),(.18,.80,.47),'livingfabric',.075);o.rotation_euler.y=-.13
 for y in [10.13,12.38]:
  o=sphere('Luxury | sofa accent cushion',(9.59,y,.78),(.10,.24,.24),'decor',sage if y<11 else terracotta);o.rotation_euler.y=-.15
 # Barrel armchairs: backs toward the window, open fronts aimed at the coffee table.
 chairs=[]
 for x in [7.78,9.31]:
  cy=8.87;target=Vector((8.12,11.15,0));forward=Vector((target.x-x,target.y-cy,0)).normalized();yaw=-math.atan2(forward.x,forward.y);rot=Matrix.Rotation(yaw,3,'Z');origin=Vector((x,cy,0))
  cylinder('Luxury | chair swivel base',(x,cy,.12),.28,.12,'interiormetal')
  cylinder('Luxury | chair upholstered seat',(x,cy,.43),.405,.20,'livingfabric')
  steps=48;verts=[];tops=[]
  for i in range(steps+1):
   t=math.radians(160+220*i/steps);top=.63+.25*max(0,-math.sin(t));tops.append(tuple(origin+rot@Vector((.45*math.cos(t),.45*math.sin(t),top))))
   for r,z in [(.39,.30),(.50,.30),(.39,top),(.50,top)]:verts.append(tuple(origin+rot@Vector((r*math.cos(t),r*math.sin(t),z))))
  faces=[]
  for i in range(steps):
   k=i*4;faces.extend([(k,k+4,k+6,k+2),(k+1,k+3,k+7,k+5),(k+2,k+6,k+7,k+3),(k,k+1,k+5,k+4)])
  faces.extend([(0,2,3,1),(steps*4,steps*4+1,steps*4+3,steps*4+2)])
  mesh=bpy.data.meshes.new('Curved barrel chair');mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new('Luxury | inward-facing barrel armchair',mesh);bpy.context.collection.objects.link(o);finish(o,'livingfabric')
  for p in mesh.polygons:p.use_smooth=True
  o['seatingForward']=list(forward);o['seatingCenter']=[x,cy,0];o['seatingTarget']=[8.12,11.15,0]
  line('Luxury | armchair upholstery piping',tops,.004,'livingfabric');chairs.append({'center':[x,cy],'forward':list(forward),'target':[8.12,11.15]})
 # Nesting stone tables and a textile rug.
 box('Luxury | woven living rug',(8.6,11.15,.021),(2.8,3.05,.024),'livingrug',.035)
 for x,y,r,h in [(8.03,11.0,.48,.40),(8.60,11.55,.34,.33)]:
  cylinder('Luxury | nesting table pedestal',(x,y,h/2),r*.50,h-.03,'interiormetal')
  cylinder('Luxury | veined stone tabletop',(x,y,h),r,.038,'coffeetop')
 cylinder('Luxury | armchair side table base',(8.53,8.88,.25),.09,.46,'interiormetal');cylinder('Luxury | armchair side table top',(8.53,8.88,.51),.18,.025,'coffeetop')
 # Floating glossy white media unit, stone feature panel and 86-inch class display.
 box('Luxury | stone media wall',(6.263,11.29,1.35),(.038,3.55,2.45),'tvwall',.008)
 for y in [9.57+i*.045 for i in range(10)]:box('Luxury | oak media-wall flute',(6.31,y,1.35),(.055,.023,2.43),'wood',.006)
 box('Luxury | floating TV console carcass',(6.48,11.3,.45),(.48,3.0,.32),'tvunit',.025)
 for y in [10.17,10.92,11.67,12.42]:box('Luxury | handleless glossy white cabinet front',(6.731,y,.45),(.028,.738,.29),'tvunit',.008)
 box('Luxury | console shadow gap',(6.749,11.3,.59),(.008,2.96,.014),'decor',.001,ink)
 box('Luxury | cabinet underlight',(6.68,11.3,.283),(.035,2.85,.014),'interiorlight',.003,glow)
 box('Luxury | large television bezel',(6.365,11.3,1.49),(.045,1.96,1.12),'decor',.012,ink)
 box('Luxury | 86-inch class television display',(6.391,11.3,1.49),(.008,1.925,1.083),'decor',.007,screen)
 box('Luxury | TV status light',(6.397,11.3,.944),(.009,.020,.004),'interiorlight',.001,glow)
 # Brass floor light, soft shade and shelf accessories.
 cylinder('Luxury | floor lamp base',(9.88,12.98,.036),.18,.05,'interiormetal');cylinder('Luxury | floor lamp stem',(9.88,12.98,.89),.012,1.7,'interiormetal')
 cylinder('Luxury | warm lamp shade',(9.88,12.98,1.68),.16,.28,'decor',cream,.20);sphere('Luxury | lamp diffuser',(9.88,12.98,1.54),(.15,.15,.025),'interiorlight',glow)
 for i,(c,w) in enumerate([(ink,.28),(terracotta,.23),(paper,.25)]):box('Luxury | art books',(8.03,11,.438+i*.025),(w,.18,.020),'decor',.003,c)
 cylinder('Luxury | sculptural bowl',(8.55,11.52,.38),.11,.065,'decor',cream,.14)
 # Original framed abstract relief artwork. No third-party image or branding.
 def art(cx,cy,cz,width=1.1,height=1.3):
  box('Luxury | original abstract artwork backing',(cx,cy,cz),(width,.025,height),'decor',.002,paper)
  for x in [cx-width/2,cx+width/2]:box('Luxury | artwork frame stile',(x,cy-.025,cz),(.018,.04,height+.035),'interiormetal',.002)
  for z in [cz-height/2,cz+height/2]:box('Luxury | artwork frame rail',(cx,cy-.025,z),(width+.035,.04,.018),'interiormetal',.002)
  # Sculptural organic discs and a fine flowing line on the canvas plane.
  for x,z,sx,sz,mat in [(-.15,.10,.25,.37,terracotta),(.19,-.23,.25,.20,sage)]:
   o=sphere('Luxury | abstract relief',(cx+x*width,cy-.024,cz+z*height),(sx*width,.007,sz*height),'decor',mat)
  points=[(cx+(u-.5)*width*.70,cy-.037,cz+math.sin(u*math.pi*2)*height*.19) for u in [i/50 for i in range(51)]];line('Luxury | abstract gallery line',points,.003,'decor',ink)
 art(8.0,13.325,1.56,1.10,1.25)
 # A coordinated pair in the dining space and small gallery pieces in bedrooms.
 art(4.45,18.605,1.58,.65,.95);art(5.30,18.605,1.58,.65,.95)
 art(.15,13.405,4.67,.70,.85);art(4.35,18.605,4.70,.70,.85)
 # Indoor planting: tapered ceramic pot, slender branches and individual olive leaves.
 px,py=10.06,9.50;cylinder('Luxury | indoor planter',(px,py,.21),.16,.39,'decor',cream,.21)
 leaves=material('Decor | olive foliage','#52664d',.9);stem=material('Decor | plant stems','#6c5a42',.85)
 for j in range(5):
  theta=j*2.4;end=(px+.16*math.cos(theta),py+.16*math.sin(theta),1.10+j*.09);line('Luxury | olive branch',[(px,py,.30),end],.007,'decor',stem)
  for k in range(7):
   t=.38+k*.085;z=.30+(end[2]-.30)*t;cx=px+(end[0]-px)*t;cy=py+(end[1]-py)*t;angle=theta+k*.8
   o=sphere('Luxury | olive leaf',(cx+.06*math.cos(angle),cy+.06*math.sin(angle),z),(.065,.019,.008),'decor',leaves);o.rotation_euler.z=angle
 # Console objects and vase stems.
 cylinder('Luxury | porcelain vase',(6.55,10.02,.74),.075,.25,'decor',cream,.04)
 for i in range(4):line('Luxury | decorative stems',[(6.55,10.02,.84),(6.56+i*.02,10.02+(i-1.5)*.035,1.15+i*.01)],.0025,'decor',stem)
 # Woven bump and stone/oak maps match the web controls in the editable scene.
 for category in (['livingfabric','livingrug','tvunit','tvwall','coffeetop','interiormetal','curtains'] if pack_finishes else []):
  m=bpy.data.materials[category];f=cfg[category];nodes=m.node_tree.nodes;links=m.node_tree.links;bs=nodes.get('Principled BSDF');tex=f.get('texture')
  if tex=='woven':
   uv=nodes.new('ShaderNodeTexNoise');uv.inputs['Scale'].default_value=220;bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.002;links.new(uv.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
  elif tex:
   uv=nodes.new('ShaderNodeTexCoord');mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='SCALE';mapping.inputs[3].default_value=f.get('scale',1);links.new(uv.outputs['UV'],mapping.inputs[0])
   for kind in ['color','normal','roughness']:
    path=os.path.join(root,'public','textures',tex,kind+'.jpg');im=bpy.data.images.load(path,check_existing=True);im.colorspace_settings.name='sRGB' if kind=='color' else 'Non-Color';im.pack();node=nodes.new('ShaderNodeTexImage');node.image=im;links.new(mapping.outputs[0],node.inputs['Vector'])
    if kind=='color':
     mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=bs.inputs['Base Color'].default_value;links.new(node.outputs['Color'],mix.inputs[1]);links.new(mix.outputs[0],bs.inputs['Base Color'])
    elif kind=='normal':
     normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.25;links.new(node.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],bs.inputs['Normal'])
    else:links.new(node.outputs['Color'],bs.inputs['Roughness'])
 # Merge only newly added non-chair decorative pieces by floor/category/material.
 groups=collections.defaultdict(list)
 for o in created:
  if 'seatingForward' in o:continue
  points=[o.matrix_world@Vector(p) for p in o.bound_box];floor=0 if min(p.z for p in points)<3 else 1;o['floor']=floor
  uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
  for face in o.data.polygons:
   axis=max(range(3),key=lambda i:abs((o.matrix_world.to_3x3()@face.normal)[i]));axes=[i for i in range(3) if i!=axis]
   for idx in face.loop_indices:
    p=o.matrix_world@o.data.vertices[o.data.loops[idx].vertex_index].co;uv.data[idx].uv=(p[axes[0]],p[axes[1]])
  groups[(floor,o['category'],o.data.materials[0].name)].append(o)
 for (floor,cat,mat),objects in groups.items():
  bpy.ops.object.select_all(action='DESELECT')
  for o in objects:o.select_set(True)
  bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name='Luxury | '+cat+' | '+mat;o['floor']=floor
 # Keep matching lamps in Blender. The web app adds the same warm lights interactively.
 for loc,power in [((6.78,11.3,.26),35),((9.88,12.98,1.55),18)]:
  light=bpy.data.lights.new('Luxury | warm practical light','POINT');light.energy=power;light.color=(1,.80,.55);light.shadow_soft_size=.35;o=bpy.data.objects.new(light.name,light);bpy.context.collection.objects.link(o);o.location=loc
 report={'style':'Warm contemporary luxury','armchairs':chairs,'tvScreenMetres':[1.925,1.083],'mediaCabinet':'Floating glossy white, handleless fronts','art':'Original geometric relief pieces in living, dining and bedrooms','removedFaces':dict(removed),'garden':'Unchanged from the user-marked layout'}
 with open(os.path.join(root,'public','interior-manifest.json'),'w') as f:json.dump(report,f,indent=2)
 return report
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'Francis-Web.blend'));print(add_luxury_interior())
 # Export lean web surfaces and retain packed textures in the editable scene.
 links=[]
 for m in bpy.data.materials:
  if not m.use_nodes:continue
  bs=m.node_tree.nodes.get('Principled BSDF')
  if not bs:continue
  for key in ['Base Color','Roughness','Normal']:
   for link in list(bs.inputs[key].links):links.append((m.node_tree,link.from_socket,link.to_socket));m.node_tree.links.remove(link)
 bpy.ops.object.select_all(action='DESELECT')
 for o in bpy.data.objects:
  if o.type=='MESH' and o.get('category'):o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=os.path.join(root,'public','models','francis.glb'),export_format='GLB',export_extras=True,export_yup=True,use_selection=True)
 for tree,a,b in links:tree.links.new(a,b)
 bpy.ops.wm.save_as_mainfile(filepath=os.path.join(root,'Francis-Web.blend'));print('LUXURY INTERIOR EXPORTED AND SAVED')
