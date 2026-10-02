import urllib.request,json,pathlib,concurrent.futures,io,zipfile
root=pathlib.Path(__file__).resolve().parent.parent
req=lambda url: urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'FrancisResidence/1.0'}),timeout=90)
assets=['curly_teddy_natural','cotton_jersey','oak_veneer_01','marble_01','plastered_wall','white_stucco','interior_tiles','concrete_block_wall','sandstone_blocks_08','granite_wall','rough_block_wall','denim_fabric','sofa_02','chinese_armchair','oak_wood_planks','concrete_pavement','grass_ground','tree_small_02','shrub_01']
def download(asset):
 data=json.load(req('https://api.polyhaven.com/files/'+asset))
 dest=root/'public'/'textures'/asset;dest.mkdir(parents=True,exist_ok=True)
 entries=[]
 if asset in ['sofa_02','chinese_armchair','tree_small_02','shrub_01']:
  info=data['blend']['1k']['blend']; path=root/'assets'/asset;path.mkdir(parents=True,exist_ok=True)
  blend=path/(asset+'.blend')
  if not blend.exists():blend.write_bytes(req(info['url']).read())
  for filename,item in info.get('include',{}).items():
   out=path/filename;out.parent.mkdir(parents=True,exist_ok=True)
   if not out.exists():out.write_bytes(req(item['url']).read())
 else:
  for key,filename in [('Diffuse','color.jpg'),('nor_gl','normal.jpg'),('Rough','roughness.jpg')]:
   if key not in data:raise RuntimeError(asset+' missing '+key)
   info=data[key]['1k']['jpg'];(dest/filename).write_bytes(req(info['url']).read())
 entries.append({'id':asset,'source':'https://polyhaven.com/a/'+asset,'license':'CC0'})
 print('Downloaded',asset,flush=True)
 return entries
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 entries=[e for result in pool.map(download,assets) for e in result]
archive=zipfile.ZipFile(io.BytesIO(req('https://ambientcg.com/get?file=Marble012_1K-JPG.zip').read()))
white=root/'public'/'textures'/'Marble012';white.mkdir(parents=True,exist_ok=True)
for suffix,name in [('Color.jpg','color.jpg'),('NormalGL.jpg','normal.jpg'),('Roughness.jpg','roughness.jpg')]:
 white.joinpath(name).write_bytes(archive.read(next(n for n in archive.namelist() if n.endswith(suffix))))
entries.append({'id':'Marble012','source':'https://ambientcg.com/a/Marble012','license':'CC0'})
(root/'public'/'asset-credits.json').write_text(json.dumps(entries,indent=2))
