"""All report figures."""
from common import *
import json, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
plt.rcParams.update({'font.family':'Liberation Serif','font.size':9.5,'axes.spines.top':False,'axes.spines.right':False,'axes.linewidth':.7,'axes.edgecolor':'#555','xtick.color':'#333','ytick.color':'#333','axes.titlesize':10,'axes.titleweight':'bold','axes.titlelocation':'left','legend.frameon':False,'legend.fontsize':8.5,'lines.linewidth':1.8,'savefig.dpi':220,'savefig.bbox':'tight'})
B,O,A,Y,G6='#2a78d6','#eb6834','#1baf7a','#eda100','#008300'; GR='#6f6e69'; DK='#2b2b2b'
FYL=['19-20','20-21','21-22','22-23','23-24','24-25']
def nm(s): return SHORT.get(s,s)
S1=json.load(open(TAB/'sq1_results.json')); S2=json.load(open(TAB/'sq2_results.json'))
n=pd.read_csv(TAB/'sq2_national.csv',index_col=0)
# Fig 1
f,ax=plt.subplots(1,3,figsize=(7,2.35),gridspec_kw={'width_ratios':[1.15,1,1],'wspace':.42})
p=pd.read_csv(PRO/'merged_panel.csv',parse_dates=['month']); q=p[p.fy.isin([2019,2024])].groupby('fy')[FUELS].sum()/1000; d=(q.loc[2024]-q.loc[2019])
d=pd.Series({'Coal':d.Coal,'Solar':d.Solar,'Wind':d.Wind,'Nuclear':d.Nuclear,'Hydro':d.Hydro,'Gas':d.Gas}).sort_values()
ax[0].barh(d.index,d.values,color=[DK if i=='Coal' else (B if i in('Solar','Wind') else '#b5b4ad') for i in d.index],height=.62)
for i,v in enumerate(d.values): ax[0].text(v+(8 if v>=0 else -8),i,f'{v:+.0f}',va='center',ha='left' if v>=0 else 'right',fontsize=8)
ax[0].axvline(0,color='#555',lw=.7); ax[0].set_xlim(-60,410); ax[0].set_xlabel('Change in generation (TWh)'); ax[0].set_title('(a) FY19-20 to FY24-25')
ax[1].plot(FYL,n.coal_cf,color=DK,marker='o',ms=3.5); ax[1].set_ylim(50,75); ax[1].set_title('(b) Coal capacity factor (%)'); ax[1].set_xticks([0,2,4],['19-20','21-22','23-24'])
for i in (0,5): ax[1].annotate(f'{n.coal_cf.iloc[i]:.1f}',(i,n.coal_cf.iloc[i]),textcoords='offset points',xytext=(0,6),ha='center',fontsize=8)
ax[2].plot(FYL,n.vre_cap_share,color=B,marker='o',ms=3.5,label='Share of capacity'); ax[2].plot(FYL,n.vre_share,color=O,marker='s',ms=3.5,label='Share of generation')
ax[2].set_ylim(0,46); ax[2].set_title('(c) Solar + wind (%)'); ax[2].legend(loc='upper left'); ax[2].set_xticks([0,2,4],['19-20','21-22','23-24'])
f.savefig(FIG/'fig1_national.png'); plt.close(f)
# Fig 2
N=pd.read_csv(TAB/'sq1_national_load_factor.csv',index_col=0); f,ax=plt.subplots(1,2,figsize=(7,2.3),gridspec_kw={'wspace':.28})
x=N.loc[2019:]; lab=[f'{str(i)[2:]}-{str(i+1)[2:]}' for i in x.index]
ax[0].plot(lab,100*x.peak_demand_mw/x.peak_demand_mw[2019],color=O,marker='s',ms=3.5,label='Peak demand (MW)'); ax[0].plot(lab,100*x.energy_req_mu/x.energy_req_mu[2019],color=B,marker='o',ms=3.5,label='Energy requirement (MU)')
ax[0].set_title('(a) All-India growth, FY19-20 = 100'); ax[0].legend(loc='lower right')
lab2=[f'{str(i)[2:]}-{str(i+1)[2:]}' for i in N.index]; ax[1].plot(lab2,N.lf,color=DK,marker='o',ms=3.5); ax[1].set_ylim(72,88); ax[1].set_title('(b) All-India annual load factor (%)'); ax[1].set_xticks(range(0,len(lab2),2),lab2[::2])
for a_ in ax: a_.grid(axis='y',color='#e6e5e0',lw=.6); a_.set_axisbelow(True)
f.savefig(FIG/'fig2_load.png'); plt.close(f)
# Fig 3 heatmap
dd,e,c=load(); y=fy(dd.index); s=pd.read_csv(TAB/'sq1_state_summary.csv',index_col=0); big=s[(s.gwh2425>10000)].index
v=dd.loc[np.isin(y,RECENT),big].resample('MS').mean(); v=v/v.groupby(v.index.year-(v.index.month<4)).transform('mean'); h=v.groupby(v.index.month).mean().reindex([4,5,6,7,8,9,10,11,12,1,2,3]); h.index=MONTHS; h=h.T
h=h.iloc[np.lexsort((-h.max(axis=1).values,h.values.argmax(axis=1)))]
f,a_=plt.subplots(figsize=(6.3,3.7)); im=a_.imshow(h.values,aspect='auto',cmap='RdBu_r',norm=TwoSlopeNorm(1,.6,1.4))
a_.set_xticks(range(12),MONTHS); a_.set_yticks(range(len(h)),[nm(i) for i in h.index],fontsize=7.4); a_.spines[:].set_visible(False); a_.tick_params(length=0)
for i,row in enumerate(h.values): a_.plot(row.argmax(),i,marker='o',ms=3,color='k')
cb=f.colorbar(im,ax=a_,fraction=.03,pad=.02); cb.set_label('Average daily energy / year average',fontsize=8.5); cb.outline.set_visible(False)
f.savefig(FIG/'fig3_heatmap.png'); plt.close(f)
# Fig 5 season
na=pd.read_csv(TAB/'sq2_national_month_TWh_per_day.csv',index_col=0); f,ax=plt.subplots(1,2,figsize=(7,2.6),gridspec_kw={'wspace':.25})
for k,col,mk in [('Hydro',A,'^'),('Wind',B,'o'),('Solar',Y,'s')]: ax[0].plot(na.index,na[k],color=col,marker=mk,ms=3.2,label=k)
ax[0].plot(na.index,na.Hydro+na.Wind+na.Solar,color=DK,lw=2,label='All three'); ax[0].set_title('(a) All-India output (TWh per day)'); ax[0].legend(ncol=2,loc='upper right',fontsize=8); ax[0].set_ylim(0,1.9); ax[0].tick_params(axis='x',labelsize=7)
rec=p[p.fy.isin(RECENT)].copy(); rec['m']=rec.month.dt.month; cv=rec.groupby(['state','m'])[['vre','dem']].sum().reset_index(); cv['cov']=100*cv.vre/cv.dem
for st,col,mk in [('Rajasthan',O,'o'),('Karnataka',B,'s'),('Gujarat',A,'^'),('Tamil Nadu',Y,'D'),('Maharashtra',GR,'v')]:
    g=cv[cv.state==st].set_index('m').reindex([4,5,6,7,8,9,10,11,12,1,2,3]); ax[1].plot(MONTHS,g['cov'],color=col,marker=mk,ms=3.2,label=st)
ax[1].set_title('(b) Solar + wind as % of state demand'); ax[1].legend(ncol=2,loc='upper center',bbox_to_anchor=(.5,1.0),fontsize=7.8); ax[1].set_ylim(0,78); ax[1].tick_params(axis='x',labelsize=7)
for a_ in ax: a_.grid(axis='y',color='#e6e5e0',lw=.6); a_.set_axisbelow(True)
f.savefig(FIG/'fig5_seasonal.png'); plt.close(f)
# Fig 6 production vs consumption intensity
b=pd.read_csv(TAB/'sq2_consumption_mix.csv',index_col=0); b=b[b.dem>10000].sort_values('ci_cons'); f,a_=plt.subplots(figsize=(6.3,3.45)); yy=np.arange(len(b))
a_.hlines(yy,b.ci_prod,b.ci_cons,color='#c8c7c0',lw=1.5); a_.scatter(b.ci_prod,yy,s=20,color=O,marker='s',label='Generated in the state',zorder=3); a_.scatter(b.ci_cons,yy,s=24,color=B,label='Consumed in the state (estimate)',zorder=3)
a_.set_yticks(yy,[nm(i) for i in b.index],fontsize=7.4); a_.set_xlabel('Carbon intensity (gCO$_2$e per kWh)'); a_.legend(loc='lower right'); a_.grid(axis='x',color='#e6e5e0',lw=.6); a_.set_axisbelow(True); a_.set_xlim(0,860)
f.savefig(FIG/'fig6_consumption.png'); plt.close(f)
# Fig 7 PCA
C=pd.read_csv(TAB/'sq3_clusters.csv',index_col=0); r=C[C.window=='recent']; ee=C[C.window=='early']
L=pd.read_csv(ROOT/'code/group_names.csv'); gid={rw.anchor:rw.name for rw in L.itertuples()}; name={int(r.loc[a,'cluster']):v for a,v in gid.items()}
sty={'Renewable-led':(B,'o'),'Coal-based':(DK,'s'),'Peaky importers':(O,'^'),'Flat-load importers':(Y,'D'),'Hydro exporters':(A,'v'),'Low-demand importers':('#e87ba4','P')}
f,a_=plt.subplots(figsize=(6.6,3.5))
for cl,g in r.groupby('cluster'):
    col,mk=sty[name[cl]]; a_.scatter(g.PC1,g.PC2,s=30,color=col,marker=mk,label=name[cl],edgecolor='white',lw=.4,zorder=3)
lab={'Rajasthan':(5,2),'Gujarat':(5,3),'Karnataka':(3,8),'Tamil Nadu':(5,1),'Andhra Pradesh':(-32,-11),'Chhattisgarh':(5,3),'Bihar':(-14,6),'Uttar Pradesh':(-16,-11),'Delhi':(5,2),'Punjab':(5,3),'Haryana':(5,2),'Himachal Pradesh':(5,3),'Kerala':(5,2),'Goa':(5,2),'Maharashtra':(5,-8),'Sikkim':(5,2),'Assam':(5,2),'Odisha':(5,2)}
for st,o_ in lab.items(): a_.annotate(nm(st),(r.PC1[st],r.PC2[st]),xytext=o_,textcoords='offset points',fontsize=7.8)
for st in ['Andhra Pradesh','Rajasthan']: a_.annotate('',xy=(r.PC1[st],r.PC2[st]),xytext=(ee.PC1[st],ee.PC2[st]),arrowprops=dict(arrowstyle='->',color=GR,lw=1))
J=json.load(open(TAB/'sq3_results.json')); a_.set_xlabel(f"PC1: solar and wind against hydro ({100*J['evr'][0]:.0f}% of variance)"); a_.set_ylabel(f"PC2: net exporter, low use ({100*J['evr'][1]:.0f}%)"); a_.axhline(0,color='#ddd',lw=.6,zorder=0); a_.axvline(0,color='#ddd',lw=.6,zorder=0)
a_.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,1.2))
f.savefig(FIG/'fig7_pca.png'); plt.close(f)

# ------------- additional figures -------------
# Fig A cross-checks
f,ax=plt.subplots(1,3,figsize=(7,2.15),gridspec_kw={'wspace':.32})
v=pd.read_csv(TAB/'validation_gridindia_vs_cea.csv',index_col=0); c_=pd.read_csv(TAB/'validation_capacity_mar2025.csv')
for a_,x_,y_,t_,xl,yl in [(ax[0],v.req_fy1920/1000,v.gi_1920/1000,'(a) Annual demand, FY19-20','CEA requirement (TWh)','Grid-India met (TWh)'),(ax[1],v.req_fy2526/1000,v.gi_2526/1000,'(b) Annual demand, FY25-26','CEA requirement (TWh)','Grid-India met (TWh)')]:
    a_.scatter(x_,y_,s=12,color=B,alpha=.7,lw=0); lo=min(x_.min(),y_.min()); hi=max(x_.max(),y_.max()); a_.plot([lo,hi],[lo,hi],color=GR,lw=.8); a_.set_xscale('log'); a_.set_yscale('log'); a_.set_title(t_,fontsize=9); a_.set_xlabel(xl,fontsize=8.3); a_.set_ylabel(yl,fontsize=8.3); a_.tick_params(labelsize=7.5)
a_=ax[2]; cs=c_[c_.SolarTotal>5]; cw=c_[c_.mnre_wind>5]
a_.scatter(cs.SolarTotal/1000,cs.cap_Solar/1000,s=12,color=Y,lw=0,label='Solar'); a_.scatter(cw.mnre_wind/1000,cw.cap_Wind/1000,s=14,color=B,marker='s',lw=0,label='Wind')
a_.plot([.003,35],[.003,35],color=GR,lw=.8); a_.set_xscale('log'); a_.set_yscale('log'); a_.set_title('(c) Capacity, 31 Mar 2025',fontsize=9); a_.set_xlabel('MNRE (GW)',fontsize=8.3); a_.set_ylabel('Ember (GW)',fontsize=8.3); a_.tick_params(labelsize=7.5); a_.legend(fontsize=7.4,loc='upper left')
f.savefig(FIG/'figA_checks.png'); plt.close(f)
# Fig B: growth, income, swing (three panels)
f,ax=plt.subplots(1,3,figsize=(7.2,2.75),gridspec_kw={'wspace':.42,'width_ratios':[.9,1.05,1]})
q=s[s.gwh2425>10000].sort_values('cagr'); ax[0].barh([nm(i) for i in q.index],q.cagr,color=[B if i not in('Bihar','Rajasthan','Odisha','Punjab') else O for i in q.index],height=.7); ax[0].tick_params(axis='y',labelsize=6.4); ax[0].axvline(s.cagr.median(),color=GR,lw=.9,ls='--'); ax[0].set_title('(a) Demand growth (% a year)'); ax[0].text(s.cagr.median()+.08,0.1,'median',fontsize=7.5,color=GR)
t=s.dropna(subset=['gsdp_pc_constant_fy2425']); a_=ax[1]
a_.scatter(t.gsdp_pc_constant_fy2425/1000,t.kwh_pc2425,s=16,color=B,edgecolor='white',lw=.4); a_.set_xscale('log'); a_.set_yscale('log')
ii=S1['income']; xs=np.array([38,340]); rx=np.polyfit(np.log(t.gsdp_pc_constant_fy2425/1000),np.log(t.kwh_pc2425),1); a_.plot(xs,np.exp(np.polyval(rx,np.log(xs))),color=GR,lw=1)
off={'Punjab':(4,3),'Bihar':(5,0),'Madhya Pradesh':(5,3),'Assam':(-4,-9),'Delhi':(5,-3),'Kerala':(4,-8),'Gujarat':(-4,6),'Uttar Pradesh':(5,-7),'Chhattisgarh':(-46,3),'Goa':(-16,3)}
for st,o_ in off.items():
    if st in t.index: a_.annotate(nm(st),(t.gsdp_pc_constant_fy2425[st]/1000,t.kwh_pc2425[st]),xytext=o_,textcoords='offset points',fontsize=7)
a_.set_xticks([50,100,200,400],['50','100','200','400']); a_.set_yticks([300,1000,3000],['300','1,000','3,000']); a_.minorticks_off()
a_.set_xlabel('GSDP per person, FY24-25 (Rs 000, constant)'); a_.set_ylabel('Electricity per person (kWh)'); a_.set_title('(b) Demand against income')
ax[2].scatter(q.swing_e,q.swing_r,s=18,color=B,edgecolor='white',lw=.3); ax[2].plot([1,2.6],[1,2.6],color=GR,lw=.8); ax[2].set_xlabel('Swing, early window'); ax[2].set_ylabel('Swing, recent window'); ax[2].set_title('(c) Seasonal swing')
for st,o_ in {'Punjab':(-30,3),'Delhi':(-24,4),'Haryana':(5,-6),'Assam':(-22,5),'Gujarat':(5,-5)}.items(): ax[2].annotate(nm(st),(q.swing_e[st],q.swing_r[st]),xytext=o_,textcoords='offset points',fontsize=7.8)
ax[1].xaxis.label.set_size(7.6); ax[1].set_xlabel('GSDP per person (Rs 000)')
f.savefig(FIG/'figB_growth.png'); plt.close(f)
# Fig C fuel mix
M_=pd.read_csv(TAB/'sq2_fuel_mix_fy2425.csv',index_col=0); M_=M_[M_.dem>10000]; tot=M_[FUELS].sum(axis=1); sh=pd.DataFrame({'Coal':M_.Coal,'Gas and other':M_.Gas+M_.OtherFossil,'Nuclear':M_.Nuclear,'Hydro':M_.Hydro,'Bio':M_.Bioenergy+M_.OtherRE,'Wind':M_.Wind,'Solar':M_.Solar}).div(tot,axis=0)*100; sh=sh.sort_values('Coal',ascending=False)
f,a_=plt.subplots(figsize=(7,2.45)); b0=np.zeros(len(sh)); cols={'Coal':DK,'Gas and other':'#8d8c86','Nuclear':'#6250d6','Hydro':A,'Bio':'#c9c8c0','Wind':B,'Solar':Y}
for k_ in sh: a_.bar([nm(i) for i in sh.index],sh[k_],bottom=b0,color=cols[k_],label=k_,width=.78,edgecolor='white',lw=.3); b0+=sh[k_].values
a_.set_ylim(0,100); a_.tick_params(axis='x',labelrotation=62,labelsize=7.6); a_.set_ylabel('% of generation'); a_.legend(ncol=7,loc='upper center',bbox_to_anchor=(.5,1.16),fontsize=7.8,columnspacing=1,handlelength=1)
f.savefig(FIG/'figC_mix.png'); plt.close(f)
# Fig D additions by state
AD=pd.read_csv(TAB/'sq2_added_by_state.csv',index_col=0); AD['t']=AD.coal.abs()+AD.vre; T_=AD.nlargest(14,'t').sort_values('t'); yy=np.arange(len(T_))
f,a_=plt.subplots(figsize=(6.4,2.75)); a_.barh(yy+.2,T_.coal,height=.38,color=DK,label='Coal'); a_.barh(yy-.2,T_.vre,height=.38,color=B,label='Solar + wind'); a_.set_yticks(yy,[nm(i) for i in T_.index],fontsize=7.8); a_.axvline(0,color='#555',lw=.7); a_.set_xlabel('Change in generation, FY19-20 to FY24-25 (TWh)'); a_.legend(loc='lower right')
f.savefig(FIG/'figD_added.png'); plt.close(f)
# Fig E: capacity vs energy, wind CF, rooftop (three panels)
t2=pd.read_csv(TAB/'sq2_state_fy2425.csv',index_col=0); f,ax=plt.subplots(1,3,figsize=(7.2,2.6),gridspec_kw={'wspace':.42})
t3=t2[t2.cap_vre>1000]; ax[0].scatter(t3.cap_vre_share,t3.gen_vre_share,s=np.sqrt(t3.cap_vre)*.9,color=B,edgecolor='white',lw=.4); ax[0].plot([0,75],[0,75],color=GR,lw=.8); ax[0].set_xlim(0,75); ax[0].set_ylim(0,75)
for st,o_ in {'Rajasthan':(-46,6),'Gujarat':(4,-10),'Karnataka':(-40,6),'Tamil Nadu':(5,-9),'Maharashtra':(6,-3)}.items(): ax[0].annotate(st,(t3.cap_vre_share[st],t3.gen_vre_share[st]),xytext=o_,textcoords='offset points',fontsize=7.8)
ax[0].text(47,60,'equal share',fontsize=7.8,color=GR,rotation=38); ax[0].set_xlabel('Solar + wind, % of capacity'); ax[0].set_ylabel('Solar + wind, % of generation'); ax[0].set_title('(a) Capacity against energy')
wd=t2[t2.cap_wind>1000].cf_wind.sort_values(); ax[1].barh([nm(i) for i in wd.index],wd,color=B,height=.62); ax[1].axvline(np.average(t2[t2.cap_wind>1000].cf_wind,weights=t2[t2.cap_wind>1000].cap_wind),color=GR,ls='--',lw=.9); ax[1].set_title('(b) Wind capacity factor (%)'); ax[1].tick_params(axis='y',labelsize=8)
for i,v_ in enumerate(wd): ax[1].text(v_+.3,i,f'{v_:.1f}',va='center',fontsize=7.8)
ax[1].set_xlim(0,28)
T=pd.read_csv(TAB/'sq2_state_fy2425.csv',index_col=0).dropna(subset=['cf_solar','roof_share']); a_=ax[2]
a_.scatter(T.roof_share,T.cf_solar,s=np.sqrt(T.cap_solar)*1.1,color=O,edgecolor='white',lw=.4,alpha=.9)
for st,o_ in {'Rajasthan':(6,1),'Gujarat':(6,2),'Maharashtra':(6,2),'Haryana':(-30,5),'Delhi':(-4,6),'Kerala':(-10,6),'Tamil Nadu':(6,4),'Uttarakhand':(5,-4)}.items():
    if st in T.index: a_.annotate(nm(st),(T.roof_share[st],T.cf_solar[st]),xytext=o_,textcoords='offset points',fontsize=7.8)
a_.set_xlabel('Rooftop + off-grid share (%)'); a_.set_ylabel('Solar capacity factor (%)'); a_.set_title('(c) Solar CF against rooftop share'); a_.set_ylim(4,25); a_.set_xlim(0,104)
ax[0].set_title('(a) Capacity against energy',fontsize=9.5)
f.savefig(FIG/'figE_capacity.png'); plt.close(f)
# Fig F national fuel by month, coal share
f,ax=plt.subplots(1,2,figsize=(7,2.35),gridspec_kw={'wspace':.24,'width_ratios':[1.35,1]})
na2=na.copy(); oth=na2.gen_total-na2.Coal-na2.Hydro-na2.Wind-na2.Solar; b0=np.zeros(12)
for lab_,vals,col in [('Coal',na2.Coal,DK),('Other',oth,'#b5b4ad'),('Hydro',na2.Hydro,A),('Wind',na2.Wind,B),('Solar',na2.Solar,Y)]: ax[0].bar(MONTHS,vals,bottom=b0,color=col,label=lab_,width=.8,edgecolor='white',lw=.3); b0+=vals.values
ax[0].plot(MONTHS,na2.dem,color=O,marker='o',ms=3,lw=1.5,label='Demand met'); ax[0].set_ylim(0,5.5); ax[0].legend(ncol=3,fontsize=7.2,loc='upper center',bbox_to_anchor=(.5,-.13),columnspacing=.8,handlelength=1); ax[0].set_title('(a) Generation by month (TWh per day)'); ax[0].tick_params(axis='x',labelsize=7)
ax[1].plot(MONTHS,100*na2.Coal/na2.gen_total,color=DK,marker='o',ms=3.2); ax[1].set_ylim(60,82); ax[1].set_xticks(range(0,12,2),MONTHS[::2]); ax[1].set_title('(b) Coal share of generation (%)'); ax[1].tick_params(axis='x',labelsize=7); ax[1].grid(axis='y',color='#e6e5e0',lw=.6)
f.savefig(FIG/'figF_month.png'); plt.close(f)
# Fig G net position heatmap
rec2=p[p.fy.isin(RECENT)].copy(); kk=rec2.groupby('fy').dem.sum()/rec2.groupby('fy').gen_total.sum(); rec2['g2']=rec2.gen_total*rec2.fy.map(kk); rec2['m']=rec2.month.dt.month
h2=rec2.groupby(['state','m'])[['g2','dem']].sum(); h2=np.log2((h2.g2/h2.dem).clip(1/8,8)).unstack()[[4,5,6,7,8,9,10,11,12,1,2,3]]; h2.columns=MONTHS; h2=h2.loc[big]; h2=h2.loc[h2.mean(axis=1).sort_values(ascending=False).index]
f,a_=plt.subplots(figsize=(6.3,3.85)); im=a_.imshow(h2.values,aspect='auto',cmap='RdBu_r',norm=TwoSlopeNorm(0,-3,3)); a_.set_xticks(range(12),MONTHS); a_.set_yticks(range(len(h2)),[nm(i) for i in h2.index],fontsize=7.6); a_.spines[:].set_visible(False); a_.tick_params(length=0)
cb=f.colorbar(im,ax=a_,fraction=.03,pad=.02,ticks=[-3,-2,-1,0,1,2,3]); cb.ax.set_yticklabels(['1/8','1/4','1/2','1','2','4','8'],fontsize=8); cb.set_label('Scaled generation / demand',fontsize=8.5); cb.outline.set_visible(False)
f.savefig(FIG/'figG_net.png'); plt.close(f)
# Fig H what-if: additions and coal paths
W_=pd.read_csv(TAB/'sq2_whatif_coal_plateau.csv'); ay=pd.read_csv(TAB/'sq2_additions_by_year.csv',index_col=0).iloc[:,0]; P_=pd.read_csv(TAB/'sq2_coal_paths.csv')
f,ax=plt.subplots(1,2,figsize=(7,2.5),gridspec_kw={'wspace':.25})
ax[0].bar([f'{str(i)[2:]}-{str(i+1)[2:]}' for i in ay.index],ay.values,color=B,width=.6); ax[0].axhspan(W_.gw.min(),W_.gw.max(),color=O,alpha=.18,lw=0); ax[0].axhline(61.9,color=O,lw=1.4); ax[0].text(-.4,64,'needed to hold coal flat: about 62 GW',fontsize=8)
for i,v_ in enumerate(ay.values): ax[0].text(i,v_+1.5,f'{v_:.0f}',ha='center',fontsize=8)
ax[0].set_ylim(0,88); ax[0].set_title('(a) Solar + wind added each year (GW)')
for x_,col,mk in [(28,DK,'o'),(45,B,'s'),(62,A,'^'),(80,O,'D')]:
    g_=P_[P_.add_gw==x_]; ax[1].plot([f'{str(i)[2:]}-{str(i+1)[2:]}' for i in g_.fy],g_.coal,color=col,marker=mk,ms=3,label=f'{x_} GW a year')
ax[1].set_title('(b) Coal generation if demand grows 5.5% (TWh)'); ax[1].legend(loc='upper left',fontsize=7.8,ncol=2); ax[1].set_ylim(600,2300); ax[1].tick_params(axis='x',labelsize=8)
f.savefig(FIG/'figH_whatif.png'); plt.close(f)
# Fig I model selection and group profile
MS=pd.read_csv(TAB/'sq3_model_selection.csv',index_col=0); f,ax=plt.subplots(1,3,figsize=(7,2.5),gridspec_kw={'wspace':.5,'width_ratios':[.8,1.35,1.1]})
ax[0].plot(MS.index,MS.sil_kmeans,color=B,marker='o',ms=3.2,label='Silhouette'); ax[0].plot(MS.index,MS.boot_ari,color=O,marker='s',ms=3.2,label='Bootstrap ARI'); ax[0].axvline(6,color=GR,ls='--',lw=.8); ax[0].set_ylim(0,1); ax[0].set_xlabel('k'); ax[0].set_xticks([2,4,6,8]); ax[0].legend(fontsize=7.2,loc='center right'); ax[0].set_title('(a) Choice of k')
gs=pd.read_csv(TAB/'sq3_group_summary.csv',index_col=0); gs.index=[name[i] for i in gs.index]; gs=gs.loc[list(sty)]
pr=gs[['coal_share','hydro_share','vre_share','log_net','log_kwh_pc','dem_growth','vre_gain','swing','flat']]; z=(pr-pr.mean())/pr.std()
im=ax[1].imshow(z.values,aspect='auto',cmap='RdBu_r',vmin=-1.8,vmax=1.8); ax[1].set_xticks(range(9),['Coal','Hydro','S+W','Net','Use','Growth','S+W gain','Swing','Flat'],rotation=70,fontsize=7.2); ax[1].set_yticks(range(6),[x.replace(' importers',' imp.').replace(' exporters',' exp.') for x in z.index],fontsize=7.2); ax[1].spines[:].set_visible(False); ax[1].tick_params(length=0); ax[1].set_title('(b) Group profiles')
y6=np.arange(6); h_=.26
ax[2].barh(y6-h_,gs.dem_pct,height=h_,color='#b5b4ad',label='Demand'); ax[2].barh(y6,gs.coal_pct,height=h_,color=DK,label='Coal'); ax[2].barh(y6+h_,gs.vre_pct,height=h_,color=B,label='S+W'); ax[2].invert_yaxis(); ax[2].set_yticks([]); ax[2].legend(fontsize=7.2,loc='lower right'); ax[2].set_title('(c) Share of India (%)'); 
f.savefig(FIG/'figI_groups.png'); plt.close(f)

# Fig J coal capacity factor by state
cfs=pd.read_csv(TAB/'sq2_coal_cf_state.csv',index_col=0).sort_values('2024'); yy=np.arange(len(cfs))
f,ax=plt.subplots(1,2,figsize=(7,2.9),gridspec_kw={'wspace':.32,'width_ratios':[1.2,1]})
ax[0].hlines(yy,cfs['2019'],cfs['2024'],color='#c8c7c0',lw=1.5); ax[0].scatter(cfs['2019'],yy,s=16,color='#9a9993',label='FY19-20',zorder=3); ax[0].scatter(cfs['2024'],yy,s=18,color=DK,label='FY24-25',zorder=3)
ax[0].set_yticks(yy,[nm(i) for i in cfs.index],fontsize=7.6); ax[0].set_xlabel('Coal capacity factor (%)'); ax[0].legend(loc='lower right',fontsize=7.6); ax[0].set_title('(a) Coal plants run harder almost everywhere'); ax[0].set_xlim(20,90)
J1=json.load(open(TAB/'sq1_results.json')); sh_=pd.Series(J1['shortage_pct']); sh_.index=[f"{str(int(i))[2:]}-{str(int(i)+1)[2:]}" for i in sh_.index]; sh_=sh_.iloc[:-1]
ax[1].bar(sh_.index,sh_.values,color=O,width=.6); ax[1].set_title('(b) Energy not supplied (% of demand)'); ax[1].tick_params(axis='x',labelsize=7.5)
for i,v_ in enumerate(sh_.values): ax[1].text(i,v_+.01,f'{v_:.2f}',ha='center',fontsize=7.4)
f.savefig(FIG/'figJ_coalcf.png'); plt.close(f)
# Fig K coverage over year vs in peak month
sm=pd.read_csv(TAB/'sq2_seasonal_match.csv',index_col=0).dropna(); sm=sm[sm.cov_year>5].sort_values('cov_year'); yy=np.arange(len(sm))
f,ax=plt.subplots(1,2,figsize=(7,2.55),gridspec_kw={'wspace':.38})
ax[0].barh(yy+.2,sm.cov_year,height=.38,color=B,label='Whole year'); ax[0].barh(yy-.2,sm.cov_peakm,height=.38,color=O,label='Peak-demand month'); ax[0].set_yticks(yy,[nm(i) for i in sm.index],fontsize=8); ax[0].set_xlabel('Solar + wind as % of demand'); ax[0].legend(loc='lower right',fontsize=7.6); ax[0].set_title('(a) Coverage when it matters')
mm=pd.read_csv(TAB/'sq2_seasonal_match.csv',index_col=0).dropna().sort_values('match'); ax[1].barh([nm(i) for i in mm.index],mm.match,color=[O if v_<0 else B for v_ in mm.match],height=.65); ax[1].axvline(0,color='#555',lw=.7); ax[1].tick_params(axis='y',labelsize=7.2); ax[1].set_xlabel('Correlation, monthly S+W vs demand'); ax[1].set_title('(b) Seasonal match'); ax[1].set_xlim(-.7,.75)
f.savefig(FIG/'figK_cover.png'); plt.close(f)
