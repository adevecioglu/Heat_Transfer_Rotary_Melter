"""3-D spherical sequential-impulse contact solver for physical-size granules.

Rigid-granule approximation, not a constitutive wax or liquid CFD model.
Normal nonpenetration, accumulated Coulomb impulses, sphere spin and walls.
"""
import math,sys
import numpy as np
from numba import njit
from numba.typed import Dict
from numba import types
from .FastContactDynamics import wall,candidates
JIT=dict(cache=not getattr(sys,'frozen',False),nogil=True)
HISTORY_VALUE=types.UniTuple(types.float64,4)
WARM_VALUE=types.UniTuple(types.float64,5)

@njit(inline='always',**JIT)
def impulse(p,i,j,n0,n1,n2,x,y,z,r):
    p[i,3]+=x;p[i,4]+=y;p[i,5]+=z
    k=-2.5/r
    wx=k*(n1*z-n2*y);wy=k*(n2*x-n0*z);wz=k*(n0*y-n1*x)
    p[i,6]+=wx;p[i,7]+=wy;p[i,8]+=wz
    if j>=0:
        p[j,3]-=x;p[j,4]-=y;p[j,5]-=z
        p[j,6]+=wx;p[j,7]+=wy;p[j,8]+=wz

@njit(inline='always',**JIT)
def relative(p,i,j,n0,n1,n2,r,omega):
    wx=p[i,6];wy=p[i,7];wz=p[i,8]
    if j>=0:
        vx=p[i,3]-p[j,3];vy=p[i,4]-p[j,4];vz=p[i,5]-p[j,5]
        wx+=p[j,6];wy+=p[j,7];wz+=p[j,8]
    else:
        # Contact lies at center-r*n; n points into the vessel.
        vx=p[i,3]+omega*(p[i,1]-r*n1)
        vy=p[i,4]-omega*(p[i,0]-r*n0);vz=p[i,5]
    return vx-r*(wy*n2-wz*n1),vy-r*(wz*n0-wx*n2),vz-r*(wx*n1-wy*n0)

@njit(**JIT)
def integrate_rigid_core(p,r,g,nsteps,dt,omega,iterations,position_iterations,gravity,warm,iteration):
    R,L,h,heads,st,ct,kn,muw,mup,e,kt,rolling,liquid,drag,slip,rhoratio=g
    history=Dict.empty(types.int64,HISTORY_VALUE)
    max_overlap=0.;pairs=0;walls=0;escaped=0
    for step in range(nsteps):
        for i in range(len(p)):
            buoy=liquid*rhoratio;d=drag*liquid
            p[i,3]+=dt*d*(-omega*slip*p[i,1]-p[i,3])
            p[i,4]+=dt*(-gravity*ct*(1-buoy)+d*(omega*slip*p[i,0]-p[i,4]))
            p[i,5]+=dt*(-gravity*st*(1-buoy)-d*p[i,5])
        left,right,_=candidates(p,r,R,L,h,history)
        # Store constraints once per physical substep, use accumulated impulses
        # across the iterative sweeps; no imposed particle orbital rotation.
        npair=len(left);cap=npair+len(p);ci=np.empty(cap,np.int64);cj=np.empty(cap,np.int64)
        normal=np.empty((cap,3));gap=np.empty(cap);target=np.empty(cap);mu=np.empty(cap)
        accum=np.zeros((cap,4));keys=np.empty(cap,np.int64);nc=0;pairs=0;walls=0;stamp=iteration+step
        for k in range(npair):
            i=left[k];j=right[k]
            dx=p[i,0]-p[j,0];dy=p[i,1]-p[j,1];dz=p[i,2]-p[j,2];dist=math.sqrt(dx*dx+dy*dy+dz*dz)
            if dist<1e-20:continue
            n0=dx/dist;n1=dy/dist;n2=dz/dist;sep=dist-2*r
            vx,vy,vz=relative(p,i,j,n0,n1,n2,r,omega);vn=vx*n0+vy*n1+vz*n2
            if sep>max(.02*r,-vn*dt):continue
            ci[nc]=i;cj[nc]=j;normal[nc,0]=n0;normal[nc,1]=n1;normal[nc,2]=n2;gap[nc]=sep;mu[nc]=mup
            keys[nc]=np.int64(i)*len(p)+j
            target[nc]=.2*max(-sep-.0002*r,0.)/dt-max(sep,0.)/dt
            if sep<.002*r and vn<-.15:target[nc]=max(target[nc],-e*vn)
            nc+=1;pairs+=1
        for i in range(len(p)):
            distance,no0,no1,no2=wall(p[i,0],p[i,1],p[i,2],R,L,h,int(heads))
            n0=-no0;n1=-no1;n2=-no2;sep=distance-r
            vx,vy,vz=relative(p,i,-1,n0,n1,n2,r,omega);vn=vx*n0+vy*n1+vz*n2
            if sep>max(.02*r,-vn*dt):continue
            ci[nc]=i;cj[nc]=-1;normal[nc,0]=n0;normal[nc,1]=n1;normal[nc,2]=n2;gap[nc]=sep;mu[nc]=muw
            keys[nc]=np.int64(len(p))*len(p)+i
            target[nc]=.2*max(-sep-.0002*r,0.)/dt-max(sep,0.)/dt
            if sep<.002*r and vn<-.15:target[nc]=max(target[nc],-e*vn)
            nc+=1;walls+=1
        for k in range(nc):
            key=keys[k]
            if key in warm:
                old=warm[key]
                if old[4]==stamp-1:
                    n0=normal[k,0];n1=normal[k,1];n2=normal[k,2]
                    dot=old[1]*n0+old[2]*n1+old[3]*n2
                    accum[k,0]=old[0];accum[k,1]=old[1]-dot*n0;accum[k,2]=old[2]-dot*n1;accum[k,3]=old[3]-dot*n2
                    impulse(p,ci[k],cj[k],n0,n1,n2,old[0]*n0+accum[k,1],old[0]*n1+accum[k,2],old[0]*n2+accum[k,3],r)
        for sweep in range(iterations):
            for it in range(nc):
                k=it if sweep%2==0 else nc-1-it
                i=ci[k];j=cj[k];n0=normal[k,0];n1=normal[k,1];n2=normal[k,2]
                vx,vy,vz=relative(p,i,j,n0,n1,n2,r,omega);vn=vx*n0+vy*n1+vz*n2
                inv=2. if j>=0 else 1.
                old=accum[k,0];new=max(0.,old+(target[k]-vn)/inv);dn=new-old;accum[k,0]=new
                # A normal impulse changes only normal contact velocity.
                # Reuse the pre-normal tangential velocity and apply both
                # components together; algebraically the same SI update.
                invt=7. if j>=0 else 3.5
                tx=accum[k,1]-(vx-vn*n0)/invt;ty=accum[k,2]-(vy-vn*n1)/invt;tz=accum[k,3]-(vz-vn*n2)/invt
                mag=math.sqrt(tx*tx+ty*ty+tz*tz);limit=mu[k]*new
                if mag>limit and mag>0:
                    fac=limit/mag;tx*=fac;ty*=fac;tz*=fac
                impulse(p,i,j,n0,n1,n2,dn*n0+tx-accum[k,1],dn*n1+ty-accum[k,2],dn*n2+tz-accum[k,3],r)
                accum[k,1]=tx;accum[k,2]=ty;accum[k,3]=tz
        for k in range(nc):warm[keys[k]]=(accum[k,0],accum[k,1],accum[k,2],accum[k,3],float(stamp))
        if stamp%25==0:
            stale=[]
            for key,value in warm.items():
                if value[4]<stamp-1:stale.append(key)
            for key in stale:del warm[key]
        for i in range(len(p)):
            for q in range(3):
                p[i,q]+=dt*p[i,q+3];p[i,q+9]+=dt*p[i,q+6]
        # Split positional correction: does not alter kinetic velocities.
        for sweep in range(position_iterations):
            for k in range(npair):
                i=left[k];j=right[k];dx=p[i,0]-p[j,0];dy=p[i,1]-p[j,1];dz=p[i,2]-p[j,2]
                dist=math.sqrt(dx*dx+dy*dy+dz*dz);over=2*r-dist
                if over>.0002*r and dist>1e-20:
                    corr=.4*(over-.0002*r)/dist
                    p[i,0]+=corr*dx;p[i,1]+=corr*dy;p[i,2]+=corr*dz
                    p[j,0]-=corr*dx;p[j,1]-=corr*dy;p[j,2]-=corr*dz
            for i in range(len(p)):
                distance,n0,n1,n2=wall(p[i,0],p[i,1],p[i,2],R,L,h,int(heads))
                over=r-distance
                if over>.0002*r:
                    corr=.8*(over-.0002*r);p[i,0]-=corr*n0;p[i,1]-=corr*n1;p[i,2]-=corr*n2
        # Post-correction residual, explicitly distinct from a material strain.
        for k in range(npair):
            i=left[k];j=right[k];dist=math.sqrt((p[i,0]-p[j,0])**2+(p[i,1]-p[j,1])**2+(p[i,2]-p[j,2])**2)
            max_overlap=max(max_overlap,(2*r-dist)/r)
        for i in range(len(p)):
            distance,_,_,_=wall(p[i,0],p[i,1],p[i,2],R,L,h,int(heads))
            max_overlap=max(max_overlap,(r-distance)/r)
            if distance<-r:escaped+=1
    return pairs,walls,max_overlap,escaped

def new_warm_history():return Dict.empty(types.int64,WARM_VALUE)

def integrate_rigid(p,r,g,nsteps,dt,omega,iterations,position_iterations,gravity=9.81,warm=None,iteration=0):
    if warm is None:warm=new_warm_history()
    return integrate_rigid_core(p,r,g,nsteps,dt,omega,iterations,position_iterations,gravity,warm,iteration)
