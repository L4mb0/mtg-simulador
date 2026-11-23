from multiprocessing import Pool
from cards import ACTUAL, swap
from harness import run, paired, summary
from scen import cfg
from v2runs import apply, PEND
N=4000; S=950000
REV=[("Commander's Sphere","Flawless Maneuver"),("Search the Premises","Leader's Talent"),("Swiftfoot Boots","Herald of the Host"),
     ("Invoke the Divine","Starnheim Unleashed"),("Vanquisher's Banner","Sigarda's Vanguard"),("Metallic Mimic","Felidar Sovereign")]
V={"Núcleo del plan (6)":apply(ACTUAL,PEND),"Revisado (5 compras + Leader's Talent)":apply(ACTUAL,REV),
   "Revisado + Resplendent por Reya":apply(ACTUAL,REV+[("Reya Dawnbringer","Resplendent Angel")])}
if __name__=="__main__":
    with Pool(2) as p:
        for br in ("B1","B2","B3"):
            a=run(ACTUAL,N,cfg=cfg(br),pool=p,seed0=S)
            print(br,"actual",round(summary(a)["win"],1),flush=True)
            for k,d in V.items():
                b=run(d,N,cfg=cfg(br),pool=p,seed0=S)
                print(br,k,round(summary(b)["win"],1),[round(x,2) for x in paired(a,b)],flush=True)
