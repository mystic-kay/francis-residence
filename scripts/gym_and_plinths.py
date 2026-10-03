"""Ground the entrance feature wall and charcoal fin (both stopped at floor level, 0.6 m above the paving), and fit
out the top-floor gym: treadmill and bench replace the grey placeholder boxes (Furniture Boxes 2321958-2321960), with
a dumbbell rack, kettlebells, exercise mat, gym ball and a wall mirror. Safe to rerun."""
import bpy,os,sys,json,math
from mathutils import Vector
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from luxury_interiors import material,remove_faces
from refine_interior_realism import export_and_save
import realism_details as rd
from exterior_stucco import world_uv
blend=os.path.join(root,'Francis-Web.blend')
F=6.15
def plinths():
 made=[]
 for name,cat,(x0,y0,x1,y1) in (('feature wall side','featurewall',(3.412,7.996,3.662,9.16)),('feature wall front','featurewall',(3.412,7.746,4.128,7.996)),('charcoal fin','accent',(6.023,7.761,6.253,9.176))):
  v=[(x0,y0,-.62),(x1,y0,-.62),(x1,y1,-.62),(x0,y1,-.62),(x0,y0,0),(x1,y0,0),(x1,y1,0),(x0,y1,0)]
  me=bpy.data.meshes.new('Plinth '+name);me.from_pydata(v,[],[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]);me.update()
  o=bpy.data.objects.new('Level -1 | grounded '+name,me);bpy.context.collection.objects.link(o);me.materials.append(bpy.data.materials[cat])
  o['category']=cat;o['finishGroup']=cat;o['floor']=-1;o['exteriorStucco']=True;o['gymPlinth']=True;world_uv(o);made.append(name)
 return made
def gym(m):
 removed=0
 for a,b in (((-.9,13.0,6.15),(-.1,14.65,6.35)),((-.9,14.5,6.35),(-.1,14.65,7.55)),((.5,13.1,6.15),(.85,14.3,6.6))):
  removed+=sum(remove_faces(o,[(a,b)]) for o in bpy.data.objects if o.type=='MESH' and o.get('floor')==2 and o.get('category') in ('details','wood','fabric','decor') and not o.get('gymPlinth'))
 B=lambda mat,lo,hi:rd.box(mat,'decor',lo,hi,'box',2)
 # Treadmill: deck, belt, motor hood, uprights, handrails and console; the runner faces +y.
 x0,x1,y0,y1=-.88,-.12,13.0,14.6
 B(m['frame'],(x0,y0,F+.05),(x1,y1-.25,F+.17));B(m['belt'],(x0+.09,y0+.04,F+.17),(x1-.09,y1-.3,F+.176))
 for x in (x0,x1-.06):B(m['frame'],(x,y0,F),(x+.06,y1-.25,F+.06))
 B(m['frame'],(x0,y1-.42,F+.05),(x1,y1-.05,F+.28))
 for x in (x0+.02,x1-.07):
  B(m['frame'],(x,y1-.2,F+.2),(x+.05,y1-.14,F+1.3));B(m['grip'],(x,y1-.75,F+.98),(x+.05,y1-.14,F+1.03))
 B(m['frame'],(x0+.02,y1-.24,F+1.22),(x1-.02,y1-.1,F+1.45));B(m['screen'],(x0+.14,y1-.245,F+1.26),(x1-.14,y1-.24,F+1.42))
 # Flat bench.
 B(m['pad'],(.5,13.15,F+.40),(.85,14.25,F+.47));B(m['frame'],(.62,13.3,F+.34),(.73,14.1,F+.40))
 for y in (13.25,14.09):B(m['frame'],(.52,y,F),(.83,y+.06,F+.05));B(m['frame'],(.645,y+.01,F+.05),(.705,y+.05,F+.34))
 # Exercise mat, rolled spare mat, gym ball and kettlebells in the open floor.
 B(m['mat'],(1.0,13.25,F),(1.6,14.65,F+.008))
 rd.cyl(m['mat2'],'decor',(1.28,13.05,F+.07),.07,.0,16,floor=2)
 seg=16;v=[(1.0+dx,13.05+.07*math.cos(2*math.pi*i/seg),F+.07+.07*math.sin(2*math.pi*i/seg)) for dx in (0,.6) for i in range(seg)]
 rd.add(m['mat2'],'decor',v,[tuple(range(seg-1,-1,-1)),tuple(range(seg,2*seg))]+[(i,(i+1)%seg,(i+1)%seg+seg,i+seg) for i in range(seg)],'box',2)
 rd.sphere(m['ball'],'decor',(-.55,12.9,F+.3),.3,2)
 for k,(x,y,r) in enumerate(((.25,14.55,.085),(.47,14.55,.1),(.7,14.56,.115))):
  rd.sphere(m['iron'],'decor',(x,y,F+r),r,2);rd.cyl(m['iron'],'decor',(x,y,F+r*1.7),.012,r*.7,10,floor=2);B(m['iron'],(x-r*.6,y-.012,F+r*2.3),(x+r*.6,y+.012,F+r*2.3+.024))
 # Dumbbell rack on the south wall: two angled shelves, five pairs.
 rx0,rx1,ry=.25,1.45,12.63
 for x in (rx0,rx1-.04):B(m['frame'],(x,ry,F),(x+.04,ry+.36,F+.78))
 for z in (F+.3,F+.62):
  B(m['frame'],(rx0,ry+.04,z),(rx1,ry+.34,z+.03))
  for k in range(5):
   cx=rx0+.14+k*.23;r=.045+.008*k if z<F+.5 else .035+.006*k
   for dy in (.1,.26):
    seg=10;c=(cx,ry+dy,z+.03+r);v=[(c[0]+dx,c[1]+r*math.cos(2*math.pi*i/seg),c[2]+r*math.sin(2*math.pi*i/seg)) for dx in (-.05,.05) for i in range(seg)]
    rd.add(m['iron'],'decor',v,[tuple(range(seg-1,-1,-1)),tuple(range(seg,2*seg))]+[(i,(i+1)%seg,(i+1)%seg+seg,i+seg) for i in range(seg)],'box',2)
   B(m['grip'],(cx-.012,ry+.1,z+.03+r-.012),(cx+.012,ry+.26,z+.03+r+.012))
 # Full-height mirror on the west wall beside the treadmill, if the wall is there.
 rd.dg=bpy.context.evaluated_depsgraph_get();h=rd.ray((-.5,13.6,F+1.3),(-1,0,0),1.2)
 if h:wx=h[0].x;B(m['mirror'],(wx+.004,13.05,F+.25),(wx+.016,14.45,F+2.15));B(m['frame'],(wx+.002,13.03,F+.23),(wx+.006,14.47,F+2.17))
 return {'placeholderFaces':removed,'mirror':bool(h)}
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 for o in [o for o in bpy.data.objects if o.get('gymPlinth')]:bpy.data.objects.remove(o,do_unlink=True)
 M=lambda n,c,r=.6,mt=0,**k:material('Decor | '+n,c,r,mt,**k)
 m={'frame':M('gym frame','#1d1f22',.45,.5),'belt':M('treadmill belt','#0f1011',.85),'grip':M('rubber grip','#2a2c2f',.9),'screen':M('monitor black','#141518',.35,.3),
  'pad':M('bench pad','#2b2622',.7),'mat':M('exercise mat','#56695a',.95),'mat2':M('exercise mat grey','#6d7378',.95),'ball':M('gym ball','#8a9aa5',.5),
  'iron':M('cast iron','#26282b',.55,.6),'mirror':M('mirror','#e9eef0',.02,1.0)}
 report={'plinths':plinths(),'gym':gym(m)}
 for (mname,cat),(v,f,meta) in rd.PARTS.items():
  me=bpy.data.meshes.new('Gym | '+mname);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new('Gym | '+mname.split('| ')[-1],me);bpy.context.collection.objects.link(o);me.materials.append(meta['mat'])
  me.uv_layers.new(name='UVMap');o['category']='decor';o['finishGroup']='decor';o['floor']=2;o['gymPlinth']=True
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 export_and_save();print('GYM SAVED',json.dumps(report))
