import './style.css';
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {PointerLockControls} from 'three/addons/controls/PointerLockControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RectAreaLightUniformsLib} from 'three/addons/lights/RectAreaLightUniformsLib.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {finishes,options,defaultDesign,validateDesign,rooms,groupLabels,palettes,applyPalette} from './design.js';
import {createHomeControls} from './home-controls.js';
import {buildSurroundings} from './surroundings.js';
import {createCinematicTour} from './tour.js';
import {createMaterialPicker} from './material-picker.js';
import {createConstruction} from './construction.js';
import {createSliders} from './sliders.js';
import {createEnvironment,sunPosition,hourOf,formatHour} from './environment.js';
const initialDetail=new URLSearchParams(location.search).get('detail')||(matchMedia('(max-width:700px)').matches?'low':'balanced');
const $=id=>document.getElementById(id),canvas=$('scene');
let renderer;
try{renderer=new THREE.WebGLRenderer({canvas,antialias:true});}catch(e){$('load-progress').textContent='WebGL is unavailable. Please open this page in a browser with hardware acceleration enabled.';throw e;}
renderer.setPixelRatio(initialDetail==='low'?.75:Math.min(devicePixelRatio,initialDetail==='high'?2:1.25));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.2;renderer.shadowMap.enabled=true;renderer.shadowMap.autoUpdate=false;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.localClippingEnabled=true;
const scene=new THREE.Scene();scene.background=new THREE.Color('#dce2df');
const camera=new THREE.PerspectiveCamera(55,1,.05,420);camera.position.set(24,16,8);
const orbit=new OrbitControls(camera,canvas);orbit.target.set(5,3,-13);orbit.enableDamping=true;orbit.minDistance=.5;orbit.maxDistance=90;orbit.maxPolarAngle=Math.PI*.49;
const walk=new PointerLockControls(camera,canvas);
const pmrem=new THREE.PMREMGenerator(renderer),roomEnvironment=new RoomEnvironment(),environment=pmrem.fromScene(roomEnvironment,.04);scene.environment=environment.texture;scene.environmentIntensity=.6;roomEnvironment.dispose();pmrem.dispose();
const ambient=new THREE.HemisphereLight(0xe9f1ff,0xb9ac91,2.3);scene.add(ambient);
const sun=new THREE.DirectionalLight(0xfff1db,3.2);sun.position.set(-12,25,8);sun.target.position.set(5,0,-13);sun.castShadow=true;sun.shadow.mapSize.set(initialDetail==='low'?512:initialDetail==='high'?2048:1024,initialDetail==='low'?512:initialDetail==='high'?2048:1024);Object.assign(sun.shadow.camera,{left:-28,right:28,top:28,bottom:-28,near:.5,far:80});sun.shadow.bias=-.0004;sun.shadow.normalBias=.03;scene.add(sun,sun.target);
RectAreaLightUniformsLib.init();
const practicalLights=[];
const consoleGlow=new THREE.RectAreaLight(0xffdbac,3.2,2.8,.10);consoleGlow.position.set(6.70,.30,-11.30);consoleGlow.lookAt(8.2,.08,-11.30);scene.add(consoleGlow);practicalLights.push(consoleGlow);
const readingLight=new THREE.PointLight(0xffdfb4,3.0,3.2,2);readingLight.position.set(9.88,1.53,-12.98);scene.add(readingLight);practicalLights.push(readingLight);
const artWash=new THREE.RectAreaLight(0xffe4bd,2.4,1.0,.08);artWash.position.set(10.04,2.32,-11.25);artWash.lookAt(10.32,1.74,-11.25);scene.add(artWash);practicalLights.push(artWash);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(150,150),new THREE.MeshStandardMaterial({color:0x938b70,roughness:1}));ground.rotation.x=-Math.PI/2;ground.position.set(5,-.65,-12);ground.receiveShadow=true;scene.add(ground);
let model=null,mode='orbit',activeRoom='exterior',tourTimer=null,design=defaultDesign(),saveTimer;
const loadErrors=[];
const meshes=[],colliders=[],groupMaterials={},textures={},keys=new Set();
const homeControls=createHomeControls({scene,camera,canvas,renderer,meshes,toast:(...a)=>toast(...a),getMode:()=>mode,onChange:()=>updateAtmosphere(),baseUrl:import.meta.env.BASE_URL,lowDetail:initialDetail==='low'});
const surroundingsLife=createEnvironment({scene,meshes,lowDetail:initialDetail==='low'});
const sliders=createSliders({meshes,camera,canvas,getMode:()=>mode,toast:(...a)=>toast(...a),renderer});
// Visual material picking: hotspots, hover highlight and an in-place swatch pop-up.
const highlightGroup=(group,on)=>{for(const m of groupMaterials[group]||[]){if(!m.emissive)continue;if(on){if(m.userData.hl!==undefined)continue;m.userData.hl=m.emissive.getHex();m.userData.hlI=m.emissiveIntensity;m.emissive.set('#5a4220');m.emissiveIntensity=1;}else if(m.userData.hl!==undefined){m.emissive.setHex(m.userData.hl);m.emissiveIntensity=m.userData.hlI;delete m.userData.hl;}}};
const picker=createMaterialPicker({container:canvas.parentElement,canvas,camera,meshes,finishes,options,groupLabels,getDesign:()=>design,baseUrl:import.meta.env.BASE_URL,highlight:highlightGroup,
 isEnabled:()=>mode==='orbit'&&!cinematic.active&&!construction?.active,
 setFinish:(group,id)=>{const f=finishes[id];design[group]={finish:id,color:f.color,roughness:f.roughness};apply(group);persist();if($('surface').value===group)updateSwatches();toast(`${groupLabels[group]}: ${f.name}`);},
 openAdvanced:group=>{$('surface').value=group;tab('materials');updateSwatches();}});
try{const saved=localStorage.getItem('francis-design-v2');if(saved)design=validateDesign(JSON.parse(saved));if(!localStorage.getItem('francis-interior-refinement-v1')){const base=defaultDesign();for(const [group,old] of [['floor','marble'],['tvwall','creamstone'],['livingfabric','taupefabric']])if(design[group].finish===old&&design[group].color===finishes[old].color&&design[group].roughness===finishes[old].roughness)design[group]=base[group];localStorage.setItem('francis-design-v2',JSON.stringify(design));localStorage.setItem('francis-interior-refinement-v1','1');}if(!localStorage.getItem('francis-stucco-v1')){for(const group of ['accent','featurewall'])if(design[group].finish==='charcoal')design[group]=defaultDesign()[group];localStorage.setItem('francis-design-v2',JSON.stringify(design));localStorage.setItem('francis-stucco-v1','1');}}catch{}
const texLoader=new THREE.TextureLoader();
function wovenTexture(type){
 const canvas=document.createElement('canvas');canvas.width=canvas.height=128;const ctx=canvas.getContext('2d'),data=ctx.createImageData(128,128);let seed=37;
 for(let y=0;y<128;y++)for(let x=0;x<128;x++){const i=(y*128+x)*4;seed=(Math.imul(seed,1664525)+1013904223)>>>0;const noise=(seed/4294967296-.5)*5,wx=Math.sin(x*Math.PI/2),wy=Math.cos(y*Math.PI/2);let rgb;
 if(type==='normal')rgb=[128+wx*12,128+wy*12,253];else{const c=(type==='color'?240:230)+wx*5+wy*5+noise;rgb=[c,c,c];}data.data.set([...rgb,255],i);}
 ctx.putImageData(data,0,0);return new THREE.CanvasTexture(canvas);
}
function texture(asset,type,scale){const key=`${asset}/${type}/${scale}`;if(!textures[key]){const t=asset==='woven'?wovenTexture(type):texLoader.load(`${import.meta.env.BASE_URL}textures/${asset}/${type}.jpg`,undefined,undefined,()=>{loadErrors.push(asset+'/'+type);toast('A texture could not load. Refresh to retry.');});t.wrapS=t.wrapT=THREE.RepeatWrapping;t.repeat.set(scale,scale);t.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());if(type==='color')t.colorSpace=THREE.SRGBColorSpace;textures[key]=t;}return textures[key];}
function apply(group){const cfg=design[group],f=finishes[cfg.finish];for(const m of groupMaterials[group]||[]){m.color.set(cfg.color);m.roughness=cfg.roughness;m.metalness=f.metalness||0;if('clearcoat' in m){m.clearcoat=f.clearcoat||0;m.clearcoatRoughness=.14;}if('sheen' in m){m.sheen=['livingfabric','livingpillows'].includes(group)?.18:0;m.sheenColor.set(cfg.color);m.sheenRoughness=.85;}if(f.opacity!==undefined){m.transparent=true;m.opacity=f.opacity;m.depthWrite=false;if('transmission' in m)m.transmission=0;m.userData.finishTransparent=true;}else if(m.userData.finishTransparent){m.transparent=false;m.opacity=1;m.depthWrite=true;m.userData.finishTransparent=false;}m.map=f.texture?texture(f.texture,'color',f.scale):null;m.normalMap=f.texture?texture(f.texture,'normal',f.scale):null;m.roughnessMap=f.texture?texture(f.texture,'roughness',f.scale):null;const bump=f.normal??(['livingfabric','livingpillows'].includes(group)?.16:.3);m.normalScale.set(bump,bump);m.needsUpdate=true;}}
function persist(){try{localStorage.setItem('francis-design-v2',JSON.stringify(design));}catch{toast('Browser storage is unavailable; download your schedule to save.');}}
new GLTFLoader().load(`${import.meta.env.BASE_URL}models/francis.glb`,gltf=>{
 model=gltf.scene;scene.add(model);
 model.traverse(o=>{if(!o.isMesh)return;meshes.push(o);o.castShadow=true;o.receiveShadow=true;const category=o.userData.category||o.material.name;o.userData.category=category;if(['glass','pergolaglass','balconyglass'].includes(category))o.castShadow=false;
 const materials=Array.isArray(o.material)?o.material:[o.material];
 for(const original of materials){const m=original.clone();m.side=THREE.DoubleSide;if(category==='glass'){if('transmission' in m)m.transmission=0;m.transparent=true;m.opacity=.23;m.depthWrite=false;m.roughness=.1;}if(category==='metal'){m.color.set('#222429');m.metalness=.7;m.roughness=.4;}if(design[category]){groupMaterials[category]??=[];groupMaterials[category].push(m);}if(Array.isArray(o.material)){o.material=o.material.map(v=>v===original?m:v);}else o.material=m;}
 if(['walls','floor','bedfloor','doors','wood','fabric','headboard','ceramic','cabinet','counter','bedwall','featurewall','balconyglass','livingfabric','tvunit','coffeetop','livingfloor','diningfabric','diningwood','render','steps','porch','stairs'].includes(category))colliders.push(o);
 });
 for(const g of Object.keys(design))apply(g);
 picker.attach();picker.maybeGuide();sliders.attach();surroundingsLife.attach();updateAtmosphere();
 homeControls.ready.then(cfg=>{homeControls.attach(cfg);updateAtmosphere();}).catch(()=>toast('Lighting controls could not load.'));
 const requestedRoom=rooms.find(r=>r.id===new URLSearchParams(location.search).get('room'));if(requestedRoom)goRoom(requestedRoom);
 $('loading').hidden=true;updateVisibility();$('stats').textContent=`${meshes.length} optimized meshes · Model scale: metres`;window.__francis={ready:true,pick:(x,y)=>{const r=canvas.getBoundingClientRect();pointer.set((x-r.left)/r.width*2-1,-(y-r.top)/r.height*2+1);ray.setFromCamera(pointer,camera);const h=ray.intersectObjects(meshes,false).find(h=>h.object.visible);return h?{name:h.object.name,category:h.object.userData.category,point:h.point.toArray().map(v=>+v.toFixed(3))}:null;},setView:(p,t)=>{if(mode==='walk')exitWalk();camera.position.fromArray(p);orbit.target.fromArray(t);camera.lookAt(orbit.target);},loadErrors,landscapeLoaded,meshCount:meshes.length,getDesign:()=>structuredClone(design),getSurfaceGeometry:group=>meshes.filter(o=>o.userData.category===group).map(o=>{const box=new THREE.Box3().setFromObject(o);return {name:o.name,floor:o.userData.floor,min:box.min.toArray(),max:box.max.toArray()};}),getSurfaceMaterials:group=>(groupMaterials[group]||[]).map(m=>({color:m.color.getHexString(),opacity:m.opacity,transparent:m.transparent,transmission:m.transmission||0,roughness:m.roughness,clearcoat:m.clearcoat||0})),getMode:()=>mode,getPosition:()=>camera.position.toArray(),getRoom:()=>activeRoom,pauseRendering:()=>renderer.setAnimationLoop(null),render:()=>{orbit.update();renderer.render(scene,camera);}};
},xhr=>{if(xhr.total)$('load-progress').textContent=`Loading architectural model · ${Math.round(xhr.loaded/xhr.total*100)}%`;},error=>{$('load-progress').textContent='The model could not load. Refresh or check that models/francis.glb was included in your deployment.';console.error(error);});
// Shared geometry and materials keep repeated planting inexpensive.
let landscapeLoaded=0;
function loadPlant(asset,placements,height,{shadowRadius=Infinity}={}){
 new GLTFLoader().load(`${import.meta.env.BASE_URL}models/${asset}.glb`,gltf=>{
  const box=new THREE.Box3().setFromObject(gltf.scene),size=box.getSize(new THREE.Vector3()),center=box.getCenter(new THREE.Vector3()),scale=height/size.y;
  gltf.scene.position.set(-center.x,-box.min.y,-center.z);
  for(const [x,z,variation] of placements){const plant=new THREE.Group(),copy=gltf.scene.clone(true);plant.add(copy);plant.scale.setScalar(scale*(variation||1));plant.position.set(x,-.59,z);plant.rotation.y=x*.41;plant.userData.plant=true;copy.traverse(o=>{if(o.isMesh){o.castShadow=initialDetail!=='low'&&Math.hypot(x-5,z+12)<shadowRadius;o.receiveShadow=true;const mats=Array.isArray(o.material)?o.material:[o.material];for(const m of mats){m.side=THREE.DoubleSide;if(m.transparent||m.alphaMap){m.alphaTest=.45;m.transparent=false;m.depthWrite=true;}}}});scene.add(plant);}
  renderer.shadowMap.needsUpdate=true;landscapeLoaded++;if(window.__francis)window.__francis.landscapeLoaded=landscapeLoaded;
 },undefined,()=>toast('Some planting could not load. The residence is still available.'));
}
loadPlant('tree_small_02',[[-5,-5,1],[19,-5,.9],[-5,-22,1.1],[19,-22,1]],6.5);
// Shrubs sit in the lawn: a bed along the south boundary wall and two near the lawn's house edge (glTF x, -y).
loadPlant('shrub_01',[[2.0,2.0,.9],[3.6,2.05,.75],[5.2,2.0,1],[6.8,2.05,.8],[8.4,2.0,.9],[2.6,-4.6,.8],[4.6,-4.6,.9]],.9);
scene.fog=new THREE.Fog(scene.background.getHex(),70,260);
buildSurroundings({scene,ground,loadPlant,baseUrl:import.meta.env.BASE_URL,anisotropy:Math.min(8,renderer.capabilities.getMaxAnisotropy()),lowDetail:initialDetail==='low'});
function toast(message){$('toast').textContent=message;$('toast').classList.add('show');clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').classList.remove('show'),4000);}
function tab(which){for(const type of ['spaces','materials','lighting']){$(`${type}-panel`).hidden=which!==type;$(`${type}-tab`).classList.toggle('active',which===type);$(`${type}-tab`).setAttribute('aria-selected',String(which===type));}}
$('spaces-tab').onclick=()=>tab('spaces');$('materials-tab').onclick=()=>tab('materials');$('lighting-tab').onclick=()=>tab('lighting');
function updateSwatches(){const group=$('surface').value,cfg=design[group];$('swatches').replaceChildren();for(const id of options[group]){const f=finishes[id],b=document.createElement('button');b.className='swatch'+(cfg.finish===id?' active':'');b.setAttribute('aria-pressed',String(cfg.finish===id));const preview=document.createElement('span');preview.className='swatch-preview';preview.style.backgroundColor=f.color;if(f.texture==='woven')preview.style.backgroundImage='repeating-linear-gradient(90deg, transparent 0 2px, #ffffff22 2px 3px)';else if(f.texture)preview.style.backgroundImage=`url('${import.meta.env.BASE_URL}textures/${f.texture}/color.jpg')`;const label=document.createElement('strong');label.textContent=f.name;b.append(preview,label);b.onclick=()=>{design[group]={finish:id,color:f.color,roughness:f.roughness};apply(group);persist();updateSwatches();};$('swatches').append(b);}$('roughness').value=cfg.roughness;$('tint').value=cfg.color;$('finish-detail').textContent=`${finishes[cfg.finish].name} · ${group} · ${finishes[cfg.finish].texture?'PBR color, normal & roughness maps':'Solid finish'}`;}
$('surface').replaceChildren(...Object.keys(groupLabels).map(key=>{const opt=document.createElement('option');opt.value=key;opt.textContent=groupLabels[key];return opt;}));
$('surface').onchange=updateSwatches;
for(const [id,palette] of Object.entries(palettes)){const option=document.createElement('option');option.value=id;option.textContent=palette.name;$('palette').append(option);}
$('apply-palette').onclick=()=>{design=applyPalette(design,$('palette').value);for(const g of Object.keys(design))apply(g);persist();updateSwatches();toast(palettes[$('palette').value].name+' applied.');};
$('roughness').oninput=()=>{const group=$('surface').value;design[group].roughness=Number($('roughness').value);apply(group);persist();};
$('tint').oninput=()=>{const group=$('surface').value;design[group].color=$('tint').value;apply(group);persist();};
$('restore').onclick=()=>{design=defaultDesign();for(const g of Object.keys(design))apply(g);persist();updateSwatches();toast('Reference palette restored.');};updateSwatches();
function stopTour(){clearInterval(tourTimer);tourTimer=null;$('tour').classList.remove('active');$('tour').textContent='▶ Watch the walkthrough';}
function exitWalk(){if(walk.isLocked)walk.unlock();mode='orbit';orbit.enabled=true;$('walk').classList.remove('active');$('orbit').classList.add('active');$('reticle').hidden=true;$('walk-hint').hidden=true;$('touch-controls').hidden=true;keys.clear();orbit.target.copy(camera.position).add(camera.getWorldDirection(new THREE.Vector3()).multiplyScalar(3));}
walk.addEventListener('unlock',exitWalk);
function goRoom(room,keepTour=false){if(cinematic.active)cinematic.stop();if(construction.active)construction.stop();if(!keepTour)stopTour();if(mode==='walk')exitWalk();activeRoom=room.id;document.querySelector('.scene-heading').classList.toggle('interior',room.id!=='exterior');camera.position.fromArray(room.position);orbit.target.fromArray(room.target);camera.lookAt(orbit.target);$('level').value=String(room.level);$('location').textContent=`${room.name} · ${room.subtitle}`;$('cutaway').checked=false;updateVisibility();updateAtmosphere();renderRooms();}
function renderRooms(){const level=$('level').value;$('rooms').replaceChildren();for(const room of rooms.filter(r=>level==='all'||String(r.level)===level)){const button=document.createElement('button');button.className='room'+(activeRoom===room.id?' active':'');button.setAttribute('aria-label',`Visit ${room.name}`);const wrap=document.createElement('span'),title=document.createElement('strong'),small=document.createElement('small'),arrow=document.createElement('span');title.textContent=room.name;small.textContent=room.subtitle;arrow.textContent='↗';wrap.append(title,small);button.append(wrap,arrow);button.onclick=()=>goRoom(room);$('rooms').append(button);}}
const clip=new THREE.Plane(new THREE.Vector3(0,-1,0),3);
function updateVisibility(){if(!model)return;renderer.shadowMap.needsUpdate=true;const level=$('level').value,cut=$('cutaway').checked;
 const top=level==='all'?6.1:[3.0,6.1,9.1][Number(level)];clip.constant=top;
 for(const o of meshes){const cat=o.userData.category,fl=o.userData.floor??-1;
 // In orbit, removing floors above reveals selected level; in walk keep complete envelope.
 o.visible=mode==='walk'||level==='all'||fl===-1||fl<=Number(level);
 if(cut&&cat==='ceiling')o.visible=false;if((cat==='doors'||o.userData.doorLeaf)&&$('doorways').checked)o.visible=false;
 for(const mat of Array.isArray(o.material)?o.material:[o.material])mat.clippingPlanes=cut?[clip]:[];
 }}
$('level').onchange=()=>{stopTour();renderRooms();const level=$('level').value;const room=rooms.find(r=>String(r.level)===level);if(room){camera.position.set(24,16,8);orbit.target.set(5,Number(level)*3.15+1,-13);activeRoom='';$('location').textContent=level==='all'?'Entire residence':$('level').selectedOptions[0].textContent;}$('cutaway').checked=level!=='all';updateVisibility();updateAtmosphere();};$('cutaway').onchange=updateVisibility;$('doorways').onchange=updateVisibility;renderRooms();
$('reset-view').onclick=()=>goRoom(rooms[0]);$('orbit').onclick=()=>{stopTour();if(mode==='walk')exitWalk();updateVisibility();};
const touch=matchMedia('(pointer:coarse)').matches;
$('walk').onclick=()=>{if(!model)return;stopTour();if(!rooms.some(r=>r.id===activeRoom&&r.level!=='all'))goRoom(rooms.find(r=>r.id==='living'));mode='walk';orbit.enabled=false;const room=rooms.find(r=>r.id===activeRoom);if(room&&Number.isInteger(room.level))camera.position.y=room.level*3.15+1.65;camera.lookAt(orbit.target);$('walk').classList.add('active');$('orbit').classList.remove('active');$('reticle').hidden=false;$('walk-hint').hidden=false;$('cutaway').checked=false;updateVisibility();if(touch)$('touch-controls').hidden=false;else{canvas.focus();try{walk.lock();}catch{exitWalk();toast('Mouse capture is unavailable in this browser.');}}};
canvas.addEventListener('pointerlockerror',()=>{exitWalk();toast('Mouse capture was blocked. Open the walkthrough directly in your browser.');});
$('tour').onclick=()=>{if(tourTimer){stopTour();return;}if(mode==='walk')exitWalk();let i=0;goRoom(rooms[i],true);$('tour').classList.add('active');$('tour').textContent='Ⅱ Pause tour';tourTimer=setInterval(()=>{i=(i+1)%rooms.length;goRoom(rooms[i],true);},6500);};
// The tour button plays the cinematic walkthrough (gate, every room with a 360 turn, stairs, terrace).
const cinematic=createCinematicTour({camera,container:canvas.parentElement,onEvent:(id,open)=>sliders.set(id,open),baseUrl:import.meta.env.BASE_URL,toast,openGate:()=>{if(!homeControls.gateOpen)homeControls.setGate(true);},
 onStart:()=>{stopTour();if(mode==='walk')exitWalk();orbit.enabled=false;sliders.setAll(false);$('level').value='all';$('cutaway').checked=false;$('doorways').checked=true;activeRoom='tour';updateVisibility();updateAtmosphere();$('tour').classList.add('active');},
 onStop:()=>{orbit.enabled=true;$('doorways').checked=false;sliders.setAll(false);updateVisibility();orbit.target.copy(camera.position).add(camera.getWorldDirection(new THREE.Vector3()).multiplyScalar(3));$('tour').classList.remove('active');}});
$('tour').onclick=()=>{if(construction.active)construction.stop();cinematic.active?cinematic.stop():cinematic.start();};
// 4D construction simulation: exterior orbit view, full model, no cutaway; restores everything on exit.
const construction=createConstruction({container:canvas.parentElement,scene,meshes,renderer,orbit,
 onStart:()=>{if(cinematic.active)cinematic.stop();stopTour();if(mode==='walk')exitWalk();picker.close();$('level').value='all';$('cutaway').checked=false;$('doorways').checked=false;activeRoom='exterior';
  camera.position.set(25,9.5,7);orbit.target.set(5,1.6,-13);orbit.enabled=true;updateAtmosphere();$('build').classList.add('active');},
 onStop:()=>{for(const g of Object.keys(design))apply(g);updateVisibility();updateAtmosphere();$('build').classList.remove('active');}});
$('build').onclick=()=>construction.active?construction.stop():construction.start();
$('hints').classList.toggle('active',picker.hints);$('hints').onclick=()=>{picker.setHints(!picker.hints);$('hints').classList.toggle('active',picker.hints);toast(picker.hints?'Hints on: tap a glowing dot to restyle it.':'Hints hidden.');};
$('detail').value=['low','balanced','high'].includes(initialDetail)?initialDetail:'balanced';
$('detail').onchange=()=>{const value=$('detail').value;renderer.setPixelRatio(value==='low'?.75:Math.min(devicePixelRatio,value==='high'?2:1.25));const size=value==='low'?512:value==='high'?2048:1024;sun.shadow.mapSize.set(size,size);if(sun.shadow.map){sun.shadow.map.dispose();sun.shadow.map=null;}scene.traverse(o=>{if(o.userData.plant)o.traverse(mesh=>{if(mesh.isMesh)mesh.castShadow=value!=='low';});});renderer.shadowMap.needsUpdate=true;};
function updateAtmosphere(){const t=Number($('daylight').value),interior=['living','tvwall','seating','chairs','gallery','kitchen','dining','guest','primary','bed1','bed2'].includes(activeRoom);const hour=hourOf(t),sp=sunPosition(hour,$('season').value),up=THREE.MathUtils.smoothstep(sp.alt,-.05,.25);sun.position.copy(sun.target.position).addScaledVector(sp.dir.clone().setY(Math.max(.06,sp.dir.y)).normalize(),40);sun.color.set('#ff9a52').lerp(new THREE.Color('#fff1db'),up);sun.intensity=(.25+t*2.95)*(.15+.85*THREE.MathUtils.smoothstep(sp.alt,-.08,.12));$('daylight-time').textContent=formatHour(hour);surroundingsLife.setLighting(THREE.MathUtils.clamp((.42-t)/.3,0,1),homeControls.zones.size?homeControls.levelOf('exterior'):1);ambient.intensity=interior?.58+t*.74:.85+t*1.45;scene.environmentIntensity=interior?.42:.6;scene.background.set(t<.35?'#475970':'#dce2df').lerp(new THREE.Color('#e7c39b'),t>=.35?Math.max(0,1-THREE.MathUtils.smoothstep(sp.alt,.02,.3))*.6:0);scene.fog.color.copy(scene.background);document.body.classList.toggle('night',t<.35);renderer.toneMappingExposure=interior?.86+t*.12:.95+t*.25;const strength=Number($('interior-light').value);practicalLights.forEach((light,i)=>{light.intensity=[3.2,3.0,2.4][i]*strength*(homeControls.zones.size?homeControls.levelOf('living'):1);light.visible=$('level').value==='all'||Number($('level').value)===0;});if(homeControls.zones.size)homeControls.apply(strength);else for(const o of meshes)if(o.userData.category==='interiorlight')for(const m of Array.isArray(o.material)?o.material:[o.material])m.emissiveIntensity=3*strength;}
$('daylight').oninput=updateAtmosphere;$('season').onchange=updateAtmosphere;$('interior-light').oninput=updateAtmosphere;
$('help').onclick=()=>{if(mode==='walk')exitWalk();$('help-dialog').showModal();};
function download(blob,name){const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
$('export').onclick=()=>{const schedule={project:'Francis Residence',version:2,status:'Reference-inspired finishes; manufacturer products and measured material properties unverified',createdAt:new Date().toISOString(),selections:design,materials:Object.entries(design).map(([surface,cfg])=>({surface,...cfg,name:finishes[cfg.finish].name,texture:finishes[cfg.finish].texture||null}))};download(new Blob([JSON.stringify(schedule,null,2)],{type:'application/json'}),'francis-finish-schedule.json');toast('Finish schedule downloaded.');};
$('capture').onclick=()=>{renderer.render(scene,camera);canvas.toBlob(blob=>{if(blob)download(blob,'francis-residence.png');});};
$('import').onclick=()=>$('import-file').click();$('import-file').onchange=async()=>{const file=$('import-file').files[0];if(!file)return;try{if(file.size>100000)throw new Error('Schedule is too large');const data=JSON.parse(await file.text());design=validateDesign(data.selections);for(const g of Object.keys(design))apply(g);persist();updateSwatches();toast('Saved design imported.');}catch(e){toast('Could not import: '+e.message);}$('import-file').value='';};
const ray=new THREE.Raycaster(),pointer=new THREE.Vector2();let down=null;
canvas.addEventListener('pointerdown',e=>{down={x:e.clientX,y:e.clientY};});canvas.addEventListener('pointerup',e=>{if(mode!=='orbit'||!down||Math.hypot(e.clientX-down.x,e.clientY-down.y)>5)return;const rect=canvas.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(pointer,camera);const hits=ray.intersectObjects(meshes,false).filter(h=>h.object.visible&&(!$('cutaway').checked||h.point.y<clip.constant));const hit=hits[0];if(homeControls.handleHit(hit?.object)||sliders.handleHit(hit?.object))return;});
window.addEventListener('keydown',e=>{if(/INPUT|SELECT|TEXTAREA/.test(e.target.tagName))return;if(['KeyW','KeyA','KeyS','KeyD','KeyQ','KeyE','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','ShiftLeft','ShiftRight'].includes(e.code)){if(mode==='walk'||(!e.ctrlKey&&!e.metaKey))e.preventDefault();keys.add(e.code);}if(mode==='orbit'&&(e.code==='Equal'||e.code==='Minus')){flySpeed=THREE.MathUtils.clamp(flySpeed*(e.code==='Equal'?1.4:1/1.4),.8,25);toast(`Fly speed ${flySpeed.toFixed(1)} m/s`);}if(e.code==='Escape'&&mode==='walk')exitWalk();});window.addEventListener('keyup',e=>keys.delete(e.code));window.addEventListener('blur',()=>keys.clear());document.addEventListener('visibilitychange',()=>{if(document.hidden){keys.clear();stopTour();}});
for(const button of document.querySelectorAll('[data-move]')){const code={forward:'KeyW',back:'KeyS',left:'KeyA',right:'KeyD'}[button.dataset.move];button.onpointerdown=e=>{button.setPointerCapture(e.pointerId);keys.add(code);};button.onpointerup=button.onpointercancel=()=>keys.delete(code);}
let lastTouch=null;canvas.addEventListener('pointermove',e=>{if(mode!=='walk'||!touch||e.buttons!==1)return;if(lastTouch){const rot=new THREE.Euler().setFromQuaternion(camera.quaternion,'YXZ');rot.y-=(e.clientX-lastTouch.x)*.004;rot.x=THREE.MathUtils.clamp(rot.x-(e.clientY-lastTouch.y)*.004,-1.35,1.35);camera.quaternion.setFromEuler(rot);}lastTouch={x:e.clientX,y:e.clientY};});canvas.addEventListener('pointerup',()=>lastTouch=null);
const collisionRay=new THREE.Raycaster(),downRay=new THREE.Raycaster(),direction=new THREE.Vector3(),right=new THREE.Vector3();
function move(dt){if(!model)return;camera.getWorldDirection(direction);direction.y=0;direction.normalize();right.crossVectors(direction,camera.up).normalize();let f=Number(keys.has('KeyW')||keys.has('ArrowUp'))-Number(keys.has('KeyS')||keys.has('ArrowDown')),s=Number(keys.has('KeyD')||keys.has('ArrowRight'))-Number(keys.has('KeyA')||keys.has('ArrowLeft'));const delta=direction.multiplyScalar(f).addScaledVector(right,s);if(delta.lengthSq()===0)return;delta.normalize();const distance=dt*(keys.has('ShiftLeft')?3.6:1.8);
 // Probe at torso and knee height; retain a 0.24 m clearance from solid geometry.
 let blocked=false;for(const h of [.6,1.25]){const origin=camera.position.clone();origin.y-=h;collisionRay.set(origin,delta);collisionRay.far=distance+.24;if(collisionRay.intersectObjects(colliders,false).some(hit=>hit.object.visible)){blocked=true;break;}}
 if(!blocked){const next=camera.position.clone().addScaledVector(delta,distance);downRay.set(new THREE.Vector3(next.x,camera.position.y-.7,next.z),new THREE.Vector3(0,-1,0));downRay.far=1.6;const floor=downRay.intersectObjects(colliders,false).find(h=>h.object.visible&&h.face&&Math.abs(h.face.normal.clone().transformDirection(h.object.matrixWorld).y)>.4);if(floor&&Math.abs(floor.point.y+1.65-camera.position.y)<.4){camera.position.copy(next);camera.position.y=floor.point.y+1.65;}}}
const resize=new ResizeObserver(()=>{const rect=canvas.parentElement.getBoundingClientRect();renderer.setSize(rect.width,rect.height,false);camera.aspect=rect.width/rect.height;camera.fov=camera.aspect<.8?74:55;camera.updateProjectionMatrix();});resize.observe(canvas.parentElement);
// Game-style fly navigation in Orbit view (as in Twinmotion): W/S along the view, A/D strafe, Q/E down/up, Shift to
// sprint, +/- to change speed. The orbit pivot is kept 2 m ahead so dragging then looks around from where you are.
let flySpeed=4;const flyDir=new THREE.Vector3(),flyRight=new THREE.Vector3(),flyMove=new THREE.Vector3();
function fly(dt){
 const f=Number(keys.has('KeyW')||keys.has('ArrowUp'))-Number(keys.has('KeyS')||keys.has('ArrowDown')),r=Number(keys.has('KeyD')||keys.has('ArrowRight'))-Number(keys.has('KeyA')||keys.has('ArrowLeft')),u=Number(keys.has('KeyE'))-Number(keys.has('KeyQ'));
 if(!f&&!r&&!u)return;stopTour();
 camera.getWorldDirection(flyDir);flyRight.crossVectors(flyDir,camera.up).normalize();
 flyMove.set(0,0,0).addScaledVector(flyDir,f).addScaledVector(flyRight,r).addScaledVector(camera.up,u).normalize().multiplyScalar(dt*flySpeed*(keys.has('ShiftLeft')||keys.has('ShiftRight')?3:1));
 camera.position.add(flyMove);camera.position.y=Math.max(-.3,camera.position.y);orbit.target.copy(camera.position).addScaledVector(flyDir,2);
}
let previous=performance.now();renderer.setAnimationLoop(time=>{const dt=Math.min((time-previous)/1000,.05);previous=time;construction.update(dt);sliders.update(dt);surroundingsLife.update(dt);if(cinematic.active)cinematic.update(dt);else if(mode==='orbit'){if(!construction.active)fly(dt);orbit.update();}else if(walk.isLocked||touch)move(dt);homeControls.update(dt);picker.update();renderer.render(scene,camera);});

// Full-view mode: the 3D view fills the screen (true fullscreen where the browser allows it).
$('expand').onclick=()=>{const on=!document.body.classList.contains('immersive');document.body.classList.toggle('immersive',on);$('expand').textContent=on?'✕ Exit full view':'⛶ Full view';
 if(on)document.documentElement.requestFullscreen?.().catch(()=>{});else if(document.fullscreenElement)document.exitFullscreen?.();};
document.addEventListener('fullscreenchange',()=>{if(!document.fullscreenElement&&document.body.classList.contains('immersive'))$('expand').click();});
$('studio-jump').onclick=()=>document.querySelector('aside').scrollIntoView({behavior:'smooth'});
canvas.addEventListener('pointerdown',()=>document.body.classList.add('engaged'),{once:true});
