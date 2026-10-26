from pathlib import Path
import sys,json,math,time
import numpy as np
from rotary_melter.Paths import DEFAULT_CONFIG, OUTPUTS_DIR
OUTPUTS_DIR.mkdir(exist_ok=True)
from rotary_melter.dynamics.ContactDynamics import DEM,MotionJobs
from rotary_melter.dynamics.RigidBodyDynamics import integrate_rigid
def run():
    c=json.loads(DEFAULT_CONFIG.read_text(encoding='utf-8'))['inputs'];checks=[]
    def check(name,ok,details=None):checks.append(dict(name=name,passed=bool(ok),details=details));assert ok,name
    g=DEM(c).g.copy();g[7:9]=0;g[9]=.5;g[12]=0
    p=np.zeros((2,12));p[:,2]=.4;p[:,0]=[-.0075,.0075];p[:,3]=[.1,-.1]
    integrate_rigid(p,.0075,g,1,1/960,0.,64,12,0.)
    check('Analytic restitution and momentum',np.max(np.abs(p[:,3]-[-.05,.05]))<1e-12 and abs(p[:,3].sum())<1e-12,p[:,3].tolist())
    p=np.zeros((2,12));p[:,2]=.4;p[:,0]=[-.0075,.0075];p[:,3]=[.1,-.1];p[0,4]=.08;g[8]=.35
    def L(p):return np.cross(p[:,:3],p[:,3:6]).sum(axis=0)+(.4*.0075**2)*p[:,6:9].sum(axis=0)
    initial=L(p);moment=p[:,3:6].sum(axis=0);integrate_rigid(p,.0075,g,1,1/960,0.,64,12,0.)
    check('Tangential impulse angular/linear momentum',np.max(abs(L(p)-initial))<1e-12 and np.max(abs(p[:,3:6].sum(axis=0)-moment))<1e-12)
    p=np.zeros((1,12));p[0,2]=.4;integrate_rigid(p,.0075,g,96,1/960,0.,64,12)
    check('Inclined free fall',abs(p[0,4]+9.81/math.sqrt(2)*.1)<1e-10 and abs(p[0,5]+9.81/math.sqrt(2)*.1)<1e-10)
    small={**c,'diameter':120,'length':160,'headDepth':30,'targetFill':.3};metrics=[]
    for direction,mu,dt in [(-1,.45,1/960),(1,.45,1/960),(-1,0.,1/960),(-1,.45,1/1920)]:
     d=DEM({**small,'rotationDirection':direction},dict(solver='rigid',dt=dt,iterations=64,positionIterations=12,muWall=mu))
     d.advance(round(.3/dt),True);d.advance(round(2./dt));met=d.metrics();metrics.append(met)
     check('Small vessel finite and contained '+str((direction,mu,dt)),np.isfinite(d.p).all() and d.escaped==0,met)
     check('Small vessel residual under one percent '+str((direction,mu,dt)),met['overlapRatio']<.01,met['overlapRatio'])
    check('Changing rotation direction changes particle orbit sign',metrics[0]['meanOrbitalRPM']<0 and metrics[1]['meanOrbitalRPM']>0)
    check('Particle motion is not forced rigid co-rotation',abs(metrics[2]['meanOrbitalRPM'])<abs(metrics[0]['meanOrbitalRPM'])*.7)
    jobs=MotionJobs();job=jobs.start(small,dict(solver='rigid',dt=1/960,iterations=64,positionIterations=12,duration=1.,settle=.1))['id'];deadline=time.monotonic()+30
    while time.monotonic()<deadline:
     f=jobs.poll(job)
     if f.get('snapshot'):break
     time.sleep(.01)
    jobs.pause(True);time.sleep(.08);a=jobs.poll(job);time.sleep(.1);b=jobs.poll(job)
    check('Background pause freezes physical time',a['snapshot']['seconds']==b['snapshot']['seconds'] and b['status']=='paused')
    jobs.pause(False)
    while time.monotonic()<deadline:
     f=jobs.poll(job)
     if f['status'] in ['complete','error']:break
     time.sleep(.02)
    check('Resume completes the computed motion',f['status']=='complete' and f['snapshot']['seconds']>=1.-1e-9)
    (OUTPUTS_DIR/'validation_rigid_units.json').write_text(json.dumps(dict(experimentalValidation=False,checks=checks,smallVesselMetrics=metrics),indent=2),encoding='utf-8')
    print(json.dumps(checks,indent=2))


if __name__ == "__main__":
    run()
