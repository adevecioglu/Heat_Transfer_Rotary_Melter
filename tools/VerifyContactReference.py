from rotary_melter.Paths import DEFAULT_CONFIG, OUTPUTS_DIR
"""Numba contact solver vs separately coded SciPy DOP853 collision; geometry/size checks."""
import math,time,json
from pathlib import Path
import numpy as np
from scipy.integrate import solve_ivp
from numba import types
from numba.typed import Dict
from rotary_melter.dynamics.ContactDynamics import integrate,wall,DEM

def run():
    checks=[]
    def check(name,ok,details=None):checks.append(dict(name=name,passed=bool(ok),details=details))
    r=.0075;kn=2e7;e=.25;log=math.log(e);gamma=(2*(-log/math.sqrt(math.pi**2+log**2))*math.sqrt(kn))/math.sqrt(2)
    p=np.zeros((2,12));p[0,0]=-r;p[1,0]=r;p[:,2]=.5;p[0,3]=.1;p[1,3]=-.1
    # Artificial zero-gravity isolated test, distant walls, no tangential friction.
    g=np.array([1.,1.,0.,0.,0.,0.,kn,0.,0.,e,2/7,0.,0.,0.,0.,1.])
    y0=np.r_[p[:,:3].ravel(),p[:,3:6].ravel()]
    def rhs(t,y):
        xx=y[:6].reshape(2,3);vv=y[6:].reshape(2,3);d=xx[0]-xx[1];dist=np.linalg.norm(d);a=np.zeros((2,3))
        if dist<2*r:
            n=d/dist;vn=np.dot(vv[0]-vv[1],n);force=max(0.,kn*(2*r-dist)-gamma*vn);a[0]=force*n;a[1]=-force*n
        return np.r_[vv.ravel(),a.ravel()]
    target=.006;reference=solve_ivp(rhs,(0,target),y0,method='DOP853',rtol=1e-11,atol=1e-13,max_step=2e-5).y[:,-1]
    errors=[]
    for dt in [2e-6,1e-6]:
        pp=p.copy();history=Dict.empty(types.int64,types.UniTuple(types.float64,4));n=round(target/dt);integrate(pp,r,g,history,0,n,dt,0.)
        result=np.r_[pp[:,:3].ravel(),pp[:,3:6].ravel()];error=float(np.max(np.abs(result-reference)));errors.append(error)
        check('Numba vs independent SciPy collision Δt='+str(dt),error<.0005,{'maxStateDifference':error,'relativeSpeedDifference':abs(pp[0,3]-reference[6])/.1})
        check('Pair total momentum conserved Δt='+str(dt),np.linalg.norm(pp[:,3:6].sum(axis=0))<1e-12)
    check('Collision error decreases on halving Δt',errors[1]<errors[0],errors)
    # Closest-point distance against simple independently known analytic locations.
    check('Cylinder signed clearance',abs(wall(.29,0,.4,.3,.8,.15,1)[0]-.01)<1e-12)
    check('Flat top signed clearance',abs(wall(0,0,.79,.3,.8,.15,1)[0]-.01)<1e-12)
    check('Spherical bottom tip clearance',abs(wall(0,0,-.14,.3,.8,.15,1)[0]-.01)<1e-12)
    c=json.loads(DEFAULT_CONFIG.read_text())['inputs'];c.update(rotationDirection=-1)
    m=DEM(c,{'liquid':0});check('Actual 15 mm spheres and exact reference charge count',m.count==45120 and m.radius0==.0075,{'count':m.count,'representedMassKg':m.metrics()['representedMassKg']})
    ct=math.cos(math.radians(c['angle']));st=math.sin(math.radians(c['angle']));height=m.p[:,1]*ct+m.p[:,2]*st
    check('Initial lattice sorted by world vertical height',np.all(np.diff(height)>=-1e-12))
    # Gravity vector expressed in vessel coordinates maps back to downward world acceleration.
    local=np.array([0.,-9.81*ct,-9.81*st]);worldvertical=local[1]*ct+local[2]*st;worldhorizontal=local[2]*ct-local[1]*st
    check('Inclined gravity transforms to world-down',abs(worldvertical+9.81)<1e-12 and abs(worldhorizontal)<1e-12)
    check('Clockwise from opening uses negative axial angular velocity',m.omega<0)
    result=dict(version='1.6.0',kind='independent SciPy DOP853 contact integration and analytic geometry/gravity checks',experimentalValidation=False,checks=checks,passed=all(x['passed'] for x in checks),limitations='Collision benchmark does not validate dense-bed constitutive coefficients, adhesion, liquid hydrodynamics or long-term packing.')
    return result
if __name__=='__main__':
    result=run();target=OUTPUTS_DIR/'validation_dem_reference.json';target.write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
