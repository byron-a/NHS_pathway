from scipy import stats, optimize
import numpy as np
from math import log
from statistics import NormalDist


#CALCULTING HANDOVER SHARE OVER 60 MINS USING THE LOGNORMAL MODEL
def handover_over_60(n_total, n_within_15, lost_hours):
    """Return (% over 60 lognormal, % over 60 exponential, sigma, mu)."""
    p15 = n_within_15 / n_total                      # share handed over within 15 min
    over15 = n_total - n_within_15                   # handovers over 15 min
    m = lost_hours * 60 / over15                     # mean minutes beyond 15, for those over 15
    target = m * (1 - p15)                           # mean minutes beyond 15, across ALL handovers

    # Lognormal: ln T ~ Normal(mu, sigma)
    z = stats.norm.ppf(p15)                          # z-score with p15 below it
    def excess(sigma):                               # E[(T - 15)+] for this sigma, mu tied to p15
        mu = np.log(15) - sigma * z
        d = (mu + sigma**2 - np.log(15)) / sigma
        return np.exp(mu + sigma**2 / 2) * stats.norm.cdf(d) - 15 * stats.norm.cdf(d - sigma)
    
    sigma = optimize.brentq(lambda s: excess(s) - target, 0.05, 6.0)   # solve for sigma
    mu = np.log(15) - sigma * z
    lognormal = stats.lognorm(s=sigma, scale=np.exp(mu)).sf(60)       # sf = share ABOVE 60

    # Exponential tail beyond 15 minutes, with mean m
    exponential = (1 - p15) * np.exp(-45 / m)
    return 100 * lognormal, 100 * exponential, sigma, mu

#CALCULATING TIME WAIT IN EDs OVER 5 HOURS USING THE PIECEWISE RULE
def ed_wait_over5hrs(share_4h,share_8h,median_t):
    N = NormalDist()                      # standard normal: mean 0, sd 1
    # print(share_4h/100, median_t)
    med_t_arr = median_t.split(':')
    if int(med_t_arr[0])>=4:
        median_t = (int(med_t_arr[0]) * 60) + int(med_t_arr[1])
        t_4h = 240
        share_4 = share_4h/100
        # p4  = 0.341747                        # share within 4 h (240 min)
        # med = 403                             # median, minutes (share 0.5)
        t_5h = 300                             # time we want: 5 h
        
        frac = (log(t_5h) - log(t_4h)) / (log(median_t) - log(t_4h))
        z = N.inv_cdf(share_4) + frac * (N.inv_cdf(0.5) - N.inv_cdf(share_4))
        within = N.cdf(z)
        
        # print(f"within 5 h: {within:.4f}  over 5 h: {1 - within:.4f}")
        return f'{((1-within)*100):.4f}',f'{(within*100):.4f}'
    else:
        median_t = (int(med_t_arr[0]) * 60) + int(med_t_arr[1])
        t_4h = 240
        share_8 = share_8h/100
        share_4 = share_4h/100
        t_5h = 300  
        t_8h = 480

        frac = (log(t_5h) - log(t_4h)) / (log(t_8h) - log(t_4h))
        z = N.inv_cdf(share_4) + frac * (N.inv_cdf(share_8) - N.inv_cdf(share_4))
        within = N.cdf(z)
        return f'{((1-within)*100):.4f}',f'{(within*100):.4f}'
    

#CALCULATING NUMBER OF PATIENTS WHO DIED IN THE MAJOR EDs:> Hold for now!!!!
def dead_patient(att, dead_share_arr):

    return True