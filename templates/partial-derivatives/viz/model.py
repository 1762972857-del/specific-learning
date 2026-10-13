"""Analytic nondimensional heat model; HTML is an independently written implementation."""
import math
DEFAULTS = {"alpha": 1.0, "beta": 0.35}
DEFAULT_INPUTS = {"x": 1.15, "t": 0.45, "h": 0.2}
def temperature(x, t, P):
    return math.exp(-P["alpha"]*t)*math.sin(x)+P["beta"]*math.exp(-4*P["alpha"]*t)*math.sin(2*x)
def evaluate(inputs, P):
    x,t,h = (inputs[k] for k in ("x","t","h"))
    a,b = P["alpha"],P["beta"]
    if not all(math.isfinite(v) for v in (x,t,h,a,b)) or a<=0 or t<0 or h<=0:
        raise ValueError("invalid model input")
    u=math.exp(-a*t); v=b*math.exp(-4*a*t)
    T=u*math.sin(x)+v*math.sin(2*x)
    Tx=u*math.cos(x)+2*v*math.cos(2*x)
    Tt=-a*u*math.sin(x)-4*a*v*math.sin(2*x)
    Txx=-u*math.sin(x)-4*v*math.sin(2*x)
    def diff(d): return (temperature(x-d,t,P)-2*T+temperature(x+d,t,P))/d**2
    discrete=diff(h); error=abs(discrete-Txx); errorHalf=abs(diff(h/2)-Txx)
    order=math.log2(error/errorHalf) if min(error,errorHalf)>1e-12 else 0.0
    return dict(T=T,Tx=Tx,Tt=Tt,Txx=Txx,discrete=discrete,error=error,errorHalf=errorHalf,order=order,residual=Tt-a*Txx,stencil_valid=float(0<=x-h and x+h<=math.pi))
# Expected numbers below follow sin(0), sin(pi/2), sin(pi/4), and exp(-ln 2).
CHECK_CASES = [
 {"name":"single-mode initial peak", "inputs":{"x":math.pi/2,"t":0},"params":{"beta":0},"expected":{"T":1,"Tx":0,"Tt":-1,"Txx":-1,"residual":0}},
 {"name":"initial mixed quarter", "inputs":{"x":math.pi/4,"t":0},"expected":{"T":math.sqrt(2)/2+.35,"Tx":math.sqrt(2)/2,"Tt":-math.sqrt(2)/2-1.4,"Txx":-math.sqrt(2)/2-1.4}},
 {"name":"left zero boundary", "inputs":{"x":0,"t":0},"expected":{"T":0,"Tx":1.7,"Tt":0,"stencil_valid":0}},
 {"name":"right zero boundary", "inputs":{"x":math.pi,"t":0},"expected":{"T":0,"Tx":-.3,"Tt":0,"stencil_valid":0}},
 {"name":"single mode decays by half", "inputs":{"x":math.pi/2,"t":math.log(2)},"params":{"beta":0},"expected":{"T":.5,"Tt":-.5,"Txx":-.5}},
 {"name":"double diffusivity at peak", "inputs":{"x":math.pi/2,"t":0},"params":{"alpha":2,"beta":0},"expected":{"T":1,"Tt":-2,"Txx":-1}},
 {"name":"negative second-mode weight", "inputs":{"x":math.pi/4,"t":0},"params":{"beta":-.5},"expected":{"T":math.sqrt(2)/2-.5,"Txx":-math.sqrt(2)/2+2}},
 {"name":"central difference h equals pi/3", "inputs":{"x":math.pi/2,"t":0,"h":math.pi/3},"params":{"beta":0},"expected":{"discrete":-9/math.pi**2,"stencil_valid":1}}
]
