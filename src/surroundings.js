import * as THREE from 'three';
// The neighbourhood around the compound, built in the browser so it stays light: grass to a hazy horizon, the street
// with kerbs, verge and footpath, neighbouring stone compound walls and houses, and scattered trees and shrubs.
// Coordinates are glTF/web (x, height, z) where z = -(Blender y). Compound: x -3.86..17.14, z -21.51..3.02.
const PLOT={x0:-3.86,x1:17.14,z0:-21.51,z1:3.02},STREET={z0:3.9,z1:9.6},SITE={x0:-14,x1:27};

export function buildSurroundings({scene,ground,loadPlant,baseUrl,anisotropy,lowDetail}){
 const loader=new THREE.TextureLoader();
 const tex=(asset,type,rx,ry)=>{const t=loader.load(`${baseUrl}textures/${asset}/${type}.jpg`);t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(rx,ry);t.anisotropy=anisotropy;if(type==='color')t.colorSpace=THREE.SRGBColorSpace;return t;};
 const pbr=(asset,rx,ry,color,roughness=.95,normal=.6)=>new THREE.MeshStandardMaterial({color,roughness,map:tex(asset,'color',rx,ry),normalMap:tex(asset,'normal',rx,ry),roughnessMap:tex(asset,'roughness',rx,ry),normalScale:new THREE.Vector2(normal,normal)});
 const add=(geo,mat,x,y,z,shadow=true)=>{const m=new THREE.Mesh(geo,mat);m.position.set(x,y,z);m.receiveShadow=true;m.castShadow=shadow;m.userData.surroundings=true;scene.add(m);return m;};

 // Grass ground to the horizon; the scene fog (set by the caller) softens its edge.
 ground.geometry.dispose();ground.geometry=new THREE.PlaneGeometry(520,520);
 ground.material=pbr('grass_ground',300,300,'#8fae6c',1,.8);ground.position.y=-.64;

 // Street: asphalt beyond the modelled strip, kerbs both sides (gap at our driveway), dashed centre line.
 const asphalt=pbr('concrete_pavement',60,2.3,'#5a5c5e',.95,.4),kerb=new THREE.MeshStandardMaterial({color:'#c9c6bf',roughness:.9});
 const len=240,w=STREET.z1-STREET.z0,zc=(STREET.z0+STREET.z1)/2;
 for(const [a,b] of [[-len,SITE.x0],[SITE.x1,len]])add(new THREE.BoxGeometry(b-a,.02,w),asphalt,(a+b)/2,-.61,zc,false);
 for(const [a,b,z] of [[-len,10.6,STREET.z0-.06],[16.0,len,STREET.z0-.06],[-len,len,STREET.z1+.06]])add(new THREE.BoxGeometry(b-a,.14,.12),kerb,(a+b)/2,-.55,z);
 const paint=new THREE.MeshStandardMaterial({color:'#e8e4d8',roughness:.7});
 for(let x=-len+2;x<len;x+=6)add(new THREE.BoxGeometry(3,.005,.1),paint,x,-.585,zc,false);
 // Grass verge, then a paved footpath on the far side.
 add(new THREE.BoxGeometry(2*len,.03,1.6),pbr('concrete_pavement',160,1.1,'#d4d0c6',.9,.4),0,-.62,STREET.z1+1.6+.8,false);

 // Neighbouring compound walls across the street: Ndarugu stone in 20 m runs with dark gates and precast coping.
 const stone=(lenM)=>pbr('concrete_block_wall',lenM/2,1.2,'#c9ae80',.92,1.2);
 const coping=new THREE.MeshStandardMaterial({color:'#cfccc5',roughness:.9}),gateMat=new THREE.MeshStandardMaterial({color:'#24272a',roughness:.5,metalness:.5});
 const wallZ=STREET.z1+4.4,wallH=2.4;
 for(let x=-110;x<130;x+=24){
  add(new THREE.BoxGeometry(19.5,wallH,.22),stone(19.5),x+9.75,-.62+wallH/2,wallZ);
  add(new THREE.BoxGeometry(19.7,.06,.32),coping,x+9.75,-.62+wallH+.03,wallZ);
  add(new THREE.BoxGeometry(4.5,2.1,.08),gateMat,x+21.75,-.62+1.05,wallZ);
 }
 // Side and rear neighbour boundaries continue our wall lines out into the estate.
 const sideRuns=[[PLOT.x0-24,PLOT.z0,PLOT.x0,PLOT.z0],[PLOT.x1,PLOT.z0,PLOT.x1+24,PLOT.z0],[PLOT.x0-24,PLOT.z0,PLOT.x0-24,STREET.z0-.6],[PLOT.x1+24,PLOT.z0,PLOT.x1+24,STREET.z0-.6],
  [PLOT.x0,PLOT.z0-28,PLOT.x1,PLOT.z0-28],[PLOT.x0,PLOT.z0,PLOT.x0,PLOT.z0-28],[PLOT.x1,PLOT.z0,PLOT.x1,PLOT.z0-28]];
 for(const [ax,az,bx,bz] of sideRuns){
  const L=Math.hypot(bx-ax,bz-az),m=add(new THREE.BoxGeometry(L,wallH,.22),stone(L),(ax+bx)/2,-.62+wallH/2,(az+bz)/2);m.rotation.y=-Math.atan2(bz-az,bx-ax);
  const c=add(new THREE.BoxGeometry(L+.2,.06,.32),coping,(ax+bx)/2,-.62+wallH+.03,(az+bz)/2);c.rotation.y=m.rotation.y;
 }

 // Neighbouring houses: contemporary rendered blocks with dark window bands and parapets, partly screened by trees.
 const render=new THREE.MeshStandardMaterial({color:'#ece8df',roughness:.9}),dark=new THREE.MeshStandardMaterial({color:'#2b3035',roughness:.35,metalness:.2}),parapet=new THREE.MeshStandardMaterial({color:'#3a3b3d',roughness:.8});
 const houses=[[-22,24,11,8,7.2,'z'],[6,26,13,9,9.6,'z'],[33,24,10,8,6.6,'z'],[-21,-9,8,11,6.6,'x'],[32,-9,8,11,6.6,'x'],[6,-40,14,9,9.6,'z']];
 const footprints=[];
 for(const [x,z,wx,wz,h,face] of houses){
  add(new THREE.BoxGeometry(wx,h,wz),render,x,-.62+h/2,z);
  add(new THREE.BoxGeometry(wx+.3,.35,wz+.3),parapet,x,-.62+h+.17,z);
  const floors=Math.round(h/3.1);
  for(let f=0;f<floors;f++){const y=-.62+1.6+f*3.1;
   if(face==='z'){for(const s of [-1,1])add(new THREE.BoxGeometry(wx*.7,1.4,.06),dark,x,y,z+s*(wz/2+.02),false);}
   else{for(const s of [-1,1])add(new THREE.BoxGeometry(.06,1.4,wz*.7),dark,x+s*(wx/2+.02),y,z,false);}
  }
  footprints.push([x-wx/2-2,x+wx/2+2,z-wz/2-2,z+wz/2+2]);
 }

 // Trees and shrubs: a deterministic scatter outside the compound, off the street, footpath and houses,
 // plus a street-tree avenue on the far verge and planting hugging the outside of our boundary walls.
 let seed=97;const rnd=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/4294967296);
 const blocked=(x,z,pad=0)=>(x>PLOT.x0-2-pad&&x<PLOT.x1+2+pad&&z>PLOT.z0-2-pad&&z<PLOT.z1+2+pad)||(z>STREET.z0-1.2&&z<STREET.z1+3.6)||Math.abs(z-wallZ)<1.4||footprints.some(([a,b,c,d])=>x>a&&x<b&&z>c&&z<d);
 const trees=[],shrubs=[],step=lowDetail?13:9;
 for(let x=-70;x<=80;x+=step)for(let z=-75;z<=48;z+=step){
  const jx=x+(rnd()-.5)*step*.8,jz=z+(rnd()-.5)*step*.8;
  if(blocked(jx,jz,1)||rnd()<.35)continue;trees.push([jx,jz,.75+rnd()*.6]);
 }
 for(let x=-60;x<=70;x+=lowDetail?20:12)trees.push([x+rnd()*2,STREET.z1+2.6,.8+rnd()*.3]);
 for(let i=0;i<(lowDetail?60:140);i++){const x=-55+rnd()*130,z=-65+rnd()*105;if(!blocked(x,z))shrubs.push([x,z,.7+rnd()*.8]);}
 for(let z=PLOT.z0+1;z<PLOT.z1-1;z+=2.2){shrubs.push([PLOT.x0-.9,z,.9+rnd()*.4]);shrubs.push([PLOT.x1+.9,z,.9+rnd()*.4]);}
 for(let x=PLOT.x0+1;x<PLOT.x1-1;x+=2.2)shrubs.push([x,PLOT.z0-.9,.9+rnd()*.4]);
 loadPlant('tree_small_02',trees,6.2,{shadowRadius:40});
 loadPlant('shrub_01',shrubs,1.1,{shadowRadius:30});
 return {trees:trees.length,shrubs:shrubs.length,houses:houses.length};
}
