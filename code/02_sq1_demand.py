"""SQ1. Level, growth and shape of demand by state."""
from common import *
import json, warnings; warnings.filterwarnings('ignore')
from statsmodels.tsa.seasonal import STL
from scipy import stats
dd,e,c=load(); R={}
y=fy(dd.index); fys=range(2019,2026)
rows=[]
for s in dd.columns:
    for f in fys:
        v=dd.loc[y==f,s]; m=v.groupby(v.index.to_period('M')).mean()
        rows.append(dict(state=s,fy=f,gwh=v.sum(),swing=m.max()/m.min(),flat=v.mean()/v.max(),peak_month=str(m.idxmax())[-2:]))
A=pd.DataFrame(rows); A['kwh_pc']=[r.gwh*1e6/pop(c,r.fy+0.75)[r.state] for r in A.itertuples()]
A.to_csv(TAB/'sq1_state_year.csv',index=False)
def climo(s,fl):
    v=dd.loc[np.isin(y,fl),s]; a=v/v.groupby(fy(v.index)).transform('mean')
    t=a.groupby([a.index.month]).mean(); return t.reindex([4,5,6,7,8,9,10,11,12,1,2,3])
rows=[]
for s in dd.columns:
    ce,cr=climo(s,EARLY),climo(s,RECENT)
    q=A[A.state==s].set_index('fy')
    def win(col,fl): return q.loc[fl,col].mean()
    # STL on log average daily energy, Apr 2019 to Mar 2026
    m=dd[s].loc[:'2026-03-31'].resample('MS').mean(); st=STL(np.log(m),period=12,robust=True).fit()
    strength=max(0,1-st.resid.var()/(st.resid+st.seasonal).var())
    rows.append(dict(state=s,gwh2425=q.loc[2024,'gwh'],gwh2526=q.loc[2025,'gwh'],cagr=100*((q.loc[2024,'gwh']/q.loc[2019,'gwh'])**(1/5)-1),kwh_pc2425=q.loc[2024,'kwh_pc'],
       swing_e=win('swing',EARLY),swing_r=win('swing',RECENT),flat_e=win('flat',EARLY),flat_r=win('flat',RECENT),
       peak_e=ce.idxmax(),peak_r=cr.idxmax(),seas_strength=strength,
       summer_e=ce.loc[[4,5,6]].mean(),summer_r=cr.loc[[4,5,6]].mean(),winter_e=ce.loc[[12,1,2]].mean(),winter_r=cr.loc[[12,1,2]].mean()))
S=pd.DataFrame(rows).set_index('state')
mnames={4:'Apr',5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec',1:'Jan',2:'Feb',3:'Mar'}
S['peak_e']=S.peak_e.map(mnames); S['peak_r']=S.peak_r.map(mnames)
ct=pd.read_csv(EXT/'cea_annual_state.csv').set_index('state')
S=S.join(ct[['req_fy2526','peak_fy2526']])
S['lf_mw_2526']=100*S.req_fy2526*1000/(8760*S.peak_fy2526)
S.loc[['Jharkhand','West Bengal'],'lf_mw_2526']=np.nan  # DVC split makes these two not comparable with published peaks
S=S.join(c[['gsdp_pc_constant_fy2425']])
S.round(3).to_csv(TAB/'sq1_state_summary.csv')
tot=A.groupby('fy').gwh.sum(); R['energy_total_TWh']={int(k):round(v/1000,1) for k,v in tot.items()}
R['cagr_total']=100*((tot[2024]/tot[2019])**.2-1)
R['cagr_median']=S.cagr.median(); R['cagr_top5']=S.cagr.nlargest(6).round(2).to_dict(); R['cagr_low5']=S.cagr.nsmallest(6).round(2).to_dict()
big=S[S.gwh2425>10000]; R['n_big']=len(big)
R['big_cagr_top']=big.cagr.nlargest(5).round(2).to_dict(); R['big_cagr_low']=big.cagr.nsmallest(5).round(2).to_dict()
R['kwh_top']=S.kwh_pc2425.nlargest(6).round(0).to_dict(); R['kwh_low']=S.kwh_pc2425.nsmallest(6).round(0).to_dict()
R['national_kwh_pc']=float(tot[2024]*1e6/pop(c,2024.75).sum())
for k,(a,b) in {'swing':('swing_e','swing_r'),'flat':('flat_e','flat_r')}.items():
    d=S[b]-S[a]; w=stats.wilcoxon(d); R[k]={'median_e':S[a].median(),'median_r':S[b].median(),'up':int((d>0).sum()),'down':int((d<0).sum()),'p':float(w.pvalue),'big_up':int(((big[b]-big[a])>0).sum())}
R['swing_top_r']=S.swing_r.nlargest(6).round(2).to_dict(); R['swing_low_r']=S.swing_r.nsmallest(6).round(2).to_dict()
R['big_swing_top_r']=big.swing_r.nlargest(6).round(2).to_dict(); R['big_swing_low_r']=big.swing_r.nsmallest(6).round(2).to_dict()
R['swing_change_big']=(big.swing_r-big.swing_e).sort_values().round(2).to_dict()
R['peak_moved']=S[S.peak_e!=S.peak_r][['peak_e','peak_r']].to_dict('index'); R['n_peak_moved']=int((S.peak_e!=S.peak_r).sum())
R['peak_month_counts_r']=S.peak_r.value_counts().to_dict(); R['peak_month_counts_e']=S.peak_e.value_counts().to_dict()
R['peak_month_counts_big_r']=big.peak_r.value_counts().to_dict()
R['summer_change_median']=float((S.summer_r-S.summer_e).median()); R['winter_change_median']=float((S.winter_r-S.winter_e).median())
R['strength_top']=big.seas_strength.nlargest(5).round(2).to_dict(); R['strength_low']=big.seas_strength.nsmallest(5).round(2).to_dict()
R['strength_median']=S.seas_strength.median()
R['lf_top']=S.lf_mw_2526.dropna().nlargest(5).round(1).to_dict(); R['lf_low']=S[S.gwh2425>10000].lf_mw_2526.dropna().nsmallest(5).round(1).to_dict()
t=S.dropna(subset=['lf_mw_2526']); R['rho_flat_lf']=float(stats.spearmanr(t.lf_mw_2526,t.flat_r).statistic)
# income relation
t=S.dropna(subset=['gsdp_pc_constant_fy2425'])
lx,ly=np.log(t.gsdp_pc_constant_fy2425),np.log(t.kwh_pc2425); r=stats.linregress(lx,ly); res=ly-(r.intercept+r.slope*lx)
R['income']={'slope':r.slope,'se':r.stderr,'r2':r.rvalue**2,'n':len(t),'res_top':(np.exp(res).nlargest(6)-1).mul(100).round(0).to_dict(),'res_low':(np.exp(res).nsmallest(6)-1).mul(100).round(0).to_dict()}
res.rename('res').to_csv(TAB/'sq1_income_residual.csv')
# national peak
d=pd.read_csv(ROOT/'data/raw/gridindia_daily_psp.csv',low_memory=False,usecols=['yyyymmdd','India: MaximumDemand','India: DemandMet','India: EnergyMet','India: PeakShortage','India: EnergyShortage'])
d['date']=pd.to_datetime(d.yyyymmdd,format='%Y%m%d'); d=d.set_index('date'); d=d.loc['2019-04-01':'2026-10-31']
nf=fy(d.index); g=d['India: DemandMet'].groupby(nf)
R['nat_peak']={int(k):{'GW':round(v.max()/1000,1),'date':str(v.idxmax().date())} for k,v in g}
sh=d.groupby(nf)[['India: EnergyShortage','India: EnergyMet']].sum(); R['shortage_pct']=(100*sh['India: EnergyShortage']/sh['India: EnergyMet']).round(3).to_dict()
# national shape: CEA official energy and peak, then coincidence across states
d2=pd.read_csv(ROOT/'data/raw/gridindia_daily_psp.csv',low_memory=False,usecols=['yyyymmdd','India: MaximumDemand']); d2['date']=pd.to_datetime(d2.yyyymmdd,format='%Y%m%d'); d2=d2.set_index('date').loc['2019-04-01':'2026-10-31']
R['nat_peak_gi']={int(k):{'GW':round(v.max()/1000,1),'date':str(v.idxmax().date())} for k,v in d2['India: MaximumDemand'].groupby(fy(d2.index))}
N=pd.read_csv(EXT/'cea_national_annual.csv').set_index('fy_start'); N['hours']=[8784 if ((f+1)%4==0) else 8760 for f in N.index]
N['lf']=100*N.energy_req_mu*1000/(N.hours*N.peak_demand_mw); N.round(2).to_csv(TAB/'sq1_national_load_factor.csv'); R['nat_lf']=N.lf.round(2).to_dict()
R['cagr_peak_1924']=100*((N.peak_demand_mw[2024]/N.peak_demand_mw[2019])**.2-1); R['cagr_energy_1924']=100*((N.energy_req_mu[2024]/N.energy_req_mu[2019])**.2-1)
sumd=dd.sum(axis=1); yy=fy(dd.index); rows=[]
for f in range(2019,2026):
    v=dd[yy==f]; t=sumd[yy==f]
    mm=v.resample('MS').mean(); 
    rows.append(dict(fy=f,nat_flat=t.mean()/t.max(),nat_swing=t.resample('MS').mean().max()/t.resample('MS').mean().min(),diversity=v.max().sum()/t.max(),peak_day=str(t.idxmax().date())))
C=pd.DataFrame(rows).set_index('fy'); C.round(4).to_csv(TAB/'sq1_coincidence.csv'); R['coincidence']=C.round(4).to_dict('index')
# pairwise correlation of detrended monthly state shapes, early vs recent, across 23 big states
b=big.index
def pc(fl):
    m=dd.loc[np.isin(yy,fl),b].resample('MS').mean().dropna(); m=m/m.groupby(m.index.year-(m.index.month<4)).transform('mean'); cc=m.corr().values; return cc[np.triu_indices(len(b),1)].mean()
R['shape_corr_e'],R['shape_corr_r']=pc(EARLY),pc(RECENT)
json.dump(R,open(TAB/'sq1_results.json','w'),indent=1,default=float); print(json.dumps(R,indent=0,default=float)[:6500])
