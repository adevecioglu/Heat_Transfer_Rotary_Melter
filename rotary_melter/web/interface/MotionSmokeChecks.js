async function motionUiSmoke(){
 const original=state.result,inputs=preserveFields(),settings=motionSettings(),checks={};
 try{
  renderFields({...original.c,diameter:120,length:160,headDepth:30,targetFill:.3});onInput('angle');
  $('motionSolver').value='rigid';$('motionDt').value=1/960;$('motionIterations').value=64;$('motionPosition').value=12;$('motionDuration').value=.06;$('motionSettle').value=.04;$('motionPhase').value=0;$('motionFollow').checked=false;$('motionLoop').checked=false;
  checks.previewLazy=motionState.system===null;const initial=motionEnsure(state.preview);const before=initial.particles.map(p=>[p.x,p.y,p.z]);await motionStart();const deadline=performance.now()+60000;
  while(motionState.running&&performance.now()<deadline)await new Promise(resolve=>setTimeout(resolve,50));
  motionPause();const frames=motionState.frames,last=frames.at(-1);checks.nativeStartCompleted=!motionState.running&&last?.stats.solver==='rigid';checks.frames=frames.length>=2;
  if(last){motionSeek(last.time);checks.vesselRotates=last.stats.phase<0;checks.granulesMove=motionState.system.particles.some((p,i)=>Math.abs(p.x-before[i][0])+Math.abs(p.y-before[i][1])+Math.abs(p.z-before[i][2])>1e-5);checks.settlingIncluded=last.time>last.seconds;}
  checks.timeline=!$('motionTimeline').disabled;motionReplay();checks.replayStarts=motionState.replaying;await motionTogglePause();checks.replayPauses=!motionState.replaying;
  motionBody();const a=motionState.system.angle;motionAdvanceBody(.15);drawMotionNow();checks.bodyRotation=motionState.system.angle!==a;motionPause();
  const defaultMotion={solver:'rigid',dt:1/960,iterations:64,positionIterations:12,muWall:.45,muParticle:.35,restitution:.25,settle:.4,duration:2,liquid:0};
  const demo=await window.pywebview.api.demo_info(original.c,defaultMotion);checks.demoCheckResponds=demo.ok;
  if(demo.available){const frames=await window.pywebview.api.demo_frames(0,2);checks.packagedDemo=frames.ok&&frames.frames.length===2&&frames.frames[0].count===45120;const mismatch=await window.pywebview.api.demo_info({...original.c,angle:original.c.angle+1},defaultMotion);checks.demoRejectsOtherGeometry=!mismatch.available;}else checks.packagedDemo=false;
  const required=Object.entries(checks).filter(([key])=>!['packagedDemo','demoRejectsOtherGeometry'].includes(key));return {...checks,passed:required.every(([,value])=>!!value)};
 }catch(e){return {...checks,passed:false,error:e.stack};}
 finally{motionInvalidate();renderFields(inputs);motionLoadSettings(settings);state.result=original;state.inputs={...original.c};state.preview=null;state.dirty=false;state.seconds=original.seconds;renderStatic();drawDisplay();}
}
