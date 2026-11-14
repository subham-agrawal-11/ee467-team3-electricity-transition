"""SQ3. PCA and clustering of state-windows; movement between early and recent."""
from common import *
import json, warnings, sys; warnings.filterwarnings('ignore')
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, adjusted_rand_score
def features(w=0.5):
    dd,e,c=load(w); y=fy(dd.index)
    dm=dd.resample('MS').sum().stack().rename('dem').reset_index(); dm.columns=['month','state','dem']
    p=e[e.month>='2019-04-01'].merge(dm,on=['state','month']); p['vre']=p.Solar+p.Wind
    k=p[p.fy.between(2019,2024)].groupby('fy').apply(lambda g:g.dem.sum()/g.gen_total.sum())
    def one(fl,base,end,label):
        g=p[p.fy.isin(fl)]; a=g.groupby('state')[['gen_total','Coal','Hydro','vre','dem']].sum()
        scale=k[fl].mean(); base_=np.maximum(a.gen_total*scale,a.dem)   # local energy base: larger of scaled generation and demand
        F=pd.DataFrame(index=a.index); F['coal_share']=100*a.Coal*scale/base_; F['hydro_share']=100*a.Hydro*scale/base_; F['vre_share']=100*a.vre*scale/base_
        F['log_net']=np.log2((a.gen_total*k[fl].mean()/a.dem).clip(lower=1/16))
        kwh=np.mean([dd[y==f].sum()*1e6/pop(c,f+.75).reindex(dd.columns) for f in fl],axis=0); F['log_kwh_pc']=pd.Series(np.log(kwh),index=dd.columns)
        F['dem_growth']=100*((dd[y==end].sum()/dd[y==base].sum())**(1/(end-base))-1)
        def vs(f_):
            q=p[p.fy==f_].groupby('state')[['vre','gen_total','dem']].sum(); return 100*q.vre*k[f_]/np.maximum(q.gen_total*k[f_],q.dem)
        F['vre_gain']=(vs(end)-vs(base))/(end-base)
        m=[]; fl_=[]
        for f in fl:
            v=dd[y==f]; mo=v.resample('MS').mean(); m.append(mo.max()/mo.min()); fl_.append(v.mean()/v.max())
        F['swing']=pd.concat(m,axis=1).mean(axis=1); F['flat']=pd.concat(fl_,axis=1).mean(axis=1)
        F['window']=label; return F
    A=pd.concat([one(EARLY,2019,2021,'early'),one(RECENT,2021,2024,'recent')])
    return A
COLS=['coal_share','hydro_share','vre_share','log_net','log_kwh_pc','dem_growth','vre_gain','swing','flat']

def scale(A):
    q=A[COLS]; return StandardScaler().fit_transform(q.clip(lower=q.quantile(.02),upper=q.quantile(.98),axis=1))
def stable_labels(X,k): return KMeans(k,n_init=50,random_state=7).fit(X)
if __name__=='__main__':
    R={}
    A=features(); A.index.name='state'; A.round(3).to_csv(TAB/'sq3_features.csv')
    X=scale(A); pca=PCA().fit(X); Z=pca.transform(X)
    R['evr']=pca.explained_variance_ratio_.round(4).tolist(); R['pcs_for_80']=int(np.searchsorted(np.cumsum(pca.explained_variance_ratio_),.8)+1)
    ld=pd.DataFrame(pca.components_[:4].T,index=COLS,columns=['PC1','PC2','PC3','PC4']); ld.round(3).to_csv(TAB/'sq3_pca_loadings.csv'); print(ld.round(2).to_string()); print(R)
    sc=[]
    for kk in range(2,9):
        km=KMeans(kk,n_init=50,random_state=7).fit(X); wd=AgglomerativeClustering(kk,linkage='ward').fit(X)
        sc.append(dict(k=kk,sil_kmeans=silhouette_score(X,km.labels_),sil_ward=silhouette_score(X,wd.labels_),ari_km_ward=adjusted_rand_score(km.labels_,wd.labels_)))
    SC=pd.DataFrame(sc).set_index('k'); SC.round(3).to_csv(TAB/'sq3_silhouette.csv'); print(SC.round(3).to_string())
    # ---- bootstrap stability: resample states with both their windows, refit, compare on the states drawn (Hennig Jaccard)
    rng=np.random.default_rng(11); states=A.index.unique().tolist(); B=300; rows=[]
    for K in [4,5,6,7]:
        base=stable_labels(X,K).labels_; jac=[[] for _ in range(K)]; aris=[]
        for b in range(B):
            pick=rng.choice(len(states),len(states),replace=True); idx=[]
            for p_ in pick:
                idx+= [i for i,st in enumerate(A.index) if st==states[p_]]
            idx=np.array(idx); lab=KMeans(K,n_init=5,random_state=b).fit(X[idx]).labels_
            aris.append(adjusted_rand_score(base[idx],lab))
            for c_ in range(K):
                m=base[idx]==c_
                if m.sum()==0: continue
                jac[c_].append(max(((m&(lab==l)).sum()/(m|(lab==l)).sum()) for l in range(K)))
        rows.append(dict(k=K,boot_ari=np.mean(aris),min_cluster_jaccard=min(np.mean(j) for j in jac),mean_cluster_jaccard=np.mean([np.mean(j) for j in jac]))); print(rows[-1])
    SB=pd.DataFrame(rows).set_index('k'); SC.join(SB).round(3).to_csv(TAB/'sq3_model_selection.csv'); print(SC.join(SB).round(3).to_string())
    K=int(sys.argv[1]) if len(sys.argv)>1 else 6
    km=stable_labels(X,K); A['cluster']=km.labels_
    A['PC1'],A['PC2'],A['PC3']=Z[:,0],Z[:,1],Z[:,2]
    from sklearn.metrics import silhouette_samples
    A['sil']=silhouette_samples(X,km.labels_)
    # distance to nearest other centre, relative to own centre
    D=km.transform(X); own=D[np.arange(len(D)),km.labels_]; D2=D.copy(); D2[np.arange(len(D)),km.labels_]=np.inf; A['margin']=(D2.min(axis=1)-own)/own; A['next_cluster']=D2.argmin(axis=1)
    A.round(3).to_csv(TAB/'sq3_clusters.csv')
    # sensitivity
    sens={}
    base=km.labels_
    sens['ward_ari']=adjusted_rand_score(base,AgglomerativeClustering(K,linkage='ward').fit(X).labels_)
    for w in (0.3,0.7):
        Aw=features(w); sens[f'dvc_{w}']=adjusted_rand_score(base,stable_labels(scale(Aw),K).labels_)
    lof={}
    for c_ in COLS:
        keep=[i for i,x in enumerate(COLS) if x!=c_]; lof[c_]=adjusted_rand_score(base,stable_labels(X[:,keep],K).labels_)
    sens['leave_one_feature_out']=lof
    bigs=pd.read_csv(TAB/'sq1_state_summary.csv',index_col=0); bigs=bigs[bigs.gwh2425>10000].index
    m=A.index.isin(bigs); sens['big_only_ari_on_shared']=adjusted_rand_score(base[m],stable_labels(scale(A[m]),min(K,5)).labels_)
    R['sens']=sens; print(sens)
    # movement
    e_=A[A.window=='early']; r_=A[A.window=='recent']; mv=[]
    for st in e_.index:
        a,b=e_.loc[st],r_.loc[st]; mv.append(dict(state=st,early=int(a.cluster),recent=int(b.cluster),dist=float(np.linalg.norm(X[(A.index==st)&(A.window=='recent')]-X[(A.index==st)&(A.window=='early')])),vre_e=a.vre_share,vre_r=b.vre_share,coal_e=a.coal_share,coal_r=b.coal_share,margin_r=b.margin,next_r=int(b.next_cluster)))
    MV=pd.DataFrame(mv).set_index('state').sort_values('dist',ascending=False); MV.round(3).to_csv(TAB/'sq3_movement.csv')
    print(MV.round(2).head(12).to_string()); print('moved:',MV[MV.early!=MV.recent].index.tolist())
    print('closest to border recent:',MV.sort_values('margin_r').head(8)[['recent','next_r','margin_r']].round(2).to_string())
    # group sizes on the recent window
    dd,e,c=load(); y=fy(dd.index); dem=dd[y==2024].sum(); P=pop(c,2024.75).reindex(dem.index)
    ee=e[e.fy==2024].groupby('state')[['gen_total','Coal','Solar','Wind','Hydro']].sum()
    G=pd.DataFrame({'cluster':r_.cluster}).join(pd.DataFrame({'dem':dem,'pop':P})).join(ee)
    H=G.groupby('cluster').sum(); H['n']=G.groupby('cluster').size()
    H2=pd.DataFrame({'n':H.n,'dem_pct':100*H.dem/H.dem.sum(),'pop_pct':100*H['pop']/H['pop'].sum(),'gen_pct':100*H.gen_total/H.gen_total.sum(),'coal_pct':100*H.Coal/H.Coal.sum(),'vre_pct':100*(H.Solar+H.Wind)/(H.Solar+H.Wind).sum(),'hydro_pct':100*H.Hydro/H.Hydro.sum(),'g_over_d':(H.gen_total*0.9265)/H.dem})
    prof=r_.groupby('cluster')[COLS].mean(); out=H2.join(prof); out.round(2).to_csv(TAB/'sq3_group_summary.csv'); print(out.round(2).T.to_string())
    for cl,g in r_.groupby('cluster'): print(cl,list(g.index))
    json.dump(R,open(TAB/'sq3_results.json','w'),indent=1,default=float)
