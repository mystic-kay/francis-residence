import * as THREE from 'three';
// Cinematic walkthrough: plays public/tour.json (built from the real floor plans by scripts/tour_builder.py) like a
// video. It enters through the gate, walks every room at eye height, turns a slow 360 degrees in each, climbs the
// stairs and ends with a fly-out. Play, pause, previous/next room, scrubbing and speed are all available.
const WALK=1.15,SPIN=13,HOLD=4,FLY=7;
const toWeb=([x,y,z])=>new THREE.Vector3(x,z,-y);
const ease=t=>t<.5?2*t*t:1-Math.pow(-2*t+2,2)/2;

export function createCinematicTour({camera,container,baseUrl,onStart,onStop,openGate,toast}){
 let segs=[],total=0,t=0,playing=false,active=false,speed=1,yaw=0,pitch=-.06,lastCaption='';
 const ui=document.createElement('div');ui.id='cine';ui.hidden=true;
 ui.innerHTML=`<div class="cine-caption"><span class="cine-room"></span><p class="cine-text"></p></div>
 <div class="cine-bar"><button data-a="prev" aria-label="Previous room">⏮</button><button data-a="play" class="cine-play" aria-label="Pause">❚❚</button><button data-a="next" aria-label="Next room">⏭</button>
 <div class="cine-track" aria-label="Tour progress"><div class="cine-fill"></div><div class="cine-marks"></div></div><span class="cine-time">0:00</span>
 <button data-a="speed" class="cine-speed" aria-label="Playback speed">1×</button><button data-a="exit" aria-label="Exit tour">✕</button></div>`;
 container.append(ui);
 const $=s=>ui.querySelector(s);

 const ready=fetch(`${baseUrl}tour.json`).then(r=>r.json()).then(({frames})=>{
  let pos=null,prevPos=null;
  for(const f of frames){
   if(f.k==='note'){segs.push({type:'note',dur:0,caption:f.caption});continue;}
   const p=toWeb(f.p);
   if(f.k==='start'){pos=p;segs.push({type:'hold',dur:HOLD,from:p,to:p,room:f.name,caption:f.caption,gate:f.gate,look:new THREE.Vector3(p.x,p.y-.15,p.z-6)});continue;}
   if(f.k==='fly'){segs.push({type:'fly',dur:FLY,from:pos.clone(),to:p,target:toWeb(f.target),room:f.name,caption:f.caption});pos=p;continue;}
   const d=p.distanceTo(pos);
   if(d>.02){segs.push({type:'walk',dur:d/WALK*(Math.abs(p.y-pos.y)>.2?1.4:1),from:pos.clone(),to:p});prevPos=pos;pos=p;}
   if(f.k==='spin')segs.push({type:'spin',dur:SPIN,from:p,to:p,room:f.name,caption:f.caption,heading:f.face!==undefined?Math.atan2(-Math.cos(f.face),Math.sin(f.face)):prevPos?Math.atan2(-(p.x-prevPos.x),-(p.z-prevPos.z)):0});
  }
  let acc=0;for(const s of segs){s.t0=acc;acc+=s.dur;}total=acc;
  const marks=$('.cine-marks');
  for(const s of segs)if(s.type==='spin'||s.type==='hold'||s.type==='fly'){const m=document.createElement('i');m.style.left=`${s.t0/total*100}%`;m.title=s.room;marks.append(m);}
 });

 function segAt(time){let i=segs.findIndex(s=>time<s.t0+s.dur);return i<0?segs.length-1:i;}
 function captionFor(i){for(let k=i;k>=0;k--)if(segs[k].caption)return segs[k];return null;}
 // Look a little way ahead along the route so corners are taken smoothly.
 function aheadPoint(time,dist=1.6){
  let i=segAt(time),s=segs[i],u=s.dur?(time-s.t0)/s.dur:1,p=s.from.clone().lerp(s.to,u),left=dist;
  let cur=p;
  while(left>0&&i<segs.length){
   s=segs[i];if(s.type!=='walk'){break;}
   const end=s.to,d=cur.distanceTo(end);
   if(d>=left)return cur.clone().lerp(end,left/d);
   left-=d;cur=end.clone();i++;
  }
  return cur;
 }
 function apply(dt){
  const i=segAt(t),s=segs[i],u=s.dur?Math.min(1,(t-s.t0)/s.dur):1;
  if(s.type==='walk'){
   camera.position.copy(s.from).lerp(s.to,u);
   const a=aheadPoint(t),dx=a.x-camera.position.x,dz=a.z-camera.position.z;
   if(dx*dx+dz*dz>1e-4){const want=Math.atan2(-dx,-dz);let diff=((want-yaw+Math.PI*3)%(Math.PI*2))-Math.PI;yaw+=diff*Math.min(1,dt*3.2);}
   const climb=(s.to.y-s.from.y)/Math.max(.01,Math.hypot(s.to.x-s.from.x,s.to.z-s.from.z));pitch+=((Math.abs(climb)>.2?Math.sign(climb)*.22:-.06)-pitch)*Math.min(1,dt*2);
  }else if(s.type==='spin'){
   camera.position.copy(s.to);const target=s.heading+ease(u)*Math.PI*2;let diff=((target-yaw+Math.PI*3)%(Math.PI*2))-Math.PI;yaw+=diff*Math.min(1,dt*6);pitch+=(-.08-pitch)*Math.min(1,dt*2);
  }else if(s.type==='hold'){
   camera.position.copy(s.to);camera.lookAt(s.look);const e=new THREE.Euler().setFromQuaternion(camera.quaternion,'YXZ');yaw=e.y;pitch=e.x;
  }else if(s.type==='fly'){
   camera.position.copy(s.from).lerp(s.to,ease(u));const q=camera.quaternion.clone();camera.lookAt(s.target);const goal=camera.quaternion.clone();camera.quaternion.copy(q).slerp(goal,Math.min(1,.04+ease(u)));
   const e=new THREE.Euler().setFromQuaternion(camera.quaternion,'YXZ');yaw=e.y;pitch=e.x;return;
  }
  camera.quaternion.setFromEuler(new THREE.Euler(pitch,yaw,0,'YXZ'));
 }
 function render(){
  const i=segAt(t),c=captionFor(i);
  if(c&&c.caption!==lastCaption){lastCaption=c.caption;$('.cine-room').textContent=c.room||'';$('.cine-text').textContent=c.caption;ui.querySelector('.cine-caption').classList.remove('show');void ui.offsetWidth;ui.querySelector('.cine-caption').classList.add('show');}
  $('.cine-fill').style.width=`${t/total*100}%`;
  const fmt=s=>`${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,'0')}`;$('.cine-time').textContent=`${fmt(t)} / ${fmt(total)}`;
  $('.cine-play').textContent=playing?'❚❚':'▶';$('.cine-play').setAttribute('aria-label',playing?'Pause':'Play');
 }
 function seek(time){
  t=Math.max(0,Math.min(total-.001,time));
  // Re-seat the view instantly when jumping.
  const i=segAt(t),s=segs[i];
  if(s.type==='walk'){const a=aheadPoint(t);yaw=Math.atan2(-(a.x-s.from.x),-(a.z-s.from.z));}
  else if(s.type==='spin')yaw=s.heading;
  for(let k=0;k<=i;k++)if(segs[k].gate)openGate();
  apply(1);render();
 }
 const roomStarts=()=>segs.filter(s=>s.room).map(s=>s.t0);
 async function start(){
  await ready;if(!total){toast('Tour could not load.');return;}
  active=true;playing=true;ui.hidden=false;document.body.classList.add('touring');onStart();t=0;lastCaption='';openGate();seek(0);
 }
 function stop(){if(!active)return;active=false;playing=false;ui.hidden=true;document.body.classList.remove('touring');onStop();}
 function update(dt){if(!active)return;if(playing){t+=dt*speed;if(t>=total){t=total-.001;playing=false;}}apply(dt*speed);render();}
 ui.addEventListener('click',e=>{const a=e.target.closest('[data-a]')?.dataset.a;if(!a)return;
  if(a==='play'){if(t>=total-.01)seek(0);playing=!playing;}
  if(a==='exit')stop();
  if(a==='speed'){speed=speed===1?1.5:speed===1.5?2:1;e.target.textContent=`${speed}×`;}
  if(a==='next'){const n=roomStarts().find(x=>x>t+.5);if(n!==undefined)seek(n);}
  if(a==='prev'){const p=roomStarts().filter(x=>x<t-1.5);seek(p.length?p[p.length-1]:0);}
  render();});
 const track=$('.cine-track');
 const scrub=e=>{const r=track.getBoundingClientRect();seek((e.clientX-r.left)/r.width*total);};
 track.addEventListener('pointerdown',e=>{track.setPointerCapture(e.pointerId);scrub(e);track.onpointermove=scrub;});
 track.addEventListener('pointerup',()=>{track.onpointermove=null;});
 window.addEventListener('keydown',e=>{if(!active)return;if(e.code==='Space'){e.preventDefault();playing=!playing;render();}if(e.code==='Escape')stop();if(e.code==='ArrowRight'){const n=roomStarts().find(x=>x>t+.5);if(n!==undefined)seek(n);}});
 return {start,stop,update,get active(){return active;},ready};
}
