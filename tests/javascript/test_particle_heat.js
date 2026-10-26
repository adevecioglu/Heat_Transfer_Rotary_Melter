/* node tests_v16.js: numerical verification, not material/plant validation. */
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),ctx=vm.createContext({console});
for(const name of ['../../rotary_melter/web/calculations/Calculation.js','../../rotary_melter/web/calculations/GeometryAndHydraulics.js','../../rotary_melter/web/calculations/WaterCircuit.js','../../rotary_melter/web/calculations/RegionalHeatTransfer.js','../../rotary_melter/web/calculations/ParticleHeatTransfer.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,name),'utf8'),ctx);
const M=ctx.RotaryModel,checks=[];function check(name,ok,value){checks.push({name,passed:!!ok,value});if(!ok)throw Error(name);}
const c={...M.defaults},r=M.simulate(c);check('Physical granule diameter',r.model.granuleDiameterMm===15);check('Radial temperature fields',r.last.radialNear.length===12&&r.last.radialCore.length===12);check('Cold center reaches target',r.last.coreProduct>=c.target);check('All-temperature bounds',r.hist.every(p=>[...p.radialNear,...p.radialCore,...p.innerSurface,...p.outerSurface,...p.waterZones].every(x=>Number.isFinite(x)&&x>=24.99&&x<=110.01)));check('Energy conservation',r.balanceRelative<1e-10,r.balanceRelative);
const half=M.simulate({...c,dt:r.dt/2},{noHistory:true});check('Time refinement',Math.abs(r.seconds-half.seconds)/r.seconds<.001);
const limited=M.simulate({...c,boiler:2,maxHours:.03,sourceMode:0},{noHistory:true});check('Boiler cap',limited.peakKW<=2*c.efficiency+1e-9);
const ad=M.simulate({...c,externalH:0,emissivity:0,extraUA:0,maxHours:.03},{noHistory:true});check('Adiabatic exterior',Math.abs(ad.lossKWh)<1e-12);
const cw=M.simulate({...c,maxHours:.03,rotationDirection:-1},{noHistory:true}),ccw=M.simulate({...c,maxHours:.03,rotationDirection:1},{noHistory:true});check('Direction symmetry for unbaffled symmetric idealization',Math.abs(cw.last.product-ccw.last.product)<1e-8);
const fine=M.simulate({...c,axialZones:32,angularZones:48,initial:74,target:75,metalInitial:75},{noHistory:true});check('Former estimated-step rejection removed',24*3600/fine.dt>3500000&&fine.targetReached);
const maxcase={...c,maxHours:1000,dt:20};M.validate(maxcase);check('No arbitrary maximum time/step input rejection',true);
console.log(JSON.stringify({version:'1.6.0',experimentalValidation:false,checks},null,2));
