"""Turn dark scanned stone colour maps into light, mostly neutral albedo so the website can tint them to any
Kenyan stone (Ndarugu sand, Nairobi blue, Juja). Keeps 30% of the original hue and all of the tonal detail."""
import bpy,os,numpy as np
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for asset in ['interior_tiles','concrete_block_wall','sandstone_blocks_08','granite_wall','rough_block_wall']:
 path=os.path.join(root,'public','textures',asset,'color.jpg');marker=path+'.normalized'
 if os.path.exists(marker):continue
 img=bpy.data.images.load(path);px=np.array(img.pixels[:],dtype=np.float32).reshape(-1,4)
 rgb=px[:,:3];lum=rgb@np.array([.2126,.7152,.0722],dtype=np.float32)
 mixed=lum[:,None]*.7+rgb*.3
 # Lift the mean to 0.78 while stretching contrast slightly so joints and split faces stay legible.
 mean=float(mixed.mean());out=np.clip(.78+(mixed-mean)*min((.78/mean)*1.15,1.6),0,1)
 px[:,:3]=out;img.pixels[:]=px.ravel();img.file_format='JPEG';img.filepath_raw=path;bpy.context.scene.render.image_settings.quality=92;img.save()
 open(marker,'w').write('albedo normalised for tinting\n');print('NORMALISED',asset,round(mean,3))
