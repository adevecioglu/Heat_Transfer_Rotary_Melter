/* Mesh/time/radial separation. No arbitrary mesh, step-count or runtime cap. */
(function(root){
'use strict';const M=root.RotaryModel;
Object.assign(M.defaults,{axialZones:16,angularZones:16,radialZones:24});
M.gridIndex=function(coarse,medium,fine,r=2,noise=0){
 const d32=coarse-medium,d21=medium-fine,base={available:false,refinementRatio:r,noiseFloor:noise};
 if(![coarse,medium,fine,r].every(Number.isFinite)||r<=1||!fine)return {...base,reason:'invalid'};
 if(Math.min(Math.abs(d32),Math.abs(d21))<=noise)return {...base,reason:'below_time_resolution'};
 if(d32*d21<=0)return {...base,reason:'nonmonotonic'};
 const order=Math.log(Math.abs(d32/d21))/Math.log(r);
 if(!(order>0))return {...base,reason:'not_contracting'};
 const den=r**order-1,gciFine=1.25*Math.abs(d21/fine)/den,gciMedium=1.25*Math.abs(d32/medium)/den;
 return {...base,available:true,order,gciFine,gciMedium,extrapolated:fine+(fine-medium)/den,asymptoticRatio:gciMedium/(r**order*gciFine),reason:'conditional_estimate',note:'Conditional numerical estimator; three grids alone do not establish an asymptotic range or physical validity.'};
};
M.verifyCase=function(input,progress){
 const c={...M.defaults,...input},co={...c,axialZones:Math.max(2,Math.floor(c.axialZones/2)),angularZones:Math.max(4,Math.floor(c.angularZones/2))},fi={...c,axialZones:c.axialZones*2,angularZones:c.angularZones*2};
 // Use one common stable time step for all three spatial grids and radial test.
 const ra={...c,radialZones:c.radialZones*2},commonDt=Math.min(...[co,c,fi,ra].map(x=>M.thermalSpec(x).dt));
 const brief=r=>({axial:r.c.axialZones,angular:r.c.angularZones,radial:r.c.radialZones,dt:r.dt,steps:r.steps,targetReached:r.targetReached,targetHours:r.targetReached?r.seconds/3600:null,coreFinal:r.last.coreProduct,energyKWh:r.sourceEnergyKWh,waterOut:r.last.waterOut,surfaceMin:r.last.surfaceMin,surfaceMax:r.last.surfaceMax,balanceRelative:r.balanceRelative});
 const run=(x,stage)=>{if(progress)progress(stage);return M.simulate({...x,dt:commonDt},{noHistory:true});};
 const coarse=run(co,'coarse'),base=run(c,'base'),fine=run(fi,'fine');if(progress)progress('time');const half=M.simulate({...c,dt:commonDt/2},{noHistory:true}),radial=run(ra,'radial');
 const metric=(a,b)=>a.targetReached&&b.targetReached?Math.abs(a.seconds-b.seconds)/b.seconds:null;
 const equalRatio=co.axialZones*2===c.axialZones&&co.angularZones*2===c.angularZones;
 const gridIndex=equalRatio&&[coarse,base,fine].every(x=>x.targetReached)?M.gridIndex(coarse.seconds,base.seconds,fine.seconds,2,Math.max(4*commonDt,4*Math.abs(base.seconds-half.seconds))):{available:false,reason:equalRatio?'target_not_reached':'unequal_refinement'};
 return {version:'1.9',base:brief(base),halfTimeStep:brief(half),coarse:brief(coarse),fine:brief(fine),radialFine:brief(radial),commonDt,timeDifference:metric(base,half),gridDifference:metric(base,fine),radialDifference:metric(base,radial),gridIndex,note:'Spatial comparison uses identical dt and radial cells. Radial and time refinements are separate. Numerical verification is not experimental validation.'};
};
})(typeof globalThis!=='undefined'?globalThis:this);
