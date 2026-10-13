"""Static velocity profile using the standard library and shared drafting tokens."""
from pathlib import Path
import json
import model as M
OUT=Path(__file__).resolve().parent/'figures'
PAPER,INK,ACCENT,ACCENT_INK,FOG='#ECEAE3','#1B1B19','#D4572A','#B4441C','#8FA8BF'
def main():
    OUT.mkdir(exist_ok=True)
    X=lambda u:80+(u+1.3)/2.6*560
    Y=lambda y:350-y/13*270
    a=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 430" role="img" aria-labelledby="title desc"><title id="title">Velocity profile at prescribed plate speeds</title><desc id="desc">Default, equal-speed, and equal-opposite profiles. Default midpoint velocity is 0.30 m/s.</desc><rect width="720" height="430" fill="{PAPER}"/><g fill="{INK}" stroke="{INK}" font-family="sans-serif" font-size="13">']
    a.append('<text x="80" y="32" stroke="none">[B] Velocity profile · fixed axes · H = 6 mm</text><path d="M80 80 V350 H640" fill="none"/>')
    for u in [-1.2,-.6,0,.6,1.2]:a.append(f'<path d="M{X(u)} 350 v6"/><text x="{X(u)}" y="375" text-anchor="middle" stroke="none">{u:g}</text>')
    for y in [0,3,6,9,12]:a.append(f'<path d="M80 {Y(y)} h-6"/><text x="65" y="{Y(y)+5}" text-anchor="end" stroke="none">{y}</text>')
    a.append('<text x="590" y="407" stroke="none">u / (m/s)</text><text x="26" y="69" stroke="none">y / mm</text>')
    for lower,dash in [(0,''),(.6,'6 4'),(-.6,'1 4')]:
        P=dict(M.DEFAULTS,lower=lower)
        pts=' '.join(f'{X(M.evaluate({"r":i/50,"t":0},P)["velocity"]):.3f},{Y(6*i/50):.3f}' for i in range(51))
        a.append(f'<polyline points="{pts}" fill="none" stroke-width="2" stroke-dasharray="{dash}"/>')
    a.extend([f'<circle cx="{X(.3)}" cy="{Y(3)}" r="5" fill="{ACCENT}" stroke="none"/>',f'<text x="{X(.3)-70}" y="{Y(3)-25}" fill="{ACCENT_INK}" stroke="none">u = 0.30 m/s</text>',f'<text x="{X(.6)+15}" y="{Y(5.6)}" stroke="none">equal speed</text>',f'<text x="{X(.12)}" y="{Y(1.7)}" stroke="none">default</text>',f'<text x="{X(-.6)}" y="{Y(.6)}" stroke="none">opposite</text>','</g></svg>'])
    (OUT/'01_profile.svg').write_text(''.join(a))
    probe=M.evaluate(M.DEFAULT_INPUTS,M.DEFAULTS)
    (OUT/'figures.json').write_text(json.dumps({'01_profile.svg':{k:probe[k] for k in ('velocity','gradient','stress','y','dissipation')}},ensure_ascii=False,indent=2)+'\n')
    print('wrote 01_profile.svg and figures.json')
if __name__=='__main__':main()
