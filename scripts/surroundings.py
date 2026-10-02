"""Surroundings: the grey site sheet outside the compound becomes lawn (same grass finish as the garden) and the
paving strip in front of the gate becomes an asphalt street ('road' group). The website adds the wider landscape."""
import bpy,os,sys,json
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)));sys.path.insert(0,os.path.join(root,'scripts'))
from refine_interior_realism import export_and_save,pack_surface
from exterior_stucco import split_exterior,world_uv
from luxury_interiors import material
blend=os.path.join(root,'Francis-Web.blend')
if __name__=='__main__':
 bpy.ops.wm.open_mainfile(filepath=blend);opened=os.path.getmtime(blend)
 assert not any(o.get('surroundings') for o in bpy.data.objects),'Already applied'
 cfg=json.load(open(os.path.join(root,'scripts','reference-materials.json')))
 for cat in ['lawn','road']:pack_surface(cat,cfg)
 site=bpy.data.objects['Level 0 | site'];site.data.materials.clear();site.data.materials.append(bpy.data.materials['lawn'])
 site['category']='lawn';site['finishGroup']='lawn';site['surroundings']=True;world_uv(site)
 pav=bpy.data.objects['Level 0 | paving'];mw=pav.matrix_world
 idx=[f.index for f in pav.data.polygons if all((mw@pav.data.vertices[v].co).y<-3.2 for v in f.vertices)]
 road=split_exterior(pav,idx,bpy.data.materials['road']);road.name='Level 0 | street';road['category']='road';road['finishGroup']='road';road['surroundings']=True;world_uv(road)
 assert os.path.getmtime(blend)==opened,'Francis-Web.blend changed while this script ran; rerun it'
 export_and_save();print('SURROUNDINGS SAVED site faces',len(site.data.polygons),'road faces',len(idx))
