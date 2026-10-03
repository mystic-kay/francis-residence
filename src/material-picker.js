import * as THREE from 'three';
// Client-friendly material picking: pulsing hotspots on key surfaces, a hover highlight with a "click to change"
// tip, a swatch pop-up right where you click, and a short first-visit guide.
// Hotspot anchors are rays in Blender coordinates (from -> towards); each snaps onto the first surface of its group.
const SPOTS=[
 ['livingfabric',[8.0,11.2,1.4],[9.6,11.25,.6]],['tvwall',[8.5,11.3,1.5],[6.2,12.4,1.5]],['coffeetop',[8.4,10.0,1.6],[8.2,11.2,.3]],
 ['livingrug',[8.5,10.3,1.6],[7.6,10.0,-.1]],['livingfloor',[8.5,9.0,1.6],[7.0,8.6,-.1]],['diningfabric',[8.0,15.6,1.4],[8.6,16.45,.5]],
 ['diningwood',[8.0,15.6,1.6],[9.27,16.9,.7]],['cabinet',[5.0,15.8,1.6],[2.4,17.3,1.8]],['counter',[5.5,15.8,1.6],[4.6,16.9,.85]],
 ['render',[.9,2.0,3.1],[.9,9.4,3.1]],['accent',[8.3,2.0,3.1],[8.3,8.0,3.1]],['frontdoor',[.17,6.0,1.2],[.17,9.4,1.2]],['entrydoor',[4.2,8.3,1.2],[6.3,8.3,1.2]],['steps',[4.9,5.6,1.0],[4.9,7.3,-.4]],['porch',[1.6,7.2,1.2],[1.6,8.9,0]],
 ['gate',[13.2,-6.0,1.0],[13.2,-2.3,1.0]],['lawn',[5.0,-.5,3.0],[5.0,-.5,-.8]],['boundarywall',[5.0,1.0,1.4],[5.0,-3.3,1.4]],
 ['watertank',[0.0,-1.0,1.5],[-2.3,-1.0,1.5]],['pergolaframe',[8.0,2.0,8.6],[8.6,9.0,8.9]]];
const toWeb=([x,y,z])=>new THREE.Vector3(x,z,-y);
const GUIDE=[['Tap a glowing dot','Every pulsing dot marks something you can restyle: sofa, stone, floors, façade, gate…'],
 ['Pick a finish','Swatches apply instantly. Use “Fine-tune” for custom colour and sheen.'],
 ['Set the mood','The Lighting tab dims every room, and Watch the walkthrough shows the whole home.']];

export function createMaterialPicker({container,canvas,camera,meshes,finishes,options,groupLabels,getDesign,setFinish,openAdvanced,highlight,baseUrl,isEnabled}){
 const ray=new THREE.Raycaster(),ndc=new THREE.Vector2(),spots=[];let hints=true,frame=0,openGroup=null;
 try{hints=localStorage.getItem('francis-hints')!=='off';}catch{}
 const layer=Object.assign(document.createElement('div'),{className:'hotspots'});
 const pop=Object.assign(document.createElement('div'),{className:'picker',hidden:true});
 container.append(layer,pop);

 function attach(){
  for(const [group,from,to] of SPOTS){
   if(!options[group])continue;
   const a=toWeb(from),b=toWeb(to);ray.set(a,b.clone().sub(a).normalize());ray.far=a.distanceTo(b)+1.5;
   const hit=ray.intersectObjects(meshes,false).find(h=>h.object.visible);
   if(!hit||hit.object.userData.category!==group)continue;
   const el=document.createElement('button');el.className='hotspot';el.setAttribute('aria-label',`Change ${groupLabels[group]}`);
   el.innerHTML=`<span class="hs-dot"></span><span class="hs-label">${groupLabels[group]}<em>Tap to change</em></span>`;
   const point=hit.point.clone().add(hit.face.normal.clone().transformDirection(hit.object.matrixWorld).multiplyScalar(.04));
   el.onclick=e=>{e.stopPropagation();const r=container.getBoundingClientRect();open(group,e.clientX-r.left,e.clientY-r.top);};
   layer.append(el);spots.push({group,point,el,visible:false});
  }
 }
 function update(){
  const on=hints&&isEnabled();layer.hidden=!on;if(!on)return;
  const w=canvas.clientWidth,h=canvas.clientHeight,check=(frame++%6)===0;
  for(const s of spots){
   const p=s.point.clone().project(camera),dist=camera.position.distanceTo(s.point);
   let vis=p.z<1&&Math.abs(p.x)<1.05&&Math.abs(p.y)<1.05&&dist<42;
   if(vis&&check){ray.set(camera.position,s.point.clone().sub(camera.position).normalize());ray.far=dist+.2;const hit=ray.intersectObjects(meshes,false).find(x=>x.object.visible);s.occluded=hit&&hit.distance<dist-.25;}
   vis=vis&&!s.occluded;s.el.style.display=vis?'':'none';
   if(vis)s.el.style.transform=`translate(${(p.x+1)/2*w}px,${(1-p.y)/2*h}px)`;
  }
 }
 function open(group,x,y){
  close();openGroup=group;highlight(group,true);
  const cur=getDesign()[group];
  pop.innerHTML=`<div class="picker-head"><span><small>Choose a finish</small>${groupLabels[group]}</span><button class="picker-close" aria-label="Close">✕</button></div><div class="picker-grid"></div><button class="picker-more">Fine-tune colour &amp; sheen →</button>`;
  const grid=pop.querySelector('.picker-grid');
  for(const id of options[group]){
   const f=finishes[id],b=document.createElement('button');b.className='picker-swatch'+(cur.finish===id?' active':'');b.title=f.name;
   const sw=document.createElement('span');sw.style.backgroundColor=f.color;if(f.texture&&f.texture!=='woven')sw.style.backgroundImage=`url('${baseUrl}textures/${f.texture}/color.jpg')`;
   if(f.texture)sw.style.backgroundBlendMode='multiply';
   const n=document.createElement('small');n.textContent=f.name;b.append(sw,n);
   b.onclick=()=>{setFinish(group,id);for(const x of grid.children)x.classList.toggle('active',x===b);};grid.append(b);
  }
  pop.querySelector('.picker-close').onclick=close;pop.querySelector('.picker-more').onclick=()=>{close();openAdvanced(group);};
  pop.hidden=false;const W=container.clientWidth,H=container.clientHeight,pw=Math.min(300,W-24),ph=pop.offsetHeight;
  pop.style.width=pw+'px';pop.style.left=Math.max(12,Math.min(W-pw-12,x+14))+'px';pop.style.top=Math.max(12,Math.min(H-ph-12,y-ph/2))+'px';
 }
 function close(){if(openGroup)highlight(openGroup,false);openGroup=null;pop.hidden=true;}
 window.addEventListener('keydown',e=>{if(e.code==='Escape')close();});

 // First-visit guide, re-openable from the hints button.
 const guide=Object.assign(document.createElement('div'),{className:'guide',hidden:true});container.append(guide);
 function showGuide(step=0){
  if(step>=GUIDE.length){guide.hidden=true;try{localStorage.setItem('francis-guide-v1','done');}catch{}return;}
  const [t,d]=GUIDE[step];
  guide.innerHTML=`<span class="guide-step">${step+1} / ${GUIDE.length}</span><b>${t}</b><p>${d}</p><div><button class="guide-skip">Skip</button><button class="guide-next">${step===GUIDE.length-1?'Got it':'Next'}</button></div>`;
  guide.hidden=false;guide.querySelector('.guide-next').onclick=()=>showGuide(step+1);guide.querySelector('.guide-skip').onclick=()=>showGuide(GUIDE.length);
 }
 function maybeGuide(){let seen=false;try{seen=localStorage.getItem('francis-guide-v1')==='done';}catch{}if(!seen)setTimeout(()=>{if(isEnabled())showGuide(0);},1800);}
 function setHints(on){hints=on;try{localStorage.setItem('francis-hints',on?'on':'off');}catch{}if(on)showGuide(0);}
 return {attach,update,open,close,showGuide,maybeGuide,setHints,get hints(){return hints;}};
}
