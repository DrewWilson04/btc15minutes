# Kalshi taker fee: ceil_to_cent(0.07 * C * P * (1-P)) per ORDER (fills of one order accumulate). Maker: 0 on these series.
import numpy as np
def order_fee(C,P,rate=0.07): return np.ceil(np.round(rate*C*P*(1-P)*100,6))/100
def per_contract(C,P,rate=0.07): return order_fee(C,P,rate)/C
