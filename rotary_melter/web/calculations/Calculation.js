/* Rotary Melter 1.1 — reduced thermal network, SI internally. No CFD. */
(function(root){
'use strict';
const defaults={diameter:600,length:800,headDepth:150,heads:1,wall:5,shell:3,gap:15,coverage:1,contact:.65,angle:45,packing:.64,freeboard:.2,mass:180,rhos:893,rhol:782,cps:2100,cpl:2490,latent:189000,ks:.21,kl:.17,solidus:58,liquidus:62,initial:25,target:75,particle:15,steelK:16.2,steelRho:8000,steelCp:500,tin:110,flow:10,waterInitial:25,metalInitial:25,waterRho:950,waterCp:4220,waterH:1500,loopL:20,pressure:3,boiler:30,efficiency:.95,sourceMode:1,ambient:25,externalH:8,emissivity:.2,insulation:0,insulationK:.045,extraUA:0,rpm:10,href:100,rpmRef:10,rpmGain:0,rpmExponent:.5,rpmMode:1,hStatic:40,hLimit:300,rpmMax:30,rpmStep:5,maxHours:24,dt:1,goalHours:2};
function validate(c){
 for(const k of Object.keys(defaults))if(!Number.isFinite(c[k]))throw Error(k+': sonlu bir sayı girin.');
 for(const k of ['diameter','length','wall','shell','gap','mass','rhos','rhol','cps','cpl','ks','kl','steelK','steelRho','steelCp','flow','waterRho','waterCp','waterH','pressure','boiler','insulationK','href','rpmRef','maxHours','dt','goalHours'])if(c[k]<=0)throw Error(k+': sıfırdan büyük olmalı.');
 for(const k of ['headDepth','latent','loopL','externalH','extraUA','insulation','rpm','rpmGain','particle'])if(c[k]<0)throw Error(k+': negatif olamaz.');
 for(const k of ['coverage','contact','packing','efficiency'])if(c[k]<=0||c[k]>1)throw Error(k+': 0–1 aralığında, sıfırdan büyük olmalı.');
 if(c.freeboard<0||c.freeboard>=1||c.emissivity<0||c.emissivity>1)throw Error('Boş hacim veya yayma katsayısı aralık dışında.');
 if(![0,1,2].includes(c.heads)||![0,1].includes(c.sourceMode))throw Error('Bombe sayısı veya kaynak modu geçersiz.');
 if(c.headDepth>c.diameter/2)throw Error('Küresel kapak yaklaşımında bombe derinliği yarıçapı aşamaz.');
 if(c.heads>0&&c.headDepth<=0)throw Error('Bombe varsa derinlik sıfırdan büyük olmalı.');
 if(c.liquidus<=c.solidus||c.target<=c.initial)throw Error('Liquidus solidustan; hedef sıcaklık başlangıçtan büyük olmalı.');
 if([c.initial,c.target,c.ambient,c.tin,c.waterInitial,c.metalInitial,c.solidus].some(x=>x<=-273.15))throw Error('Sıcaklık mutlak sıfırın altında olamaz.');
 if(c.tin>=374||c.tin<=0)throw Error('Bu su modeli için giriş 0–374 °C arasında olmalı.');
 if(c.angle<0||c.angle>90||c.rpmExponent<0||c.rpmExponent>2)throw Error('Açı 0–90°, üs 0–2, süre ve adım pozitif olmalı.');
 if(![0,1].includes(c.rpmMode)||c.hStatic<=0||c.hLimit<=0||c.rpmMax<=0||c.rpmStep<=0)throw Error('RPM modu veya tarama aralığı geçersiz.');
 if(c.rpmMode===1&&(c.href<c.hStatic||c.hLimit<c.href||c.rpmExponent<=0))throw Error('RPM senaryosunda 0 < h₀ ≤ href ≤ hsınır ve üs > 0 olmalı.');
}
// Phenomenological sensitivity law; not a published wax/food drum correlation.
function rpmHeatTransfer(c){return c.rpmMode===0?c.href*(1+c.rpmGain*(c.rpm/c.rpmRef)**c.rpmExponent):Math.min(c.hLimit,c.hStatic+(c.href-c.hStatic)*(c.rpm/c.rpmRef)**c.rpmExponent);}
function rotation(c){const omega=2*Math.PI*c.rpm/60,r=c.diameter/2000,gNormal=9.80665*Math.cos(c.angle*Math.PI/180);return {omega,wallSpeed:omega*r,fr:omega*omega*r/9.80665,frNormal:gNormal>1e-6?omega*omega*r/gNormal:null,balanceRpm:gNormal>1e-6?60/(2*Math.PI)*Math.sqrt(gNormal/r):null};}
function migrateInputs(data){const input=data.inputs||data;const c={...defaults,...input};if(!Object.prototype.hasOwnProperty.call(input,'rpmMode'))c.rpmMode=0;validate(c);return c;}
function psat(t){const tau=1-(t+273.15)/647.096;return 220.64*Math.exp(647.096/(t+273.15)*(-7.85951783*tau+1.84408259*tau**1.5-11.7866497*tau**3+22.6807411*tau**3.5-15.9618719*tau**4+1.80122502*tau**7.5));}
function geometry(c){
 const r=c.diameter/2000,L=c.length/1000,h=c.headDepth/1000,delta=c.wall/1000,gap=c.gap/1000,sh=c.shell/1000;
 const headV=c.heads*Math.PI*h*(3*r*r+h*h)/6,volume=Math.PI*r*r*L+headV;
 const area=Math.PI*2*r*L+c.heads*Math.PI*(r*r+h*h),heated=area*c.coverage;
 const ro=r+delta+gap+sh,ho=h+delta+gap+sh;
 const external=(2*Math.PI*ro*L+c.heads*Math.PI*(ro*ro+ho*ho))*c.coverage;
 const waterV=(Math.PI*((r+delta+gap)**2-(r+delta)**2)*L+c.heads*Math.PI*(r*r+h*h)*gap)*c.coverage+c.loopL/1000;
 const mInner=area*delta*c.steelRho,mOuter=external*sh*c.steelRho;
 const liquidV=c.mass/c.rhol,bulkV=c.mass/(c.rhos*c.packing),solidV=c.mass/c.rhos;
 const limit=volume*(1-c.freeboard),maxMass=Math.min(limit*c.rhos*c.packing,limit*c.rhol);
 return {volume,headV,area,heated,external,waterV,mInner,mOuter,liquidV,bulkV,solidV,maxMass,feasible:bulkV<=limit&&liquidV<=limit,bulkFill:bulkV/volume,liquidFill:liquidV/volume};
}
function enthalpy(c,t){const cm=(c.cps+c.cpl)/2+c.latent/(c.liquidus-c.solidus),hs=c.cps*c.solidus,hl=hs+cm*(c.liquidus-c.solidus);return t<=c.solidus?c.cps*t:t<c.liquidus?hs+cm*(t-c.solidus):hl+c.cpl*(t-c.liquidus);}
function temperature(c,h){const cm=(c.cps+c.cpl)/2+c.latent/(c.liquidus-c.solidus),hs=c.cps*c.solidus,hl=hs+cm*(c.liquidus-c.solidus);return h<=hs?h/c.cps:h<hl?c.solidus+(h-hs)/cm:c.liquidus+(h-hl)/c.cpl;}
function surface(c,g,ts){
 const sigma=5.670374419e-8,area=g.external,ta=c.ambient;
 const loss=t=>({conv:c.externalH*area*(t-ta),rad:c.emissivity*sigma*area*((t+273.15)**4-(ta+273.15)**4)});
 let surf=ts;
 if(c.insulation>0){const K=c.insulationK*area/(c.insulation/1000);let lo=Math.min(ts,ta),hi=Math.max(ts,ta);for(let i=0;i<32;i++){const t=(lo+hi)/2,q=loss(t);if(K*(ts-t)-q.conv-q.rad>0)lo=t;else hi=t;}surf=(lo+hi)/2;}
 return {surface:surf,...loss(surf)};
}
function simulate(input,options={}){
 const c={...defaults,...input};validate(c);const g=geometry(c),h0=enthalpy(c,c.initial),targetH=enthalpy(c,c.target),cm=c.mass*Math.min(c.cps,c.cpl);
 const hp=rpmHeatTransfer(c);
 const Gp=g.heated*c.contact/(1/hp+c.wall/2000/c.steelK),Gw=g.heated/(1/c.waterH+c.wall/2000/c.steelK),Go=g.external/(1/c.waterH+c.shell/2000/c.steelK);
 const Cw=g.mInner*c.steelCp,Cj=g.waterV*c.waterRho*c.waterCp,Cs=g.mOuter*c.steelCp,F=c.flow/3600*c.waterRho*c.waterCp;
 const dt=Math.min(c.dt,.18*cm/Gp,.18*Cw/(Gp+Gw),.18*Cj/(Gw+Go+F+c.extraUA),.18*Cs/(Go+g.external*(c.externalH+4*5.670374419e-8*c.emissivity*(Math.max(c.tin,c.waterInitial,c.metalInitial)+273.15)**3)));
 if(c.maxHours*3600/dt>2500000)throw Error('Bu parametreler çok küçük zaman adımı gerektiriyor. Süreyi azaltın veya çok ince sac/küçük hacimleri kontrol edin.');
 let y=[c.mass*h0,c.metalInitial,c.waterInitial,c.metalInitial],t=0,ein=0,eloss=0,econv=0,erad=0,eextra=0,peak=0,peakLoss=0,meltingTime=c.initial>=c.liquidus?0:null;
 const hist=[],end=c.maxHours*3600,recordEvery=Math.max(10,end/600);let nextRecord=0;
 function rates(v){const tp=temperature(c,v[0]/c.mass),s=surface(c,g,v[3]);const qp=Gp*(v[1]-tp),qw=Gw*(v[2]-v[1]),qo=Go*(v[2]-v[3]);const requested=Math.max(0,F*(c.tin-v[2])),qin=c.sourceMode?requested:Math.min(requested,c.boiler*1000*c.efficiency),extra=c.extraUA*(v[2]-c.ambient),ql=s.conv+s.rad+extra;
 return {dy:[qp,(qw-qp)/Cw,(qin-qw-qo-extra)/Cj,(qo-s.conv-s.rad)/Cs],tp,qp,qin,ql,conv:s.conv,rad:s.rad,extra,surface:s.surface,tin:v[2]+qin/F};}
 function record(){const r=rates(y);hist.push({seconds:t,product:r.tp,liquidFraction:Math.max(0,Math.min(1,(r.tp-c.solidus)/(c.liquidus-c.solidus))),wall:y[1],waterOut:y[2],waterIn:r.tin,shell:y[3],surface:r.surface,productKW:r.qp/1000,boilerWaterKW:r.qin/1000,lossKW:r.ql/1000,inputKWh:ein/3.6e6,lossKWh:eloss/3.6e6});}
 while(t<end&&y[0]<c.mass*targetH){
  if(t>=nextRecord){record();nextRecord+=recordEvery;}
  const step=Math.min(dt,end-t),r=rates(y),mid=y.map((v,i)=>v+r.dy[i]*step/2),m=rates(mid);
  y=y.map((v,i)=>v+m.dy[i]*step);t+=step;ein+=m.qin*step;eloss+=m.ql*step;econv+=m.conv*step;erad+=m.rad*step;eextra+=m.extra*step;peak=Math.max(peak,m.qin);peakLoss=Math.max(peakLoss,m.ql);
  if(meltingTime===null&&y[0]>=c.mass*enthalpy(c,c.liquidus))meltingTime=t;
 }
 record();const storedProduct=y[0]-c.mass*h0,storedMetal=Cw*(y[1]-c.metalInitial)+Cs*(y[3]-c.metalInitial),storedWater=Cj*(y[2]-c.waterInitial),balance=ein-eloss-storedProduct-storedMetal-storedWater;
 return {c,g,hp,Gp,Gw,Go,dt,hist:options.noHistory?[]:hist,targetReached:y[0]>=c.mass*targetH,seconds:t,meltingTime,productEnergyKWh:c.mass*(targetH-h0)/3.6e6,energyInKWh:ein/3.6e6,sourceEnergyKWh:ein/c.efficiency/3.6e6,lossKWh:eloss/3.6e6,convKWh:econv/3.6e6,radKWh:erad/3.6e6,extraKWh:eextra/3.6e6,storedProductKWh:storedProduct/3.6e6,storedMetalKWh:storedMetal/3.6e6,storedWaterKWh:storedWater/3.6e6,balanceJ:balance,peakKW:peak/1000,peakLossKW:peakLoss/1000,psat:psat(c.tin),last:hist[hist.length-1]};
}
function sizeBoiler(input){const c={...defaults,...input,sourceMode:0,maxHours:input.goalHours||defaults.goalHours};let lo=.01,hi=1000;const top=simulate({...c,boiler:hi},{noHistory:true});if(!top.targetReached)return {possible:false};let result=top;for(let i=0;i<13;i++){const mid=(lo+hi)/2,r=simulate({...c,boiler:mid},{noHistory:true});if(r.targetReached){hi=mid;result=r;}else lo=mid;}return {possible:true,kw:hi,result};}
root.RotaryModel={defaults,validate,geometry,enthalpy,temperature,simulate,sizeBoiler,psat,rpmHeatTransfer,rotation,migrateInputs};
if(typeof module!=='undefined')module.exports=root.RotaryModel;
})(typeof globalThis!=='undefined'?globalThis:this);
