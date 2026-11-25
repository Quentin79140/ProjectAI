#!/usr/bin/env python3
"""Génère les deux formats de la vidéo agence (16:9 et 9:16) à partir des mêmes scènes.

Usage : python3 build.py   -> écrit horizontal/ et vertical/
Les fichiers générés restent des projets HyperFrames normaux, éditables dans le Studio.
Relancer ce script écrase les modifications faites à la main dans les scènes.
"""
import json
import os
import shutil
from string import Template

HERE = os.path.dirname(os.path.abspath(__file__))
SFX_SRC = os.path.join(HERE, "..", ".claude", "skills", "media-use", "audio", "assets", "sfx")

INK = "#14161B"
ACCENT = "#FF5A36"
BROWN = "#4A2C1A"
WHEAT = "#E8A33D"
PENCIL = "#5B6270"

FORMATS = {
    "horizontal": dict(
        W=1920, H=1080, TX=200, TY=150, TS=96, TW=760,
        CX=1240, CY=560, LOGO=520,
        VANW=1100, VANCX=1220, VANCY=640,
        TEEH=860, TEECX=1260, TEECY=600,
        PHONEH=900, PHONECX=1300, PHONECY=560,
        BUBX=200, BUBY=560, BUBS=40,
        EX=200, EY=250, ES=190, ESVC=40, ESVCW=1500,
    ),
    "vertical": dict(
        W=1080, H=1920, TX=140, TY=300, TS=96, TW=860,
        CX=540, CY=1150, LOGO=600,
        VANW=960, VANCX=540, VANCY=1240,
        TEEH=1000, TEECX=540, TEECY=1220,
        PHONEH=880, PHONECX=540, PHONECY=980,
        BUBX=140, BUBY=1180, BUBS=38,
        EX=140, EY=620, ES=118, ESVC=40, ESVCW=860,
    ),
}

SCENES = [  # id, start, duration
    ("sketch", 0, 4),
    ("vector", 4, 4),
    ("road", 8, 5),
    ("tee", 13, 4),
    ("social", 17, 4),
    ("endcard", 21, 4),
]
TOTAL = 25

# Bruitages : (id, fichier, début, durée, décalage dans le fichier, piste Studio, volume)
# Chaque début place le pic du son une image après l'événement à l'écran (pics mesurés avec `audio --json`).
SFX = [
    ("sfx-cut-1", "whoosh-short.mp3", 3.87, 0.4, 0, 3, 0.7),
    ("sfx-click", "click.mp3", 5.46, 0.3, 0, 3, 0.9),
    ("sfx-cut-2", "whoosh-cinematic.mp3", 7.33, 1.6, 1.8, 3, 0.6),
    ("sfx-stick", "pop.mp3", 9.06, 0.4, 0, 3, 0.8),
    ("sfx-cut-3", "whoosh.mp3", 12.37, 0.4, 0, 3, 0.6),
    ("sfx-cut-4", "whoosh-cinematic.mp3", 16.33, 1.4, 1.8, 3, 0.55),
    ("sfx-like", "pop.mp3", 18.11, 0.4, 0, 3, 0.8),
    ("sfx-c1", "click-soft.mp3", 18.46, 0.3, 0, 5, 0.8),
    ("sfx-c2", "click-soft.mp3", 18.76, 0.3, 0, 5, 0.8),
    ("sfx-c3", "click-soft.mp3", 19.06, 0.3, 0, 5, 0.8),
    ("sfx-riser", "riser.mp3", 18.46, 2.7, 0.8, 4, 0.45),
    ("sfx-impact", "impact-bass-1.mp3", 21.06, 2.1, 0, 3, 0.9),
]


def logo_svg(pid, mode):
    """Logo épi de blé. mode: 'sketch' (crayon), 'color' (couleurs), 'print' (blé sur brun)."""
    grains = []
    for i, y in enumerate((150, 200, 250)):
        grains.append((170, y, -32))
        grains.append((230, y, 32))
    grains.append((200, 100, 0))
    if mode == "sketch":
        ring = f'fill="none" stroke="{PENCIL}" stroke-width="5" stroke-dasharray="1 1"'
        stem = f'stroke="{PENCIL}" stroke-width="5" stroke-dasharray="1 1"'
        grain = f'fill="none" stroke="{PENCIL}" stroke-width="5" stroke-dasharray="1 1"'
    elif mode == "color":
        ring = f'fill="{BROWN}" stroke="{BROWN}" stroke-width="8"'
        stem = f'stroke="{WHEAT}" stroke-width="10"'
        grain = f'fill="{WHEAT}" stroke="{WHEAT}" stroke-width="4"'
    else:  # print
        ring = f'fill="none" stroke="{WHEAT}" stroke-width="12"'
        stem = f'stroke="{WHEAT}" stroke-width="10"'
        grain = f'fill="{WHEAT}" stroke="{WHEAT}" stroke-width="4"'
    out = [f'<svg viewBox="0 0 400 400" width="100%" height="100%">']
    out.append(f'<circle class="{pid}-ring {pid}-line" cx="200" cy="200" r="180" pathLength="1" {ring}/>')
    out.append(f'<path class="{pid}-stem {pid}-line" d="M200 330 L200 120" pathLength="1" fill="none" stroke-linecap="round" {stem}/>')
    for x, y, r in grains:
        out.append(
            f'<ellipse class="{pid}-grain {pid}-line" cx="{x}" cy="{y}" rx="20" ry="38" '
            f'transform="rotate({r} {x} {y})" pathLength="1" {grain}/>'
        )
    out.append("</svg>")
    return "".join(out)


def title_css(P, color):
    return f"""
    .title {{
      position: absolute; left: {P['TX']}px; top: {P['TY']}px; width: {P['TW']}px;
      font-family: "Montserrat"; font-weight: 800; font-size: {P['TS']}px; line-height: 1.04;
      letter-spacing: -0.02em; color: {color};
    }}"""


def scene(cid, P, css, body, js, extra_attrs=""):
    return f"""<template>
  <style>
    #root {{ position: absolute; inset: 0; overflow: hidden; }}{css}
  </style>
  <div id="root" data-composition-id="{cid}" data-width="{P['W']}" data-height="{P['H']}"{extra_attrs}>
{body}
  </div>
  <script>
    const tl = gsap.timeline({{ paused: true }});
{js}
    window.__timelines["{cid}"] = tl;
  </script>
</template>
"""


def logo_box(P, scale=1.0):
    s = P["LOGO"] * scale
    return P["CX"] - s / 2, P["CY"] - s / 2, s


# ---------------------------------------------------------------- S1 croquis
def s_sketch(P):
    x, y, s = logo_box(P)
    css = f"""
    #sk-bg {{ position: absolute; inset: 0; background-color: #F2F4F7;
      background-image: linear-gradient(#D9DEE6 2px, transparent 2px), linear-gradient(90deg, #D9DEE6 2px, transparent 2px);
      background-size: 48px 48px; }}
    #sk-cam {{ position: absolute; inset: 0; transform-origin: {P['CX']}px {P['CY']}px; }}
    #sk-logo {{ position: absolute; left: {x}px; top: {y}px; width: {s}px; height: {s}px; }}
    #sk-name {{ position: absolute; left: {P['CX'] - 400}px; top: {P['CY'] + s / 2 + 20}px; width: 800px;
      text-align: center; font-family: "Playfair Display"; font-weight: 700; font-size: {int(s * 0.15)}px;
      color: transparent; -webkit-text-stroke: 2px {PENCIL}; }}
    #sk-title {{ }}{title_css(P, INK)}"""
    body = f"""    <div id="sk-bg"></div>
    <div id="sk-cam">
      <div id="sk-logo" class="clip" data-start="0" data-duration="4">{logo_svg('sk', 'sketch')}</div>
      <div id="sk-name" class="clip" data-start="0" data-duration="4">Fournil Martin</div>
    </div>
    <h1 id="sk-title" class="title clip" data-start="0" data-duration="3.6">Tout part<br />d'un croquis.</h1>"""
    js = """    tl.fromTo(".sk-ring", { attr: { "stroke-dashoffset": 0.6 } }, { attr: { "stroke-dashoffset": 0 }, duration: 1.1, ease: "power1.inOut" }, 0);
    tl.fromTo(".sk-stem", { attr: { "stroke-dashoffset": 0.5 } }, { attr: { "stroke-dashoffset": 0 }, duration: 0.6, ease: "power1.inOut" }, 0);
    tl.fromTo(".sk-grain", { attr: { "stroke-dashoffset": 1 } }, { attr: { "stroke-dashoffset": 0 }, duration: 0.35, ease: "power1.inOut", stagger: 0.14 }, 0.4);
    tl.fromTo("#sk-name", { clipPath: "inset(0 100% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 0.8, ease: "power2.inOut" }, 1.7);
    tl.fromTo("#sk-title", { clipPath: "inset(0 0% 0 0)" }, { clipPath: "inset(0 0% 0 0)", duration: 0.01 }, 0);
    tl.to("#sk-title", { x: -60, opacity: 0, duration: 0.3, ease: "power2.in" }, 3.2);
    tl.fromTo("#sk-cam", { scale: 1 }, { scale: 1.12, duration: 0.6, ease: "expo.in" }, 3.4);"""
    return scene("sketch", P, css, body, js)


# ---------------------------------------------------------------- S2 logiciel
def s_vector(P):
    x, y, s = logo_box(P)
    pad = 60
    cur = int(P["H"] * 0.06)
    # pastilles de couleur
    swx = x + s + 70 if P["W"] > P["H"] else P["CX"] - 150
    swy = y + 40 if P["W"] > P["H"] else y + s + 190
    vertical_sw = P["W"] > P["H"]
    sw = []
    for i, c in enumerate(["#14161B", WHEAT, "#2E7D6B"]):
        sx = swx if vertical_sw else swx + i * 110
        sy = swy + i * 110 if vertical_sw else swy
        sw.append((sx, sy, c))
    wheat_sw = sw[1]
    css = f"""
    #ve-bg {{ position: absolute; inset: 0; background: #E6E8EC; }}
    #ve-board {{ position: absolute; left: {x - pad}px; top: {y - pad}px; width: {s + 2 * pad}px; height: {s + 2 * pad + int(s * 0.32)}px;
      background: #FFFFFF; box-shadow: 0 6px 18px rgba(20, 22, 27, 0.12); }}
    #ve-cam {{ position: absolute; inset: 0; transform-origin: {P['CX']}px {P['CY']}px; }}
    .ve-logo {{ position: absolute; left: {x}px; top: {y}px; width: {s}px; height: {s}px; }}
    .ve-h {{ position: absolute; width: 18px; height: 18px; background: #FFFFFF; border: 3px solid #2F80ED; }}
    #ve-name {{ position: absolute; left: {P['CX'] - 400}px; top: {y + s + 16}px; width: 800px; text-align: center;
      font-family: "Playfair Display"; font-weight: 700; font-size: {int(s * 0.15)}px; color: {BROWN}; }}
    .ve-sw {{ position: absolute; width: 84px; height: 84px; border-radius: 50%; border: 5px solid #FFFFFF;
      box-shadow: 0 3px 8px rgba(20, 22, 27, 0.18); }}
    #ve-cursor {{ position: absolute; left: {wheat_sw[0] + 50}px; top: {wheat_sw[1] + 50}px; width: {cur}px; height: {cur}px; }}
    {title_css(P, INK)}"""
    handles = []
    # poignées sur quelques points du cercle et de l'épi (coordonnées du viewBox 400)
    for i, (hx, hy) in enumerate([(200, 20), (380, 200), (200, 380), (20, 200), (200, 120), (200, 330)]):
        handles.append(
            f'      <div class="ve-h" style="left:{x + hx / 400 * s - 9}px; top:{y + hy / 400 * s - 9}px"></div>'
        )
    swatches = "\n".join(
        f'      <div class="ve-sw" id="ve-sw-{i}" style="left:{sx}px; top:{sy}px; background:{c}"></div>'
        for i, (sx, sy, c) in enumerate(sw)
    )
    body = f"""    <div id="ve-bg"></div>
    <div id="ve-cam">
      <div id="ve-board" class="clip" data-start="0" data-duration="4"></div>
      <div id="ve-sketch" class="ve-logo clip" data-start="0" data-duration="4">{logo_svg('vs', 'sketch')}</div>
      <div id="ve-color" class="ve-logo clip" data-start="0" data-duration="4">{logo_svg('vc', 'color')}</div>
      <div id="ve-handles" class="clip" data-start="0" data-duration="4">
{chr(10).join(handles)}
      </div>
      <div id="ve-name" class="clip" data-start="0" data-duration="4">Fournil Martin</div>
      <div id="ve-swatches" class="clip" data-start="0" data-duration="4">
{swatches}
      </div>
      <svg id="ve-cursor" class="clip" data-start="0" data-duration="4" viewBox="0 0 40 40">
        <path d="M4 2 L4 32 L12 25 L18 38 L24 35 L18 22 L29 22 Z" fill="{INK}" stroke="#FFFFFF" stroke-width="2.5" stroke-linejoin="round" />
      </svg>
    </div>
    <h1 id="ve-title" class="title clip" data-start="0.4" data-duration="3.4">Qui devient<br />un vrai logo.</h1>"""
    js = f"""    tl.fromTo("#ve-cam", {{ scale: 1.12 }}, {{ scale: 1, duration: 0.6, ease: "expo.out" }}, 0);
    tl.fromTo("#ve-board", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.3, ease: "power2.out" }}, 0.1);
    tl.fromTo(".ve-h", {{ scale: 0 }}, {{ scale: 1, duration: 0.25, ease: "back.out(2)", stagger: 0.05 }}, 0.35);
    tl.fromTo("#ve-swatches .ve-sw", {{ scale: 0 }}, {{ scale: 1, duration: 0.3, ease: "back.out(2)", stagger: 0.06 }}, 0.6);
    tl.fromTo("#ve-title", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: 0.5, ease: "power3.out" }}, 0.4);
    tl.fromTo("#ve-cursor", {{ x: {P['W'] * 0.35}, y: {P['H'] * 0.25} }}, {{ x: 0, y: 0, duration: 0.7, ease: "power3.out" }}, 0.75);
    tl.fromTo("#ve-cursor", {{ scale: 1 }}, {{ scale: 0.85, duration: 0.08, yoyo: true, repeat: 1, ease: "power1.inOut" }}, 1.5);
    tl.fromTo("#ve-sw-1", {{ scale: 1 }}, {{ scale: 1.18, duration: 0.12, yoyo: true, repeat: 1, ease: "power1.out" }}, 1.52);
    tl.fromTo("#ve-color", {{ clipPath: "circle(0% at 50% 50%)" }}, {{ clipPath: "circle(75% at 50% 50%)", duration: 0.6, ease: "expo.out" }}, 1.58);
    tl.fromTo("#ve-handles", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.25, ease: "power1.in" }}, 2.0);
    tl.fromTo("#ve-name", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: 0.6, ease: "steps(14)" }}, 2.1);
    tl.to("#ve-cursor", {{ x: {P['W'] * 0.3}, y: {P['H'] * 0.3}, duration: 0.5, ease: "power2.in" }}, 2.6);
    tl.to("#ve-title", {{ x: -60, opacity: 0, duration: 0.3, ease: "power2.in" }}, 3.4);
    tl.to(["#ve-board", "#ve-swatches", "#ve-name"], {{ opacity: 0, duration: 0.3, ease: "power2.in" }}, 3.5);"""
    return scene("vector", P, css, body, js)


# ---------------------------------------------------------------- S3 rue
def s_road(P):
    vw = P["VANW"]
    vh = vw * 0.45
    vx = P["VANCX"] - vw / 2
    vy = P["VANCY"] - vh / 2
    L = 0.19 * vw
    lx = 0.37 * vw - L / 2
    ly = 0.31 * vh - L / 2
    # départ du logo : centre et taille du plan précédent
    sx = P["CX"] - (vx + lx + L / 2)
    sy = P["CY"] - (vy + ly + L / 2)
    sc = P["LOGO"] / L
    road_top = vy + vh - 6
    css = f"""
    #ro-sky {{ position: absolute; inset: 0; background: #CFE6F2; }}
    #ro-city {{ position: absolute; left: 0; top: {road_top - 380}px; width: {P['W'] * 3}px; height: 380px; }}
    .ro-b {{ position: absolute; bottom: 0; background: #A9CFE2; }}
    #ro-road {{ position: absolute; left: 0; top: {road_top}px; width: {P['W']}px; height: {P['H'] - road_top}px; background: #2E3138; }}
    #ro-walk {{ position: absolute; left: 0; top: {road_top - 22}px; width: {P['W']}px; height: 22px; background: #8E99A6; }}
    #ro-dashes {{ position: absolute; left: 0; top: {road_top + 70}px; width: {P['W'] * 3}px; height: 14px;
      background-image: linear-gradient(90deg, #F2F4F7 0 120px, transparent 120px 220px); background-size: 220px 14px; }}
    #ro-van {{ position: absolute; left: {vx}px; top: {vy}px; width: {vw}px; height: {vh}px; }}
    #ro-van svg.body {{ position: absolute; inset: 0; }}
    #ro-logo {{ position: absolute; left: {lx}px; top: {ly}px; width: {L}px; height: {L}px; }}
    #ro-name {{ position: absolute; left: {0.37 * vw - 300}px; top: {ly + L + 2}px; width: 600px; text-align: center;
      font-family: "Playfair Display"; font-weight: 700; font-size: {int(L * 0.18)}px; color: {BROWN}; }}
    .ro-wheel {{ position: absolute; width: {0.13 * vw}px; height: {0.13 * vw}px; top: {vh * 0.78 - 0.065 * vw}px; }}
    {title_css(P, INK)}"""
    buildings = []
    bx = 0
    widths = [220, 160, 300, 180, 260, 140, 240, 200, 320, 170, 230, 280, 150, 260]
    heights = [260, 340, 200, 300, 240, 360, 220, 310, 180, 330, 250, 210, 350, 270]
    k = 0
    while bx < P["W"] * 3:
        w, h = widths[k % len(widths)], heights[k % len(heights)]
        buildings.append(f'<div class="ro-b" style="left:{bx}px; width:{w}px; height:{h}px"></div>')
        bx += w + 40
        k += 1
    wheel = (
        '<svg viewBox="0 0 100 100" width="100%" height="100%"><circle cx="50" cy="50" r="48" fill="#1B1D22"/>'
        '<circle cx="50" cy="50" r="28" fill="#C9CED6"/><g class="ro-spokes" style="transform-origin:50px 50px">'
        '<rect x="47" y="24" width="6" height="52" fill="#7D8590"/><rect x="24" y="47" width="52" height="6" fill="#7D8590"/>'
        '</g><circle cx="50" cy="50" r="7" fill="#7D8590"/></svg>'
    )
    van = f"""<svg class="body" viewBox="0 0 1000 450" width="100%" height="100%">
          <path d="M30 360 L30 70 Q30 40 60 40 L700 40 L700 360 Z" fill="#FFFFFF" stroke="#C9CED6" stroke-width="4"/>
          <path d="M700 360 L700 60 Q700 40 722 40 L815 40 Q835 40 848 56 L950 190 Q968 210 968 240 L968 360 Z" fill="#FFFFFF" stroke="#C9CED6" stroke-width="4"/>
          <path d="M722 74 L812 74 L900 190 L722 190 Z" fill="#8FBFD6"/>
          <rect x="705" y="210" width="6" height="140" fill="#D5DAE1"/>
          <rect x="740" y="215" width="40" height="8" rx="4" fill="#9AA3AE"/>
          <rect x="20" y="340" width="960" height="34" rx="10" fill="#3A3E47"/>
          <rect x="940" y="250" width="30" height="26" rx="6" fill="#F6C44F"/>
          <rect x="30" y="250" width="16" height="30" fill="{ACCENT}"/>
        </svg>"""
    body = f"""    <div id="ro-sky"></div>
    <div id="ro-city">{''.join(buildings)}</div>
    <div id="ro-walk"></div>
    <div id="ro-road"></div>
    <div id="ro-dashes"></div>
    <div id="ro-van" class="clip" data-start="0" data-duration="5">
        {van}
        <div class="ro-wheel" style="left:{0.2 * vw - 0.065 * vw}px">{wheel}</div>
        <div class="ro-wheel" style="left:{0.8 * vw - 0.065 * vw}px">{wheel}</div>
        <div id="ro-name">Fournil Martin</div>
        <div id="ro-logo">{logo_svg('rl', 'color')}</div>
    </div>
    <h1 id="ro-title" class="title clip" data-start="1.2" data-duration="3.2">Qui prend<br />la route.</h1>"""
    js = f"""    tl.fromTo("#ro-logo", {{ x: {sx:.1f}, y: {sy:.1f}, scale: {sc:.3f} }}, {{ x: 0, y: 0, scale: 1, duration: 0.9, ease: "power3.inOut" }}, 0.25);
    tl.fromTo("#ro-logo", {{ scaleX: 1 }}, {{ scaleX: 1.12, scaleY: 0.9, duration: 0.08, yoyo: true, repeat: 1, ease: "power1.out" }}, 1.15);
    tl.fromTo("#ro-name", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: 0.4, ease: "power2.out" }}, 1.25);
    tl.fromTo("#ro-title", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: 0.5, ease: "power3.out" }}, 1.2);
    tl.fromTo("#ro-dashes", {{ x: 0 }}, {{ x: -2200, duration: 3.6, ease: "power1.in" }}, 1.4);
    tl.fromTo("#ro-city", {{ x: 0 }}, {{ x: -700, duration: 3.6, ease: "power1.in" }}, 1.4);
    tl.fromTo(".ro-spokes", {{ rotation: 0 }}, {{ rotation: 1440, duration: 3.6, ease: "power1.in" }}, 1.4);
    tl.fromTo("#ro-van", {{ y: 0 }}, {{ y: -4, duration: 0.18, yoyo: true, repeat: 9, ease: "sine.inOut" }}, 1.5);
    tl.to("#ro-title", {{ x: -60, opacity: 0, duration: 0.3, ease: "power2.in" }}, 4.1);
    tl.to("#ro-van", {{ x: {P['W'] + vw}, duration: 0.8, ease: "power3.in" }}, 4.15);"""
    return scene("road", P, css, body, js)


# ---------------------------------------------------------------- S4 tee-shirt
def s_tee(P):
    th = P["TEEH"]
    tw = th * 600 / 640
    tx = P["TEECX"] - tw / 2
    ty = P["TEECY"] - th / 2
    L = tw * 0.36
    lx = tw / 2 - L / 2
    ly = th * 0.3
    # centre du logo dans le cadre, pour la poussée finale
    lcx = tx + lx + L / 2
    lcy = ty + ly + L / 2
    css = f"""
    #te-bg {{ position: absolute; inset: 0; background: #F3D9A4; }}
    #te-cam {{ position: absolute; inset: 0; transform-origin: {lcx}px {lcy}px; }}
    #te-shirt {{ position: absolute; left: {tx}px; top: {ty}px; width: {tw}px; height: {th}px; transform-origin: 50% 0%; }}
    #te-logo {{ position: absolute; left: {lx}px; top: {ly}px; width: {L}px; height: {L}px; }}
    #te-name {{ position: absolute; left: {tw / 2 - 300}px; top: {ly + L + 8}px; width: 600px; text-align: center;
      font-family: "Playfair Display"; font-weight: 700; font-size: {int(L * 0.19)}px; color: {WHEAT}; }}
    #te-print {{ position: absolute; left: 0; top: 0; width: 100%; height: 100%; }}
    #te-squeegee {{ position: absolute; left: {lx - 60}px; top: {ly - 30}px; width: {L + 120}px; height: 26px;
      background: #2E3138; border-bottom: 8px solid #C9CED6; }}
    {title_css(P, BROWN)}"""
    body = f"""    <div id="te-bg"></div>
    <div id="te-cam">
      <div id="te-shirt" class="clip" data-start="0" data-duration="4">
        <svg viewBox="0 0 600 640" width="100%" height="100%">
          <path d="M190 40 Q300 110 410 40 L580 130 L520 260 L455 230 L455 630 L145 630 L145 230 L80 260 L20 130 Z" fill="{BROWN}"/>
          <path d="M190 40 Q300 110 410 40 L392 34 Q300 86 208 34 Z" fill="#3A2214"/>
          <path d="M145 230 L145 630" stroke="#3A2214" stroke-width="6"/>
          <path d="M455 230 L455 630" stroke="#3A2214" stroke-width="6"/>
        </svg>
        <div id="te-print">
          <div id="te-logo">{logo_svg('tl', 'print')}</div>
          <div id="te-name">Fournil Martin</div>
        </div>
        <div id="te-squeegee"></div>
      </div>
    </div>
    <h1 id="te-title" class="title clip" data-start="1.6" data-duration="2.1">Qui se porte<br />fièrement.</h1>"""
    js = f"""    tl.fromTo("#te-shirt", {{ y: {-P['H']} }}, {{ y: 0, duration: 0.55, ease: "power3.out" }}, 0);
    tl.fromTo("#te-shirt", {{ rotation: 6 }}, {{ rotation: 0, duration: 1.1, ease: "elastic.out(1, 0.5)" }}, 0.35);
    tl.fromTo("#te-squeegee", {{ y: 0, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.15 }}, 0.75);
    tl.fromTo("#te-squeegee", {{ y: 0 }}, {{ y: {L + L * 0.35 + 60:.0f}, duration: 0.8, ease: "power2.inOut", immediateRender: false }}, 0.9);
    tl.fromTo("#te-print", {{ clipPath: "inset(0 0 100% 0)" }}, {{ clipPath: "inset(0 0 0% 0)", duration: 0.8, ease: "power2.inOut" }}, 0.9);
    tl.to("#te-squeegee", {{ opacity: 0, duration: 0.2 }}, 1.75);
    tl.fromTo("#te-title", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: 0.5, ease: "power3.out" }}, 1.6);
    tl.to("#te-title", {{ x: -60, opacity: 0, duration: 0.25, ease: "power2.in" }}, 3.4);
    tl.fromTo("#te-cam", {{ scale: 1 }}, {{ scale: 3.2, duration: 0.6, ease: "expo.in" }}, 3.4);"""
    return scene("tee", P, css, body, js)


# ---------------------------------------------------------------- S5 réseaux
def s_social(P):
    ph = P["PHONEH"]
    pw = ph * 0.49
    px = P["PHONECX"] - pw / 2
    py = P["PHONECY"] - ph / 2
    pad = pw * 0.05
    head = pw * 0.17
    img = pw - 2 * pad
    imgx = px + pad
    imgy = py + pad + head + pw * 0.06
    icx = imgx + img / 2
    icy = imgy + img / 2
    f = pw / 430  # échelle de la typo dans le téléphone
    bub = P["BUBS"]
    css = f"""
    #so-bg {{ position: absolute; inset: 0; background: #12403C; }}
    #so-cam {{ position: absolute; inset: 0; transform-origin: {icx}px {icy}px; }}
    #so-phone {{ position: absolute; left: {px - 14}px; top: {py - 14}px; width: {pw + 28}px; height: {ph + 28}px;
      background: #0B0C0F; border-radius: {pw * 0.13}px; }}
    #so-screen {{ position: absolute; left: {px}px; top: {py}px; width: {pw}px; height: {ph}px; background: #FFFFFF;
      border-radius: {pw * 0.1}px; overflow: hidden; }}
    #so-head {{ position: absolute; left: {pad}px; top: {pad + pw * 0.04}px; height: {head}px; display: flex; align-items: center; gap: {12 * f}px;
      font-family: "Inter"; font-weight: 700; font-size: {24 * f}px; color: {INK}; }}
    #so-avatar {{ width: {head * 0.8}px; height: {head * 0.8}px; border-radius: 50%; background: {BROWN}; padding: {head * 0.08}px; }}
    #so-img {{ position: absolute; left: {imgx}px; top: {imgy}px; width: {img}px; height: {img}px; background: #F3D9A4; }}
    #so-img-logo {{ position: absolute; left: {img * 0.2}px; top: {img * 0.14}px; width: {img * 0.6}px; height: {img * 0.6}px; }}
    #so-img-name {{ position: absolute; left: 0; top: {img * 0.77}px; width: {img}px; text-align: center;
      font-family: "Playfair Display"; font-weight: 700; font-size: {img * 0.09}px; color: {BROWN}; }}
    #so-bar {{ position: absolute; left: {pad}px; top: {imgy - py + img + 18 * f}px; display: flex; align-items: center; gap: {14 * f}px;
      font-family: "Inter"; font-weight: 700; font-size: {30 * f}px; color: {INK}; font-variant-numeric: tabular-nums; }}
    #so-heart {{ width: {46 * f}px; height: {46 * f}px; }}
    #so-cap {{ position: absolute; left: {pad}px; top: {imgy - py + img + 80 * f}px; width: {pw - 2 * pad}px;
      font-family: "Inter"; font-weight: 400; font-size: {22 * f}px; line-height: 1.35; color: #3A3E47; }}
    .so-bub {{ position: absolute; padding: {bub * 0.45}px {bub * 0.7}px; background: #FFFFFF; color: {INK};
      font-family: "Inter"; font-weight: 700; font-size: {bub}px; border-radius: 6px;
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.22); white-space: nowrap; }}
    {title_css(P, "#FFFFFF")}
    #so-title {{ z-index: 10; }}"""
    horiz = P["W"] > P["H"]
    if horiz:
        bubs = [(P["BUBX"], P["BUBY"] + 0), (P["BUBX"] + 70, P["BUBY"] + 120), (P["BUBX"] + 20, P["BUBY"] + 240)]
    else:
        bubs = [(P["BUBX"], py + ph + 50), (P["BUBX"] + 60, py + ph + 150), (P["BUBX"] + 10, py + ph + 250)]
    texts = ["Trop beau le camion !", "Je veux le tee-shirt", "On passe demain matin"]
    bub_html = "\n".join(
        f'      <div id="so-b{i + 1}" class="so-bub clip" data-start="{1.5 + i * 0.3:.1f}" data-duration="{2.5 - i * 0.3:.1f}" '
        f'style="left:{bx:.0f}px; top:{by:.0f}px">{t}</div>'
        for i, ((bx, by), t) in enumerate(zip(bubs, texts))
    )
    css += f"""
    #so-cam .so-bub {{ z-index: 5; }}"""
    # zoom de départ : l'image du post remplit le cadre comme le logo du plan précédent
    z = max(P["W"], P["H"]) / img * 1.05
    body = f"""    <div id="so-bg"></div>
    <div id="so-cam">
      <div id="so-phone" class="clip" data-start="0" data-duration="4"></div>
      <div id="so-screen" class="clip" data-start="0" data-duration="4">
        <div id="so-head"><div id="so-avatar">{logo_svg('sa', 'color')}</div>fournil.martin</div>
        <div id="so-bar">
          <svg id="so-heart" viewBox="0 0 24 24"><path id="so-heart-p" d="M12 21 L10.6 19.7 C5.4 15 2 11.9 2 8.1 C2 5 4.4 2.6 7.5 2.6 C9.2 2.6 10.9 3.4 12 4.7 C13.1 3.4 14.8 2.6 16.5 2.6 C19.6 2.6 22 5 22 8.1 C22 11.9 18.6 15 13.4 19.7 Z" fill="none" stroke="{INK}" stroke-width="2"/></svg>
          <span id="so-count">0</span>
        </div>
        <div id="so-cap"><b>fournil.martin</b> Nouvelle identité, nouveau camion, nouveaux tee-shirts. Merci à notre agence !</div>
      </div>
      <div id="so-img" class="clip" data-start="0" data-duration="4">
        <div id="so-img-logo">{logo_svg('si', 'color')}</div>
        <div id="so-img-name">Fournil Martin</div>
      </div>
{bub_html}
    </div>
    <h1 id="so-title" class="title clip" data-layout-allow-occlusion data-start="1.0" data-duration="2.8">Et qui fait<br />parler.</h1>"""
    js = f"""    tl.fromTo("#so-cam", {{ scale: {z:.3f} }}, {{ scale: 1, duration: 0.9, ease: "expo.out" }}, 0);
    tl.fromTo("#so-title", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: 0.5, ease: "power3.out" }}, 1.0);
    tl.fromTo("#so-heart", {{ scale: 1 }}, {{ scale: 1.35, duration: 0.12, yoyo: true, repeat: 1, ease: "power2.out" }}, 1.2);
    tl.fromTo("#so-heart-p", {{ fill: "rgba(255,90,54,0)", stroke: "{INK}" }}, {{ fill: "rgba(255,90,54,1)", stroke: "{ACCENT}", duration: 0.12 }}, 1.2);
    const counter = {{ v: 0 }};
    tl.fromTo(counter, {{ v: 0 }}, {{ v: 1248, duration: 2.2, ease: "power2.out",
      onUpdate: () => {{ document.querySelector("#so-count").textContent = Math.round(counter.v).toLocaleString("fr-FR") + " j'aime"; }} }}, 1.2);
    tl.fromTo("#so-b1", {{ scale: 0.6, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.2)" }}, 1.5);
    tl.fromTo("#so-b2", {{ scale: 0.6, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.2)" }}, 1.8);
    tl.fromTo("#so-b3", {{ scale: 0.6, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.3, ease: "back.out(2.2)" }}, 2.1);
    tl.to("#so-title", {{ opacity: 0, duration: 0.2, ease: "power2.in" }}, 3.65);
    tl.to("#so-cam", {{ x: {-P['W'] * 1.1}, duration: 0.35, ease: "power3.in" }}, 3.65);"""
    return scene("social", P, css, body, js)


# ---------------------------------------------------------------- S6 fin
def s_endcard(P):
    es = P["ES"]
    horiz = P["W"] > P["H"]
    services = "Graphisme · Marquage véhicule · Textile · Digital" if horiz else "Graphisme · Marquage véhicule<br />Textile · Digital"
    y1 = P["EY"]
    y2 = y1 + es * 1.0
    ysv = y2 + es * 1.25
    ycta = ysv + (90 if horiz else 150)
    variables = json.dumps([
        {"id": "kicker", "type": "string", "label": "Nom de l’agence", "default": "Votre agence de communication"},
        {"id": "cta", "type": "string", "label": "Appel à l’action", "default": "Parlons de votre projet"},
    ], ensure_ascii=False)
    css = f"""
    #en-bg {{ position: absolute; inset: 0; background: {INK}; }}
    .en-l {{ position: absolute; left: {P['EX'] - 8}px; font-family: "Montserrat"; font-weight: 900; font-size: {es}px;
      line-height: 1; letter-spacing: -0.04em; color: #F4F1EA; white-space: nowrap; }}
    #en-l1 {{ top: {y1}px; }}
    #en-l2 {{ top: {y2}px; color: {ACCENT}; }}
    #en-kicker {{ position: absolute; left: {P['EX']}px; top: {y1 - 70}px; font-family: "Montserrat"; font-weight: 700;
      font-size: 34px; letter-spacing: 0.18em; text-transform: uppercase; color: #9AA3AE; }}
    #en-svc {{ position: absolute; left: {P['EX']}px; top: {ysv}px; width: {P['ESVCW']}px; font-family: "Montserrat"; font-weight: 600;
      font-size: {P['ESVC']}px; line-height: 1.35; color: #F4F1EA; }}
    #en-cta {{ position: absolute; left: {P['EX']}px; top: {ycta}px; padding: 26px 40px; background: {ACCENT}; color: {INK};
      font-family: "Montserrat"; font-weight: 800; font-size: 44px; }}"""
    body = f"""    <div id="en-bg"></div>
    <p id="en-kicker" class="clip" data-start="0.9" data-duration="3.1" data-var-text="kicker">Votre agence de communication</p>
    <div id="en-l1" class="en-l clip" data-start="0.1" data-duration="3.9">Votre marque,</div>
    <div id="en-l2" class="en-l clip" data-start="0.35" data-duration="3.65">partout.</div>
    <div id="en-svc" class="clip" data-start="1.2" data-duration="2.8">{services}</div>
    <div id="en-cta" class="clip" data-start="1.6" data-duration="2.4"><span data-var-text="cta">Parlons de votre projet</span> →</div>"""
    js = f"""    tl.fromTo("#en-l1", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: 0.45, ease: "expo.out" }}, 0.1);
    tl.fromTo("#en-l2", {{ clipPath: "inset(0 100% 0 0)", x: -30 }}, {{ clipPath: "inset(0 0% 0 0)", x: 0, duration: 0.5, ease: "expo.out" }}, 0.35);
    tl.fromTo("#en-kicker", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: "power2.out" }}, 0.9);
    tl.fromTo("#en-svc", {{ clipPath: "inset(0 100% 0 0)" }}, {{ clipPath: "inset(0 0% 0 0)", duration: 0.6, ease: "power2.inOut" }}, 1.2);
    tl.fromTo("#en-cta", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.45, ease: "expo.out", transformOrigin: "0% 50%" }}, 1.6);"""
    return scene("endcard", P, css, body, js, extra_attrs=f" data-composition-variables='{variables}'")


BUILDERS = {
    "sketch": s_sketch, "vector": s_vector, "road": s_road,
    "tee": s_tee, "social": s_social, "endcard": s_endcard,
}


def index_html(P, name):
    hosts = "\n".join(
        f'      <div id="{cid}" data-composition-id="{cid}" data-composition-src="compositions/{cid}.html" '
        f'data-start="{st}" data-duration="{du}" data-track-index="1" data-track-kind="graphics" '
        f'data-width="{P["W"]}" data-height="{P["H"]}"></div>'
        for cid, st, du in SCENES
    )
    audio = "\n".join(
        f'      <audio id="{aid}" class="clip" src="assets/sfx/{f}" data-start="{st}" data-duration="{du}" '
        f'data-media-start="{ms}" data-track-index="{tr}" data-volume="{vol}"></audio>'
        for aid, f, st, du, ms, tr, vol in SFX
    )
    return f"""<!doctype html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={P['W']}, height={P['H']}" />
    <title>{name}</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: {P['W']}px; height: {P['H']}px; overflow: hidden; background: {INK}; }}
      #root {{ width: 100%; height: 100%; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="{P['W']}" data-height="{P['H']}">
{hosts}
{audio}
    </div>
    <script>
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""


def main():
    for fmt, P in FORMATS.items():
        out = os.path.join(HERE, fmt)
        os.makedirs(os.path.join(out, "compositions"), exist_ok=True)
        os.makedirs(os.path.join(out, "assets", "sfx"), exist_ok=True)
        with open(os.path.join(out, "index.html"), "w") as fh:
            fh.write(index_html(P, f"Agence — {fmt}"))
        for cid, _, _ in SCENES:
            with open(os.path.join(out, "compositions", f"{cid}.html"), "w") as fh:
                fh.write(BUILDERS[cid](P))
        for _, f, *_ in SFX:
            shutil.copy(os.path.join(SFX_SRC, f), os.path.join(out, "assets", "sfx", f))
        print("écrit", out)


if __name__ == "__main__":
    main()
