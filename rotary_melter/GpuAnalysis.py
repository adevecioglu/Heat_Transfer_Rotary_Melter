"""Optional NVIDIA field analysis; thermal integration stays in the C++ core."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import numpy as np
from .Paths import PROJECT_ROOT, OUTPUTS_DIR

_handles=[]
_cupy=None


def runtime():
    global _cupy
    if _cupy is not None:
        return _cupy
    os.environ.setdefault('CUPY_CACHE_DIR',str(OUTPUTS_DIR/'cuda_cache'))
    site=Path(sys._MEIPASS) if getattr(sys,'frozen',False) else Path(sys.prefix)/'Lib'/'site-packages' if os.name=='nt' else next(Path(sys.prefix).glob('lib/python*/site-packages'))
    root=site/'nvidia'
    for name in ('cuda_runtime','cuda_nvrtc'):
        folder=root/name/'bin'
        if os.name=='nt' and folder.is_dir():
            _handles.append(os.add_dll_directory(str(folder)))
            os.environ['PATH']=str(folder)+os.pathsep+os.environ.get('PATH','')
            import ctypes
            for builtin in folder.glob('nvrtc-builtins*.dll'):
                _handles.append(ctypes.WinDLL(str(builtin)))
    if (root/'cuda_runtime'/'include').exists():
        os.environ.setdefault('CUDA_PATH',str(root/'cuda_runtime'))
    import cupy
    _cupy=cupy
    return cupy


def info():
    try:
        cp=runtime()
        devices=[]
        for i in range(cp.cuda.runtime.getDeviceCount()):
            properties=cp.cuda.runtime.getDeviceProperties(i)
            name=properties['name']
            devices.append({'id':i,'name':name.decode() if isinstance(name,bytes) else name,
                'memoryBytes':int(properties['totalGlobalMem']),'computeCapability':f"{properties['major']}.{properties['minor']}"})
        return {'available':bool(devices),'devices':devices,'cupy':cp.__version__,
                'runtime':cp.cuda.runtime.runtimeGetVersion(),'driver':cp.cuda.runtime.driverGetVersion()}
    except Exception as error:
        return {'available':False,'error':str(error)}


def audit(result,device=0):
    cp=runtime()
    if not result.get('hist'):
        raise ValueError('GPU field analysis requires saved history.')
    c=result['c'];history=result['hist'];cells=c['axialZones']*c['angularZones']
    temperature=np.asarray([row['outerSurface'] for row in history],dtype=np.float64)
    area=np.repeat(np.asarray(result['mesh']['weights'],dtype=np.float64)*result['g']['external']/c['angularZones'],c['angularZones'])
    kernel_path=(Path(sys._MEIPASS)/'cuda'/'FieldAnalysis.cu') if getattr(sys,'frozen',False) else PROJECT_ROOT/'native'/'cuda'/'FieldAnalysis.cu'
    source=kernel_path.read_text(encoding='utf-8')
    with cp.cuda.Device(int(device)):
        kernel=cp.RawKernel(source,'exterior_flux',options=('--std=c++17','--fmad=false'))
        started=time.perf_counter()
        values=cp.asarray(temperature.ravel());areas=cp.asarray(area)
        convection=cp.empty_like(values);radiation=cp.empty_like(values)
        kernel(((values.size+255)//256,),(256,),(values,areas,np.float64(c['ambient']),np.float64(c['externalH']),
            np.float64(c['emissivity']),np.int32(cells),np.int32(values.size),convection,radiation))
        conv=cp.asnumpy(convection.reshape(temperature.shape).sum(axis=1))
        rad=cp.asnumpy(radiation.reshape(temperature.shape).sum(axis=1))
        cp.cuda.get_current_stream().synchronize()
        gpu_wall=time.perf_counter()-started
    started=time.perf_counter()
    reference_conv=(c['externalH']*area*(temperature-c['ambient'])).sum(axis=1)
    tk=temperature+273.15;ak=c['ambient']+273.15
    reference_rad=(c['emissivity']*5.670374419e-8*area*(tk*tk*tk*tk-ak*ak*ak*ak)).sum(axis=1)
    cpu_wall=time.perf_counter()-started
    error=float(max(np.max(np.abs(conv-reference_conv)),np.max(np.abs(rad-reference_rad))))
    expected=np.asarray([(row['lossKW']-row['waterExtraKW'])*1000 for row in history])
    closure=float(np.max(np.abs(conv+rad-expected)))
    return {'analysis':'NVIDIA exterior-field audit','device':info()['devices'][int(device)],'precision':'float64',
        'snapshots':len(history),'surfaceCells':cells,'evaluations':int(temperature.size),
        'maxCpuGpuDifferenceW':error,'maxRecordedFluxDifferenceW':closure,'passed':error<1e-7 and closure<1e-6,
        'gpuWallSecondsIncludingJitAndTransfers':gpu_wall,'cpuVectorizedWallSeconds':cpu_wall,
        'kernelSha256':hashlib.sha256(source.encode()).hexdigest(),
        'inputSha256':result.get('traceability',{}).get('inputSha256'),
        'sourceRunId':result.get('traceability',{}).get('runId'),
        'note':'Independent post-processing of the computed exterior temperatures. It does not change thermal integration or establish experimental validation.',
        'first':{'seconds':history[0]['seconds'],'convectionW':float(conv[0]),'radiationW':float(rad[0])},
        'last':{'seconds':history[-1]['seconds'],'convectionW':float(conv[-1]),'radiationW':float(rad[-1])}}


def save_audit(result,directory,device=0):
    report=audit(result,device)
    folder=Path(directory);folder.mkdir(parents=True,exist_ok=True)
    (folder/'gpu_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    text=['# NVIDIA GPU field audit','',f"Device: {report['device']['name']}; precision: float64.",'',
        f"Independent surface evaluations: {report['evaluations']}.",'',
        f"Maximum CPU/GPU difference: {report['maxCpuGpuDifferenceW']:.10g} W.",
        f"Maximum difference from stored thermal flux: {report['maxRecordedFluxDifferenceW']:.10g} W.",'',
        report['note'],'',f"CUDA C++ kernel SHA-256: `{report['kernelSha256']}`.",'',
        'Qconv = h A (Ts − Tamb); Qrad = ε σ A [(Ts+273.15)^4 − (Tamb+273.15)^4].','',
        'Kernel execution uses CuPy RawKernel / NVIDIA NVRTC. JIT and transfer costs are included in the GPU wall time; small workloads may be faster on CPU.','']
    (folder/'GPU_REPORT.md').write_text('\n'.join(text),encoding='utf-8')
    return report
