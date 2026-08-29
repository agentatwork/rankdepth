#!/usr/bin/env python3
"""Minimum detectable effect for the depth comparison.

Search DOWNWARD from p1: the MDE is the deep-arm rate *closest* to p1 that is still
detectable, not the smallest rate that clears the bar. My first draft iterated upward
from 2% and broke on the first hit, so it printed "2.0%" for every n -- a table that
does not vary with n is not a power table. [[power-table-assumes-a-control-rate]]
"""
import math, sys

Z = 1.959964 + 0.8416212  # two-sided alpha=.05, power=.80

def mde(p1, n):
    for k in range(int(p1 * 1000), -1, -1):
        p2 = k / 1000
        pb = (p1 + p2) / 2
        if pb in (0, 1):
            continue
        se = math.sqrt(2 * pb * (1 - pb) / n)
        if (p1 - p2) / se >= Z:
            return p2
    return 0.0

if __name__ == "__main__":
    p1 = float(sys.argv[1]) if len(sys.argv) > 1 else 0.185
    print(f"control (shallow) rate assumed: {p1*100:.1f}%")
    for n in (150, 200, 250, 300, 400, 500):
        p2 = mde(p1, n)
        print(f"  n={n:4d}/arm  detectable down to {p2*100:5.1f}%  (drop of {(p1-p2)*100:4.1f} pts)")


def mde_unequal(p1, n1, n2):
    """MDE with unequal arms. Pooled SE uses (1/n1 + 1/n2), not 2/n."""
    for k in range(int(p1 * 1000), -1, -1):
        p2 = k / 1000
        pb = (n1 * p1 + n2 * p2) / (n1 + n2)
        if pb in (0, 1):
            continue
        se = math.sqrt(pb * (1 - pb) * (1 / n1 + 1 / n2))
        if (p1 - p2) / se >= Z:
            return p2
    return 0.0
