"""SQ2. Capacity against delivered energy, seasonal match with demand, and who consumes what."""
from common import *
import json, warnings; warnings.filterwarnings('ignore')
from scipy import stats
dd,e,c=load(); R={}
dm=dd.resample('MS').sum(); e=e[(e.month>='2019-04-01')]
e['hours']=e.month.dt.days_in_month*24
L=dm.stack().rename('dem').reset_index(); L.columns=['month','state','dem']
p=e.merge(L,on=['state','month'],how='left'); p['vre']=p.Solar+p.Wind; p['cap_vre']=p.cap_Solar+p.cap_Wind
p['cap_total']=p[[f'cap_{f}' for f in FUELS]].sum(axis=1)
p.to_csv(PRO/'merged_panel.csv',index=False)
full=p[p.fy.between(2019,2024)]
# --- national picture
n=full.groupby('fy')[['gen_total','Coal','Solar','Wind','Hydro','Gas','Nuclear','Bioenergy','dem']].sum()/1000
cp=full.groupby(['fy','month'])[[f'cap_{f}' for f in FUELS]].sum().groupby('fy').mean()/1000
cap_end=full[full.month.dt.month==3].groupby('fy')[[f'cap_{f}' for f in FUELS]].sum()/1000
HRS=pd.Series({2019:8.784,2020:8.76,2021:8.76,2022:8.76,2023:8.784,2024:8.76})
nn=pd.DataFrame({'gen_TWh':n.gen_total,'coal_share':100*n.Coal/n.gen_total,'solar_share':100*n.Solar/n.gen_total,'wind_share':100*n.Wind/n.gen_total,'hydro_share':100*n.Hydro/n.gen_total,'vre_share':100*(n.Solar+n.Wind)/n.gen_total,
 'cap_solar_GW':cap_end.cap_Solar,'cap_wind_GW':cap_end.cap_Wind,'cap_coal_GW':cap_end.cap_Coal,
 'vre_cap_share':100*(cap_end.cap_Solar+cap_end.cap_Wind)/cap_end.sum(axis=1),'coal_cf':100*n.Coal/(cp.cap_Coal*HRS),'solar_cf':100*n.Solar/(cp.cap_Solar*HRS),'wind_cf':100*n.Wind/(cp.cap_Wind*HRS)})
nn.round(2).to_csv(TAB/'sq2_national.csv'); print(nn.round(2).to_string()); R['national']=nn.round(2).to_dict('index')
coalinc=n.Coal[2024]-n.Coal[2019]; vreinc=(n.Solar+n.Wind)[2024]-(n.Solar+n.Wind)[2019]; geninc=n.gen_total[2024]-n.gen_total[2019]; hyd=n.Hydro[2024]-n.Hydro[2019]
R['increment']={'gen':geninc,'coal':coalinc,'vre':vreinc,'hydro':hyd,'coal_pct':100*coalinc/geninc,'vre_pct':100*vreinc/geninc}
R['k_gen_over_dem']={int(f):n.gen_total[f]/n.dem[f] for f in n.index}
# --- state capacity factors, FY2024-25
mn=pd.read_csv(EXT/'mnre_state_capacity_31mar2025.csv').replace({'Ladakh':'Jammu and Kashmir'}).groupby('state').sum(numeric_only=True)  # official MNRE table, 31.03.2025
rows=[]
for s,g in full[full.fy==2024].groupby('state'):
    h=g.hours.sum()/1000
    r=dict(state=s,gen=g.gen_total.sum(),dem=g.dem.sum(),solar=g.Solar.sum(),wind=g.Wind.sum(),vre=g.vre.sum(),coal=g.Coal.sum(),hydro=g.Hydro.sum(),cap_solar=g.cap_Solar.mean(),cap_wind=g.cap_Wind.mean(),cap_vre=g.cap_vre.mean(),cap_total=g.cap_total.mean())
    r['cf_solar']=100*r['solar']/(r['cap_solar']*h) if r['cap_solar']>200 else np.nan
    r['cf_wind']=100*r['wind']/(r['cap_wind']*h) if r['cap_wind']>200 else np.nan
    r['cf_vre']=100*r['vre']/(r['cap_vre']*h) if r['cap_vre']>200 else np.nan
    r['cap_vre_share']=100*r['cap_vre']/r['cap_total']; r['gen_vre_share']=100*r['vre']/r['gen']; r['coal_share']=100*r['coal']/r['gen']; r['cover']=100*r['vre']/r['dem']
    r['roof_share']=100*(mn.solar_rooftop[s]+mn.solar_offgrid[s])/mn.solar_total[s] if s in mn.index and mn.solar_total[s]>0 else np.nan
    rows.append(r)
T=pd.DataFrame(rows).set_index('state'); T['cf_solar_ground']=T.cf_solar/(1-T.roof_share/100)
t=T.dropna(subset=['cf_solar','roof_share']); r=stats.pearsonr(t.roof_share,t.cf_solar); rs=stats.spearmanr(t.roof_share,t.cf_solar)
R['cf_roof']={'n':len(t),'pearson':r.statistic,'p':r.pvalue,'spearman':rs.statistic,'slope':stats.linregress(t.roof_share,t.cf_solar).slope,'rate':float((T.solar.sum()/(T.cap_solar.sum()*8.76))*100)}
print(T[['cap_vre','vre','cf_solar','cf_wind','cf_vre','roof_share','cf_solar_ground','cap_vre_share','gen_vre_share','cover']].sort_values('cap_vre',ascending=False).head(16).round(1).to_string())
R['cf_solar_range']={'max':T.cf_solar.nlargest(4).round(1).to_dict(),'min':T.cf_solar.nsmallest(4).round(1).to_dict(),'ground_max':T.cf_solar_ground.nlargest(4).round(1).to_dict(),'ground_min':T.cf_solar_ground.nsmallest(4).round(1).to_dict()}
R['cf_wind_range']={'max':T.cf_wind.nlargest(4).round(1).to_dict(),'min':T.cf_wind.nsmallest(4).round(1).to_dict()}
# what-if 1: wind and solar states below the median reach it
top=T[T.cap_vre>2000]; R['n_top_vre']=len(top)
# Solar: rooftop capacity is in the denominator but rooftop output looks mostly missing from generation.
# Keep the adjusted factor only where it is physically believable (under 26%) and the state has at least 1 GW solar.
ok=T[(T.cap_solar>=1000)&(T.cf_solar_ground<26)]; R['ground_ok']=ok.cf_solar_ground.round(1).to_dict(); R['ground_bad']=T[(T.cap_solar>=500)&(T.cf_solar_ground>=26)].cf_solar_ground.round(0).to_dict()
wind7=T[T.cap_wind>1000]; wm=np.average(wind7.cf_wind,weights=wind7.cap_wind); R['wind_states']=wind7.cf_wind.round(1).to_dict()
xw=((wm-wind7.cf_wind).clip(lower=0)*wind7.cap_wind*8.76/1000/100).sum()
roof_gw=(T.cap_solar*T.roof_share.fillna(0)/100).sum()/1000; hid={p_:roof_gw*8.76*p_/100 for p_ in (13,15,17)}
R['whatif_cf']={'wind_cf_weighted':wm,'extra_wind_TWh':xw,'roof_gw':roof_gw,'hidden_rooftop_TWh':hid,'solar_TWh':T.solar.sum()/1000,'hidden_pct_of_solar':100*hid[15]/(T.solar.sum()/1000),'hidden_pct_of_dem':100*hid[15]/(T.dem.sum()/1000)}
# --- seasonal match on FY2023-24 and FY2024-25
rec=full[full.fy.isin(RECENT)].copy(); rec['m']=rec.month.dt.month
cl=rec.groupby(['state','m'])[['dem','vre','Solar','Wind','Hydro','Coal','gen_total']].mean().reset_index()
days=rec.groupby('m').month.apply(lambda s:s.dt.days_in_month.mean())
for k in ['dem','vre','Solar','Wind','Hydro','Coal','gen_total']: cl[k]=cl[k]/cl.m.map(days)   # per-day so month length does not matter
rows=[]
for s,g in cl.groupby('state'):
    g=g.set_index('m').reindex([4,5,6,7,8,9,10,11,12,1,2,3])
    r=dict(state=s)
    if g.vre.sum()/g.dem.sum()>0.01 and g.vre.std()>0:
        r['match']=np.corrcoef(g.vre,g.dem)[0,1]; cov=100*g.vre/g.dem; r['cov_max']=cov.max(); r['cov_min']=cov.min(); r['cov_peakm']=cov.loc[g.dem.idxmax()]; r['cov_year']=100*g.vre.sum()/g.dem.sum(); r['best_m']=cov.idxmax(); r['worst_m']=cov.idxmin(); r['peak_m']=g.dem.idxmax()
    rows.append(r)
M=pd.DataFrame(rows).set_index('state'); M.round(2).to_csv(TAB/'sq2_seasonal_match.csv')
print(M.dropna().sort_values('cov_year',ascending=False).round(2).head(14).to_string())
Tt=T.join(M); Tt.round(3).to_csv(TAB/'sq2_state_fy2425.csv')
m2=M.dropna(); R['match']={'n':len(m2),'median':m2.match.median(),'top':m2.match.nlargest(5).round(2).to_dict(),'low':m2.match.nsmallest(6).round(2).to_dict(),'neg':int((m2.match<0).sum())}
na=rec.groupby('m')[['dem','Solar','Wind','Hydro','Coal','gen_total']].sum().reindex([4,5,6,7,8,9,10,11,12,1,2,3]).div(days.reindex([4,5,6,7,8,9,10,11,12,1,2,3])*2,axis=0)/1000
na.index=MONTHS; na.round(2).to_csv(TAB/'sq2_national_month_TWh_per_day.csv'); print(na.round(2).to_string())
na['coal_share']=100*na.Coal/na.gen_total; na['clean']=na.Solar+na.Wind+na.Hydro; R['coal_share_month']=na.coal_share.round(1).to_dict(); R['clean_month']=na.clean.round(2).to_dict()
R['nat_seasonal']={k:{'peak':na[k].idxmax(),'ratio':na[k].max()/na[k].mean(),'min':na[k].idxmin(),'low_ratio':na[k].min()/na[k].mean()} for k in ['dem','Solar','Wind','Hydro','Coal']}
R['coal_dem_corr']=float(np.corrcoef(na.Coal,na.dem)[0,1]); R['wind_dem_corr']=float(np.corrcoef(na.Wind,na.dem)[0,1]); R['solar_dem_corr']=float(np.corrcoef(na.Solar,na.dem)[0,1])
# --- net position, with generation scaled down so all-India generation equals demand
k=full[full.fy==2024].dem.sum()/full[full.fy==2024].gen_total.sum()
T['net']=T.gen*k/T.dem
yr=T.net.copy()
q=full[full.fy.isin(RECENT)].copy(); kk=q.groupby('fy').dem.sum()/q.groupby('fy').gen_total.sum(); q['g2']=q.gen_total*q.fy.map(kk); q['surp']=q.g2>q.dem
fl=q.groupby('state').surp.mean().mul(24).round(0); fs=pd.DataFrame({'surplus_months_of_24':fl,'net_fy2425':yr}); fs.round(2).to_csv(TAB/'sq2_net_position.csv')
sw=fs[(fs.surplus_months_of_24>0)&(fs.surplus_months_of_24<24)]; R['net']={'k':k,'always_import':int((fl==0).sum()),'always_export':int((fl==24).sum()),'flip':int(len(sw)),'flip_list':sw.surplus_months_of_24.to_dict(),'export_top':yr.nlargest(7).round(2).to_dict(),'import_top_big':yr[T.dem>15000].nsmallest(6).round(2).to_dict()}
# --- what-if 2: production mix against consumption mix
def consmix(frame,pool='national',key='month'):
    fr=frame.copy(); kk=fr.dem.sum()/fr.gen_total.sum(); out={}
    res=[]
    for t,g in (fr.groupby(key) if key else [(0,fr)]):
        g=g.set_index('state'); kx=g.dem.sum()/g.gen_total.sum(); G=g.gen_total*kx; D=g.dem; loc=np.minimum(G,D); imp=D-loc; ex=G-loc
        mix=g[FUELS].div(g.gen_total.replace(0,np.nan),axis=0).fillna(0)
        if pool=='national':
            pm=mix.mul(ex,axis=0).sum()/ex.sum(); pmix=pd.DataFrame([pm]*len(g),index=g.index)
        else:
            reg=g.index.map(ST2REG); pm={}
            allp=mix.mul(ex,axis=0).sum()/ex.sum()
            rows_={}
            impR=imp.groupby(reg).sum(); exR=ex.groupby(reg).sum()
            for rr in impR.index:
                ix=reg==rr; mm=mix[ix].mul(ex[ix],axis=0).sum()/max(ex[ix].sum(),1e-9)
                fromreg=min(impR[rr],exR[rr])/max(impR[rr],1e-9)
                rows_[rr]=fromreg*mm+(1-fromreg)*allp
            pmix=pd.DataFrame([rows_[z] for z in reg],index=g.index)
        c_=mix.mul(loc,axis=0)+pmix.mul(imp,axis=0)
        res.append(c_)
    C=pd.concat(res).groupby(level=0).sum()
    P=fr.groupby('state')[FUELS].sum()
    ef=pd.Series(EF); dmd=fr.groupby('state').dem.sum()
    o=pd.DataFrame({'dem':dmd,'coal_prod':100*P.Coal/P.sum(axis=1),'coal_cons':100*C.Coal/C.sum(axis=1),'vre_prod':100*(P.Solar+P.Wind)/P.sum(axis=1),'vre_cons':100*(C.Solar+C.Wind)/C.sum(axis=1),
      'ci_prod':(P[list(ef.index)]*ef).sum(axis=1)/P.sum(axis=1),'ci_cons':(C[list(ef.index)]*ef).sum(axis=1)/C.sum(axis=1)})
    return o
f24=full[full.fy==2024]
base=consmix(f24); base.round(2).to_csv(TAB/'sq2_consumption_mix.csv')
s1=consmix(f24,key=None); s2=consmix(f24,pool='region')
print(base.sort_values('dem',ascending=False).head(24).round(1).to_string())
bb=base[base.dem>10000]
R['consmix']={'n':len(bb),'range_prod':[bb.coal_prod.min(),bb.coal_prod.max()],'range_cons':[bb.coal_cons.min(),bb.coal_cons.max()],'sd_prod':bb.coal_prod.std(),'sd_cons':bb.coal_cons.std(),'ci_sd_prod':bb.ci_prod.std(),'ci_sd_cons':bb.ci_cons.std(),'ci_nat':float((base.ci_cons*base.dem).sum()/base.dem.sum()),'ci_range_cons':[bb.ci_cons.min(),bb.ci_cons.max()],'ci_range_prod':[bb.ci_prod.min(),bb.ci_prod.max()],
 'rho_prod_cons':stats.spearmanr(bb.ci_prod,bb.ci_cons).statistic,'annual_vs_month_mad':float((s1.ci_cons-base.ci_cons).abs()[bb.index].median()),'region_vs_nat_mad':float((s2.ci_cons-base.ci_cons).abs()[bb.index].median()),'region_vs_nat_max':float((s2.ci_cons-base.ci_cons).abs()[bb.index].max()),
 'delhi':base.loc['Delhi'].round(1).to_dict(),'rajasthan':base.loc['Rajasthan'].round(1).to_dict(),'chhattisgarh':base.loc['Chhattisgarh'].round(1).to_dict(),'kerala':base.loc['Kerala'].round(1).to_dict(),'himachal':base.loc['Himachal Pradesh'].round(1).to_dict(),'karnataka':base.loc['Karnataka'].round(1).to_dict(),'tn':base.loc['Tamil Nadu'].round(1).to_dict(),'gujarat':base.loc['Gujarat'].round(1).to_dict()}
# --- what-if 3: solar and wind needed each year to cover demand growth, so coal stops growing
base_dem=full[full.fy==2024].dem.sum()/1000; gr_k=full[full.fy==2024].gen_total.sum()/full[full.fy==2024].dem.sum()
cf=(n.Solar[2024]+n.Wind[2024])/((cp.cap_Solar[2024]+cp.cap_Wind[2024])*8.76)
added=cap_end.loc[2024,['cap_Solar','cap_Wind']].sum()-cap_end.loc[2023,['cap_Solar','cap_Wind']].sum()
added5=(cap_end.loc[2024,['cap_Solar','cap_Wind']].sum()-cap_end.loc[2019,['cap_Solar','cap_Wind']].sum())/5
rows=[]
for g_ in (4.0,5.5,6.5):
    for c_ in (.17,.185,.20):
        twh=base_dem*g_/100*gr_k; rows.append(dict(growth=g_,cf=100*c_,twh=twh,gw=twh/(c_*8.76)))
W3=pd.DataFrame(rows); W3.round(1).to_csv(TAB/'sq2_whatif_coal_plateau.csv',index=False)
R['whatif_plateau']={'cf_blended':cf,'added_fy2425':added,'added_avg5':added5,'base_dem':base_dem,'table':rows}
print(W3.round(1).to_string())
# additions by state, FY2019-20 to FY2024-25
ad=full[full.fy.isin([2019,2024])].groupby(['state','fy'])[['Coal','vre','gen_total','Hydro']].sum().unstack()/1000
AD=pd.DataFrame({'coal':ad['Coal'][2024]-ad['Coal'][2019],'vre':ad['vre'][2024]-ad['vre'][2019],'gen':ad['gen_total'][2024]-ad['gen_total'][2019],'hydro':ad['Hydro'][2024]-ad['Hydro'][2019]}).sort_values('coal',ascending=False); AD.round(2).to_csv(TAB/'sq2_added_by_state.csv')
tv=AD.vre.sum(); tc=AD.coal.sum(); R['added']={'vre_top4':AD.vre.nlargest(4).round(1).to_dict(),'vre_top4_pct':100*AD.vre.nlargest(4).sum()/tv,'coal_top6':AD.coal.nlargest(6).round(1).to_dict(),'coal_top6_pct':100*AD.coal.nlargest(6).sum()/tc,'raj_pct':100*AD.vre['Rajasthan']/tv,'n_coal_exceeds_vre':int((AD.coal>AD.vre).sum()),'n_vre_exceeds_coal':[x for x in AD.index if AD.vre[x]>AD.coal[x] and AD.vre[x]>2]}
# fuel mix by state, FY2024-25
mx=full[full.fy==2024].groupby('state')[FUELS+['dem']].sum(); mx.round(1).to_csv(TAB/'sq2_fuel_mix_fy2425.csv')
# coal capacity factor by state
cc=full[full.fy.isin([2019,2024])].groupby(['state','fy']).agg(c=('Coal','sum'),k=('cap_Coal','mean'),h=('hours','sum')); cc=cc[cc.k>500]; cc['cf']=100*cc.c/(cc.k*cc.h/1000); ccf=cc.cf.unstack().dropna(); ccf['chg']=ccf[2024]-ccf[2019]; ccf.round(1).to_csv(TAB/'sq2_coal_cf_state.csv'); R['coal_cf_state']={'n':len(ccf),'up':int((ccf.chg>0).sum()),'top':ccf[2024].nlargest(4).round(1).to_dict(),'low':ccf[2024].nsmallest(4).round(1).to_dict(),'chg_top':ccf.chg.nlargest(4).round(1).to_dict()}
# coal path to FY2029-30 under fixed solar and wind additions
G0=n.gen_total[2024]; C0=n.Coal[2024]; rows=[]
for x_ in (28,45,62,80):
    g_=G0; c_=C0
    rows.append(dict(add_gw=x_,fy=2024,coal=c_))
    for y_ in range(2025,2030):
        dG=g_*0.055; dV=x_*cf*8.76; g_+=dG; c_+=dG-dV; rows.append(dict(add_gw=x_,fy=y_,coal=c_))
P=pd.DataFrame(rows); P.round(1).to_csv(TAB/'sq2_coal_paths.csv',index=False); R['coal_paths_2029']=P[P.fy==2029].set_index('add_gw').coal.round(0).to_dict(); R['coal_2024']=float(C0)
yrs=cap_end[['cap_Solar','cap_Wind']].sum(axis=1).diff().dropna(); yrs.round(2).to_csv(TAB/'sq2_additions_by_year.csv'); R['additions_by_year']=yrs.round(1).to_dict()
# carbon intensity of generation
ef=pd.Series(EF); ci=(full.groupby('fy')[FUELS].sum()[list(ef.index)]*ef).sum(axis=1)/full.groupby('fy')[FUELS].sum().sum(axis=1); R['ci_gen']=ci.round(1).to_dict()
json.dump(R,open(TAB/'sq2_results.json','w'),indent=1,default=float)
print({k:R[k] for k in ['increment','cf_roof','cf_solar_range','cf_wind_range','whatif_cf','match','net','consmix','nat_seasonal','coal_dem_corr','wind_dem_corr','solar_dem_corr']})
