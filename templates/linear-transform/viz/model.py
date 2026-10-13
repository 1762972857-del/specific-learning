"""2x2 linear map A=[[a,b],[c,d]] on the plane; HTML is an independently written implementation."""
import math
DEFAULTS = {"a": 1.2, "b": 0.5, "c": 0.3, "d": 0.9}
DEFAULT_INPUTS = {"x": 1.0, "y": 0.5}
def evaluate(inputs, P):
    x, y = inputs["x"], inputs["y"]
    a, b, c, d = (P[k] for k in "abcd")
    if not all(math.isfinite(v) for v in (x, y, a, b, c, d)):
        raise ValueError("invalid model input")
    det, tr = a*d-b*c, a+d
    disc = tr*tr-4*det                       # eigenvalues solve l^2 - tr*l + det = 0
    real = disc >= 0
    s = math.sqrt(max(disc, 0.0))
    # Singular values: sqrt of eigenvalues of A^T A (semi-axes of the image ellipse).
    root = math.sqrt((a*a+b*b-c*c-d*d)**2+4*(a*c+b*d)**2)
    sig1 = math.sqrt(((a*a+b*b+c*c+d*d)+root)/2)
    sig2 = abs(det)/sig1 if sig1 > 0 else 0.0
    return dict(det=det, trace=tr, Ax_x=a*x+b*y, Ax_y=c*x+d*y, area_scale=abs(det),
                orientation=float((det > 0)-(det < 0)), eig_real=float(real),
                eig1=(tr+s)/2 if real else 0.0, eig2=(tr-s)/2 if real else 0.0,
                eig_re=tr/2, eig_im=0.0 if real else math.sqrt(-disc)/2, sigma1=sig1, sigma2=sig2)
# Expected values are hand-computed from the entries (eig1 >= eig2 when real; 0 placeholders when complex).
CHECK_CASES = [
 {"name":"identity", "inputs":{"x":2,"y":-1}, "params":{"a":1,"b":0,"c":0,"d":1},
  "expected":{"det":1,"trace":2,"Ax_x":2,"Ax_y":-1,"eig_real":1,"eig1":1,"eig2":1,"sigma1":1,"sigma2":1,"orientation":1}},
 {"name":"rotation by 90 degrees", "inputs":{"x":1,"y":2}, "params":{"a":0,"b":-1,"c":1,"d":0},
  "expected":{"det":1,"trace":0,"Ax_x":-2,"Ax_y":1,"eig_real":0,"eig1":0,"eig2":0,"eig_re":0,"eig_im":1,"sigma1":1,"sigma2":1}},
 {"name":"rotation-scaling with complex pair", "inputs":{"x":1,"y":0}, "params":{"a":1,"b":-1,"c":1,"d":1},
  "expected":{"det":2,"trace":2,"Ax_x":1,"Ax_y":1,"eig_real":0,"eig_re":1,"eig_im":1,"sigma1":math.sqrt(2),"sigma2":math.sqrt(2)}},
 {"name":"shear k=3", "inputs":{"x":1,"y":1}, "params":{"a":1,"b":3,"c":0,"d":1},
  "expected":{"det":1,"trace":2,"Ax_x":4,"Ax_y":1,"eig_real":1,"eig1":1,"eig2":1,"area_scale":1}},
 {"name":"reflection about y=x", "inputs":{"x":2,"y":5}, "params":{"a":0,"b":1,"c":1,"d":0},
  "expected":{"det":-1,"trace":0,"Ax_x":5,"Ax_y":2,"eig_real":1,"eig1":1,"eig2":-1,"orientation":-1,"area_scale":1,"sigma1":1,"sigma2":1}},
 {"name":"singular rank one", "inputs":{"x":1,"y":-1}, "params":{"a":1,"b":2,"c":2,"d":4},
  "expected":{"det":0,"trace":5,"Ax_x":-1,"Ax_y":-2,"eig_real":1,"eig1":5,"eig2":0,"area_scale":0,"orientation":0,"sigma1":5,"sigma2":0}},
 {"name":"diagonal scaling 3 and -2", "inputs":{"x":1,"y":1}, "params":{"a":3,"b":0,"c":0,"d":-2},
  "expected":{"det":-6,"trace":1,"Ax_x":3,"Ax_y":-2,"eig_real":1,"eig1":3,"eig2":-2,"area_scale":6,"sigma1":3,"sigma2":2}},
]
