# Generador del logo final de Eastern Trailers (opción 3 mejorada)
import math
CREMA="#F6F1E7"; NAR="#FF7A00"; CAR="#2B3D45"; OSC="#17232b"
def tire(cx, cy, r, tire_col, rim_col):
    s=[f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{tire_col}"/>']
    for k in range(12):
        a=k*math.pi/6
        s.append(f'<line x1="{cx+math.cos(a)*r*0.86:.1f}" y1="{cy+math.sin(a)*r*0.86:.1f}" x2="{cx+math.cos(a)*r:.1f}" y2="{cy+math.sin(a)*r:.1f}" stroke="{rim_col}" stroke-width="{r*0.11:.1f}" opacity=".55"/>')
    s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r*0.58:.1f}" fill="{rim_col}"/>')
    s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r*0.42:.1f}" fill="{tire_col}"/>')
    s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r*0.16:.1f}" fill="{rim_col}"/>')
    for k in range(5):
        a=-math.pi/2+k*2*math.pi/5
        s.append(f'<circle cx="{cx+math.cos(a)*r*0.29:.1f}" cy="{cy+math.sin(a)*r*0.29:.1f}" r="{r*0.055:.1f}" fill="{rim_col}"/>')
    return "".join(s)

def logo(c_east, c_trail, c_chasis, c_tire, c_rim, c_tag, bg=None, square=None, tagline=True, wid=560, pad=34, out_size=None):
    x0=pad; fs1=wid*0.195; fs2=wid*0.1
    y1=pad+fs1*0.76; y2=y1+fs2*1.55
    lw=wid*0.042; yl=y2+fs2*0.62
    r=wid*0.058; yw=yl+lw+r*1.05
    tongue=wid*0.11
    W=wid+pad*2+tongue; H=yw+r*1.15+pad*0.7
    s=[]
    if square:
        S=square; sc=S/max(W,H)*0.84; ox=(S-W*sc)/2; oy=(S-H*sc)/2
        o=out_size or S
        s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {S} {S}" width="{o}" height="{o}"><rect width="{S}" height="{S}" fill="{bg}"/><g transform="translate({ox:.1f},{oy:.1f}) scale({sc:.3f})">')
    else:
        ow = out_size or f"{W:.0f}"; oh = f"{H*(out_size/W):.0f}" if out_size else f"{H:.0f}"
        s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{ow}" height="{oh}">')
        if bg: s.append(f'<rect width="{W:.0f}" height="{H:.0f}" rx="26" fill="{bg}"/>')
    s.append(f'<text x="{x0}" y="{y1:.1f}" font-family="DejaVu Sans" font-weight="900" font-size="{fs1:.1f}" fill="{c_east}" textLength="{wid}" lengthAdjust="spacingAndGlyphs">EASTERN</text>')
    cell=wid/8; centers=[x0+cell*(i+0.5) for i in range(8)]
    for i,ch in enumerate("TRAILERS"):
        s.append(f'<text x="{centers[i]:.1f}" y="{y2:.1f}" text-anchor="middle" font-family="DejaVu Sans" font-weight="900" font-size="{fs2:.1f}" fill="{c_trail}">{ch}</text>')
    s.append(f'<rect x="{x0}" y="{yl:.1f}" width="{wid}" height="{lw:.1f}" rx="{lw*0.25:.1f}" fill="{c_chasis}"/>')
    tx=x0+wid; ty=yl+lw/2
    s.append(f'<path d="M{tx-lw*0.4:.1f} {yl:.1f} L{tx+tongue*0.78:.1f} {ty-lw*0.22:.1f} L{tx+tongue*0.78:.1f} {ty+lw*0.22:.1f} L{tx-lw*0.4:.1f} {yl+lw:.1f} Z" fill="{c_chasis}"/>')
    s.append(f'<rect x="{tx+tongue*0.72:.1f}" y="{ty-lw*0.34:.1f}" width="{tongue*0.16:.1f}" height="{lw*0.68:.1f}" rx="{lw*0.12:.1f}" fill="{c_chasis}"/>')
    s.append(f'<circle cx="{tx+tongue*0.96:.1f}" cy="{ty:.1f}" r="{lw*0.34:.1f}" fill="none" stroke="{c_chasis}" stroke-width="{lw*0.22:.1f}"/>')
    for cx in (centers[1], centers[2]):
        s.append(tire(cx, yw, r, c_tire, c_rim))
    if tagline:
        s.append(f'<text x="{centers[3]+r*0.15:.1f}" y="{yw+fs2*0.2:.1f}" font-family="DejaVu Sans" font-weight="700" font-size="{fs2*0.36:.1f}" fill="{c_tag}" letter-spacing="{fs2*0.07:.1f}">NEW &amp; PRE-OWNED</text>')
    s.append('</g></svg>' if square else '</svg>')
    return "".join(s)

dark  = dict(c_east=CREMA, c_trail=NAR, c_chasis=NAR, c_tire=CREMA, c_rim=OSC, c_tag="#9fb0ba")
light = dict(c_east=CAR, c_trail=NAR, c_chasis=NAR, c_tire=CAR, c_rim="#ffffff", c_tag="#6b7a82")
avat  = dict(c_east=CREMA, c_trail=NAR, c_chasis=NAR, c_tire=CREMA, c_rim=CAR, c_tag=CREMA)
if __name__=="__main__":
    open("eastern_trailers_final_oscuro.svg","w").write(logo(**dark, bg=OSC))
    open("eastern_trailers_final_claro.svg","w").write(logo(**light, bg="#ffffff"))
    open("eastern_trailers_final_transparente_claro.svg","w").write(logo(**light))
    open("eastern_trailers_final_transparente_oscuro.svg","w").write(logo(**dark))
    open("eastern_trailers_final_avatar.svg","w").write(logo(**avat, bg=CAR, square=600, tagline=False))
    open("eastern_trailers_final_firma_oscuro.svg","w").write(logo(**dark, tagline=False))
    html=f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}body{{width:1400px;background:#f3f4f6;font-family:"DejaVu Sans",Arial;padding:40px;color:#111}}
h1{{font-size:34px;margin-bottom:6px}}p.sub{{color:#555;margin-bottom:26px;font-size:18px;line-height:1.5}}
.card{{background:#fff;border-radius:22px;padding:26px 32px;margin-bottom:24px;box-shadow:0 2px 12px rgba(0,0,0,.06)}}
.card h2{{font-size:20px;margin-bottom:14px;color:#333}}
.big{{border-radius:18px;display:flex;align-items:center;justify-content:center;padding:40px}}
.dark{{background:#17232b}}.light{{background:#fff;border:1px solid #e5e7eb}}
.row{{display:flex;gap:40px;align-items:center;flex-wrap:wrap}}
.av{{display:flex;flex-direction:column;align-items:center;gap:10px;color:#777;font-size:14px}}.av svg{{border-radius:50%}}
.chip{{display:flex;align-items:center;gap:14px;background:#17232b;border-radius:12px;padding:14px 18px;color:#fff;font-size:14px}}
</style></head><body>
<h1>Eastern Trailers — logo final (opción 3 mejorada)</h1>
<p class="sub">Mejoras: llantas con rin, birlos y dibujo de banda; lengua en "A" con acoplador y bola de enganche; EASTERN más pesado al mismo ancho que TRAILERS; línea secundaria "NEW &amp; PRE-OWNED" junto a las llantas (se quita en avatar y tamaños chicos).</p>
<div class="card"><h2>Versión principal · fondo oscuro</h2><div class="big dark">{logo(**dark, out_size=900)}</div></div>
<div class="card"><h2>Versión fondo claro</h2><div class="big light">{logo(**light, out_size=900)}</div></div>
<div class="card"><h2>Avatar de Facebook / Instagram y prueba de tamaños</h2><div class="row">
 <div class="av">{logo(**avat, bg=CAR, square=600, tagline=False, out_size=260)}Avatar 260 px</div>
 <div class="av">{logo(**avat, bg=CAR, square=600, tagline=False, out_size=120)}Avatar 120 px</div>
 <div class="av">{logo(**avat, bg=CAR, square=600, tagline=False, out_size=48)}48 px</div>
 <div class="chip">{logo(**dark, tagline=False, out_size=160)}<span>firma de 160 px<br>(pie de flyer)</span></div>
 <div class="chip" style="background:#fff;color:#333;border:1px solid #e5e7eb">{logo(**light, tagline=False, out_size=160)}<span>firma clara</span></div>
</div></div></body></html>'''
    open("logo_final.html","w").write(html)
