"""Run in Blender: imports original FBX, rebuilds finishes and exports self-contained GLB."""
import bpy,os,json,math,collections,re
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=os.path.join(root,'FrancisProject-3DView-{3D}.fbx'))
def bounds(o):
 p=[o.matrix_world@Vector(v) for v in o.bound_box]
 return Vector([min(v[i] for v in p) for i in range(3)]),Vector([max(v[i] for v in p) for i in range(3)])
def classify(n):
 n=n.lower()
 if 'kerb' in n:return 'kerb'
 if 'pergola roof' in n:return 'pergolaglass'
 if 'coping' in n:return 'coping'
 if 'top rail' in n or 'handrail' in n:return 'pergolaframe'
 if 'dark aluminium' in n or 'mullion' in n:return 'metal'
 if 'basic roof' in n:return 'roof'
 if 'rt roof sheeting' in n:return 'roof'
 if 'door-' in n:return 'doors'
 if any(s in n for s in ['window-fixed','glaz','glass']):return 'glass'
 if any(s in n for s in ['muntin','frame','railing','rhs','steel','trim-window']):return 'metal'
 if any(s in n for s in ['light','dl1','dl2','dl3','dl4','dl5','dl6','pendant','led']):return 'lighting'
 if any(s in n for s in ['sofa','chair','bed-standard']):return 'fabric'
 if any(s in n for s in ['table','casework','timber','cabinet']):return 'wood'
 if any(s in n for s in ['floor rc','floor porch','subregion','stair','monolithic','topography','toposolid']):return 'floor'
 if 'charcoal' in n:return 'accent'
 if any(s in n for s in ['ceiling','roof','coping']):return 'ceiling'
 if any(s in n for s in ['wall','column','concrete','rectangular','footing']):return 'walls'
 if any(s in n for s in ['sink','wc','bath','plumbing']):return 'ceramic'
 return 'details'
colors={'livingfloor':(.75,.55,.3,1),'livingpillows':(.3,.4,.3,1),'curtains':(.9,.88,.8,1),'livingfabric':(.4,.36,.3,1),'livingrug':(.7,.65,.55,1),'tvunit':(.9,.88,.82,1),'tvwall':(.85,.8,.7,1),'coffeetop':(.9,.9,.9,1),'interiormetal':(.6,.4,.2,1),'kerb':(.12,.13,.14,1),'balconyglass':(.65,.78,.8,.16),'balconyrail':(.55,.58,.6,1),'site':(.28,.25,.2,1),'featurewall':(.06,.065,.06,1),'lightstrip':(.95,.88,.72,1),'pergolaframe':(.025,.028,.032,1),'pergolaglass':(.2,.28,.3,.28),'coping':(.08,.085,.09,1),'cabinet':(.92,.92,.9,1),'counter':(.025,.025,.028,1),'hardware':(.025,.025,.028,1),'bedwall':(.25,.32,.27,1),'bedding':(.92,.89,.83,1),'headboard':(.72,.69,.62,1),'bedfloor':(.64,.44,.23,1),'paving':(.3,.3,.3,1),'lawn':(.23,.36,.12,1),'roof':(.03,.035,.04,1),'walls':(.82,.8,.75,1),'floor':(.66,.62,.54,1),'accent':(.08,.09,.085,1),'wood':(.58,.38,.20,1),'fabric':(.72,.69,.62,1),'glass':(.55,.74,.8,1),'metal':(.075,.08,.08,1),'ceramic':(.93,.94,.93,1),'ceiling':(.88,.86,.81,1),'details':(.3,.32,.32,1),'doors':(.42,.28,.15,1),'lighting':(.95,.80,.49,1)}
mats={}
for key,color in colors.items():
 m=bpy.data.materials.new(key);m.diffuse_color=color;m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=color;bs.inputs['Roughness'].default_value=.8
 if key in ['metal','pergolaframe','balconyrail']:bs.inputs['Metallic'].default_value=.8;bs.inputs['Roughness'].default_value=.3
 if key in ['glass','pergolaglass','balconyglass']:bs.inputs['Transmission Weight'].default_value=0;bs.inputs['Roughness'].default_value=.08;bs.inputs['Alpha'].default_value=.3;m.surface_render_method='DITHERED'
 if key in ['lighting','lightstrip']:bs.inputs['Emission Color'].default_value=(1,.75,.4,1);bs.inputs['Emission Strength'].default_value=3
 if key=='lightstrip':bs.inputs['Base Color'].default_value=(1,.91,.76,1);bs.inputs['Emission Color'].default_value=(1,.82,.57,1);bs.inputs['Emission Strength'].default_value=4
 mats[key]=m
originals=list(bpy.data.objects)
furniture=[]
def rounded(name,loc,size,mat,radius=.06):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 mod=o.modifiers.new('Soft upholstery edges','BEVEL');mod.width=radius;mod.segments=4
 bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 o.data.materials.append(mats[mat]);o['finishGroup']=mat;return o
# Retain architectural bed positions and infer headboard side from the original joinery.
for o in [v for v in originals if 'bed-standard' in v.name.lower()]:
 if o.type!='MESH':continue
 lo,hi=bounds(o);n=o.name.lower()
 if 'bed-standard' not in n:continue
 c=(lo+hi)/2;length=hi.x-lo.x;width=hi.y-lo.y;z=lo.z
 candidates=[]
 for panel in list(bpy.data.objects):
  if 'casework' not in panel.name.lower():continue
  a,b=bounds(panel);p=(a+b)/2;d=b-a
  if d.x<.08 and d.y>width*.85 and .8<d.z<1.3 and abs(p.y-c.y)<.2 and abs(p.z-(z+.75))<.25 and abs(p.x-c.x)<1.4:candidates.append(panel)
 side=1
 if candidates:
  panel=min(candidates,key=lambda p:abs(((sum(bounds(p),Vector()))/2).x-c.x));a,b=bounds(panel);side=1 if (a.x+b.x)/2>c.x else -1
  bpy.data.objects.remove(panel,do_unlink=True)
 headx=hi.x if side==1 else lo.x
 rounded('Bed | upholstered base',(c.x,c.y,z+.22),(length,width,.36),'headboard')
 rounded('Bed | mattress',(c.x,c.y,z+.48),(length-.07,width-.06,.22),'bedding',.10)
 rounded('Bed | upholstered headboard',(headx,c.y,z+.66),(.12,width+.12,1.15),'headboard',.08)
 for offset in [-width*.24,width*.24]:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=(headx-side*.42,c.y+offset,z+.67));p=bpy.context.object;p.name='Bed | soft pillow';p.scale=(.29,width*.24,.115);p.rotation_euler.y=-side*.1;p['finishGroup']='bedding'
  for v in p.data.vertices:
   v.co.x=math.copysign(abs(v.co.x)**.48,v.co.x);v.co.y=math.copysign(abs(v.co.y)**.48,v.co.y);v.co.z=math.copysign(abs(v.co.z)**.8,v.co.z)
  for f in p.data.polygons:f.use_smooth=True
 # A draped throw with gentle folds and dropped edges rather than a rigid slab.
 nx,ny=25,37;verts=[];faces=[];footx=(lo.x+length*.27) if side==1 else (hi.x-length*.27)
 for ix in range(nx):
  u=ix/(nx-1)
  for iy in range(ny):
   v=iy/(ny-1);yy=(v-.5)*(width+.25);edge=max(0,abs(yy)-width*.45)
   zz=z+.625+.012*math.sin(u*24+v*7)+.008*math.cos(v*39)-min(.26,edge*1.5)
   verts.append((footx+(u-.5)*length*.5,c.y+yy,zz))
 for ix in range(nx-1):
  for iy in range(ny-1):
   k=ix*ny+iy;faces.append((k,k+ny,k+ny+1,k+1))
 mesh=bpy.data.meshes.new('Draped textile');mesh.from_pydata(verts,[],faces);mesh.update();throw=bpy.data.objects.new('Bed | draped throw',mesh);bpy.context.collection.objects.link(throw);throw['finishGroup']='fabric'
 for f in mesh.polygons:f.use_smooth=True
 # Sage paneling follows the wall immediately behind the headboard.
 panelx=headx+side*.11
 rounded('Bedroom | paneled backdrop',(panelx,c.y,z+1.24),(.028,width+.55,2.48),'bedwall',.004)
 for j in range(5):rounded('Bedroom | panel stile',(panelx-side*.022,c.y+(j/4-.5)*(width+.5),z+1.24),(.035,.026,2.45),'bedwall',.003)
 rounded('Bedroom | panel rail',(panelx-side*.022,c.y,z+1.30),(.035,width+.53,.028),'bedwall',.003)
 furniture.append({'type':'bed','source':'Custom Blender model; reference-inspired upholstery and draped textiles','position':list(c),'headboardSide':side})
 bpy.data.objects.remove(o,do_unlink=True)
# Bedroom finish overlays and rugs keep kitchen flooring independent.
for x0,x1,y0,y1,z in [(-1.13,1.55,15.66,18.66,0),(-1.13,3.48,9.38,13.46,3.15),(2.44,6.12,15.1,18.65,3.15),(6.26,10.32,9.38,13.42,3.15)]:
 rounded('Bedroom | oak floor',((x0+x1)/2,(y0+y1)/2,z+.009),(x1-x0,y1-y0,.012),'bedfloor',.001)
# Append licensed furniture, fitted to the original furniture footprints.
for asset,match in [('sofa_02','sofa w'),('chinese_armchair','chair-corbu')]:
 targets=[o for o in list(bpy.data.objects) if match in o.name.lower()]
 path=os.path.join(root,'assets',asset,asset+'.blend')
 with bpy.data.libraries.load(path,link=False) as (src,dst):dst.objects=src.objects
 templates=[o for o in dst.objects if o and o.type=='MESH']
 for o in templates:
  bpy.context.collection.objects.link(o)
 bpy.context.view_layer.update()
 if not templates:continue
 lows,highs=zip(*(bounds(o) for o in templates));a=Vector([min(v[i] for v in lows) for i in range(3)]);b=Vector([max(v[i] for v in highs) for i in range(3)])
 # Flatten source transforms and fit each copy, preserving furniture proportions in plan.
 for target in targets:
  lo,hi=bounds(target);dims=hi-lo;center=(lo+hi)/2
  turn=(dims.y>dims.x)!=(b.y-a.y>b.x-a.x)
  source_dims=b-a
  sx=dims.x/(source_dims.y if turn else source_dims.x);sy=dims.y/(source_dims.x if turn else source_dims.y);sz=max(.8,dims.z)/source_dims.z
  for template in templates:
   new=bpy.data.objects.new('Furniture | '+asset,template.data.copy());bpy.context.collection.objects.link(new)
   for v in new.data.vertices:
    p=template.matrix_world@v.co-(a+b)/2
    if turn:p=Vector((p.y,-p.x,p.z))
    v.co=Vector((p.x*sx+center.x,p.y*sy+center.y,p.z*sz+lo.z+max(.8,dims.z)/2))
   new.data.materials.clear();new.data.materials.append(mats['fabric'])
  furniture.append({'type':asset,'source':'https://polyhaven.com/a/'+asset,'position':list(center)})
  bpy.data.objects.remove(target,do_unlink=True)
 for o in templates:bpy.data.objects.remove(o,do_unlink=True)
# Cabinet materials and shaker detailing use actual exported joinery dimensions.
for o in list(bpy.data.objects):
 if o.type!='MESH':continue
 lo,hi=bounds(o);c=(lo+hi)/2;d=hi-lo;n=o.name.lower();match=re.search(r'\[(\d+)\]',o.name);oid=int(match.group(1)) if match else 0
 if 'casework' in n and 2.4<c.x<7.5 and 15.05<c.y<18.8 and -.02<c.z<2.6:
  cat='cabinet'
  if d.z<.055 and .84<c.z<.96:cat='counter'
  elif min(d.x,d.y)<.015 and max(d.x,d.y)<.43 and d.z<.65:cat='hardware'
  elif min(d.x,d.y)<.025 and .95<c.z<1.4 and d.z>.12 and max(d.x,d.y)>1:cat='ceramic'
  o['finishGroup']=cat
  # Thin vertical cabinet fronts, excluding oven inserts and appliance faces.
  axis=0 if d.x<.025 else (1 if d.y<.025 else None)
  if cat=='cabinet' and axis is not None and .2<d.z<1.5 and max(d.x,d.y)>.3 and oid not in range(2323230,2323235):
   tangent=1-axis;width=d[tangent];height=d.z;normal=1 if axis==0 else (-1 if c.y>17 else 1)
   for offset in [-1,1]:
    pos=c.copy();pos[axis]+=normal*.014;pos[tangent]+=offset*(width/2-.034);size=[.04,.04,height-.01];size[axis]=.025;size[tangent]=.055
    rounded('Kitchen | shaker stile',pos,size,'cabinet',.002)
    pos=c.copy();pos[axis]+=normal*.014;pos.z+=offset*(height/2-.034);size=[width-.01,width-.01,.055];size[axis]=.025;size[tangent]=width-.01
    rounded('Kitchen | shaker rail',pos,size,'cabinet',.002)
 if 2329056<=oid<=2329102 or 2329106<=oid<=2329117:o['finishGroup']='pergolaframe'
 if oid in [2329100,2329103,2329104]:o['finishGroup']='pergolaglass'
 if oid in [1876760,1876763,1876770,1876772,1876821]:o['finishGroup']='featurewall'
 if oid in [2325270,2356935]:o['finishGroup']='lightstrip'
 if oid in [2322897,2323171,2323110]:o['finishGroup']='bedwall'
 if 'subregion' in n:
  o['finishGroup']='lawn' if oid in [2331112] else ('site' if oid in [2331182,2331189,2331196] else 'paving')
  # Bring the landscape finish to its actual site datum; the source surface sits 620mm down.
  o.location.z+=.02
 if n.startswith('surface'):o['finishGroup']='paving'
 if 'generic model box' in n and -3<c.x<-.5 and 1<c.y<7 and c.z>1 and (d.z>1 or max(d.x,d.y)>1):o['finishGroup']='wood'
# Only replace the explicitly marked glass infills; retain every masonry parapet and coping.
def guard_run(a,b,z,height):
 start=Vector((*a,z));end=Vector((*b,z));delta=end-start;length=delta.length;count=max(1,math.ceil(length/1.15));direction=delta.normalized();angle=math.atan2(direction.y,direction.x)
 def bar(name,point,along,depth,h,category):
  # Direct meshes keep repetitive railing hardware inexpensive to build.
  verts=[(x*along/2,y*depth/2,t*h/2) for x,y,t in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
  mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);mesh.update();ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob);ob.location=point;ob.rotation_euler.z=angle;ob['finishGroup']=category
 for i in range(count+1):
  pos=start+delta*(i/count)
  bar('Balustrade | slim post',pos+Vector((0,0,height/2)),.035,.035,height,'balconyrail')
  bar('Balustrade | base plate',pos+Vector((0,0,.008)),.085,.08,.016,'balconyrail')
  for h in [.18,height-.18]:
   for sign in [-1,1]:
    if (i==0 and sign==-1) or (i==count and sign==1):continue
    bar('Balustrade | clamp',pos+direction*(sign*.045)+Vector((0,0,h)),.065,.035,.028,'balconyrail')
 for i in range(count):bar('Balustrade | glass panel',start+delta*((i+.5)/count)+Vector((0,0,height/2)),length/count-.055,.012,height-.035,'balconyglass')
 bar('Balustrade | top rail',(start+end)/2+Vector((0,0,height)),length+.025,.04,.03,'balconyrail')
marked=[]
for o in list(bpy.data.objects):
 match=re.search(r'\[(\d+)\]',o.name);oid=int(match.group(1)) if match else 0
 if oid in list(range(2328805,2328821))+[2328756,2328757]:
  if oid==2328756 or (2328805<=oid<=2328819 and oid%2==1):
   lo,hi=bounds(o);center=(lo+hi)/2
   if hi.x-lo.x>hi.y-lo.y:a=(lo.x,center.y);b=(hi.x,center.y)
   else:a=(center.x,lo.y);b=(center.x,hi.y)
   marked.append((a,b,lo.z,hi.z-lo.z))
  bpy.data.objects.remove(o,do_unlink=True)
for a,b,z,height in marked:guard_run(a,b,z,height)
# Match the user annotation: grass inside the large kerbed landscape; front strips are walkways.
import sys
sys.path.insert(0,os.path.join(root,'scripts'))
from garden_layout import create_marked_lawn
create_marked_lawn()

# Compact island inspired by the kitchen references, within the existing clear floor area.
rounded('Kitchen | island carcass',(4.65,16.90,.47),(1.34,.72,.80),'cabinet',.006)
rounded('Kitchen | island plinth',(4.65,16.90,.08),(1.23,.61,.12),'hardware',.003)
rounded('Kitchen | polished island worktop',(4.65,16.90,.89),(1.44,.82,.045),'counter',.005)
for x in [4.31,4.99]:
 for y,normal in [(16.535,-1),(17.265,1)]:
  for xx in [x-.29,x+.29]:rounded('Kitchen | island panel stile',(xx,y,.48),(.045,.028,.72),'cabinet',.002)
  for zz in [.145,.815]:rounded('Kitchen | island panel rail',(x,y,zz),(.60,.028,.045),'cabinet',.002)
  rounded('Kitchen | island pull',(x,y+normal*.034,.74),(.18,.018,.018),'hardware',.003)
furniture.append({'type':'kitchen island','source':'Custom Blender model inspired by supplied kitchen references','position':[4.65,16.90,.47]})
groups=collections.defaultdict(list);doors=[]
for o in list(bpy.data.objects):
 if o.type!='MESH':continue
 lo,hi=bounds(o);category=o.get('finishGroup') or ('fabric' if o.name.startswith('Furniture |') else classify(o.name))
 if category=='floor' and lo.z>=-.25 and hi.z<6.3:category='bedfloor' if lo.z>3 else 'floor'
 floor=max(0,min(3,int((lo.z+.2)/3.15)))
 if hi.z-lo.z>3.5:floor=-1
 o.data.materials.clear();o.data.materials.append(mats[category])
 # World-aligned UVs in metres, with dominant face axis chosen per polygon.
 uv=o.data.uv_layers.get('UVMap') or o.data.uv_layers.new(name='UVMap')
 for face in o.data.polygons:
  normal=o.matrix_world.to_3x3()@face.normal;axis=max(range(3),key=lambda i:abs(normal[i]));axes=[i for i in range(3) if i!=axis]
  for idx in face.loop_indices:
   p=o.matrix_world@o.data.vertices[o.data.loops[idx].vertex_index].co;uv.data[idx].uv=(p[axes[0]],p[axes[1]])
 o['category']=category;o['floor']=floor
 if category=='doors':
  o['sourceName']=o.name;doors.append(o);continue
 groups[(floor,category)].append(o)
for (floor,cat),objects in groups.items():
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();o=bpy.context.object;o.name=f'Level {floor} | {cat}';o['category']=cat;o['floor']=floor
from luxury_interiors import add_luxury_interior
add_luxury_interior(pack_finishes=False)
from refine_interior_realism import refine_interior
refine_interior(pack_finishes=False)
bpy.ops.export_scene.gltf(filepath=os.path.join(root,'public','models','francis.glb'),export_format='GLB',export_extras=True,export_yup=True)
# Pack the matching PBR finishes into the editable Blender scene after the lean web export.
with open(os.path.join(root,'scripts','reference-materials.json')) as f:reference_materials=json.load(f)
def linear(c):return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
for category,finish in reference_materials.items():
 material=mats[category];nodes=material.node_tree.nodes;links=material.node_tree.links;bs=nodes.get('Principled BSDF')
 color=tuple(linear(int(finish['color'][i:i+2],16)/255) for i in (1,3,5))+(1,)
 bs.inputs['Base Color'].default_value=color;material.diffuse_color=color;bs.inputs['Roughness'].default_value=finish['roughness'];bs.inputs['Metallic'].default_value=finish.get('metalness',0);bs.inputs['Coat Weight'].default_value=finish.get('clearcoat',0);bs.inputs['Sheen Weight'].default_value=.18 if category in ['livingfabric','livingpillows'] else 0
 if 'opacity' in finish:bs.inputs['Alpha'].default_value=finish['opacity'];bs.inputs['Transmission Weight'].default_value=0;material.surface_render_method='DITHERED'
 texture=finish.get('texture')
 if texture and texture!='woven':
  uv=nodes.new('ShaderNodeTexCoord');mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='SCALE';mapping.inputs[3].default_value=finish.get('scale',1);links.new(uv.outputs['UV'],mapping.inputs[0])
  for map_type in ['color','normal','roughness']:
   path=os.path.join(root,'public','textures',texture,map_type+'.jpg')
   if not os.path.exists(path):continue
   image=bpy.data.images.load(path,check_existing=True);image.colorspace_settings.name='sRGB' if map_type=='color' else 'Non-Color';image.pack()
   node=nodes.new('ShaderNodeTexImage');node.image=image;links.new(mapping.outputs[0],node.inputs['Vector'])
   if map_type=='color':
    mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=color;links.new(node.outputs['Color'],mix.inputs[1]);links.new(mix.outputs[0],bs.inputs['Base Color'])
   elif map_type=='normal':
    normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.3;links.new(node.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],bs.inputs['Normal'])
   else:
    multiply=nodes.new('ShaderNodeMath');multiply.operation='MULTIPLY';multiply.inputs[1].default_value=finish['roughness'];links.new(node.outputs['Color'],multiply.inputs[0]);links.new(multiply.outputs[0],bs.inputs['Roughness'])
 elif texture=='woven':
  noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=220;bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.002;links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],bs.inputs['Normal'])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(root,'Francis-Web.blend'))
with open(os.path.join(root,'public','scene-manifest.json'),'w') as f:json.dump({'source':'FrancisProject-3DView-{3D}.fbx','units':'metres','materialsStatus':'Reference-inspired palette from user-supplied exterior, kitchen and bedroom images; product codes and measured properties are unverified','furniture':furniture,'meshCount':len([o for o in bpy.data.objects if o.type=='MESH'])},f,indent=2)
print('WEB EXPORT COMPLETE')
