"""Two-slit scalar wave superposition. Lengths and wavelength in mm (ripple-tank scale).

Exact model: each slit is M equal in-phase point sources spread across its width a, centred at
y = +-d/2 on the wall x = 0; amplitude exp(i k r), no 1/sqrt(r) decay. I is normalised to its
value at the screen centre (L, 0). Far field: I0 cos^2(pi d y/(lam L)) sinc^2(pi a y/(lam L)).
"""
import math
M = 9
DEFAULTS = {"lam": 2., "d": 8., "a": 2.4, "L": 60.}
DEFAULT_INPUTS = {"y": 11.25}
def amp(x, y, P):
    k = 2*math.pi/P["lam"]; re = im = 0.
    for s in (P["d"]/2, -P["d"]/2):
        for j in range(M):
            r = math.hypot(x, y - (s + ((j+.5)/M - .5)*P["a"]))
            re += math.cos(k*r); im += math.sin(k*r)
    return re, im
def sinc(x): return 1. if x == 0 else math.sin(x)/x
def evaluate(inputs, P):
    y = inputs["y"]; lam, d, a, L = (P[k] for k in ("lam", "d", "a", "L"))
    if not all(math.isfinite(v) for v in (y, lam, d, a, L)) or min(lam, d, a, L) <= 0 or a >= d:
        raise ValueError("Invalid model input")
    r_up, r_lo = math.hypot(L, y - d/2), math.hypot(L, y + d/2)
    path_diff = r_lo - r_up                      # lower-slit path minus upper-slit path
    far = d*y/(lam*L); env = sinc(math.pi*a*y/(lam*L))**2
    re, im = amp(L, y, P); re0, im0 = amp(L, 0., P)
    return dict(path_diff=path_diff, phase=2*math.pi*path_diff/lam, order=far, path_diff_far=d*y/L,
                phase_far=2*math.pi*far, envelope=env, intensity_far=math.cos(math.pi*far)**2*env,
                intensity_exact=(re*re + im*im)/(re0*re0 + im0*im0),
                fringe_spacing=lam*L/d, envelope_zero=lam*L/a)
# Hand-calculated references (paraxial formulas, geometry, series), not outputs of evaluate().
CHECK_CASES = [
 {"name":"default y=11.25: order 3/4", "expected":{"path_diff_far":1.5,"order":.75,"phase_far":4.71238898038469,"fringe_spacing":15,"envelope_zero":50,"intensity_far":.42207930114570696}},
 {"name":"exact path difference, 2dy/(r1+r2)", "expected":{"path_diff":1.471259834986449,"phase":4.622099089115156}},
 {"name":"centre maximum", "inputs":{"y":0},"expected":{"path_diff":0,"phase":0,"order":0,"intensity_far":1,"intensity_exact":1,"envelope":1}},
 {"name":"first minimum y=lam L/2d, narrow slits", "params":{"a":.4},"inputs":{"y":7.5},"expected":{"order":.5,"intensity_far":0,"envelope":.9979455228015723}},
 {"name":"first maximum order 1, sinc^2 = (sin .3pi/.3pi)^2", "inputs":{"y":15},"expected":{"order":1,"intensity_far":.7368397293222505}},
 {"name":"envelope zero kills order 2 (a=d/2)", "params":{"a":4},"inputs":{"y":30},"expected":{"order":2,"envelope":0,"intensity_far":0}},
 {"name":"order 1 under a=d/2 envelope: (2/pi)^2", "params":{"a":4},"inputs":{"y":15},"expected":{"intensity_far":.4052847345693511}},
 {"name":"mirror symmetry y=-11.25", "inputs":{"y":-11.25},"expected":{"path_diff_far":-1.5,"phase_far":-4.71238898038469,"intensity_far":.42207930114570696}},
 {"name":"fringe spacing lam=1, d=5, L=80", "params":{"lam":1,"d":5,"L":80},"expected":{"fringe_spacing":16}},
 {"name":"fringe spacing at slider ends", "params":{"lam":1,"d":12,"L":30},"expected":{"fringe_spacing":2.5}},
 {"name":"exact first minimum approaches far field (L=1e4)", "params":{"d":10,"a":.4,"L":10000},"inputs":{"y":1000},"expected":{"path_diff":.9950370682811328,"intensity_exact":0},"atol":2e-3},
 {"name":"exact vs far field at L=1e4, order 1/4", "params":{"d":10,"a":2,"L":10000},"inputs":{"y":500},"expected":{"intensity_far":.4959011700554512,"intensity_exact":.4959011700554512},"atol":5e-3},
]
for case in CHECK_CASES: case.setdefault("atol", 1e-9); case.setdefault("rtol", 1e-9)
