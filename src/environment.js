import * as THREE from 'three';
// Real sun for Nairobi, night exterior lighting, a parked car and architectural scale figures.
// Web coordinates are (x, height, -y) of the Blender model; the model's +y is taken as north.
const LAT=THREE.MathUtils.degToRad(-1.29);
const SEASONS={mar:{label:'March equinox',decl:0},jun:{label:'June solstice',decl:23.44},sep:{label:'September equinox',decl:0},dec:{label:'December solstice',decl:-23.44}};
const W=(x,y)=>new THREE.Vector3(x,0,-y);

// Slider t: 1 = noon, 0 = 19:15 (after dusk). The square root keeps more travel in the golden hour.
export const hourOf=t=>12+7.25*Math.sqrt(1-THREE.MathUtils.clamp(t,0,1));
export function sunPosition(hour,season){
 const d=THREE.MathUtils.degToRad(SEASONS[season]?.decl??0),H=THREE.MathUtils.degToRad((hour-12)*15);
 const alt=Math.asin(Math.sin(LAT)*Math.sin(d)+Math.cos(LAT)*Math.cos(d)*Math.cos(H));
 const az=Math.atan2(-Math.sin(H)*Math.cos(d),Math.cos(LAT)*Math.sin(d)-Math.sin(LAT)*Math.cos(d)*Math.cos(H));
 return {alt,az,dir:new THREE.Vector3(Math.sin(az)*Math.cos(alt),Math.sin(alt),-Math.cos(az)*Math.cos(alt))};
}
export const formatHour=h=>{const m=Math.round(h*60),hh=Math.floor(m/60),mm=m%60;return `${hh>12?hh-12:hh}:${String(mm).padStart(2,'0')} ${hh>=12?'pm':'am'}`;};

function gradientTexture(){
 const c=document.createElement('canvas');c.width=64;c.height=128;const g=c.getContext('2d'),grd=g.createRadialGradient(32,128,4,32,128,128);
 grd.addColorStop(0,'rgba(255,214,160,1)');grd.addColorStop(.45,'rgba(255,196,130,.45)');grd.addColorStop(1,'rgba(255,190,120,0)');g.fillStyle=grd;g.fillRect(0,0,64,128);
 const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;return t;
}

export function createEnvironment({scene,meshes,lowDetail}){
 const ray=new THREE.Raycaster();
 const groundAt=(x,z,from=12)=>{ray.set(new THREE.Vector3(x,from,z),new THREE.Vector3(0,-1,0));ray.far=from+2;const h=ray.intersectObjects(meshes,false).find(h=>h.object.visible&&!h.object.userData.slideGroup);return h?h.point.y:-.6;};
 const lights=[],glows=[],pools=[];let built=false;
 const fixtureMat=new THREE.MeshStandardMaterial({color:'#1c1e21',roughness:.4,metalness:.6});
 const lensMat=new THREE.MeshStandardMaterial({color:'#2a2620',emissive:'#ffcf94',emissiveIntensity:0});glows.push(lensMat);
 const poolTex=gradientTexture();

 function uplight(bx,by,aimHeight){
  const g=groundAt(bx,-by),base=new THREE.Vector3(bx,g,-by);
  const body=new THREE.Mesh(new THREE.CylinderGeometry(.06,.07,.09,16),fixtureMat);body.position.copy(base).add(new THREE.Vector3(0,.045,0));scene.add(body);
  const lens=new THREE.Mesh(new THREE.CircleGeometry(.05,16),lensMat);lens.rotation.x=-Math.PI/2;lens.position.copy(base).add(new THREE.Vector3(0,.091,0));scene.add(lens);
  if(!lowDetail){const s=new THREE.SpotLight(0xffd29a,0,11,.42,.9,1.6);s.position.copy(base).add(new THREE.Vector3(0,.12,0));s.target.position.copy(base).add(new THREE.Vector3(0,aimHeight,.0));scene.add(s,s.target);lights.push({l:s,max:140});}
 }
 // Fake light pool: an additive gradient card just off a wall face, cheap enough to use generously.
 function pool(bx,by,face,width,height){
  const g=groundAt(bx,-by),m=new THREE.MeshBasicMaterial({map:poolTex,transparent:true,blending:THREE.AdditiveBlending,depthWrite:false,opacity:0,toneMapped:false});
  const p=new THREE.Mesh(new THREE.PlaneGeometry(width,height),m);p.position.set(bx,g+height/2,-by);p.lookAt(p.position.clone().add(face));scene.add(p);pools.push(m);
 }
 function lantern(bx,by,z){
  const base=new THREE.Vector3(bx,z,-by);
  const box=new THREE.Mesh(new THREE.BoxGeometry(.22,.3,.22),fixtureMat);box.position.copy(base).add(new THREE.Vector3(0,.15,0));scene.add(box);
  const glass=new THREE.Mesh(new THREE.BoxGeometry(.17,.24,.23),lensMat);glass.position.copy(box.position);scene.add(glass);
  const glass2=new THREE.Mesh(new THREE.BoxGeometry(.23,.24,.17),lensMat);glass2.position.copy(box.position);scene.add(glass2);
  if(!lowDetail){const l=new THREE.PointLight(0xffc98a,0,7,1.8);l.position.copy(box.position);scene.add(l);lights.push({l,max:14});}
 }
 function buildLights(){
  // Front façade uplighters: white bay (wall y 9.16) and charcoal bay (wall y 7.76).
  // Kept clear of the front door (x -0.33..0.67): one on the wall left of it, one on the pier between the windows.
  for(const x of [-.85,2.38])uplight(x,8.86,6);for(const x of [7.0,9.5])uplight(x,7.46,6);
  // Gate pillar lanterns (pillar tops at 2.55 m) and pools washing the boundary pillars and rear façade.
  lantern(10.74,-2.77,2.55);lantern(15.64,-2.77,2.55);
  for(const x of [-.07,3.46,7.0])pool(x,-2.53,new THREE.Vector3(0,0,-1),1.1,2.4);
  for(const x of [.6,4.6,8.6])pool(x,18.9,new THREE.Vector3(0,0,-1),1.6,3.0);
  // Water bowl glow.
  if(!lowDetail){const l=new THREE.PointLight(0x9fd8e6,0,3.2,2);l.position.set(5.6,groundAt(5.6,-3.7)+.62,-3.7);scene.add(l);lights.push({l,max:3});}
 }

 // ---------- car ----------
 function buildCar(){
  const paint=new THREE.MeshPhysicalMaterial({color:'#e9e7e2',metalness:.45,roughness:.28,clearcoat:1,clearcoatRoughness:.08});
  const glass=new THREE.MeshPhysicalMaterial({color:'#1b232a',metalness:.2,roughness:.05,clearcoat:1});
  const trim=new THREE.MeshStandardMaterial({color:'#17181a',roughness:.55});
  const shape=new THREE.Shape(),P=(x,y)=>shape.lineTo(x,y);
  shape.moveTo(-2.36,.36);
  const arch=(cx,dir)=>{for(let i=0;i<=12;i++){const a=Math.PI-(i/12)*Math.PI;P(cx+dir*.44*Math.cos(a)*-1,.36+.44*Math.sin(a));}};
  P(-1.86,.36);arch(-1.42,-1);P(1.0,.36);arch(1.44,-1);P(1.88,.36);P(2.34,.38);P(2.40,.62);P(2.30,.86);P(1.36,1.0);P(.62,1.04);P(-1.9,1.06);P(-2.34,.98);P(-2.40,.62);P(-2.36,.36);
  const ext={depth:1.62,bevelEnabled:true,bevelThickness:.12,bevelSize:.1,bevelSegments:4,curveSegments:10};
  const car=new THREE.Group();
  const body=new THREE.Mesh(new THREE.ExtrudeGeometry(shape,ext),paint);body.position.z=-.81;body.castShadow=true;car.add(body);
  const cab=new THREE.Shape();cab.moveTo(-1.98,1.0);cab.lineTo(-1.74,1.6);cab.lineTo(.48,1.64);cab.lineTo(1.28,1.02);cab.lineTo(-1.98,1.0);
  const cabin=new THREE.Mesh(new THREE.ExtrudeGeometry(cab,{depth:1.42,bevelEnabled:true,bevelThickness:.06,bevelSize:.05,bevelSegments:3}),glass);cabin.position.z=-.71;car.add(cabin);
  const roof=new THREE.Mesh(new THREE.BoxGeometry(2.05,.05,1.42),paint);roof.position.set(-.62,1.66,0);car.add(roof);
  for(const x of [-.55,.2])for(const s of [-1,1]){const p=new THREE.Mesh(new THREE.BoxGeometry(.07,.6,.02),trim);p.position.set(x,1.32,s*.79);car.add(p);}
  const tyre=new THREE.MeshStandardMaterial({color:'#111214',roughness:.85}),rim=new THREE.MeshStandardMaterial({color:'#c9ccd0',metalness:.9,roughness:.25});
  for(const x of [-1.42,1.44])for(const s of [-1,1]){
   const w=new THREE.Group();w.position.set(x,.37,s*.82);
   const t=new THREE.Mesh(new THREE.CylinderGeometry(.37,.37,.26,28),tyre);t.rotation.x=Math.PI/2;t.castShadow=true;w.add(t);
   const r=new THREE.Mesh(new THREE.CylinderGeometry(.24,.24,.27,24),rim);r.rotation.x=Math.PI/2;w.add(r);
   for(let k=0;k<5;k++){const sp=new THREE.Mesh(new THREE.BoxGeometry(.04,.42,.02),trim);sp.rotation.z=k*Math.PI*2/5;sp.position.z=s*.14;w.add(sp);}
   car.add(w);}
  const head=new THREE.MeshStandardMaterial({color:'#ffffff',emissive:'#f4f6ff',emissiveIntensity:.6}),tail=new THREE.MeshStandardMaterial({color:'#5a0d10',emissive:'#ff2a2a',emissiveIntensity:.5});
  for(const s of [-1,1]){const h=new THREE.Mesh(new THREE.BoxGeometry(.05,.07,.42),head);h.position.set(2.39,.8,s*.58);car.add(h);const tl=new THREE.Mesh(new THREE.BoxGeometry(.05,.08,.4),tail);tl.position.set(-2.44,.88,s*.6);car.add(tl);}
  const grille=new THREE.Mesh(new THREE.BoxGeometry(.04,.2,1.1),trim);grille.position.set(2.42,.62,0);car.add(grille);
  for(const s of [-1,1]){const mir=new THREE.Mesh(new THREE.BoxGeometry(.18,.1,.16),paint);mir.position.set(1.05,1.13,s*.98);car.add(mir);}
  // Under the carport (canopy x 11.75-16.09, y 6-17.94), nose towards the gate.
  const cx=13.9,cy=10.2;car.position.set(cx,groundAt(cx,-cy,2.5)+.01,-cy);car.rotation.y=-Math.PI/2;car.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});scene.add(car);
  return car;
 }

 // ---------- architectural scale figures ----------
 const skin=new THREE.MeshStandardMaterial({color:'#f2efe9',roughness:.85});
 function figure(pose='stand'){
  const f=new THREE.Group(),limb=(r,l)=>new THREE.CapsuleGeometry(r,l,4,10);
  const head=new THREE.Mesh(new THREE.SphereGeometry(.105,16,12),skin);head.scale.y=1.12;head.position.y=1.62;f.add(head);
  const torso=new THREE.Mesh(limb(.16,.36),skin);torso.scale.z=.62;torso.position.y=1.2;f.add(torso);
  const hips=new THREE.Mesh(limb(.14,.06),skin);hips.scale.z=.7;hips.rotation.z=Math.PI/2;hips.position.y=.92;f.add(hips);
  const joints={};
  for(const s of [-1,1]){
   const leg=new THREE.Group();leg.position.set(s*.09,.9,0);const l=new THREE.Mesh(limb(.062,.74),skin);l.position.y=-.44;leg.add(l);f.add(leg);joints['leg'+s]=leg;
   const arm=new THREE.Group();arm.position.set(s*.21,1.38,0);const a=new THREE.Mesh(limb(.045,.56),skin);a.position.y=-.32;arm.add(a);arm.rotation.z=s*.08;f.add(arm);joints['arm'+s]=arm;
  }
  if(pose==='lean'){f.rotation.x=.08;joints['arm-1'].rotation.x=-.9;joints['arm1'].rotation.x=-.9;}
  if(pose==='talk'){joints['arm1'].rotation.x=-.6;joints['arm1'].rotation.z=.2;}
  f.traverse(o=>{if(o.isMesh)o.castShadow=true;});f.userData.joints=joints;return f;
 }
 const people=[];let walker=null;
 function buildPeople(){
  // [blender x, y, facing (radians, 0 = facing -y/front), pose, height of floor probe]
  const spots=[[8.35,12.45,2.2,'talk',8.5],[8.95,12.95,-.95,'stand',8.5],[9.9,9.0,0,'lean',8.5],[4.6,15.85,Math.PI,'stand',2.4],[12.8,7.6,.4,'stand',2.5]];
  for(const [x,y,face,pose,from] of spots){const p=figure(pose);p.position.set(x,groundAt(x,-y,from),-y);p.rotation.y=face;scene.add(p);people.push(p);}
  walker=figure('stand');scene.add(walker);people.push(walker);
 }
 let walkT=0;
 const path=[[2.0,4.2],[8.8,4.2],[8.8,1.4],[2.0,1.4]].map(([x,y])=>W(x,y));
 function updateWalker(dt){
  if(!walker)return;walkT=(walkT+dt*1.1)%1e6;const per=path.map((p,i)=>p.distanceTo(path[(i+1)%path.length])),total=per.reduce((a,b)=>a+b),d=walkT%total;
  let acc=0,i=0;while(acc+per[i]<d){acc+=per[i];i++;}const a=path[i],b=path[(i+1)%path.length],u=(d-acc)/per[i];
  const p=a.clone().lerp(b,u);walker.position.set(p.x,groundAt(p.x,p.z,3),p.z);walker.rotation.y=Math.atan2(b.x-a.x,b.z-a.z);
  const sw=Math.sin(walkT*5.2)*.45,j=walker.userData.joints;j['leg-1'].rotation.x=sw;j.leg1.rotation.x=-sw;j['arm-1'].rotation.x=-sw*.7;j.arm1.rotation.x=sw*.7;
 }

 let car=null;
 // The car and scale figures are left out on request; the owner will add their own.
 function attach(){if(built)return;built=true;buildLights();}
 function setPeople(on){for(const p of people)p.visible=on;}
 // night: 0..1; exterior: zone dimmer 0..1.
 function setLighting(night,exterior){
  const k=night*exterior;for(const {l,max} of lights)l.intensity=max*k;lensMat.emissiveIntensity=2.2*k;for(const m of pools)m.opacity=.55*k;
  if(car)car.traverse(o=>{if(o.isMesh&&o.material.emissive&&o.material.emissive.r>.9)o.material.emissiveIntensity=.2+.8*night;});
 }
 function update(dt){if(walker?.visible)updateWalker(dt);}
 return {attach,update,setLighting,setPeople,get people(){return people;}};
}
export {SEASONS};
