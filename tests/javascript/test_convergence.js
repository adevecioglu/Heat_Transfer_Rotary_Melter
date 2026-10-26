/* Focused regression tests. Full default mesh results are saved separately. */
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path'),ctx=vm.createContext({console});
for(const name of ['../../rotary_melter/web/calculations/Calculation.js','../../rotary_melter/web/calculations/GeometryAndHydraulics.js','../../rotary_melter/web/calculations/WaterCircuit.js','../../rotary_melter/web/calculations/RegionalHeatTransfer.js','../../rotary_melter/web/calculations/ParticleHeatTransfer.js','../../rotary_melter/web/calculations/Convergence.js'])vm.runInContext(fs.readFileSync(path.join(__dirname,name),'utf8'),ctx);
const M=ctx.RotaryModel,checks=[];function check(name,ok,value){checks.push({name,passed:!!ok,value});if(!ok)throw Error(name);}
check('Fine defaults',M.defaults.axialZones===16&&M.defaults.angularZones===16&&M.defaults.radialZones===24);
const synthetic=M.gridIndex(1.016,1.004,1.001);check('Known second-order sequence',Math.abs(synthetic.order-2)<1e-10&&Math.abs(synthetic.extrapolated-1)<1e-10);
check('Oscillating sequence not claimed converged',!M.gridIndex(1.01,.99,1.005).available);
check('Diverging sequence not claimed converged',!M.gridIndex(1.001,1.002,1.004).available);
check('Time-quantized sequence not claimed converged',!M.gridIndex(100,99.9,99.85,2,.06).available);
const warm={...M.defaults,initial:74,target:75,metalInitial:75};
for(const n of [8,16,32]){const r=M.simulate({...warm,axialZones:n,angularZones:n},{noHistory:true});check(n+'x'+n+' solves without region reduction',r.targetReached&&r.mesh.axial===n&&r.mesh.angular===n&&r.balanceRelative<1e-9,{seconds:r.seconds,steps:r.steps,balance:r.balanceRelative});}
M.validate({...M.defaults,axialZones:64,angularZones:96});check('No former 24/32 grid cap',true);
const migrated=M.migrateInputs({inputs:{axialZones:8,angularZones:8}});check('JSON grid selection preserved',migrated.axialZones===8&&migrated.angularZones===8);
const v=M.verifyCase({...warm,axialZones:8,angularZones:8,radialZones:8});
check('Spatial grids use identical dt',v.coarse.dt===v.base.dt&&v.base.dt===v.fine.dt);
check('Time and radial controls independent',v.halfTimeStep.dt===v.base.dt/2&&v.radialFine.radial===16&&v.radialFine.axial===8);
console.log(JSON.stringify({version:'1.9.0',experimentalValidation:false,checks},null,2));
