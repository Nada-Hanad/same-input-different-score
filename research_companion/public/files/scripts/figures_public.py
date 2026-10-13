#!/usr/bin/env python3
"""Regenerate current manuscript figure content from included anonymous summaries.
Layout is reconstructed; no restricted records, downloaded images or new intervals.
"""
import argparse,json,csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ART=Path(__file__).resolve().parents[1]
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'pdf.fonttype':42})
GREEN='#32675b';COLORS=['#87b6a3','#5a907d','#32675b','#193c34']
def save(fig,out,name):
 fig.tight_layout();fig.savefig(out/(name+'.png'),dpi=200)
 fig.savefig(out/(name+'.pdf'),metadata={'Author':'Anonymous','CreationDate':None,'ModDate':None})
 plt.close(fig)
def generate(data,out):
 out.mkdir(parents=True,exist_ok=True);records=[]
 pairs=[p for p in data['pairs'] if p['class'] in ['scoring','defensive']]
 fig,ax=plt.subplots(figsize=(7,4));markers=['o','s','D','^'];floor=.001
 for i,p in enumerate(pairs):
  for j,k in enumerate(['E','T','S','G']):
   q=p['exposure'].get('corrected_weighted') if k=='E' and p['exposure']['corrected'] is not None else p['weighted_top1M'][k]
   if q is None:continue
   v=q['pct'];ci=q['ci95'];y=i+(j-1.5)*.14
   ax.plot([max(ci[0],floor),max(ci[1],floor)],[y,y],color=COLORS[j],linewidth=1)
   ax.scatter(max(v,floor),y,color=COLORS[j],marker=markers[j],s=22,label={'E':'Exposure','T':'Any test outcome','S':'Score','G':'Grade'}[k] if i==0 else None)
   records.append({'figure':'fig_cascade','pair':p['pair'],'metric':k,'value':v,'ci95':ci,'exposure_status':'parser-faithful corrected' if k=='E' and p['exposure']['corrected'] is not None else 'recorded'})
 ax.set_yticks(range(len(pairs)),[p['pair'].replace('->',' → ') for p in pairs]);ax.invert_yaxis();ax.set_xscale('log');ax.set_xticks([floor,.01,.1,1,10,100],['0','.01','.1','1','10','100']);ax.set_xlabel('Weighted percent · original recorded stratified-bootstrap 95% intervals');ax.legend(ncol=4,loc='upper center',bbox_to_anchor=(.5,1.15));ax.grid(axis='x',alpha=.15)
 fig.text(.5,.01,'Zeros use a plotting floor of .001; the 18 test-outcome control pairs have no observed change.',ha='center',fontsize=7);save(fig,out,'fig_cascade')
 affected=[p for p in data['pairs'] if p['plans']['B']['scope']=='full-corpus' and any(p['plans'][t]['fate'].get('every_fails',0)+p['plans'][t]['fate'].get('some_fail',0)>0 for t in ['B','A','A+'])]
 fig,axes=plt.subplots(1,3,figsize=(10,3),sharey=True)
 for ax,t in zip(axes,['B','A','A+']):
  every=[p['plans'][t]['fate'].get('every_fails',0) for p in affected];some=[p['plans'][t]['fate'].get('some_fail',0) for p in affected]
  ax.barh(range(len(affected)),every,color=GREEN,label='Every tied plan fails');ax.barh(range(len(affected)),some,left=every,color='#abcaba',hatch='///',edgecolor=GREEN,label='Some tied plans fail')
  for i,(e,s) in enumerate(zip(every,some)):
   ax.text(e+s+.5,i,str(e+s),va='center');records.append({'figure':'fig_remediation_plan_failures','pair':affected[i]['pair'],'target':t,'every':e,'some':s})
  ax.set_title('Target '+t);ax.set_xlabel('Websites within pair');ax.set_yticks(range(len(affected)),[p['pair'].replace('->',' → ') for p in affected]);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
 axes[0].invert_yaxis();axes[0].legend(fontsize=7,loc='lower right');save(fig,out,'fig_remediation_plan_failures')
 m=data['margins']['1.7.1']['T90'];fig,axes=plt.subplots(1,2,figsize=(8,3),sharey=True)
 for ax,key,title in zip(axes,['uncurved_margin','displayed_margin'],['Uncurved margin','Displayed margin']):
  xs=sorted(map(int,m[key]));ys=[m[key][str(x)] for x in xs];ax.bar(xs,ys,width=3.8,color=GREEN);ax.set_title(title);ax.set_xlabel('Score points above A boundary');ax.set_ylabel('Individual minimum-action plans');records.extend({'figure':'fig_margin_companion','metric':key,'margin':x,'plans':y} for x,y in zip(xs,ys))
 save(fig,out,'fig_margin_companion')
 (out/'figure-values.json').write_text(json.dumps({'scope':'Exact plotted values from included aggregates; geometry reconstructed, not pixel-identical manuscript reproduction. No new uncertainty estimates.','values':records},indent=2)+'\n')
 return {'status':'passed','figures':3,'current_manuscript_figures':2,'plotted_values':len(records)}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ART/'figures');a=ap.parse_args();print(json.dumps(generate(json.loads((ART/'data/research.json').read_text()),a.out)))
