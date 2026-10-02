import bpy,os
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for asset in ['tree_small_02','shrub_01']:
 bpy.ops.wm.open_mainfile(filepath=os.path.join(root,'assets',asset,asset+'.blend'))
 print('ASSET',asset)
 for o in bpy.context.scene.objects:print(o.name,o.type,'hide',o.hide_render,o.hide_viewport,o.hide_get(),'size',list(o.dimensions),'polys',len(o.data.polygons) if o.type=='MESH' else 0,'collections',[(c.name,c.hide_render,c.hide_viewport) for c in o.users_collection])
