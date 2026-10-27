"""Validate the full default particle count and save a provenance-bearing recording.

All artifacts stay in outputs. Create CANCEL in the printed run directory to stop
between native batches. A cancelled/failed run never publishes a reusable cache.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time
import numpy as np
from rotary_melter.Configuration import load_inputs
from rotary_melter.NativeEngine import info
from rotary_melter.dynamics.ContactDynamics import DEM
from rotary_melter.Paths import OUTPUTS_DIR


def validate():
    directory=OUTPUTS_DIR/'full_motion'/datetime.now().strftime('%Y%m%d_%H%M%S')
    directory.mkdir(parents=True,exist_ok=True)
    c=load_inputs()['inputs']
    settings={'solver':'rigid','dt':1/960,'iterations':64,'positionIterations':12,'muWall':.45,
              'muParticle':.35,'restitution':.25,'settle':.4,'duration':2.,'liquid':0.,'backend':'cpp'}
    backend=info()
    report={'createdUtc':datetime.now(timezone.utc).isoformat(),'inputs':c,'settings':settings,'backend':backend,
            'experimentalValidation':False,'status':'running','passed':False}
    print('Full-size motion validation:',directory,flush=True)
    frames=[];positions=[];started=time.perf_counter();next_frame=0;next_log=0

    def write_status():
        report['wallSeconds']=time.perf_counter()-started
        temporary=directory/'progress.tmp'
        temporary.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
        temporary.replace(directory/'progress.json')

    try:
        dem=DEM(c,settings)
        report['count']=dem.count
        frames.append(dem.metrics())
        positions.append(dem.p[:,:3].astype('<f4').copy())
        next_frame=.025
        while dem.settled+dem.seconds < settings['settle']+settings['duration']-1e-10:
            if (directory/'CANCEL').exists():
                report['status']='cancelled'
                write_status()
                return directory
            settling=dem.settled<settings['settle']-1e-10
            remaining=settings['settle']-dem.settled if settling else settings['duration']-dem.seconds
            dem.advance(max(1,min(4,round(remaining/dem.dt))),settling)
            physical=dem.seconds+dem.settled
            if physical+1e-10>=next_frame:
                frames.append(dem.metrics())
                positions.append(dem.p[:,:3].astype('<f4').copy())
                next_frame=physical+.025
            report['last']=dem.metrics()
            if time.perf_counter()>=next_log:
                write_status()
                print(f"{physical:.4f} / 2.4 physical s; {report['wallSeconds']:.1f} wall s; overlap/r {dem.last[2]:.5g}",flush=True)
                next_log=time.perf_counter()+15
        report['status']='complete'
        report['passed']=dem.escaped==0 and np.isfinite(dem.p).all() and dem.max_overlap<.1
        report['last']=dem.metrics()
        if frames[-1]['seconds']+frames[-1]['settledSeconds'] < dem.seconds+dem.settled-1e-9:
            frames.append(dem.metrics())
            positions.append(dem.p[:,:3].astype('<f4').copy())
        report['frameCount']=len(frames)
        record=directory/'motion_cpp_record.npz'
        if report['passed']:
            np.savez_compressed(record,inputs=json.dumps(c),settings=json.dumps(settings),metadata=json.dumps(frames),
                                positions=np.asarray(positions),provenance=json.dumps(report,default=lambda v:bool(v) if isinstance(v,np.bool_) else v))
            report['recordingSha256']=hashlib.sha256(record.read_bytes()).hexdigest()
        report['passed']=bool(report['passed'])
        write_status()
        lines=['# Full-size native motion validation','',f"Particles: {dem.count}; physical time: {dem.seconds+dem.settled:.8g} s.",'',
            f"C++ source fingerprint: `{backend['sourceFingerprint']}`.",'',
            f"Final overlap/radius: {dem.last[2]:.8g}; maximum: {dem.max_overlap:.8g}; escaped: {dem.escaped}.",'',
            f"Wall time: {report['wallSeconds']:.8g} s; passed numerical finite/containment gates: {report['passed']}.",'',
            'This is a numerical contact/containment check of an uncalibrated rigid-sphere approximation. '
            'It is not experimental validation or a resolved liquid-flow simulation.','']
        (directory/'MOTION_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
        print('Complete:',directory,flush=True)
        if not report['passed']:
            raise RuntimeError('Full-size motion validation failed.')
        return directory
    except Exception as error:
        report.update(status='error',error=str(error),passed=False)
        write_status()
        raise


if __name__=='__main__':
    validate()
