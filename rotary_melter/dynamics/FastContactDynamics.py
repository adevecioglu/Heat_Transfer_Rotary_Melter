"""Verlet/history-array acceleration of the unchanged compliant contact law."""
import math,sys
import numpy as np
from numba import njit
JIT=dict(cache=not getattr(sys,'frozen',False),nogil=True)
@njit(**JIT)
def candidates(p,r,R,L,h,history):
    N=len(p);skin=.25*r;cell=2*r+skin;nx=int(math.ceil(2*R/cell))+5;ny=nx;nz=int(math.ceil((L+2*h)/cell))+7
    bins=np.full(nx*ny*nz,-1,np.int64);nxt=np.empty(N,np.int64);coords=np.empty((N,3),np.int64)
    for i in range(N):
        ix=min(nx-2,max(1,int(math.floor((p[i,0]+R)/cell))+2));iy=min(ny-2,max(1,int(math.floor((p[i,1]+R)/cell))+2));iz=min(nz-2,max(1,int(math.floor((p[i,2]+h)/cell))+2));coords[i,0]=ix;coords[i,1]=iy;coords[i,2]=iz;k=ix+nx*(iy+ny*iz);nxt[i]=bins[k];bins[k]=i
    left=[];right=[]
    for i in range(N):
      for dz in range(-1,2):
       for dy in range(-1,2):
        for dx in range(-1,2):
         j=bins[coords[i,0]+dx+nx*(coords[i,1]+dy+ny*(coords[i,2]+dz))]
         while j>=0:
          if j>i:
           d2=(p[i,0]-p[j,0])**2+(p[i,1]-p[j,1])**2+(p[i,2]-p[j,2])**2
           if d2<cell*cell:left.append(i);right.append(j)
          j=nxt[j]
    cache=np.zeros((len(left),4));cache[:,3]=-9.
    for k in range(len(left)):
        key=np.int64(left[k])*N+right[k]
        if key in history:
            value=history[key]
            for j in range(4):cache[k,j]=value[j]
    return left,right,cache
@njit(**JIT)
def flush(left,right,cache,history,N):
    for k in range(len(left)):
        if cache[k,3]>=0:
            history[np.int64(left[k])*N+right[k]]=(cache[k,0],cache[k,1],cache[k,2],cache[k,3])
@njit(**JIT)
def wall(x,y,z,R,L,h,heads):
    rho=math.hypot(x,y);rs=(R*R+h*h)/(2*h) if h>0 else R
    # Closest point on the cylinder, spherical-cap arcs, and flat closure disks.
    bz=min(L,max(0.,z));br=R;best=(rho-br)**2+(z-bz)**2
    if heads>0:
        center=rs-h;dz=z-center;d=math.hypot(rho,dz)
        zz=center+rs*dz/max(d,1e-30)
        if zz<=0:rr=rs*rho/max(d,1e-30)
        else:zz=0.;rr=R
        q=(rho-rr)**2+(z-zz)**2
        if q<best:best=q;br=rr;bz=zz
    else:
        rr=min(R,rho);q=(rho-rr)**2+z*z
        if q<best:best=q;br=rr;bz=0.
    if heads==2:
        center=L-rs+h;dz=z-center;d=math.hypot(rho,dz);zz=center+rs*dz/max(d,1e-30)
        if zz>=L:rr=rs*rho/max(d,1e-30)
        else:zz=L;rr=R
        q=(rho-rr)**2+(z-zz)**2
        if q<best:best=q;br=rr;bz=zz
    else:
        rr=min(R,rho);q=(rho-rr)**2+(z-L)**2
        if q<best:best=q;br=rr;bz=L
    lower=-h if heads else 0.;upper=L+h if heads==2 else L
    rad=R
    if z<0 and heads>0:rad=math.sqrt(max(0.,rs*rs-(z-(rs-h))**2))
    if z>L and heads==2:rad=math.sqrt(max(0.,rs*rs-(z-(L-rs+h))**2))
    inside=(lower<=z<=upper and rho<=rad)
    dist=math.sqrt(best);fac=1. if inside else -1.
    dx=br-rho;dz=bz-z
    if dist<1e-20:return 0.,(x/max(rho,1e-30)),(y/max(rho,1e-30)),0.
    nx=fac*dx/dist*x/max(rho,1e-30);ny=fac*dx/dist*y/max(rho,1e-30);nz=fac*dz/dist
    if rho<1e-15:nx=0.;ny=0.
    return fac*dist,nx,ny,nz


@njit(**JIT)
def integrate_fast(p,r,g,history,iteration,steps,dt,omega):
    R,L,h,heads,st,ct,kn,muw,mup,restitution,kt_ratio,rolling,liquid,drag,slip,rhoratio=g
    heads=int(heads);N=len(p);force=np.empty((N,6));left,right,cache=candidates(p,r,R,L,h,history);reference=p[:,:3].copy();skin=.25*r
    log=math.log(max(.01,min(.99,restitution)));zeta=-log/math.sqrt(math.pi**2+log**2)
    gamma=2*zeta*math.sqrt(kn);gp=gamma/math.sqrt(2.);kt=kt_ratio*kn
    maxover=0.;pairs=0;walls=0;escaped=0;diss=0.
    for sub in range(steps):
      force[:]=0.;pairs=0;walls=0;maxover=0.;stamp=iteration+sub
      moved=0.
      for i in range(N):
          moved=max(moved,(p[i,0]-reference[i,0])**2+(p[i,1]-reference[i,1])**2+(p[i,2]-reference[i,2])**2)
      if moved>(skin*.45)**2:
          flush(left,right,cache,history,N);left,right,cache=candidates(p,r,R,L,h,history);reference=p[:,:3].copy()
      for i in range(N):
        x,y=p[i,0],p[i,1];buoy=liquid*rhoratio
        force[i,0]=liquid*drag*(-omega*slip*y-p[i,3]);force[i,1]=-9.81*ct*(1-buoy)+liquid*drag*(omega*slip*x-p[i,4]);force[i,2]=-9.81*st*(1-buoy)-liquid*drag*p[i,5]
      for pair in range(len(left)):
       i=left[pair];j=right[pair];xx=p[i,0]-p[j,0];yy=p[i,1]-p[j,1];zz=p[i,2]-p[j,2];d2=xx*xx+yy*yy+zz*zz
       if 1e-24<d2<4*r*r:
        d=math.sqrt(d2);n0=xx/d;n1=yy/d;n2=zz/d;overlap=2*r-d
        wx=p[i,6]+p[j,6];wy=p[i,7]+p[j,7];wz=p[i,8]+p[j,8]
        vx=p[i,3]-p[j,3]-r*(wy*n2-wz*n1);vy=p[i,4]-p[j,4]-r*(wz*n0-wx*n2);vz=p[i,5]-p[j,5]-r*(wx*n1-wy*n0)
        vn=vx*n0+vy*n1+vz*n2;fn=max(0.,kn*overlap-gp*vn);tx=vx-vn*n0;ty=vy-vn*n1;tz=vz-vn*n2
        key=np.int64(i)*np.int64(N)+j
        prev=(cache[pair,0],cache[pair,1],cache[pair,2],cache[pair,3]);hx,hy,hz=prev[0],prev[1],prev[2]
        if prev[3]<stamp-1:hx=0.;hy=0.;hz=0.
        dot=hx*n0+hy*n1+hz*n2;hx=hx-dot*n0+tx*dt;hy=hy-dot*n1+ty*dt;hz=hz-dot*n2+tz*dt
        fx=-kt*hx-gp*tx;fy=-kt*hy-gp*ty;fz=-kt*hz-gp*tz;ft=math.sqrt(fx*fx+fy*fy+fz*fz);limit=mup*fn
        if ft>limit and ft>0:
         q=limit/ft;fx*=q;fy*=q;fz*=q
         if kt>0:hx=-(fx+gp*tx)/kt;hy=-(fy+gp*ty)/kt;hz=-(fz+gp*tz)/kt
        cache[pair,0]=hx;cache[pair,1]=hy;cache[pair,2]=hz;cache[pair,3]=float(stamp)
        ax=fn*n0+fx;ay=fn*n1+fy;az=fn*n2+fz
        force[i,0]+=ax;force[i,1]+=ay;force[i,2]+=az;force[j,0]-=ax;force[j,1]-=ay;force[j,2]-=az
        cx=n1*fz-n2*fy;cy=n2*fx-n0*fz;cz=n0*fy-n1*fx
        for k in (i,j):force[k,3]-=2.5/r*cx;force[k,4]-=2.5/r*cy;force[k,5]-=2.5/r*cz
        pairs+=1;maxover=max(maxover,overlap/r)
      for i in range(N):
       gap,n0,n1,n2=wall(p[i,0],p[i,1],p[i,2],R,L,h,heads);delta=r-gap
       if delta>0:
        vx=p[i,3]+r*(p[i,7]*n2-p[i,8]*n1)+omega*(p[i,1]+gap*n1)
        vy=p[i,4]+r*(p[i,8]*n0-p[i,6]*n2)-omega*(p[i,0]+gap*n0)
        vz=p[i,5]+r*(p[i,6]*n1-p[i,7]*n0);vn=vx*n0+vy*n1+vz*n2;fn=max(0.,kn*delta+gamma*vn)
        tx=vx-vn*n0;ty=vy-vn*n1;tz=vz-vn*n2
        key=-np.int64(i)-1;prev=history[key] if key in history else (0.,0.,0.,-9.);hx,hy,hz=prev[0],prev[1],prev[2]
        if prev[3]<stamp-1:hx=0.;hy=0.;hz=0.
        dot=hx*n0+hy*n1+hz*n2;hx=hx-dot*n0+tx*dt;hy=hy-dot*n1+ty*dt;hz=hz-dot*n2+tz*dt
        fx=-kt*hx-gamma*tx;fy=-kt*hy-gamma*ty;fz=-kt*hz-gamma*tz;ft=math.sqrt(fx*fx+fy*fy+fz*fz);limit=muw*fn
        if ft>limit and ft>0:
         q=limit/ft;fx*=q;fy*=q;fz*=q
         if kt>0:hx=-(fx+gamma*tx)/kt;hy=-(fy+gamma*ty)/kt;hz=-(fz+gamma*tz)/kt
        history[key]=(hx,hy,hz,float(stamp))
        force[i,0]+=-fn*n0+fx;force[i,1]+=-fn*n1+fy;force[i,2]+=-fn*n2+fz
        force[i,3]+=2.5/r*(n1*fz-n2*fy);force[i,4]+=2.5/r*(n2*fx-n0*fz);force[i,5]+=2.5/r*(n0*fy-n1*fx)
        spin=math.sqrt(p[i,6]**2+p[i,7]**2+p[i,8]**2)
        if spin>0:
         damp=min(rolling*fn*2.5/r/spin,1/dt)
         force[i,3]-=damp*p[i,6];force[i,4]-=damp*p[i,7];force[i,5]-=damp*p[i,8]
        walls+=1;maxover=max(maxover,delta/r)
       for k in range(3):p[i,3+k]+=force[i,k]*dt;p[i,6+k]+=force[i,3+k]*dt;p[i,k]+=p[i,3+k]*dt;p[i,9+k]+=p[i,6+k]*dt
       gap,_,_,_=wall(p[i,0],p[i,1],p[i,2],R,L,h,heads)
       if gap<-r:escaped+=1
      if (stamp+1)%25==0:
       old=[]
       for key,value in history.items():
        if value[3]<stamp:old.append(key)
       for key in old:del history[key]
    flush(left,right,cache,history,N)
    return pairs,walls,maxover,escaped

