/* Local real-time, representative-sphere contact model; independent of thermal solver. */
(function(root){
'use strict';
const TAU=2*Math.PI,clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const defaults={count:320,muWall:.45,muParticle:.35,restitution:.25,stiffness:16000,drag:4,liquidSlip:.35};
function create(c,options={}){
 const settings={...defaults,...options};settings.count=Math.round(root.RotaryModel.geometry(c).chargeMass/(c.rhos*4*Math.PI*(c.particle/2000)**3/3));
 for(const key of ['muWall','muParticle','drag','liquidSlip'])if(!Number.isFinite(settings[key])||settings[key]<0)throw Error('Invalid motion coefficient: '+key);
 if(!Number.isFinite(settings.stiffness)||settings.stiffness<=0||!Number.isFinite(settings.count))throw Error('Invalid motion resolution/stiffness.');
 const g=root.RotaryModel.geometry(c),R=c.diameter/2000,L=c.length/1000,h=c.headDepth/1000,Rs=h>0?(R*R+h*h)/(2*h):R;
 const bulk=clamp(g.bulkFill,.05,.75),solidVolume=g.volume*bulk*c.packing;
 const radius=c.particle/2000;
 const system={c:{...c},settings,R,L,h,Rs,g,baseRadius:radius,radius,particles:[],seconds:0,angle:0,liquid:0,contacts:0,wallContacts:0,maxOverlap:0,accumulator:0,steps:0,discardedWallSeconds:0};
 const a=2*Math.SQRT2*radius*(settings.spacingFactor||1.025),candidates=[],basis=[[0,0,0],[0,.5,.5],[.5,0,.5],[.5,.5,0]],theta=c.angle*Math.PI/180;
 const zmin=c.heads>0?-h:0,zmax=L+(c.heads===2?h:0);
 for(let iz=Math.floor(zmin/a)-1;iz<=Math.ceil(zmax/a);iz++)for(let iy=Math.floor(-R/a)-1;iy<=Math.ceil(R/a);iy++)for(let ix=Math.floor(-R/a)-1;ix<=Math.ceil(R/a);ix++)for(const b of basis){
  const p={x:(ix+b[0])*a,y:(iy+b[1])*a,z:(iz+b[2])*a};
  if(clearance(system,p).gap>radius*1.01)candidates.push(p);
 }
 candidates.sort((p,q)=>(p.y*Math.cos(theta)+p.z*Math.sin(theta))-(q.y*Math.cos(theta)+q.z*Math.sin(theta)));
 for(const p of candidates.slice(0,settings.count))system.particles.push({...p,vx:0,vy:0,vz:0,wx:0,wy:0,wz:0,ax:0,ay:0,az:0,awx:0,awy:0,awz:0,id:system.particles.length,path:[]});
 system.representedMass=g.chargeMass;system.countLimited=system.particles.length<settings.count;system.count=system.particles.length;
 return system;
}
function clearance(s,p){
 const {R,L,h,Rs,c}=s,rho=Math.hypot(p.x,p.y);let gap=R-rho,nx=rho?p.x/rho:1,ny=rho?p.y/rho:0,nz=0;
 function plane(d,x,y,z){if(d<gap){gap=d;nx=x;ny=y;nz=z;}}
 if(c.heads===0)plane(p.z,0,0,-1);
 else if(p.z<0){const zz=p.z-(Rs-h),d=Math.hypot(p.x,p.y,zz);gap=Rs-d;nx=p.x/d;ny=p.y/d;nz=zz/d;}
 if(c.heads!==2)plane(L-p.z,0,0,1);
 else if(p.z>L){const zz=p.z-(L-Rs+h),d=Math.hypot(p.x,p.y,zz);gap=Rs-d;nx=p.x/d;ny=p.y/d;nz=zz/d;}
 return {gap,nx,ny,nz};
}
function phase(s,fraction){const f=clamp(fraction,0,1);if(f!==s.liquid||f>=1){s.contacts=0;s.wallContacts=0;s.maxOverlap=0;}s.liquid=f;s.radius=s.baseRadius*Math.cbrt(1-s.liquid);}
function contact(s,a,b,dx,dy,dz,d,r,kn,gamma){
 const overlap=2*r-d;if(overlap<=0)return;
 const nx=dx/d,ny=dy/d,nz=dz/d;
 // Contact-point relative velocity includes sphere spins; normal and Coulomb sliding forces.
 const rx=a.vx-b.vx-r*((a.wy+b.wy)*nz-(a.wz+b.wz)*ny),ry=a.vy-b.vy-r*((a.wz+b.wz)*nx-(a.wx+b.wx)*nz),rz=a.vz-b.vz-r*((a.wx+b.wx)*ny-(a.wy+b.wy)*nx);
 const vn=rx*nx+ry*ny+rz*nz,fn=Math.max(0,kn*overlap-gamma*vn),tx=rx-vn*nx,ty=ry-vn*ny,tz=rz-vn*nz,vt=Math.hypot(tx,ty,tz),fr=vt?Math.min(s.settings.muParticle*fn,gamma*vt)/vt:0;
 const fx=-fr*tx,fy=-fr*ty,fz=-fr*tz;
 a.ax+=fn*nx+fx;a.ay+=fn*ny+fy;a.az+=fn*nz+fz;b.ax-=fn*nx+fx;b.ay-=fn*ny+fy;b.az-=fn*nz+fz;
 const k=-2.5/r,cx=ny*fz-nz*fy,cy=nz*fx-nx*fz,cz=nx*fy-ny*fx;
 a.awx+=k*cx;a.awy+=k*cy;a.awz+=k*cz;b.awx+=k*cx;b.awy+=k*cy;b.awz+=k*cz;
 s.contacts++;s.maxOverlap=Math.max(s.maxOverlap,overlap/r);
}
function step(s,dt){
 const theta=s.c.angle*Math.PI/180,omega=(s.c.rotationDirection||-1)*s.c.rpm*TAU/60,r=s.radius,kn=s.settings.stiffness,log=Math.log(clamp(s.settings.restitution,.05,.95)),zeta=-log/Math.sqrt(Math.PI*Math.PI+log*log),gamma=2*zeta*Math.sqrt(kn),ps=s.particles;
 s.contacts=0;s.wallContacts=0;s.maxOverlap=0;
 s.angle=(s.angle+omega*dt)%TAU;s.seconds+=dt;s.steps++;
 if(r<s.baseRadius*.035)return;
 // Buoyancy and linear drag are a prescribed mixed-liquid closure, not a fluid solver.
 for(const p of ps){const buoy=s.liquid*(s.c.rhol/s.c.rhos),drag=s.liquid*s.settings.drag,slip=omega*s.settings.liquidSlip;
  p.ax=drag*(-slip*p.y-p.vx);p.ay=-9.81*Math.cos(theta)*(1-buoy)+drag*(slip*p.x-p.vy);p.az=-9.81*Math.sin(theta)*(1-buoy)-drag*p.vz;p.awx=p.awy=p.awz=0;
 }
 const cell=2*r,grid=new Map(),key=(x,y,z)=>(x+128)+(y+128)*512+(z+128)*262144;
 for(let i=0;i<ps.length;i++){const p=ps[i],x=Math.floor(p.x/cell),y=Math.floor(p.y/cell),z=Math.floor(p.z/cell);p.cx=x;p.cy=y;p.cz=z;const k=key(x,y,z),arr=grid.get(k);if(arr)arr.push(i);else grid.set(k,[i]);}
 for(let i=0;i<ps.length;i++){const p=ps[i];for(let z=-1;z<=1;z++)for(let y=-1;y<=1;y++)for(let x=-1;x<=1;x++){const bucket=grid.get(key(p.cx+x,p.cy+y,p.cz+z));if(!bucket)continue;for(const j of bucket){if(j<=i)continue;const q=ps[j],dx=p.x-q.x,dy=p.y-q.y,dz=p.z-q.z,d2=dx*dx+dy*dy+dz*dz;if(d2<4*r*r&&d2>1e-18)contact(s,p,q,dx,dy,dz,Math.sqrt(d2),r,kn,gamma/Math.SQRT2);}}}
 for(const p of ps){const wall=clearance(s,p),delta=r-wall.gap;
  if(delta>0){const {nx,ny,nz}=wall,rx=p.vx+r*(p.wy*nz-p.wz*ny)+omega*(p.y+r*ny),ry=p.vy+r*(p.wz*nx-p.wx*nz)-omega*(p.x+r*nx),rz=p.vz+r*(p.wx*ny-p.wy*nx),vn=rx*nx+ry*ny+rz*nz,fn=Math.max(0,kn*delta+gamma*vn),tx=rx-vn*nx,ty=ry-vn*ny,tz=rz-vn*nz,vt=Math.hypot(tx,ty,tz),fr=vt?Math.min(s.settings.muWall*fn,gamma*vt)/vt:0,fx=-fr*tx,fy=-fr*ty,fz=-fr*tz;
   p.ax+=-fn*nx+fx;p.ay+=-fn*ny+fy;p.az+=-fn*nz+fz;p.awx+=2.5/r*(ny*fz-nz*fy);p.awy+=2.5/r*(nz*fx-nx*fz);p.awz+=2.5/r*(nx*fy-ny*fx);s.wallContacts++;s.maxOverlap=Math.max(s.maxOverlap,delta/r);
  }
  p.vx+=p.ax*dt;p.vy+=p.ay*dt;p.vz+=p.az*dt;p.wx+=p.awx*dt;p.wy+=p.awy*dt;p.wz+=p.awz*dt;
  p.x+=p.vx*dt;p.y+=p.vy*dt;p.z+=p.vz*dt;
  // Geometric safety projection only for unusually deep soft contacts; tracked explicitly.
  const after=clearance(s,p);if(after.gap<r*.55){const push=r*.55-after.gap;p.x-=push*after.nx;p.y-=push*after.ny;p.z-=push*after.nz;s.projections=(s.projections||0)+1;const vn=p.vx*after.nx+p.vy*after.ny+p.vz*after.nz;if(vn>0){p.vx-=vn*after.nx;p.vy-=vn*after.ny;p.vz-=vn*after.nz;}}
 }
 if(s.steps%12===0)for(let i=0;i<Math.min(12,ps.length);i++){const p=ps[i];p.path.push([p.x,p.y,p.z]);if(p.path.length>65)p.path.shift();}
}
function advance(s,seconds){const limit=Math.min(.25,Math.max(0,seconds));s.discardedWallSeconds+=Math.max(0,seconds-limit);s.accumulator+=limit;const dt=Math.min(1/480,.2/Math.sqrt(s.settings.stiffness));let n=0;while(s.accumulator>=dt&&n<160){step(s,dt);s.accumulator-=dt;n++;}return n;}
function stats(s){let speed=0,energy=0,angular=0;for(const p of s.particles){const v2=p.vx*p.vx+p.vy*p.vy+p.vz*p.vz;speed+=Math.sqrt(v2);energy+=v2;angular+=p.x*p.vy-p.y*p.vx;}if(s.liquid>=1){speed=energy=angular=0;}return {seconds:s.seconds,angle:s.angle,meanSpeed:s.native?s.native.meanSpeed:(s.count?speed/s.count:0),kineticJ:.5*s.representedMass*(1-s.liquid)*energy/Math.max(1,s.count),contacts:s.contacts,wallContacts:s.wallContacts,maxOverlap:s.maxOverlap,meanAngularMomentum:angular/Math.max(1,s.count),proxyDiameterMm:2*s.baseRadius*1000,count:s.count,projectionCount:s.projections||0};}
function liquidPlane(s){
 const key=s.seconds+':'+s.liquid+':'+s.radius;if(s._planeKey===key)return s._plane;
 const c=s.c,theta=c.angle*Math.PI/180,st=Math.sin(theta),ct=Math.cos(theta),slices=root.RotaryModel.fillProfile(c,.5,220).profile,V=s.g.chargeMass*s.liquid/c.rhol,r=s.radius;let lo=-s.h-s.R,hi=s.L+s.h+s.R;
 const heights=s.particles.map(p=>p.y*ct+p.z*st);
 for(let j=0;j<36;j++){const H=(lo+hi)/2;let vessel=0,solid=0;for(const p of slices){const u=ct<1e-10?(H>=p.z*st?2:-2):(H-p.z*st)/(p.r*ct),f=u<=-1?0:u>=1?1:.5+(Math.asin(u)+u*Math.sqrt(1-u*u))/Math.PI;vessel+=p.dV*f;}for(const h of heights){const cap=Math.min(2*r,Math.max(0,H-h+r));solid+=Math.PI*cap*cap*(r-cap/3);}if(Math.max(0,vessel-solid)<V)lo=H;else hi=H;}
 s._planeKey=key;s._plane=(lo+hi)/2;return s._plane;
}
root.RotaryMotion={defaults,create,step,advance,phase,stats,clearance,liquidPlane};
})(typeof globalThis!=='undefined'?globalThis:this);
