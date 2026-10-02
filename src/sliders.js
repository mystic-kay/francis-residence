import * as THREE from 'three';
// Stacking aluminium sliders (scripts/sliding_panels.py): each moving panel glides behind the fixed one on its own
// track. Groups open from the Spaces toggle, by clicking a panel, or automatically during the walkthrough.
const DURATION=2.2,ease=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
export function createSliders({meshes,camera,canvas,getMode,toast,renderer}){
 const groups=new Map();
 function attach(){
  for(const o of meshes){const u=o.userData;if(!u.slideGroup)continue;
   if(!groups.has(u.slideGroup))groups.set(u.slideGroup,{label:u.slideLabel,open:false,t:0,panels:[]});
   const [x,y,z]=u.slideVec;groups.get(u.slideGroup).panels.push({o,base:o.position.clone(),vec:new THREE.Vector3(x,z,-y)});}
 }
 function set(id,open,announce=false){const g=groups.get(id);if(!g||g.open===open)return;g.open=open;if(announce)toast(`${g.label}: sliding ${open?'open':'closed'}`);sync();}
 const setAll=open=>{for(const id of groups.keys())set(id,open);};
 const sync=()=>{const box=document.getElementById('sliders-toggle');if(box)box.checked=[...groups.values()].some(g=>g.open);};
 function update(dt){
  for(const g of groups.values()){
   const target=g.open?1:0;if(g.t===target)continue;
   g.t=g.open?Math.min(1,g.t+dt/DURATION):Math.max(0,g.t-dt/DURATION);
   // Panels further from the fixed one travel further, so all arrive together.
   const e=ease(g.t);for(const p of g.panels)p.o.position.copy(p.base).addScaledVector(p.vec,e);
   renderer.shadowMap.needsUpdate=true;
  }
 }
 const handleHit=o=>{const id=o?.userData.slideGroup;if(!id)return false;set(id,!groups.get(id).open,true);return true;};
 // Walk mode: aim the reticle at a panel and click.
 const ray=new THREE.Raycaster(),centre=new THREE.Vector2();
 canvas.addEventListener('click',()=>{if(getMode()!=='walk')return;ray.setFromCamera(centre,camera);ray.far=3;const h=ray.intersectObjects(meshes,false).find(h=>h.object.visible);if(h)handleHit(h.object);});
 const box=document.getElementById('sliders-toggle');if(box)box.onchange=()=>{setAll(box.checked);toast(box.checked?'Sliding doors opening…':'Sliding doors closing…');};
 return {attach,update,set,setAll,handleHit,groups};
}
