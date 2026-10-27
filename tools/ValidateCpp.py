"""Measured regression, convergence and parallel checks against the retained V11 model."""
from datetime import datetime, timezone
import argparse
import json
import platform
import time
from rotary_melter.Configuration import load_inputs
from rotary_melter.NativeEngine import simulate, execute, info
from rotary_melter.JavaScriptEngine import simulate as reference
from rotary_melter.AnalysisReporting import export_analysis
from rotary_melter.Paths import PROJECT_ROOT, OUTPUTS_DIR


def validate(full=False):
    base=load_inputs()['inputs']
    directory=OUTPUTS_DIR/'cpp_validation'/datetime.now().strftime('%Y%m%d_%H%M%S')
    directory.mkdir(parents=True,exist_ok=True)
    fixtures=[('cold_default',{}),('limited_source',{'sourceMode':0,'boiler':5,'maxHours':.03}),
              ('warm_start',{'initial':74,'target':75,'waterInitial':75,'metalInitial':75,'maxHours':.01}),
              ('two_heads',{'heads':2,'maxHours':.02}),('flat_ends',{'heads':0,'maxHours':.02}),
              ('insulated',{'insulation':40,'maxHours':.02}),('reverse_rotation',{'rotationDirection':1,'maxHours':.02})]
    rows=[]
    for name,changes in fixtures:
        configuration={**base,**changes}
        started=time.perf_counter();old=reference(configuration,no_history=True);old_wall=time.perf_counter()-started
        started=time.perf_counter();new=simulate(configuration,no_history=True);new_wall=time.perf_counter()-started
        differences={key:abs(new[key]-old[key])/max(1.,abs(old[key])) for key in
                     ('seconds','energyInKWh','lossKWh','storedProductKWh','storedMetalKWh','storedWaterKWh')}
        passed=max(differences.values())<1e-9 and new['targetReached']==old['targetReached'] and new['balanceRelative']<1e-9
        rows.append({'name':name,'configuration':configuration,'differences':differences,'javascriptWallSeconds':old_wall,
            'cppWallSeconds':new_wall,'speedup':old_wall/new_wall,'cppBalanceRelative':new['balanceRelative'],
            'targetReached':new['targetReached'],'physicalSeconds':new['seconds'],'energyInKWh':new['energyInKWh'],'passed':passed})
        print(name+': '+('PASS' if passed else 'FAIL'),flush=True)
    analyses={}
    if full:
        for analysis in ('convergence','sensitivity'):
            print('Running '+analysis,flush=True)
            result=execute({'action':'analyse','analysis':analysis,'configuration':base,'options':{'threads':4}})
            export_analysis(result,directory/analysis)
            analyses[analysis]={'cases':len(result.get('cases',[])),'wallSeconds':result.get('wallSeconds'),
                'ok':all(row.get('ok') and not row['summary'].get('cancelled') and row['summary']['balanceRelative']<1e-9 for row in result.get('cases',[]))}
    report={'createdUtc':datetime.now(timezone.utc).isoformat(),'platform':platform.platform(),'processor':platform.processor(),
        'backend':info(),'regression':rows,'analyses':analyses,'passed':all(row['passed'] for row in rows) and all(row['ok'] for row in analyses.values()),
        'note':'Wall times include per-call adapter overhead. These are single-run fixture measurements, not general performance guarantees or experimental validation.'}
    (directory/'validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    lines=['# Measured C++ regression and analyses','',f"Date (UTC): {report['createdUtc']}",'',
        f"Platform: {report['platform']}. Compiler: {report['backend']['compiler']}.",'',report['note'],'',
        '| Fixture | Physical time (s) | Input (kWh) | Maximum scaled difference | Energy residual | JS wall (s) | C++ wall (s) | Ratio | Pass |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |']
    for row in rows:
        lines.append(f"| {row['name']} | {row['physicalSeconds']:.10g} | {row['energyInKWh']:.10g} | {max(row['differences'].values()):.3g} | {row['cppBalanceRelative']:.3g} | {row['javascriptWallSeconds']:.5g} | {row['cppWallSeconds']:.5g} | {row['speedup']:.4g} | {row['passed']} |")
    lines+=['','Scaled difference is `abs(C++ − V11) / max(1, abs(V11))`, so it is an absolute difference below unit scale. '
        'Target status is also checked. The requested input for every fixture is retained in the adjacent JSON.','',
        '## Analysis execution','']
    for name,analysis in analyses.items():
        lines.append(f"- {name}: {analysis['cases']} cases; {analysis['wallSeconds']:.6g} wall seconds; all numerical energy checks passed: {analysis['ok']}.")
    lines+=['','[Formula catalogue](CPP_CALCULATION_EQUATIONS.md). Independent numerical agreement does not establish real melting performance.','']
    document='\n'.join(lines)
    (directory/'VALIDATION_REPORT.md').write_text(document,encoding='utf-8')
    print('Report:',directory,flush=True)
    if not report['passed']:
        raise SystemExit(1)
    return directory


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--full',action='store_true')
    validate(parser.parse_args().full)
