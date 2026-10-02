import * as THREE from 'three';
// Room lighting zones, clickable wall switches and the sliding gate.
// Zones and the gate come from public/lighting-zones.json, written by scripts/site_and_lighting.py.
const STORAGE='francis-lighting-v1';
const LEVEL_NAMES={0:'Ground floor',1:'First floor',2:'Top floor & terrace',null:'Outside'};
const SCENES={
 all:{label:'All on',zones:()=>1},
 evening:{label:'Evening',zones:id=>['living','dining','kitchen','corridor','roofdining','terrace','exterior'].includes(id)?.6:0},
 night:{label:'Night path',zones:id=>['corridor','landing','stair','exterior'].includes(id)?.25:0},
 off:{label:'All off',zones:()=>0}
};

export function createHomeControls({scene,camera,canvas,renderer,meshes,toast,getMode,onChange,baseUrl,lowDetail}){
 const zones=new Map(),switches=[],leaves=[];let gate=null,gateOpen=false,gateT=0,strength=1;
 let saved={};try{saved=JSON.parse(localStorage.getItem(STORAGE)||'{}');}catch{}
 const persist=()=>{try{localStorage.setItem(STORAGE,JSON.stringify(Object.fromEntries([...zones].map(([id,z])=>[id,{on:z.on,dim:z.dim}]))));}catch{}};

 function attach(config){
  gate=config.gate;
  for(const z of config.zones){
   if(!z.fixtureFaces&&!z.switchPlates)continue;
   const prev=saved[z.id]||{};
   zones.set(z.id,{...z,on:prev.on??true,dim:prev.dim??1,meshes:[],light:null});
  }
  for(const o of meshes){
   const u=o.userData;
   if(u.lightZone&&zones.has(u.lightZone)){
    zones.get(u.lightZone).meshes.push(o);
    for(const m of mats(o))m.userData.baseEmissive=u.category==='interiorlight'?3:(m.emissiveIntensity||1);
   }
   if(u.lightSwitch&&zones.has(u.lightSwitch)){switches.push(o);for(const m of mats(o))m.emissive?.set('#ffcf8a');}
   if(u.slidingGate)leaves.push({mesh:o,x:o.position.x});
  }
  // One soft, shadowless fill light per room so switching a zone visibly changes the space.
  if(!lowDetail)for(const z of zones.values())if(z.center){
   const [x,y,h]=z.center,[w,d]=z.size;
   z.light=new THREE.PointLight(0xffd6a0,0,Math.max(w,d)*1.15,2);z.light.position.set(x,h-.25,-y);scene.add(z.light);
  }
  apply();
 }
 const mats=o=>Array.isArray(o.material)?o.material:[o.material];
 const levelOf=id=>{const z=zones.get(id);return z&&z.on?z.dim:0;};

 function apply(globalStrength=strength){
  strength=globalStrength;
  for(const z of zones.values()){
   const level=levelOf(z.id)*strength;
   for(const o of z.meshes)for(const m of mats(o))m.emissiveIntensity=(m.userData.baseEmissive??1)*level;
   if(z.light)z.light.intensity=9*level;
  }
  for(const o of switches)for(const m of mats(o))m.emissiveIntensity=levelOf(o.userData.lightSwitch)?.12:0;
  renderPanel();
 }
 function setZone(id,patch,announce=false){
  const z=zones.get(id);if(!z)return;Object.assign(z,patch);persist();apply();onChange?.();
  if(announce)toast(`${z.name} lights ${z.on?'on':'off'}`);
 }
 function scenePreset(key){
  for(const z of zones.values()){const v=SCENES[key].zones(z.id);z.on=v>0;if(v>0)z.dim=v;}
  persist();apply();onChange?.();toast(`${SCENES[key].label} lighting`);
 }

 // ---- Sliding gate: eased travel behind the boundary wall ----
 function setGate(open){
  if(!leaves.length)return;gateOpen=open;const box=document.getElementById('gate-toggle');if(box)box.checked=open;
  toast(open?'Gate opening…':'Gate closing…');
 }
 function update(dt){
  if(!leaves.length||!gate)return;
  const target=gateOpen?1:0;if(gateT===target)return;
  gateT=gateOpen?Math.min(1,gateT+dt/7):Math.max(0,gateT-dt/7);
  const ease=gateT<.5?2*gateT*gateT:1-Math.pow(-2*gateT+2,2)/2;
  for(const l of leaves)l.mesh.position.x=l.x-gate.slide*ease;
  renderer.shadowMap.needsUpdate=true;
 }

 // Returns true when the clicked object was a switch or the gate, so material selection is skipped.
 function handleHit(object){
  if(!object)return false;
  if(object.userData.lightSwitch&&zones.has(object.userData.lightSwitch)){const id=object.userData.lightSwitch;setZone(id,{on:!zones.get(id).on},true);return true;}
  if(object.userData.slidingGate){setGate(!gateOpen);return true;}
  return false;
 }
 // In walk mode the reticle is the pointer: click a switch within arm's reach.
 const centre=new THREE.Raycaster(),origin=new THREE.Vector2(0,0);
 canvas.addEventListener('click',()=>{
  if(getMode()!=='walk')return;centre.setFromCamera(origin,camera);centre.far=2.6;
  const hit=centre.intersectObjects(meshes,false).find(h=>h.object.visible);
  if(hit&&(hit.object.userData.lightSwitch||hit.object.userData.slidingGate))handleHit(hit.object);
 });

 function renderPanel(){
  const panel=document.getElementById('lighting-panel');if(!panel||!zones.size)return;
  if(!panel.dataset.built){
   panel.dataset.built='1';panel.replaceChildren();
   const label=Object.assign(document.createElement('p'),{className:'field-label',textContent:'LIGHTING SCENES'});
   const row=Object.assign(document.createElement('div'),{className:'light-scenes'});
   for(const [key,s] of Object.entries(SCENES)){const b=Object.assign(document.createElement('button'),{className:'text-button',textContent:s.label});b.onclick=()=>scenePreset(key);row.append(b);}
   const hint=Object.assign(document.createElement('p'),{className:'small muted',textContent:'Every wall switch in the model works: click one, or aim the reticle at it in Walk mode.'});
   panel.append(label,row,hint);
   for(const level of [0,1,2,null]){
    const list=[...zones.values()].filter(z=>z.level===level);if(!list.length)continue;
    panel.append(Object.assign(document.createElement('p'),{className:'field-label',textContent:LEVEL_NAMES[level].toUpperCase()}));
    for(const z of list){
     const item=document.createElement('div');item.className='light-row';item.dataset.zone=z.id;
     const name=Object.assign(document.createElement('span'),{textContent:z.name});
     const dim=Object.assign(document.createElement('input'),{type:'range',min:'.1',max:'1',step:'.05'});dim.setAttribute('aria-label',`${z.name} dimmer`);dim.oninput=()=>setZone(z.id,{dim:Number(dim.value),on:true});
     const sw=Object.assign(document.createElement('button'),{className:'light-switch'});sw.onclick=()=>setZone(z.id,{on:!zones.get(z.id).on});
     item.append(name,dim,sw);panel.append(item);
    }
   }
  }
  for(const item of panel.querySelectorAll('.light-row')){
   const z=zones.get(item.dataset.zone),sw=item.querySelector('.light-switch');
   item.querySelector('input').value=z.dim;sw.textContent=z.on?'On':'Off';sw.classList.toggle('on',z.on);sw.setAttribute('aria-pressed',String(z.on));sw.setAttribute('aria-label',`${z.name} lights`);
  }
 }

 const gateBox=document.getElementById('gate-toggle');if(gateBox)gateBox.onchange=()=>setGate(gateBox.checked);
 const ready=fetch(`${baseUrl}lighting-zones.json`).then(r=>r.ok?r.json():Promise.reject(new Error(r.statusText)));
 return {ready,attach,apply,update,handleHit,setGate,scenePreset,levelOf,zones,get gateOpen(){return gateOpen;}};
}
