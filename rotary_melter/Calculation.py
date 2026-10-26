"""Independent NumPy/SciPy assembly/integration of the documented thermal equations.
Shares exported geometry/coefficients explicitly. Does not establish physical validation.
"""
import time,math,json
import numpy as np
from scipy.integrate import solve_ivp,quad
from scipy.optimize import brentq
from scipy.sparse import csr_matrix
from threadpoolctl import threadpool_limits

def enthalpy(c,t):
    t=np.asarray(t);cm=(c['cps']+c['cpl'])/2+c['latent']/(c['liquidus']-c['solidus']);hs=c['cps']*c['solidus'];hl=hs+cm*(c['liquidus']-c['solidus'])
    return np.where(t<=c['solidus'],c['cps']*t,np.where(t<c['liquidus'],hs+cm*(t-c['solidus']),hl+c['cpl']*(t-c['liquidus'])))
def temperature(c,h):
    cm=(c['cps']+c['cpl'])/2+c['latent']/(c['liquidus']-c['solidus']);hs=c['cps']*c['solidus'];hl=hs+cm*(c['liquidus']-c['solidus'])
    return np.where(h<=hs,h/c['cps'],np.where(h<hl,c['solidus']+(h-hs)/cm,c['liquidus']+(h-hl)/c['cpl']))

def solve(spec,method='BDF',rtol=1e-8):
    started=time.perf_counter();c=spec['c'];A=spec['mesh']['A'];P=spec['mesh']['P'];N=A*P;K=spec['K'];B=2*K;D=B+2*N+A
    mass=np.array(spec['mass']);weights=np.array(spec['weights']);Ci=np.array(spec['Ci']);Co=np.array(spec['Co']);Cj=np.array(spec['Cj']);C=np.r_[Ci,Cj,Co]
    Gi=np.array(spec['Gwi']);Go=np.array(spec['Gwo']);Gp=np.array(spec['Gp']);Ao=np.array(spec['Ao']);base=np.array(spec['radialBase']);F=spec['F'];wet=np.array(spec['mesh']['wet']);mw=spec['flowMass'];omega=spec['rotationRate'];sign=c['rotationDirection']
    ntemp=2*N+A;matrix=np.zeros((ntemp,ntemp));wi=N;oi=N+A
    def link(i,j,G):matrix[i,i]-=G;matrix[i,j]+=G;matrix[j,j]-=G;matrix[j,i]+=G
    for a in range(A):
      matrix[wi+a,wi+a]-=F;matrix[wi+a,wi+(a-1)%A]+=F
      for j in range(P):
       k=a*P+j;link(k,wi+a,Gi[k]);link(oi+k,wi+a,Go[k]);link(k,a*P+(j+1)%P,spec['innerAngular'][a]);link(oi+k,oi+a*P+(j+1)%P,spec['outerAngular'][a]);up=a*P+(j+sign)%P
       matrix[k,k]-=Ci[k]*omega;matrix[k,up]+=Ci[k]*omega;matrix[oi+k,oi+k]-=Co[k]*omega;matrix[oi+k,oi+up]+=Co[k]*omega
       if a<A-1:link(k,k+P,spec['innerAxial'][a]);link(oi+k,oi+k+P,spec['outerAxial'][a])
    # Preserve the independently assembled flux matrix, using sparse products.
    matrix=csr_matrix(matrix)
    y0=np.r_[np.full(B,float(enthalpy(c,c['initial']))),np.full(N,c['metalInitial']),np.full(A,c['waterInitial']),np.full(N,c['metalInitial']),np.zeros(5)]
    def rhs(t,y):
      hv=y[:B];T=temperature(c,hv);phase=np.clip((T-c['solidus'])/(c['liquidus']-c['solidus']),0,1);f=float(np.dot(mass,phase)/c['mass']);u=y[B:D];e=np.zeros(B);du=matrix@u
      xx=min(8.,max(0.,f*8));i=min(7,int(xx));b=xx-i;w=(wet[i]*(1-b)+wet[i+1]*b)
      # Independent face-flux assembly for the two spherical populations.
      conductivity=c['ks']*(1-phase)+c['kl']*phase
      for pop in range(2):
       lo=pop*K;kk=conductivity[lo:lo+K];flux=base[pop]*2*kk[:-1]*kk[1:]/(kk[:-1]+kk[1:])*(T[lo+1:lo+K]-T[lo:lo+K-1]);e[lo:lo+K-1]+=flux;e[lo+1:lo+K]-=flux
      mix=mw*weights*(hv[:K]-hv[K:]);e[:K]-=mix;e[K:]+=mix
      sk=c['ks']/(1+c['contactR']*c['ks']/(c['particle']/1000));p=c['packing']+(1-c['packing'])*f;k1=sk*(1-f)+c['kl']*f;k0=c['gasK']*(1-f)+c['kl']*f;series=1/(p/k1+(1-p)/k0);parallel=p*k1+(1-p)*k0;kbed=series+c['contactTopology']*(parallel-series);v=c['mass']*((1-f)/(c['rhos']*c['packing'])+f/c['rhol']);Gbed=kbed*v**(2/3)/max(c['particle']/1000,c['bedPathFactor']*c['diameter']/1000)
      radius=c['particle']/2000;dr=radius/K;particles=np.array(spec['population'])/(c['rhos']*4*math.pi*radius**3/3);gs=particles*4*math.pi*radius**2/(dr/2)*conductivity[[K-1,B-1]]
      film=Gp*w;H=np.array([[gs[0]+film.sum()+Gbed,-Gbed],[-Gbed,gs[1]+Gbed]]);boundary=np.linalg.solve(H,np.array([gs[0]*T[K-1]+np.dot(film,u[:N]),gs[1]*T[B-1]]));q=film*(u[:N]-boundary[0]);du[:N]-=q;e[K-1]+=q.sum();qb=Gbed*(boundary[0]-boundary[1]);e[K-1]-=qb;e[B-1]+=qb
      ret=u[wi+A-1];qin=max(0.,F*(c['tin']-ret))
      if not c['sourceMode']:qin=min(qin,c['boiler']*1000*c['efficiency'])
      du[wi]+=qin;outer=u[oi:];surface=outer.copy()
      if c['insulation']>0:
       lo=np.minimum(outer,c['ambient']);hi=np.maximum(outer,c['ambient']);gg=c['insulationK']*Ao/(c['insulation']/1000)
       for _ in range(28):
        mid=(lo+hi)/2;qq=c['externalH']*Ao*(mid-c['ambient'])+c['emissivity']*5.670374419e-8*Ao*((mid+273.15)**4-(c['ambient']+273.15)**4);test=gg*(outer-mid)>qq;lo=np.where(test,mid,lo);hi=np.where(test,hi,mid)
       surface=(lo+hi)/2
      conv=c['externalH']*Ao*(surface-c['ambient']);rad=c['emissivity']*5.670374419e-8*Ao*((surface+273.15)**4-(c['ambient']+273.15)**4);du[oi:]-=conv+rad;extra=c['extraUA']*np.array(spec['mesh']['weights'])*(u[wi:wi+A]-c['ambient']);du[wi:wi+A]-=extra
      return np.r_[e/mass,du/C,qin,conv.sum()+rad.sum()+extra.sum(),conv.sum(),rad.sum(),extra.sum()]
    def target(t,y):return float(np.min(temperature(c,y[:B]))-c['target'])
    target.terminal=True;target.direction=1
    atol=np.r_[np.full(B,1e-4),np.full(ntemp,1e-8),np.full(5,.001)]
    def jacobian(t,y):
        # The five accumulated-energy states never feed back into rhs. Keep
        # their columns exactly zero instead of repeatedly increasing finite-
        # difference factors for these structurally zero derivatives.
        f0=rhs(t,y);J=np.zeros((D+5,D+5));scale=np.r_[np.full(B,1000.),np.ones(ntemp),np.ones(5)]
        step=np.sqrt(np.finfo(float).eps)*np.maximum(np.abs(y),scale)
        for j in range(D):
            trial=y.copy();trial[j]+=step[j];delta=trial[j]-y[j]
            J[:,j]=(rhs(t,trial)-f0)/delta
        return csr_matrix(J)
    with threadpool_limits(limits=1, user_api='blas'):
        result=solve_ivp(rhs,(0,c['maxHours']*3600),y0,method=method,rtol=rtol,atol=atol,events=target,dense_output=True,jac=jacobian)
    if not result.success:raise RuntimeError(result.message)
    end=result.y[:,-1];T=temperature(c,end[:B]);stored=np.dot(mass,end[:B]-y0[:B])+np.dot(C,end[B:D]-y0[B:D]);residual=float(end[D]-end[D+1]-stored);tin=end[B+wi+A-1]+rhs(result.t[-1],end)[D]/F
    return dict(method=method,success=True,targetReached=len(result.t_events[0])>0,seconds=float(result.t[-1]),targetHours=float(result.t[-1]/3600),nearCenter=float(T[0]),coreCenter=float(T[K]),waterIn=float(tin),waterOut=float(end[B+wi+A-1]),energyInKWh=float(end[D]/3.6e6),lossKWh=float(end[D+1]/3.6e6),balanceJ=residual,balanceRelative=abs(residual)/max(1,abs(float(end[D]))),nfev=result.nfev,njev=result.njev,nlu=result.nlu,wallSeconds=time.perf_counter()-started,solution=result)

def geometry_check(c):
    R=c['diameter']/2000;L=c['length']/1000;h=c['headDepth']/1000;rs=(R*R+h*h)/(2*h);heads=c['heads'];st=math.sin(math.radians(c['angle']));ct=math.cos(math.radians(c['angle']))
    segments=[(0,L,'cylinder')]+([(-h,0,'bottom')] if heads else [])+([(L,L+h,'top')] if heads==2 else [])
    volume=0.;area=0.
    for low,high,kind in segments:
      def radius(z):return R if kind=='cylinder' else math.sqrt(max(0,rs*rs-((z if kind=='bottom' else L-z)-(rs-h))**2))
      volume+=quad(lambda z:math.pi*radius(z)**2,low,high,epsabs=1e-12)[0];area+=quad(lambda z:2*math.pi*(R if kind=='cylinder' else rs),low,high,epsabs=1e-12)[0]
    return {'method':'SciPy QUADPACK independent meridian quadrature','volumeM3':volume,'areaM2':area}

def compare(spec,javascript):
    results=[]
    for method in ['BDF','Radau']:
      r=solve(spec,method);r.pop('solution');r['relativeTimeDifferenceFromJS']=abs(r['seconds']-javascript['seconds'])/r['seconds'];r['waterOutDifferenceC']=r['waterOut']-javascript['last']['waterOut'];r['energyInRelativeDifference']=abs(r['energyInKWh']-javascript['energyInKWh'])/r['energyInKWh'];results.append(r)
    gg=geometry_check(spec['c']);gg['volumeRelativeDifference']=abs(gg['volumeM3']-spec['g']['volume'])/gg['volumeM3'];gg['areaRelativeDifference']=abs(gg['areaM2']-spec['g']['area'])/gg['areaM2']
    c=spec['c'];flow=c['flow']/3600;total=0.;hydraulic=[]
    segments=[(c['supplyD'],0,c['supplyL'],c['supplyK']),(c['feedD'],0,c['feedL'],c['feedK']),(c['diameter']+2*c['wall']+2*c['gap'],c['diameter']+2*c['wall'],c['length']/1000,c['jacketK']),(c['returnOuter'],c['returnInner'],c['shaftReturnL'],c['shaftReturnK']),(c['returnD'],0,c['returnL'],c['returnK'])]
    for outer,inner,length,Klocal in segments:
      D=outer/1000;d=inner/1000;area=math.pi*(D*D-d*d)/4;dh=D-d;velocity=flow/area;Re=c['waterRho']*velocity*dh/c['waterMu'];ratio=d/D
      po=64 if ratio==0 else 64*(1-ratio)**2*(1-ratio**2)/(1-ratio**4-(1-ratio**2)**2/math.log(1/ratio));lam=po/Re
      if Re>=2300:
       turbulent=brentq(lambda f:1/math.sqrt(f)+2*math.log10(c['roughness']/1000/(3.7*dh)+2.51/(Re*math.sqrt(f))),.0001,.5,xtol=1e-14);friction=turbulent if Re>=4000 else lam+(turbulent-lam)*(Re-2300)/1700
      else:friction=lam
      dp=(friction*length/dh+Klocal)*c['waterRho']*velocity**2/2;total+=dp;hydraulic.append(dict(Re=Re,friction=friction,pressurePa=dp))
    total+=(c['jointDropBar']+c['equipmentDropBar'])*1e5;hydcheck={'method':'Independent SciPy brentq Colebrook root and pressure assembly','totalBar':total/1e5,'relativeDifference':abs(total-javascript['hydraulics']['totalPa'])/max(1,abs(total)),'segments':hydraulic}
    return {'version':'1.9.0','kind':'independent integration and assembly; shared documented coefficients','experimentalValidation':False,'sharedInputs':'Exported geometry, wet-area table, material/contact/film coefficients. Python separately assembles all ODE fluxes; BDF/Radau differ from JS midpoint RK2.','javascript':{'seconds':javascript['seconds'],'energyInKWh':javascript['energyInKWh'],'balanceRelative':javascript['balanceRelative']},'references':results,'geometry':gg,'hydraulics':hydcheck,'passed':all(x['relativeTimeDifferenceFromJS']<.005 and x['energyInRelativeDifference']<.005 for x in results) and hydcheck['relativeDifference']<1e-8}

if __name__=='__main__':
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser();parser.add_argument('spec');parser.add_argument('javascript');parser.add_argument('output');args=parser.parse_args();r=compare(json.loads(Path(args.spec).read_text()),json.loads(Path(args.javascript).read_text()));Path(args.output).write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2),flush=True)
