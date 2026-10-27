"""Native/JIT 3D sphere DEM. Physical diameters; friction history; no particle-count cap.
Not a calibrated material model and not a liquid CFD solver.
"""
import math,sys,time,json,base64,threading,uuid
import numpy as np
from numba import njit,types
from numba.typed import Dict

JIT=dict(cache=not getattr(sys,'frozen',False),nogil=True)
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
def lattice(R,L,h,heads,r,count,st,ct):
    a=2*math.sqrt(2.)*r*1.025
    lo=-h if heads else 0.;hi=L+h if heads==2 else L
    basis=np.array([[0.,0.,0.],[0.,.5,.5],[.5,0.,.5],[.5,.5,0.]])
    size=int((2*R/a+5)**2*((hi-lo)/a+5)*4)
    candidates=np.empty((size,3));height=np.empty(size);n=0
    for iz in range(int(math.floor(lo/a))-1,int(math.ceil(hi/a))+1):
      for iy in range(int(math.floor(-R/a))-1,int(math.ceil(R/a))+1):
       for ix in range(int(math.floor(-R/a))-1,int(math.ceil(R/a))+1):
        for b in range(4):
         x=(ix+basis[b,0])*a;y=(iy+basis[b,1])*a;z=(iz+basis[b,2])*a
         d,_,_,_=wall(x,y,z,R,L,h,heads)
         if d>r*1.005:
          candidates[n,0]=x;candidates[n,1]=y;candidates[n,2]=z;height[n]=y*ct+z*st;n+=1
    if n<count:raise ValueError('The specified physical spheres cannot be packed into this assumed vessel. Reduce charge or correct geometry/packing.')
    order=np.argsort(height[:n]);p=np.zeros((count,12))
    for i in range(count):p[i,:3]=candidates[order[i]]
    return p

@njit(**JIT)
def integrate(p,r,g,history,iteration,steps,dt,omega):
    R,L,h,heads,st,ct,kn,muw,mup,restitution,kt_ratio,rolling,liquid,drag,slip,rhoratio=g
    heads=int(heads);N=len(p);cell=2*r;nx=int(math.ceil(2*R/cell))+5;ny=nx;nz=int(math.ceil((L+2*h)/cell))+7
    bins=np.empty(nx*ny*nz,np.int64);nxt=np.empty(N,np.int64);force=np.empty((N,6));coords=np.empty((N,3),np.int64)
    log=math.log(max(.01,min(.99,restitution)));zeta=-log/math.sqrt(math.pi**2+log**2)
    gamma=2*zeta*math.sqrt(kn);gp=gamma/math.sqrt(2.);kt=kt_ratio*kn
    maxover=0.;pairs=0;walls=0;escaped=0;diss=0.
    for sub in range(steps):
      bins[:]=-1;force[:]=0.;pairs=0;walls=0;maxover=0.;stamp=iteration+sub
      for i in range(N):
        x,y,z=p[i,0],p[i,1],p[i,2]
        ix=min(nx-2,max(1,int(math.floor((x+R)/cell))+2));iy=min(ny-2,max(1,int(math.floor((y+R)/cell))+2));iz=min(nz-2,max(1,int(math.floor((z+h)/cell))+2))
        coords[i,0]=ix;coords[i,1]=iy;coords[i,2]=iz;k=ix+nx*(iy+ny*iz);nxt[i]=bins[k];bins[k]=i
        buoy=liquid*rhoratio
        force[i,0]=liquid*drag*(-omega*slip*y-p[i,3]);force[i,1]=-9.81*ct*(1-buoy)+liquid*drag*(omega*slip*x-p[i,4]);force[i,2]=-9.81*st*(1-buoy)-liquid*drag*p[i,5]
      for i in range(N):
       for dz in range(-1,2):
        for dy in range(-1,2):
         for dx in range(-1,2):
          j=bins[coords[i,0]+dx+nx*(coords[i,1]+dy+ny*(coords[i,2]+dz))]
          while j>=0:
           if j>i:
            xx=p[i,0]-p[j,0];yy=p[i,1]-p[j,1];zz=p[i,2]-p[j,2];d2=xx*xx+yy*yy+zz*zz
            if 1e-24<d2<4*r*r:
             d=math.sqrt(d2);n0=xx/d;n1=yy/d;n2=zz/d;overlap=2*r-d
             wx=p[i,6]+p[j,6];wy=p[i,7]+p[j,7];wz=p[i,8]+p[j,8]
             vx=p[i,3]-p[j,3]-r*(wy*n2-wz*n1);vy=p[i,4]-p[j,4]-r*(wz*n0-wx*n2);vz=p[i,5]-p[j,5]-r*(wx*n1-wy*n0)
             vn=vx*n0+vy*n1+vz*n2;fn=max(0.,kn*overlap-gp*vn);tx=vx-vn*n0;ty=vy-vn*n1;tz=vz-vn*n2
             key=np.int64(i)*np.int64(N)+j
             prev=history[key] if key in history else (0.,0.,0.,-9.);hx,hy,hz=prev[0],prev[1],prev[2]
             if prev[3]<stamp-1:hx=0.;hy=0.;hz=0.
             dot=hx*n0+hy*n1+hz*n2;hx=hx-dot*n0+tx*dt;hy=hy-dot*n1+ty*dt;hz=hz-dot*n2+tz*dt
             fx=-kt*hx-gp*tx;fy=-kt*hy-gp*ty;fz=-kt*hz-gp*tz;ft=math.sqrt(fx*fx+fy*fy+fz*fz);limit=mup*fn
             if ft>limit and ft>0:
              q=limit/ft;fx*=q;fy*=q;fz*=q
              if kt>0:hx=-(fx+gp*tx)/kt;hy=-(fy+gp*ty)/kt;hz=-(fz+gp*tz)/kt
             history[key]=(hx,hy,hz,float(stamp))
             ax=fn*n0+fx;ay=fn*n1+fy;az=fn*n2+fz
             force[i,0]+=ax;force[i,1]+=ay;force[i,2]+=az;force[j,0]-=ax;force[j,1]-=ay;force[j,2]-=az
             cx=n1*fz-n2*fy;cy=n2*fx-n0*fz;cz=n0*fy-n1*fx
             for k in (i,j):force[k,3]-=2.5/r*cx;force[k,4]-=2.5/r*cy;force[k,5]-=2.5/r*cz
             pairs+=1;maxover=max(maxover,overlap/r)
           j=nxt[j]
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
    return pairs,walls,maxover,escaped

@njit(**JIT)
def volume_below(H,R,L,h,heads,st,ct,n=600):
    total=0.;rs=(R*R+h*h)/(2*h) if h>0 else R
    lo=-h if heads else 0.;hi=L+h if heads==2 else L;dz=(hi-lo)/n
    for j in range(n):
     z=lo+(j+.5)*dz;r=R
     if z<0:r=math.sqrt(max(0.,rs*rs-(z-(rs-h))**2))
     if z>L:r=math.sqrt(max(0.,rs*rs-(z-(L-rs+h))**2))
     if ct<1e-12:f=1. if H>=z*st else 0.
     else:
      u=(H-z*st)/max(1e-30,r*ct)
      f=0. if u<=-1 else 1. if u>=1 else .5+(math.asin(u)+u*math.sqrt(1-u*u))/math.pi
     total+=math.pi*r*r*dz*f
    return total

@njit(**JIT)
def liquid_plane(p,r,R,L,h,heads,st,ct,volume):
    lo=-h-R;hi=L+h+R
    if volume<=0:return lo
    for k in range(38):
     H=(lo+hi)/2;solid=0.
     for i in range(len(p)):
      cap=min(2*r,max(0.,H-(p[i,1]*ct+p[i,2]*st)+r));solid+=math.pi*cap*cap*(r-cap/3)
     void=max(0.,volume_below(H,R,L,h,heads,st,ct)-solid)
     if void<volume:lo=H
     else:hi=H
    return (lo+hi)/2

from .FastContactDynamics import integrate_fast
from .RigidBodyDynamics import integrate_rigid,new_warm_history

class DEM:
    def __init__(self,c,settings=None):
        self.c=dict(c);self.settings={'muWall':.45,'muParticle':.35,'restitution':.25,'stiffness':20000000.,'tangentRatio':2/7,'rolling':.01,'dt':.0002,'duration':10.,'settle':1.,'liquid':0.,**(settings or {})}
        s=self.settings;R=c['diameter']/2000;L=c['length']/1000;h=c['headDepth']/1000;heads=int(c['heads']);theta=math.radians(c['angle']);self.radius0=c['particle']/2000
        self.volume=math.pi*R*R*L+heads*math.pi*h*(3*R*R+h*h)/6
        self.mass=self.volume*c['targetFill']*c['packing']*c['rhos'] if c['chargeMode']==1 else c['mass']
        self.count=max(1,round(self.mass/(c['rhos']*4*math.pi*self.radius0**3/3)))
        self.liquid=min(1.,max(0.,float(s['liquid'])));self.r=self.radius0*(max(1-self.liquid,1e-12))**(1/3)
        # Keep a valid finite-radius initialization for the all-liquid display, but skip solid integration.
        initr=self.r if self.liquid<.999999 else self.radius0
        if not 1 <= self.count <= 2_000_000:raise ValueError('Physical particle count must lie between 1 and 2,000,000.')
        self.g=np.array([R,L,h,heads,math.sin(theta),math.cos(theta),s['stiffness'],s['muWall'],s['muParticle'],s['restitution'],s['tangentRatio'],s['rolling'],self.liquid,4.,.35,c['rhol']/c['rhos']],dtype=np.float64)
        self.native=None
        if s.get('backend','cpp')=='cpp':
            from .NativeContactEngine import NativeContacts
            self.native=NativeContacts()
            self.p=self.native.lattice(self.count,initr,self.g)
        else:self.p=lattice(R,L,h,heads,initr,self.count,math.sin(theta),math.cos(theta))
        self.solver=s.get('solver','compliant');self.iterations=int(s.get('iterations',16));self.position_iterations=int(s.get('positionIterations',4))
        self.dt=float(s['dt']) if self.solver=='rigid' else min(float(s['dt']),.15/math.sqrt(float(s['stiffness'])))
        if not 1 <= self.iterations or not 1 <= self.position_iterations or self.dt<=0:raise ValueError('Positive step and contact iterations required.')
        self.omega=float(c.get('rotationDirection',-1))*c['rpm']*2*math.pi/60
        self.history=Dict.empty(types.int64,types.UniTuple(types.float64,4));self.rigid_history=new_warm_history();self.steps=0;self.seconds=0.;self.settled=0.;self.last=(0,0,0.,0);self.started=time.perf_counter();self.max_overlap=0.;self.escaped=0
    def advance(self,n=10,settling=False):
        if self.liquid<.999999:
            if self.native:self.last=self.native.advance(self.p,self.r,self.g,int(n),self.dt,0. if settling else self.omega,self.iterations,self.position_iterations,self.steps,self.solver=='rigid')
            elif self.solver=='rigid':self.last=integrate_rigid(self.p,self.r,self.g,int(n),self.dt,0. if settling else self.omega,self.iterations,self.position_iterations,warm=self.rigid_history,iteration=self.steps)
            else:self.last=integrate_fast(self.p,self.r,self.g,self.history,self.steps,int(n),self.dt,0. if settling else self.omega)
            self.max_overlap=max(self.max_overlap,float(self.last[2]));self.escaped+=int(self.last[3])
        self.steps+=n
        if settling:self.settled+=n*self.dt
        else:self.seconds+=n*self.dt
        if not np.isfinite(self.p).all():raise FloatingPointError('DEM became non-finite. Decrease time step or revise contact parameters; result is rejected.')
        if self.last[3]:raise FloatingPointError('A sphere escaped the wall. Result rejected; reduce the step and increase contact iterations/stiffness for the selected solver.')
        if self.solver=='rigid' and self.seconds+self.settled>.2 and self.last[2]>.1:raise FloatingPointError('Rigid contact residual exceeds 10% of radius. Motion rejected: reduce time step and increase contact iterations.')
    def metrics(self):
        speed=np.linalg.norm(self.p[:,3:6],axis=1)
        orbital=self.p[:,0]*self.p[:,4]-self.p[:,1]*self.p[:,3]
        meanomega=float(orbital.sum()/max(1e-30,np.sum(self.p[:,0]**2+self.p[:,1]**2)))
        return dict(backend='cpp' if self.native else 'numba_reference',solver=self.solver,contactIterations=self.iterations,positionIterations=self.position_iterations,seconds=self.seconds,settledSeconds=self.settled,wallSeconds=time.perf_counter()-self.started,count=self.count,diameterMm=self.radius0*2000,dt=self.dt,steps=self.steps,contacts=int(self.last[0]),wallContacts=int(self.last[1]),overlapRatio=float(self.last[2]),maxOverlapRatio=self.max_overlap,meanSpeed=float(speed.mean()) if self.liquid<1 else 0.,meanOrbitalRPM=meanomega*60/(2*math.pi),counterMovingFraction=float(np.mean(orbital*self.omega<-1e-8)),phase=float(self.omega*self.seconds),liquid=self.liquid,rotationDirection=self.c.get('rotationDirection',-1),massKg=self.mass,representedMassKg=self.count*self.c['rhos']*4*math.pi*self.radius0**3/3,historyEntries=self.native.history_size if self.native else (len(self.rigid_history) if self.solver=='rigid' else len(self.history)),escaped=self.escaped)
    def snapshot(self):
        info=self.metrics();info['positions']=base64.b64encode(np.asarray(self.p[:,:3],dtype='<f4').tobytes()).decode('ascii')
        if self.liquid>0:info['liquidPlane']=float(self.native.liquid_plane(self.p,self.r,self.g,self.mass*self.liquid/self.c['rhol']) if self.native else liquid_plane(self.p,self.r,*self.g[:6],self.mass*self.liquid/self.c['rhol']))
        return info

class MotionJobs:
    def __init__(self):self.job=None;self.lock=threading.Lock()
    def start(self,c,settings):
        if self.job and self.job['status'] in ('initializing','running','settling','paused'):raise RuntimeError('Stop the active motion analysis before starting another.')
        job={'id':uuid.uuid4().hex,'status':'initializing','stop':threading.Event(),'pause':threading.Event(),'snapshot':None,'sequence':0,'frames':[],'error':None};self.job=job
        def run():
            try:
                dem=DEM(c,settings);job['dem']=dem;duration=max(0.,float(settings.get('duration',10)));settle=max(0.,float(settings.get('settle',1)));next_frame=0.;next_physical=0.
                with self.lock:
                    job['snapshot']=dem.snapshot();job['sequence']+=1;job['frames'].append((job['sequence'],job['snapshot']))
                while (dem.settled<settle-1e-10 or dem.seconds<duration-1e-10) and not job['stop'].is_set():
                    if job['pause'].is_set():
                        job['status']='paused';job['stop'].wait(.05);continue
                    settling=dem.settled<settle-1e-10;job['status']='settling' if settling else 'running'
                    remaining=(settle-dem.settled) if settling else (duration-dem.seconds)
                    batch=4 if dem.solver=='rigid' else 50
                    dem.advance(max(1,min(batch,int(math.ceil((remaining-1e-10)/dem.dt)))),settling)
                    now=time.perf_counter()
                    if now>=next_frame or dem.settled+dem.seconds>=next_physical:
                        frame=dem.snapshot()
                        with self.lock:
                            job['snapshot']=frame;job['sequence']+=1;job['frames'].append((job['sequence'],frame))
                        next_frame=now+.12;next_physical=dem.settled+dem.seconds+.025
                with self.lock:
                    job['snapshot']=dem.snapshot();job['sequence']+=1;job['frames'].append((job['sequence'],job['snapshot']))
                job['status']='cancelled' if job['stop'].is_set() else 'complete'
            except Exception as exc:job['error']=str(exc);job['status']='error'
        threading.Thread(target=run,daemon=True).start();return {'ok':True,'id':job['id']}
    def poll(self,ident,sequence=-1):
        job=self.job
        if not job or job['id']!=ident:return {'ok':False,'error':'Unknown analysis'}
        with self.lock:
            job['frames']=[(seq,frame) for seq,frame in job['frames'] if seq>sequence]
            return {'ok':True,'status':job['status'],'error':job['error'],'sequence':job['sequence'],'frames':[frame for seq,frame in job['frames']],'snapshot':job['snapshot'] if job['sequence']!=sequence else None}
    def pause(self,paused=True):
        if self.job:
            if paused:self.job['pause'].set()
            else:self.job['pause'].clear()
        return {'ok':True}
    def stop(self):
        if self.job:self.job['stop'].set()
        return {'ok':True}
