"""Make the pergola room's east glass wall (x 10.30, y 8.0-14.916, one 6.9 m sheet with six 24 mm mullions) open to
the roof balcony. The sheet is rebuilt as seven panes; bays 3-6 (y 9.988-13.916) become sliders in group 'eastwall':
bays 3 and 4 stack south behind bay 2, bays 5 and 6 stack north behind bay 7, each on its own track 70 mm apart on
the room side. Head and sill rails stay fixed. Opening: 3.93 m."""
import bpy,os,sys,json
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import remove_faces
from fixtures_and_lamps import take
from refine_interior_realism import export_and_save
blend=os.path.join(root,'Francis-Web.blend')
X0,X1,Z0,Z1=10.295,10.305,6.18,8.82;PITCH=.988
BAYS=[(8.0,8.976),(9.0,9.964),(9.988,10.952),(10.976,11.94),(11.964,12.928),(12.952,13.916),(13.94,14.916)]
MULL=[8.988,9.976,10.964,11.952,12.94,13.928]
# bay index -> (bays travelled, track number, mullions that ride with it)
MOVE={2:(-1,1,[MULL[1]]),3:(-2,2,[MULL[2],MULL[3]]),4:(2,2,[MULL[4]]),5:(1,1,[MULL[5]])}
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 assert not any(o.get('slideGroup')=='eastwall' for o in bpy.data.objects),'Already applied'
 glass=bpy.data.materials['pergolaglass']
 removed=sum(remove_faces(o,[((X0-.002,7.99,Z0-.002),(X1+.002,14.93,Z1+.002))]) for o in bpy.data.objects if o.type=='MESH' and o.get('floor')==2 and o.get('category')=='pergolaglass')
 assert removed>=6,removed
 made=[]
 for k,(y0,y1) in enumerate(BAYS):
  v=[(X0,y0,Z0),(X1,y0,Z0),(X1,y1,Z0),(X0,y1,Z0),(X0,y0,Z1),(X1,y0,Z1),(X1,y1,Z1),(X0,y1,Z1)]
  me=bpy.data.meshes.new(f'East wall pane {k+1}');me.from_pydata(v,[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.update()
  o=bpy.data.objects.new(f'Level 2 | east wall pane {k+1}',me);bpy.context.collection.objects.link(o);me.materials.append(glass);me.uv_layers.new(name='UVMap')
  o['category']='pergolaglass';o['finishGroup']='pergolaglass';o['floor']=2
  if k in MOVE:
   n,track,_=MOVE[k];o['slideGroup']='eastwall';o['slideLabel']='Pergola room to roof balcony';o['slideVec']=[-.07*track,n*PITCH,0];made.append(o.name)
 for k,(n,track,mulls) in MOVE.items():
  for my in mulls:
   lo=Vector((10.285,my-.014,Z0-.002));hi=Vector((10.315,my+.014,Z1+.002))
   for o in [o for o in bpy.data.objects if o.type=='MESH' and o.get('floor')==2 and o.get('category')=='pergolaframe' and not o.get('slideGroup')]:
    mats=[m.name for m in o.data.materials]
    for new in take([o],lambda ob,f,p,lo=lo,hi=hi:all(all(lo[i]<=q[i]<=hi[i] for i in range(3)) for q in p),o.data.materials[0],'pergolaframe',f'Slider | east wall mullion {my}'):
     new.data.materials.clear();[new.data.materials.append(bpy.data.materials[m]) for m in mats]
     new['slideGroup']='eastwall';new['slideLabel']='Pergola room to roof balcony';new['slideVec']=[-.07*track,n*PITCH,0];new['floor']=2;made.append(new.name)
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 export_and_save();print('EAST WALL SAVED',removed,made)
