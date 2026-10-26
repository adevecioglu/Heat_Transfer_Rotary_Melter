from pathlib import Path
import sys,json,time,math
import numpy as np
from rotary_melter.Paths import DEFAULT_CONFIG, OUTPUTS_DIR
OUTPUTS_DIR.mkdir(exist_ok=True)
from rotary_melter.dynamics.ContactDynamics import DEM
def run():
    c=json.loads(DEFAULT_CONFIG.read_text(encoding='utf-8'))['inputs'];c.update(diameter=120,length=160,headDepth=30,targetFill=.3)
    results=[]
    for method,dt in [('compliant',.00003),('rigid',1/960)]:
     d=DEM(c,dict(solver=method,dt=dt,iterations=64,positionIterations=12));start=time.perf_counter()
     for settling,seconds in [(True,.3),(False,2.)]:
      remaining=math.ceil(seconds/d.dt)
      while remaining:
       n=min(200,remaining);d.advance(n,settling);remaining-=n
     met=d.metrics();met['benchmarkSeconds']=time.perf_counter()-start;results.append(met)
    a,b=results
    out=dict(numericalCrossCheckOnly=True,experimentalValidation=False,geometry='120 mm ID, 160 mm cylinder, 30 mm head, 217 actual 15 mm granules; not the full 600 mm vessel',models=results,relativeOrbitalSpeedDifference=abs(a['meanOrbitalRPM']-b['meanOrbitalRPM'])/max(1e-9,abs(a['meanOrbitalRPM'])),relativeMeanSpeedDifference=abs(a['meanSpeed']-b['meanSpeed'])/max(1e-9,abs(a['meanSpeed'])))
    (OUTPUTS_DIR/'validation_contact_model_comparison.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out,indent=2))


if __name__ == "__main__":
    run()
