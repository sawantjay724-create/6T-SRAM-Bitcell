"""Static noise margin from a half-cell voltage transfer curve (VTC).

The cell is symmetric, so the second butterfly curve is the mirror image of the
first. SNM is the side of the largest axis-aligned square that fits inside the
smaller of the two "eyes" of the butterfly plot.
"""
import sys


def load(path):
    xs, ys = [], []
    with open(path) as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2:
                xs.append(float(parts[0]))
                ys.append(float(parts[1]))
    return xs, ys


def interp(x, xs, ys):
    """Linear interpolation, clamped at the ends (xs ascending)."""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    lo, hi = 0, len(xs) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if xs[mid] <= x:
            lo = mid
        else:
            hi = mid
    t = (x - xs[lo]) / (xs[hi] - xs[lo])
    return ys[lo] + t * (ys[hi] - ys[lo])


def snm(vin, vout, steps=900):
    """Return the static noise margin (volts) for a decreasing VTC vout(vin)."""
    vdd = max(max(vin), max(vout))
    g = lambda x: interp(x, vin, vout)                      # curve 1: y = g(x)
    rev_out, rev_in = vout[::-1], vin[::-1]                 # ascending vout
    h = lambda x: interp(x, rev_out, rev_in)                # curve 2 (mirror): y = g^-1(x)

    def best_square(upper, lower):
        best = 0.0
        for i in range(steps + 1):
            x0 = vdd * i / steps
            if upper(x0) - lower(x0) <= 0:
                continue
            lo, hi = 0.0, vdd - x0
            for _ in range(40):                             # bisection on side length
                s = (lo + hi) / 2
                if upper(x0 + s) - lower(x0) - s >= 0:
                    lo = s
                else:
                    hi = s
            best = max(best, lo)
        return best

    return min(best_square(g, h), best_square(h, g))


if __name__ == "__main__":
    for path in sys.argv[1:]:
        vin, vout = load(path)
        print(f"{path}: SNM = {snm(vin, vout) * 1000:.0f} mV")
