/* Thermal-result replay. Geometry is a volume-preserving visual closure,
   not a new particle-resolved melting or melt-flow CFD solution. */
(function(root){'use strict';const M=root.RotaryModel;
const clamp=x=>Math.max(0,Math.min(1,x)),phase=(c,t)=>clamp((t-c.solidus)/(c.liquidus-c.solidus));
function at(result,seconds){
 const H=result.hist;if(!H?.length)return result.last;const time=Math.max(0,Math.min(result.seconds,seconds));let hi=H.findIndex(p=>p.seconds>=time);if(hi<0)return H.at(-1);const a=H[Math.max(0,hi-1)],b=H[hi],u=b.seconds===a.seconds?0:(time-a.seconds)/(b.seconds-a.seconds),p={};
 for(const key of Object.keys(b)){if(Array.isArray(b[key]))p[key]=b[key].map((v,i)=>a[key][i]+u*(v-a[key][i]));else p[key]=a[key]+u*(b[key]-a[key]);}
 // Cross a phase interval in enthalpy, not by linear temperature interpolation.
 for(const key of ['radialNear','radialCore'])p[key]=b[key].map((t,i)=>M.temperature(result.c,M.enthalpy(result.c,a[key][i])+u*(M.enthalpy(result.c,t)-M.enthalpy(result.c,a[key][i]))));
 const K=p.radialNear.length,weights=Array.from({length:K},(_,i)=>((i+1)**3-i**3)/K**3),pop=array=>array.reduce((q,t,i)=>q+weights[i]*phase(result.c,t),0);
 p.nearLiquidFraction=pop(p.radialNear);p.coreLiquidFraction=pop(p.radialCore);p.liquidFraction=result.c.nearFraction*p.nearLiquidFraction+(1-result.c.nearFraction)*p.coreLiquidFraction;p.seconds=time;
 p.nearProduct=p.radialNear.reduce((s,t,i)=>s+weights[i]*t,0);p.coreMean=p.radialCore.reduce((s,t,i)=>s+weights[i]*t,0);p.coreProduct=Math.min(p.radialNear[0],p.radialCore[0]);p.product=result.c.nearFraction*p.nearProduct+(1-result.c.nearFraction)*p.coreMean;
 return p;
}
function summary(r,p){const c=r.c,f=clamp(p.liquidFraction),solidMass=c.mass*(1-f),liquidMass=c.mass*f;
 return {fraction:f,solidMass,liquidMass,solidVolume:solidMass/c.rhos,liquidVolume:liquidMass/c.rhol,equivalentDiameterMm:c.particle*Math.cbrt(1-f),nearEquivalentDiameterMm:c.particle*Math.cbrt(1-p.nearLiquidFraction),coreEquivalentDiameterMm:c.particle*Math.cbrt(1-p.coreLiquidFraction),massResidualKg:solidMass+liquidMass-c.mass};}
function create(r){
 const spacingFactor=Math.max(1,Math.cbrt((Math.PI/(3*Math.SQRT2))/r.c.packing)),s=root.RotaryMotion.create(r.c,{spacingFactor}),theta=r.c.angle*Math.PI/180,st=Math.sin(theta),ct=Math.cos(theta),R=s.R,h=s.h,rs=s.Rs;
 let anchor=[0,-R,0];if(r.c.heads>0){const z=rs-h-rs*st;if(z<=0&&z>=-h-1e-12)anchor=[0,-rs*ct,z];}
 const base=s.particles.map(p=>[p.x,p.y,p.z]),height=base.map(p=>p[1]*ct+p[2]*st).sort((a,b)=>a-b),prefix=[new Float64Array(height.length+1),new Float64Array(height.length+1),new Float64Array(height.length+1)];
 for(let i=0;i<height.length;i++)for(let j=0;j<3;j++)prefix[j][i+1]=prefix[j][i]+height[i]**(j+1);
 const slices=M.fillProfile(r.c,.5,300).profile,Ha=anchor[1]*ct+anchor[2]*st;
 return {s,base,height,prefix,slices,anchor,Ha,st,ct,normalization:(r.c.mass/r.c.rhos)/(s.count*4*Math.PI*s.baseRadius**3/3),lastScale:NaN,lastFraction:NaN};
}
function index(a,x){let lo=0,hi=a.length;while(lo<hi){const m=(lo+hi)>>1;if(a[m]<=x)lo=m+1;else hi=m;}return lo;}
function solidBelow(g,H,scale){
 if(scale<=0)return 0;const r=g.s.baseRadius*scale,N=g.height.length,A=H-g.Ha+scale*g.Ha;
 const lower=index(g.height,(H-r-g.Ha)/scale+g.Ha),upper=index(g.height,(H+r-g.Ha)/scale+g.Ha),n=upper-lower,S1=g.prefix[0][upper]-g.prefix[0][lower],S2=g.prefix[1][upper]-g.prefix[1][lower],S3=g.prefix[2][upper]-g.prefix[2][lower];
 const U1=n*A-scale*S1,U3=n*A**3-3*A*A*scale*S1+3*A*scale*scale*S2-scale**3*S3;
 const v=lower*4*Math.PI*r**3/3+Math.PI/3*(2*n*r**3+3*r*r*U1-U3);
 return Math.max(0,Math.min(N*4*Math.PI*r**3/3,v))*g.normalization;
}
function vesselBelow(g,H){
 // Integrate disk occupancy across each finite axial slice. A midpoint-only
 // disk turns into discontinuous volume jumps as inclination approaches 90°.
 const disk=u=>u<=-1?0:u>=1?1:.5+(Math.asin(u)+u*Math.sqrt(1-u*u))/Math.PI;
 const primitive=u=>u<=-1?0:u>=1?u:u/2+(u*Math.asin(u)+Math.sqrt(1-u*u)-(1-u*u)**1.5/3)/Math.PI;
 let volume=0;for(const p of g.slices){const width=p.dz*g.st,transverse=p.r*g.ct;let f;
  if(transverse<1e-10)f=width>0?clamp((H-(p.z-p.dz/2)*g.st)/width):(H>=0?1:0);
  else if(width<1e-10)f=disk((H-p.z*g.st)/transverse);
  else {const a=(H-(p.z+p.dz/2)*g.st)/transverse,b=(H-(p.z-p.dz/2)*g.st)/transverse;f=clamp((primitive(b)-primitive(a))/(b-a));}
  volume+=p.dV*f;
 }return volume;
}
function level(g,liquidVolume,scale){if(liquidVolume<=0)return g.Ha-g.s.baseRadius;let lo=-g.s.h-g.s.R,hi=g.s.L+g.s.h+g.s.R;for(let i=0;i<44;i++){const H=(lo+hi)/2;if(vesselBelow(g,H)-solidBelow(g,H,scale)<liquidVolume)lo=H;else hi=H;}return (lo+hi)/2;}
function apply(g,r,p,bodyAngle=0){const q=summary(r,p),scale=Math.cbrt(Math.max(0,1-q.fraction)),s=g.s;
 if(scale!==g.lastScale){for(let i=0;i<s.count;i++){const b=g.base[i],v=s.particles[i];v.x=g.anchor[0]+scale*(b[0]-g.anchor[0]);v.y=g.anchor[1]+scale*(b[1]-g.anchor[1]);v.z=g.anchor[2]+scale*(b[2]-g.anchor[2]);}g.lastScale=scale;}
 s.radius=s.baseRadius*scale;s.liquid=q.fraction;s.seconds=p.seconds;s.angle=bodyAngle;s.liquidPlane=level(g,q.liquidVolume,scale);s.native=null;
 return {...q,level:s.liquidPlane,scale,liquidVolumeResidual:vesselBelow(g,s.liquidPlane)-solidBelow(g,s.liquidPlane,scale)-q.liquidVolume};
}
function energyBalance(r,p,S){const K=p.radialNear.length,w=Array.from({length:K},(_,i)=>((i+1)**3-i**3)/K**3),H0=M.enthalpy(r.c,r.c.initial);let Ep=0,Em=0,Ew=0;for(let j=0;j<K;j++)Ep+=r.c.mass*w[j]*(r.c.nearFraction*(M.enthalpy(r.c,p.radialNear[j])-H0)+(1-r.c.nearFraction)*(M.enthalpy(r.c,p.radialCore[j])-H0));for(let j=0;j<S.mesh.N;j++)Em+=S.Ci[j]*(p.innerSurface[j]-r.c.metalInitial)+S.Co[j]*(p.outerMetal[j]-r.c.metalInitial);for(let a=0;a<S.mesh.A;a++)Ew+=S.Cj[a]*(p.waterZones[a]-r.c.waterInitial);const residual=(p.inputKWh-p.lossKWh)*3.6e6-Ep-Em-Ew;return {productJ:Ep,metalJ:Em,waterJ:Ew,residualJ:residual,relative:Math.abs(residual)/Math.max(1,p.inputKWh*3.6e6)};}
root.MeltReplay={at,summary,create,apply,solidBelow,vesselBelow,level,phase,energyBalance};
})(typeof globalThis!=='undefined'?globalThis:this);
