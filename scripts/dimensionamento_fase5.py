import json, csv, sys, math, statistics as st
D = sys.argv[1]
v = json.load(open(f"{D}/fase5_resultados_val.json"))["por_execucao"]
rows = []
for k, m in v.items():
    _, S, arm, seed = k.split("_"); seed = seed.replace("seed", "")
    rows.append(dict(split="val", S=S, arm=arm, seed=seed, recall=m["recall"], map50=m["map50"], auc=m["auc"], small=m["small"]))
for r in csv.DictReader(open(f"{D}/fase5_teste_metricas.csv")):
    rows.append(dict(split="teste", S=r["orcamento"], arm=r["braco"], seed=r["seed"], recall=float(r["recall"]), map50=float(r["mAP50"]), small=float(r["recall_small"])))
assert sum(r["split"]=="val" for r in rows)==30 and sum(r["split"]=="teste" for r in rows)==30

def tq(p, df):  # quantil t por bisseção sobre a CDF (integração numérica)
    def cdf(t):
        n=4000; a=-60.0; h=(t-a)/n
        c=math.gamma((df+1)/2)/(math.sqrt(df*math.pi)*math.gamma(df/2))
        f=lambda x: c*(1+x*x/df)**(-(df+1)/2)
        s=f(a)+f(t)+sum((4 if i%2 else 2)*f(a+i*h) for i in range(1,n))
        return s*h/3
    lo,hi=-50,50
    for _ in range(60):
        mid=(lo+hi)/2
        if cdf(mid)<p: lo=mid
        else: hi=mid
    return (lo+hi)/2
assert abs(tq(0.975,4)-2.776)<0.01 and abs(tq(0.975,20)-2.086)<0.01

def n_pareado(sd, delta, alpha=0.05, power=0.8):
    n=3
    while n<2000:
        df=n-1
        if (tq(1-alpha/2,df)+tq(power,df))*sd/math.sqrt(n) <= delta: return n
        n+=1
    return None

print("Métrica | split | dp entre seeds (dentro do braço) | dp residual (bloco seed) | dp dif. pareada M50-C S2 | S1")
res={}
for split in ("val","teste"):
    for met in ("recall","map50","auc","small"):
        R=[r for r in rows if r["split"]==split and met in r]
        if not R: continue
        # dp dentro do braço, agrupado nos 6 braços
        var=[]
        for S in ("S1","S2"):
            for arm in ("C","M25","M50"):
                x=[100*r[met] for r in R if r["S"]==S and r["arm"]==arm]; assert len(x)==5
                var.append(st.variance(x))
        sd_within=math.sqrt(sum(var)/len(var))
        # residual após efeitos de célula e de seed (bloco) : 30 obs, df=20
        cell={}; seedm={}; g=st.mean(100*r[met] for r in R)
        for S in ("S1","S2"):
            for arm in ("C","M25","M50"):
                cell[(S,arm)]=st.mean(100*r[met] for r in R if r["S"]==S and r["arm"]==arm)
        for s in set(r["seed"] for r in R):
            seedm[s]=st.mean(100*r[met] for r in R if r["seed"]==s)
        sse=sum((100*r[met]-cell[(r["S"],r["arm"])]-seedm[r["seed"]]+g)**2 for r in R)
        sd_res=math.sqrt(sse/20)
        def dpar(S):
            d=[]
            for s in seedm:
                a=[r for r in R if r["S"]==S and r["seed"]==s]
                d.append(100*([x for x in a if x["arm"]=="M50"][0][met]-[x for x in a if x["arm"]=="C"][0][met]))
            return st.stdev(d), st.mean(d)
        d2,m2=dpar("S2"); d1,m1=dpar("S1")
        res[(split,met)]=(sd_within,sd_res,d2,d1)
        print(f"{met:7s} {split:5s}  within={sd_within:.2f}  resid={sd_res:.2f}  dp_par_S2={d2:.2f} (média {m2:+.2f})  dp_par_S1={d1:.2f} (média {m1:+.2f})")

print("\nSeeds necessárias por braço, contraste pareado, alfa=0,05 bicaudal, poder 80%")
print("métrica split dp_par | delta=0,5 | 1,0 | 1,5 | 2,0")
for (split,met),(w,rs,d2,d1) in res.items():
    for lab,sd in (("S2",d2),("S1",d1)):
        print(f"{met:7s} {split:5s} {lab} dp={sd:.2f} | "+" | ".join(str(n_pareado(sd,dl)) for dl in (0.5,1.0,1.5,2.0)))

print("\nDesenho por subconjuntos aleatórios: efeito mínimo detectável (pp por 1 dp da característica), poder 80%, z")
z=1.96+0.8416
for (split,met),(w,rs,d2,d1) in res.items():
    print(f"{met:7s} {split:5s} dp_within={w:.2f} | "+" | ".join(f"N={N}: {z*w/math.sqrt(N):.2f}" for N in (40,60,100,150)))

# erro amostral binomial do recall
for n,p,lab in ((1267,0.69,"val"),(1247,0.72,"teste")):
    print(f"erro-padrão binomial do recall {lab}: {100*math.sqrt(p*(1-p)/n):.2f} pp")
# efeito de orçamento no teste
for split in ("val","teste"):
    for S in ("S1","S2"):
        x=[100*r["recall"] for r in rows if r["split"]==split and r["S"]==S and r["arm"]=="C"]
        print(split,S,"C recall média=%.2f dp=%.2f min=%.2f max=%.2f"%(st.mean(x),st.stdev(x),min(x),max(x)))
