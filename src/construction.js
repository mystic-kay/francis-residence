import * as THREE from 'three';
// 4D construction simulation: the residence assembles package by package on a 38-week programme.
// Each package sweeps a horizontal cut plane up through its own elements, so blockwork climbs storey by storey,
// slabs appear as the walls reach them, and later trades follow floor by floor. Structural surfaces stay raw
// concrete grey until the render and paint package; the garden is bare earth until landscaping.
// Heights are web y (metres); the house footprint is x -1.3..11.7, z -19.4..-7.5.
const STRUCTURE=['walls','render','accent','featurewall','floor'];
const PACKAGES=[
 {id:'site',name:'Site set-up & perimeter wall',weeks:[1,4],cats:['boundarywall','boundarypillar','boundarycoping'],note:'Hoarding, setting out and the stone perimeter wall: in Kenya the compound wall goes up first for security.'},
 {id:'exc',name:'Excavation',weeks:[3,4],note:'Bulk excavation to 1.5 m for the column bases and strip footings; spoil is stockpiled on site for backfill.'},
 {id:'found',name:'Column bases & strip footings',weeks:[5,6],structure:[-1.7,-1.02],note:'Blinding, 1.5 m pad footings under every column with starter bars cast in, and 600 mm strip footings under the walls.'},
 {id:'plinth',name:'Foundation walling, backfill & slab',weeks:[6,8],structure:[-1.02,.02],note:'Natural-stone foundation walling, compacted backfill and hardcore, then the 200 mm ground-floor slab.'},
 {id:'gf',name:'Ground-floor columns & walling',weeks:[8,12],structure:[.02,3.0],note:'Reinforced-concrete columns and machine-cut stone walling to first-floor level.'},
 {id:'s1',name:'First-floor slab',weeks:[12,14],structure:[3.0,3.16],note:'Formwork, reinforcement and the 150 mm first-floor slab pour, then 28 days of curing.'},
 {id:'ff',name:'First-floor walling',weeks:[14,18],structure:[3.16,6.0],note:'Walling and ring beams for the bedroom floor.'},
 {id:'s2',name:'Second slab & top-floor walling',weeks:[18,22],structure:[6.0,9.0],note:'Top-floor slab, terrace walls and the stair core.'},
 {id:'roofslab',name:'Roof slab & parapets',weeks:[22,24],structure:[9.0,11.5],note:'Roof slab, upstands and parapets around the terrace.'},
 {id:'roof',name:'Roofing, pergola & solar',weeks:[23,26],cats:['roof','coping','pergolaframe'],note:'Waterproofing, precast coping, the steel pergola, PV modules and the solar water heater.'},
 {id:'glaze',name:'Windows, doors & glazing',weeks:[25,29],cats:['glass','metal','doors','frontdoor','frontdoorframe','frontdoorhardware','balconyglass','balconyrail','pergolaglass'],note:'Aluminium frames, glazing, balustrades, the pergola roof glass and the matte-black front door.'},
 {id:'mep',name:'Electrical & plumbing rough-in',weeks:[24,29],cats:['details','lightstrip'],note:'Conduits, back boxes, pipework, sleeves and the consumer units.'},
 {id:'paint',name:'External render & painting',weeks:[28,32],repaint:['render','accent','featurewall','walls'],note:'Wallmaster-style stucco in white and charcoal, and the interior paint.'},
 {id:'fin',name:'Internal finishes & joinery',weeks:[29,35],cats:['ceiling','livingfloor','bedfloor','bedwall','tvwall','skirting','ceramic','wood','cabinet','counter','hardware','tapware'],repaint:['floor'],note:'Ceilings and soffits, oak floors, kitchen, sanitaryware, taps, wardrobes and panelling.'},
 {id:'ext',name:'External works & landscaping',weeks:[31,37],cats:['paving','kerb','gate','gateframe','watertank','tankbase'],plants:true,note:'Paving, the sliding gate, the 10,000 L tank, lawn and planting.'},
 {id:'ffe',name:'Furniture, lighting & décor',weeks:[35,38],cats:['lighting','interiorlight','fabric','bedding','headboard','livingfabric','livingpillows','livingrug','curtains','coffeetop','tvunit','diningfabric','diningwood','interiormetal','decor'],note:'Light fittings, the chandelier, furniture, soft furnishings, art and styling: ready for handover.'}];
const WEEKS=38,SECONDS=70;
const RAW=new THREE.Color('#9d9a94'),EARTH=new THREE.Color('#7b5e40');
const inHouse=b=>b.min.x>-1.6&&b.max.x<12&&b.min.z>-19.8&&b.max.z<-7.2;

export function createConstruction({container,scene,meshes,renderer,orbit,onStart,onStop}){
 let active=false,playing=false,t=0,speed=1,items=[],plants=[],built=false;
 // Bare, compacted earth over the whole plot while it is a building site; fades as the external works finish.
 const earth=new THREE.Mesh(new THREE.PlaneGeometry(21.0,24.53),new THREE.MeshStandardMaterial({color:'#8a6a4a',roughness:1,transparent:true}));
 earth.rotation.x=-Math.PI/2;earth.position.set(6.64,-.634,-9.245);earth.receiveShadow=true;earth.visible=false;scene.add(earth);
 // ---- Excavation: a real pit cut through the ground surfaces, an excavator, spoil heaps and starter bars ----
 const PIT={x0:-2.2,x1:12.5,z0:-19.8,z1:-6.9},GL=-.634,BOTTOM=-1.56;
 const holed=(w,h,cx,cz)=>{const s=new THREE.Shape([new THREE.Vector2(-w/2,-h/2),new THREE.Vector2(w/2,-h/2),new THREE.Vector2(w/2,h/2),new THREE.Vector2(-w/2,h/2)]);
  // Local plane coords after the -90 degree X rotation: x = world x - cx, y = -(world z - cz).
  const hx0=PIT.x0-cx,hx1=PIT.x1-cx,hy0=-(PIT.z1-cz),hy1=-(PIT.z0-cz);s.holes.push(new THREE.Path([new THREE.Vector2(hx0,hy0),new THREE.Vector2(hx0,hy1),new THREE.Vector2(hx1,hy1),new THREE.Vector2(hx1,hy0)]));
  const g=new THREE.ShapeGeometry(s),p=g.attributes.position,uv=g.attributes.uv;for(let k=0;k<p.count;k++)uv.setXY(k,p.getX(k)/w+.5,p.getY(k)/h+.5);return g;};
 let groundRef=null,groundOrig=null,groundHoled=null;const earthOrig=earth.geometry,earthHoled=holed(21.0,24.53,6.64,-9.245);
 const soil=new THREE.MeshStandardMaterial({color:'#6e5236',roughness:1}),soilDark=new THREE.MeshStandardMaterial({color:'#5a4330',roughness:1});
 const pit=new THREE.Group();pit.visible=false;scene.add(pit);
 const W=PIT.x1-PIT.x0,D=PIT.z1-PIT.z0,cx=(PIT.x0+PIT.x1)/2,cz=(PIT.z0+PIT.z1)/2;
 const floor=new THREE.Mesh(new THREE.BoxGeometry(W,.04,D),soilDark);floor.position.set(cx,0,cz);floor.receiveShadow=true;pit.add(floor);
 const sides=[[W,cx,PIT.z0,0],[W,cx,PIT.z1,0],[D,PIT.x0,cz,1],[D,PIT.x1,cz,1]].map(([len,x,z,rot])=>{const m=new THREE.Mesh(new THREE.BoxGeometry(len,1,.05),soil);m.position.set(x,0,z);m.rotation.y=rot?Math.PI/2:0;m.receiveShadow=true;pit.add(m);return m;});
 const blinding=new THREE.Mesh(new THREE.BoxGeometry(W-1.2,.05,D-1.2),new THREE.MeshStandardMaterial({color:'#9b9890',roughness:.95}));blinding.position.set(cx,BOTTOM+.03,cz);blinding.visible=false;scene.add(blinding);
 // Spoil heaps in the garden, growing as the pit deepens and drawn back down for backfill.
 const heaps=[[3.2,-2.6,3.4],[7.4,-2.2,2.8],[11.6,-3.0,2.4]].map(([x,z,r])=>{const m=new THREE.Mesh(new THREE.SphereGeometry(r,24,12,0,Math.PI*2,0,Math.PI/2),soil);m.position.set(x,GL,z);m.castShadow=m.receiveShadow=true;m.userData.r=r;m.visible=false;scene.add(m);return m;});
 // Starter bars: four 16 mm bars per column, cast into the pad and lapped above the slab.
 const COLS=[[6.14,9.28],[10.44,9.28],[6.14,7.88],[10.44,7.88],[6.14,13.48],[10.44,13.48],[6.14,18.78],[10.44,18.78],[3.54,9.28],[-1.16,13.48],[3.54,13.48],[3.54,7.9],[-1.16,9.28],[-1.16,18.78],[2.34,18.78]];
 const bars=new THREE.InstancedMesh(new THREE.CylinderGeometry(.008,.008,1.65,6),new THREE.MeshStandardMaterial({color:'#6b4a35',roughness:.7,metalness:.4}),COLS.length*4);
 {const m=new THREE.Matrix4();let k=0;for(const [x,y] of COLS)for(const [dx,dz] of [[-.06,-.06],[.06,-.06],[.06,.06],[-.06,.06]]){m.makeTranslation(x+dx,-1.05+.825,-y+dz);bars.setMatrixAt(k++,m);}}
 bars.visible=false;scene.add(bars);
 // Excavator: tracks, slewing body, cab, boom, stick and bucket (in site yellow), working the north-east corner.
 const yellow=new THREE.MeshStandardMaterial({color:'#e2a91f',roughness:.5,metalness:.2}),dark=new THREE.MeshStandardMaterial({color:'#25272a',roughness:.7}),glassM=new THREE.MeshStandardMaterial({color:'#2c3a44',roughness:.15,metalness:.3});
 const exc=new THREE.Group();exc.position.set(14.2,GL,-15.5);exc.visible=false;scene.add(exc);
 const part=(geo,mat,x,y,z,parent=exc)=>{const m=new THREE.Mesh(geo,mat);m.position.set(x,y,z);m.castShadow=true;parent.add(m);return m;};
 for(const z of [-.85,.85])part(new THREE.BoxGeometry(3.2,.7,.6),dark,0,.35,z);
 const body=new THREE.Group();body.position.y=.75;exc.add(body);
 part(new THREE.BoxGeometry(2.6,.9,2.2),yellow,.35,.45,0,body);part(new THREE.BoxGeometry(1.0,1.1,.95),yellow,-.55,1.45,.55,body);part(new THREE.BoxGeometry(.9,.75,.97),glassM,-.6,1.55,.55,body);
 part(new THREE.BoxGeometry(.9,.6,2.2),dark,1.45,.55,0,body);
 const boom=new THREE.Group();boom.position.set(-.9,1.0,-.3);body.add(boom);part(new THREE.BoxGeometry(3.4,.35,.32),yellow,-1.6,0,0,boom);
 const stick=new THREE.Group();stick.position.set(-3.3,0,0);boom.add(stick);part(new THREE.BoxGeometry(.28,2.4,.26),yellow,0,-1.15,0,stick);
 const bucket=part(new THREE.BoxGeometry(.7,.55,.8),dark,-.15,-2.45,0,stick);
 body.rotation.y=.35;
 function placeExcavation(){
  const pe=progress(PACKAGES.find(p=>p.id==='exc')),pf=progress(PACKAGES.find(p=>p.id==='found')),pp=progress(PACKAGES.find(p=>p.id==='plinth'));
  const fill=THREE.MathUtils.clamp((pp-.55)/.4,0,1);
  const level=pe<1?GL+(BOTTOM-GL)*pe:BOTTOM+(GL-BOTTOM)*fill;
  const open=pe>0&&fill<1;pit.visible=open;
  if(groundRef){const g=open?groundHoled:groundOrig;if(groundRef.geometry!==g)groundRef.geometry=g;}
  const eg=open?earthHoled:earthOrig;if(earth.geometry!==eg)earth.geometry=eg;
  floor.position.y=level-.02;const depth=Math.max(.001,GL-level);
  for(const m of sides){m.scale.y=depth;m.position.y=GL-depth/2;}
  blinding.visible=open&&pf>0&&level<BOTTOM+.05;
  const heap=pe<1?pe:1-fill;for(const h of heaps){h.visible=heap>.02;h.scale.set(1,Math.max(.01,heap*.55),1);}
  bars.visible=pf>.35&&progress(PACKAGES.find(p=>p.id==='gf'))<.35;
  exc.visible=pe>0&&fill<1&&pf<.15||(pp>.5&&fill<1);
  if(exc.visible){const k=performance.now()/1000;body.rotation.y=.35+.45*Math.sin(k*.6);boom.rotation.z=-.25+.18*Math.sin(k*1.1);stick.rotation.z=.35+.25*Math.sin(k*1.1+1.2);bucket.rotation.z=.3*Math.sin(k*1.1+2);}
 }
 const planes=new Map(),snap=new Map();
 const ui=document.createElement('div');ui.id='build4d';ui.hidden=true;
 ui.innerHTML=`<div class="b4-head"><div><small>4D construction programme</small><b class="b4-week">Week 0</b><span class="b4-pkg"></span></div><div class="b4-tools"><button class="b4-toggle" aria-expanded="false">Programme ▴</button><button class="b4-x" aria-label="Exit construction simulation">✕</button></div></div>
 <p class="b4-note"></p><div class="b4-gantt"></div>
 <div class="b4-bar"><button data-a="restart" aria-label="Restart">⟲</button><button data-a="play" class="b4-play" aria-label="Pause">❚❚</button>
 <div class="b4-track"><div class="b4-fill"></div></div><button data-a="speed" class="b4-speed">1×</button></div>`;
 container.append(ui);const q=s=>ui.querySelector(s);
 const gantt=q('.b4-gantt');gantt.hidden=true;
 q('.b4-toggle').onclick=e=>{e.stopPropagation();gantt.hidden=!gantt.hidden;e.target.textContent=gantt.hidden?'Programme ▴':'Programme ▾';e.target.setAttribute('aria-expanded',String(!gantt.hidden));};
 for(const p of PACKAGES){const r=document.createElement('div');r.className='b4-row';r.dataset.id=p.id;
  r.innerHTML=`<span class="b4-name">${p.name}</span><span class="b4-lane"><i style="left:${(p.weeks[0]-1)/WEEKS*100}%;width:${(p.weeks[1]-p.weeks[0]+1)/WEEKS*100}%"></i></span>`;gantt.append(r);}
 const head=document.createElement('div');head.className='b4-playhead';gantt.append(head);

 function classify(){
  items=[];
  for(const o of meshes){
   const cat=o.userData.category,b=new THREE.Box3().setFromObject(o);
   const info={roof:b.min.y>9.25,external:!inHouse(b)};
   let pkg=null;
   if(STRUCTURE.includes(cat))pkg='structure';
   if(cat==='lawn'||cat==='road')pkg='always';
   for(const p of PACKAGES){if(pkg)break;if(p.cats?.includes(cat))pkg=p.id;}
   // Route by position: rooftop decor (solar) with roofing, decor and fittings outside the house with external works.
   if(['decor','details','interiormetal'].includes(cat)){if(info.roof)pkg='roof';else if(info.external)pkg='ext';}
   if(!pkg)pkg='ffe';
   items.push({o,pkg,min:b.min.y,max:b.max.y});
  }
  plants=[];scene.traverse(o=>{if(o.userData.plant){const p=o.position;if(p.x>-4&&p.x<17.2&&p.z>-21.6&&p.z<3.1)plants.push({o,scale:o.scale.x});}});
  built=true;
 }
 const plane=id=>{if(!planes.has(id))planes.set(id,new THREE.Plane(new THREE.Vector3(0,-1,0),0));return planes.get(id);};
 const mats=o=>Array.isArray(o.material)?o.material:[o.material];
 function rawify(cats,color){for(const it of items){if(!cats.includes(it.o.userData.category))continue;for(const m of mats(it.o)){if(!snap.has(m))snap.set(m,{color:m.color.clone(),map:m.map});m.color.copy(color);m.map=null;m.needsUpdate=true;}}}
 function blend(cats,u){for(const it of items){if(!cats.includes(it.o.userData.category))continue;for(const m of mats(it.o)){const s=snap.get(m);if(!s)continue;
  const want=u>=(it.o.userData.category==='lawn'?.3:1)?s.map:null;if(m.map!==want){m.map=want;m.needsUpdate=true;}m.color.copy(it.o.userData.category==='lawn'?EARTH:RAW).lerp(s.color,Math.min(1,u));}}}
 const week=()=>t/SECONDS*WEEKS+1;
 const progress=p=>THREE.MathUtils.clamp((week()-p.weeks[0])/(p.weeks[1]-p.weeks[0]+1),0,1);
 function apply(){
  const w=week();
  // Structural sweep: piecewise across the structural packages.
  let H=-1.8;for(const p of PACKAGES)if(p.structure){const u=progress(p);if(u>0)H=p.structure[0]+(p.structure[1]-p.structure[0])*u;}
  const pkgH={};
  for(const p of PACKAGES)if(p.cats||p.id==='roof'||p.id==='ext'){
   const own=items.filter(i=>i.pkg===p.id);if(!own.length)continue;
   const lo=Math.min(...own.map(i=>i.min)),hi=Math.max(...own.map(i=>i.max));pkgH[p.id]=lo-.01+(hi-lo+.02)*progress(p);
  }
  for(const it of items){
   if(it.pkg==='always'){it.o.visible=true;continue;}
   const h=it.pkg==='structure'?H:pkgH[it.pkg]??-99,pl=plane(it.pkg);pl.constant=h;
   const done=h>=it.max+.01;it.o.visible=h>it.min;
   for(const m of mats(it.o)){const want=done?null:pl;if((m.clippingPlanes?.[0]||null)!==want){m.clippingPlanes=want?[want]:[];m.needsUpdate=true;}}
  }
  for(const p of PACKAGES)if(p.repaint)blend(p.repaint,progress(p));
  blend(['lawn'],progress(PACKAGES.find(p=>p.id==='ext')));
  const g=progress(PACKAGES.find(p=>p.id==='ext'));
  for(const pl of plants){const s=THREE.MathUtils.clamp(g*1.6-.4,0,1);pl.o.visible=s>0;pl.o.scale.setScalar(pl.scale*Math.max(.001,s));}
  placeExcavation();
  const ext=progress(PACKAGES.find(p=>p.id==='ext'));earth.material.opacity=1-THREE.MathUtils.clamp((ext-.35)/.6,0,1);earth.visible=earth.material.opacity>.01;
  renderer.shadowMap.needsUpdate=true;
  // UI
  const cur=PACKAGES.filter(p=>w>=p.weeks[0]&&w<p.weeks[1]+1);const main=cur[cur.length-1]||PACKAGES[PACKAGES.length-1];
  q('.b4-week').textContent=w>=WEEKS+.98?'Handover':`Week ${Math.min(WEEKS,Math.floor(w))}`;q('.b4-pkg').textContent=cur.map(p=>p.name).join(' · ')||'Handover';
  q('.b4-note').textContent=w>=WEEKS+.98?'The Francis Residence is complete and ready to move in.':main.note;
  for(const r of gantt.querySelectorAll('.b4-row')){const p=PACKAGES.find(x=>x.id===r.dataset.id);r.classList.toggle('now',cur.includes(p));r.classList.toggle('done',w>=p.weeks[1]+1);}
  const x=(w-1)/WEEKS;head.style.left=`calc(var(--b4-name) + (100% - var(--b4-name)) * ${Math.min(1,x)})`;q('.b4-fill').style.width=`${Math.min(1,t/SECONDS)*100}%`;
  q('.b4-play').textContent=playing?'❚❚':'▶';
 }
 function start(){
  if(!groundRef){scene.traverse(o=>{if(!groundRef&&o.isMesh&&o.geometry?.parameters?.width>=500)groundRef=o;});if(groundRef){groundOrig=groundRef.geometry;const p=groundOrig.parameters;groundHoled=holed(p.width,p.height,groundRef.position.x,groundRef.position.z);}}
  if(!built)classify();active=true;playing=true;t=0;ui.hidden=false;document.body.classList.add('building');onStart();
  rawify(['render','accent','featurewall','walls','floor'],RAW);rawify(['lawn'],EARTH);
  orbit.autoRotate=true;orbit.autoRotateSpeed=.6;apply();
 }
 function stop(){
  if(!active)return;active=false;playing=false;ui.hidden=true;document.body.classList.remove('building');orbit.autoRotate=false;
  for(const [m,s] of snap){m.color.copy(s.color);m.map=s.map;m.needsUpdate=true;}snap.clear();
  earth.visible=false;earth.geometry=earthOrig;if(groundRef)groundRef.geometry=groundOrig;pit.visible=blinding.visible=bars.visible=exc.visible=false;for(const h of heaps)h.visible=false;
  for(const pl of plants){pl.o.visible=true;pl.o.scale.setScalar(pl.scale);}
  for(const it of items){it.o.visible=true;for(const m of mats(it.o)){m.clippingPlanes=[];m.needsUpdate=true;}}
  onStop();
 }
 function update(dt){if(!active)return;if(playing){t=Math.min(SECONDS*(WEEKS+.99)/WEEKS,t+dt*speed);if(t>=SECONDS*(WEEKS+.98)/WEEKS){playing=false;orbit.autoRotate=false;}}apply();}
 ui.addEventListener('click',e=>{const a=e.target.closest('[data-a]')?.dataset.a;
  if(e.target.closest('.b4-x'))stop();
  if(a==='play'){if(t>=SECONDS)t=0;playing=!playing;orbit.autoRotate=playing;}
  if(a==='restart'){t=0;playing=true;orbit.autoRotate=true;}
  if(a==='speed'){speed=speed===1?2:speed===2?4:1;e.target.textContent=`${speed}×`;}
  if(active)apply();});
 const seekFrom=(el,e)=>{const r=el.getBoundingClientRect();return THREE.MathUtils.clamp((e.clientX-r.left)/r.width,0,1);};
 const track=q('.b4-track');
 track.addEventListener('pointerdown',e=>{track.setPointerCapture(e.pointerId);const go=ev=>{t=seekFrom(track,ev)*SECONDS*(WEEKS+.99)/WEEKS;apply();};go(e);track.onpointermove=go;});
 track.addEventListener('pointerup',()=>{track.onpointermove=null;});
 // Clicking a Gantt row jumps to the start of that package.
 gantt.addEventListener('click',e=>{const r=e.target.closest('.b4-row');if(!r)return;const p=PACKAGES.find(x=>x.id===r.dataset.id);t=(p.weeks[0]-1+.01)/WEEKS*SECONDS;apply();});
 window.addEventListener('keydown',e=>{if(!active)return;if(e.code==='Escape')stop();if(e.code==='Space'){e.preventDefault();playing=!playing;orbit.autoRotate=playing;apply();}});
 return {start,stop,update,get active(){return active;}};
}
