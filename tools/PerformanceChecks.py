from rotary_melter.Paths import DEFAULT_CONFIG, OUTPUTS_DIR
"""Portable physical-size DEM endurance / same-force-law A/B runner.
Examples:
 python performance_checks.py --seconds 1200 --engine fast --out test_output
 python performance_checks.py --compare Example_DEM_end_state.npz --out comparison
"""
import argparse,json,time,math,platform,os
from pathlib import Path
import numpy as np
from numba import types
from numba.typed import Dict
from rotary_melter.dynamics import ContactDynamics as native
from rotary_melter.dynamics.FastContactDynamics import integrate_fast

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seconds',type=float,default=1200);parser.add_argument('--engine',choices=['grid','fast'],default='fast');parser.add_argument('--out',type=Path,default=Path('performance_output'));parser.add_argument('--compare',type=Path);parser.add_argument('--inputs',type=Path,default=Path(__file__).parent/'default_inputs.json');args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    fresh=lambda:Dict.empty(types.int64,types.UniTuple(types.float64,4))
    if args.compare:
        d=np.load(args.compare);p=d['p'];r=float(d['r']);g=d['g'];dt=min(.0002,.15/math.sqrt(g[6]));omega=-10*2*math.pi/60;rows=[];states=[]
        # Compile on a small subset first; exclude compilation from the timed A/B runs.
        for fn in [native.integrate,integrate_fast]:fn(p[:20].copy(),r,g,fresh(),0,1,dt,omega)
        for fn in [native.integrate,integrate_fast]:
            pp=p.copy();start=time.perf_counter();stats=fn(pp,r,g,fresh(),0,100,dt,omega);rows.append({'engine':fn.__name__,'wallSeconds':time.perf_counter()-start,'contactPairs':int(stats[0])});states.append(pp)
        diff=float(np.max(np.abs(states[0]-states[1])));result={'kind':'same-force-law A/B, 100 steps','count':len(p),'maxStateDifference':diff,'passed':diff<1e-8,'timings':rows,'experimentalValidation':False}
    else:
        c=json.loads(args.inputs.read_text(encoding='utf-8'))['inputs']
        if args.engine=='grid':native.integrate_fast=native.integrate
        start=time.perf_counter();m=native.DEM(c,{'settle':.75});events=[];last=0
        while time.perf_counter()-start<args.seconds:
            m.advance(50,settling=m.settled<.75);elapsed=time.perf_counter()-start
            if elapsed-last>=10:events.append(m.metrics());print(json.dumps(events[-1]),flush=True);last=elapsed
        result={'kind':'computer wall-clock endurance','engine':args.engine,'requestedWallSeconds':args.seconds,'elapsedWallSeconds':time.perf_counter()-start,'final':m.metrics(),'events':events,'passed':m.escaped==0 and bool(np.isfinite(m.p).all()),'quantitativeDenseFlowVerified':False,'experimentalValidation':False}
        np.savez_compressed(args.out/'end_state.npz',p=m.p,g=m.g,r=m.r,metrics=json.dumps(m.metrics()))
    result['environment']={'platform':platform.platform(),'python':platform.python_version(),'logicalCPUs':os.cpu_count()};(args.out/'report.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
