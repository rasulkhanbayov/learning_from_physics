"""
Generate IRIS ECCV 2026 presentation slides as .pptx
Run: python make_slides.py
Requires: pip install python-pptx Pillow
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import os
from PIL import Image
import io

# ── Colors ────────────────────────────────────────────────────────────────────
BLUE       = RGBColor(0x1F, 0x49, 0x7D)   # dark blue header
LIGHT_BLUE = RGBColor(0xDC, 0xEB, 0xF8)   # panel background
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
GRAY       = RGBColor(0x5A, 0x5A, 0x5A)
GREEN      = RGBColor(0x00, 0x80, 0x60)
RED        = RGBColor(0xC0, 0x00, 0x00)
BLACK      = RGBColor(0x00, 0x00, 0x00)

GIF_DIR = "gifs"
GIFS = [
    "Dropping_ball.gif",
    "Falling_ball.gif",
    "Sliding_cone.gif",
    "Rotation.gif",
    "Hitting_cones.gif",
    "Two_Moving_Pendulums.gif",
    "Two_Moving_Pendulum_One_Static.gif",
]

# Slide is 13.33 x 7.5 inches (widescreen 16:9)
W, H = Inches(13.33), Inches(7.5)

prs = Presentation()
prs.slide_width  = W
prs.slide_height = H

BLANK = prs.slide_layouts[6]   # completely blank layout


# ── Helpers ───────────────────────────────────────────────────────────────────

def add_rect(slide, x, y, w, h, fill=None, line=None):
    shape = slide.shapes.add_shape(1, x, y, w, h)   # MSO_SHAPE_TYPE.RECTANGLE = 1
    shape.line.fill.background()
    if fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = fill
    else:
        shape.fill.background()
    if line:
        shape.line.color.rgb = line
        shape.line.width = Pt(1)
    else:
        shape.line.fill.background()
    return shape


def add_text(slide, text, x, y, w, h,
             size=18, bold=False, color=BLACK, align=PP_ALIGN.LEFT,
             wrap=True, italic=False):
    txb = slide.shapes.add_textbox(x, y, w, h)
    tf  = txb.text_frame
    tf.word_wrap = wrap
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size  = Pt(size)
    run.font.bold  = bold
    run.font.color.rgb = color
    run.font.italic = italic
    run.font.name  = "Calibri"
    return txb


def add_header(slide, title):
    """Blue header bar with white title."""
    add_rect(slide, 0, 0, W, Inches(0.65), fill=BLUE)
    add_text(slide, title,
             Inches(0.3), Inches(0.07), Inches(12.7), Inches(0.55),
             size=24, bold=True, color=WHITE, align=PP_ALIGN.LEFT)


def add_gif(slide, filename, x, y, width):
    """Add GIF (first frame as PNG) to slide."""
    path = os.path.join(GIF_DIR, filename)
    img  = Image.open(path)
    img.seek(0)
    buf = io.BytesIO()
    img.convert("RGBA").save(buf, format="PNG")
    buf.seek(0)
    # Preserve aspect ratio
    w_px, h_px = img.size
    height = width * h_px / w_px
    slide.shapes.add_picture(buf, x, y, width=width, height=height)
    return height


def bullet_tf(tf, items, size=16, indent=False):
    """Fill a text frame with bullet items."""
    first = True
    for item in items:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.text = item
        p.level = 1 if indent else 0
        run = p.runs[0] if p.runs else p.add_run()
        run.font.size = Pt(size)
        run.font.name = "Calibri"
        run.font.color.rgb = BLACK


# ── SLIDE 1 — Title ───────────────────────────────────────────────────────────
sl = prs.slides.add_slide(BLANK)

# background
add_rect(sl, 0, 0, W, H, fill=WHITE)

# top accent bar
add_rect(sl, 0, 0, W, Inches(0.12), fill=BLUE)
# bottom accent bar
add_rect(sl, 0, H - Inches(0.12), W, Inches(0.12), fill=BLUE)

add_text(sl, "IRIS",
         Inches(0.5), Inches(0.3), Inches(12), Inches(1.1),
         size=54, bold=True, color=BLUE, align=PP_ALIGN.CENTER)

add_text(sl,
         "A Real-World Benchmark for Inverse Recovery and Identification\n"
         "of Physical Dynamic Systems from Monocular Video",
         Inches(0.5), Inches(1.35), Inches(12.3), Inches(1.2),
         size=22, bold=False, color=GRAY, align=PP_ALIGN.CENTER)

add_text(sl, "ECCV 2026  •  Anonymous Submission #13771",
         Inches(0.5), Inches(2.5), Inches(12.3), Inches(0.5),
         size=16, color=GRAY, align=PP_ALIGN.CENTER)

# GIFs row
gif_y = Inches(3.2)
gif_w = Inches(1.7)
total_w = gif_w * len(GIFS) + Inches(0.2) * (len(GIFS) - 1)
gif_x = (W - total_w) / 2
for gname in GIFS:
    h = add_gif(sl, gname, gif_x, gif_y, gif_w)
    gif_x += gif_w + Inches(0.2)


# ── SLIDE 2 — Motivation ──────────────────────────────────────────────────────
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, W, H, fill=WHITE)
add_header(sl, "Motivation: What is Missing?")

# Left column — problems
add_text(sl, "Existing methods suffer from:",
         Inches(0.4), Inches(0.85), Inches(6), Inches(0.4),
         size=16, bold=True, color=BLUE)

problems = [
    "•  Evaluated on synthetic data only\n    (cartoon objects, black backgrounds)",
    "•  Only single-body real-world data exists",
    "•  No multi-body or interaction scenarios",
    "•  No standardised evaluation protocol",
    "•  Equation family must be given manually\n    at test time (oracle condition)",
]
y = Inches(1.3)
for p in problems:
    add_text(sl, p, Inches(0.5), y, Inches(5.8), Inches(0.75), size=15, color=BLACK)
    y += Inches(0.78)

# Right column — comparison panels
def mini_table(sl, title, rows, x, y, w, h, title_color=BLUE):
    add_rect(sl, x, y, w, Inches(0.38), fill=title_color)
    add_text(sl, title, x + Inches(0.1), y + Inches(0.04),
             w - Inches(0.15), Inches(0.3),
             size=14, bold=True, color=WHITE)
    row_h = (h - Inches(0.38)) / len(rows)
    ry = y + Inches(0.38)
    for i, (label, val, good) in enumerate(rows):
        bg = RGBColor(0xF0, 0xF8, 0xFF) if i % 2 == 0 else WHITE
        add_rect(sl, x, ry, w, row_h, fill=bg)
        add_text(sl, label, x + Inches(0.12), ry + Inches(0.03),
                 w * 0.55, row_h, size=13, color=GRAY)
        add_text(sl, val,
                 x + w * 0.58, ry + Inches(0.03), w * 0.4, row_h,
                 size=13, bold=good, color=GREEN if good else RED)
        ry += row_h

mini_table(sl, "Delfys75 — Prior State of the Art",
           [("Videos",         "75",            False),
            ("Resolution",     "1080p / 25fps", False),
            ("Phenomena",      "5 (single only)",False),
            ("Multi-body",     "None",          False),
            ("Trials/setting", "5",             False)],
           Inches(6.8), Inches(0.85), Inches(6.1), Inches(2.6),
           title_color=GRAY)

mini_table(sl, "IRIS — This Work",
           [("Videos",         "220",            True),
            ("Resolution",     "4K / 60fps",     True),
            ("Phenomena",      "8 (multi-body)", True),
            ("Multi-body",     "3 novel",        True),
            ("Trials/setting", "10",             True)],
           Inches(6.8), Inches(3.65), Inches(6.1), Inches(2.6),
           title_color=BLUE)


# ── SLIDE 3 — Dataset ─────────────────────────────────────────────────────────
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, W, H, fill=WHITE)
add_header(sl, "The IRIS Dataset — 8 Phenomena, 220 Videos")

labels = [
    ("Dropping ball",           "g, β"),
    ("Falling ball",            "g, r₀"),
    ("Sliding cone",            "μ, α"),
    ("Rotating cone",           "α, β"),
    ("Hitting cones",           "κ, ζ"),
    ("Two moving pendulums",    "Lᵢ, ζᵢ, κᵢⱼ"),
    ("One static pendulum",     "Lᵢ, ζᵢ, κᵢⱼ"),
]

n = len(GIFS)
margin = Inches(0.3)
spacing = Inches(0.15)
gif_w = (W - 2 * margin - spacing * (n - 1)) / n
gif_y = Inches(0.9)

x = margin
for gname, (label, params) in zip(GIFS, labels):
    h = add_gif(sl, gname, x, gif_y, gif_w)
    add_text(sl, label, x, gif_y + h + Inches(0.05), gif_w, Inches(0.35),
             size=12, bold=True, color=BLUE, align=PP_ALIGN.CENTER)
    add_text(sl, params, x, gif_y + h + Inches(0.38), gif_w, Inches(0.3),
             size=11, bold=False, color=GRAY, align=PP_ALIGN.CENTER)
    x += gif_w + spacing

# bottom bar
add_rect(sl, 0, H - Inches(0.7), W, Inches(0.7), fill=LIGHT_BLUE)
add_text(sl,
         "4K / 60fps  •  10 trials per setting  •  Independently measured ground truth  •  Uncertainty estimates  •  SAM2 segmentation masks",
         Inches(0.3), H - Inches(0.62), Inches(12.7), Inches(0.55),
         size=14, color=BLUE, align=PP_ALIGN.CENTER, bold=True)


# ── SLIDE 4 — Evaluation Protocol ────────────────────────────────────────────
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, W, H, fill=WHITE)
add_header(sl, "Standardised Evaluation Protocol")

# Left
add_text(sl, "Train-per-clip protocol",
         Inches(0.4), Inches(0.85), Inches(5.8), Inches(0.4),
         size=16, bold=True, color=BLUE)
proto = [
    "•  Each video clip trained independently from scratch",
    "•  No parameter sharing across clips",
    "•  Fixed random seed (42) for reproducibility",
    "•  Equation family selected automatically",
]
y = Inches(1.3)
for p in proto:
    add_text(sl, p, Inches(0.5), y, Inches(5.8), Inches(0.42), size=15)
    y += Inches(0.43)

add_text(sl, "Five evaluation axes:",
         Inches(0.4), Inches(2.7), Inches(5.8), Inches(0.4),
         size=16, bold=True, color=BLUE)
axes = [
    ("1.  Parameter accuracy",   "MAE vs. ground truth (primary)"),
    ("2.  Equation selection",   "Classification accuracy + confusion"),
    ("3.  Identifiability",      "Gradient norms, ODE residual"),
    ("4.  Robustness",           "Consistency across configurations"),
    ("5.  Extrapolation",        "Prediction beyond training horizon"),
]
y = Inches(3.15)
for name, desc in axes:
    add_text(sl, name, Inches(0.5), y, Inches(2.8), Inches(0.4),
             size=14, bold=True, color=BLUE)
    add_text(sl, desc, Inches(3.4), y, Inches(3.0), Inches(0.4),
             size=14, color=GRAY)
    y += Inches(0.43)

# Right — ODE bank table
add_rect(sl, Inches(6.7), Inches(0.85), Inches(6.3), Inches(0.42), fill=BLUE)
add_text(sl, "ODE Bank (5 families)",
         Inches(6.8), Inches(0.88), Inches(6.1), Inches(0.38),
         size=15, bold=True, color=WHITE)

ode_rows = [
    ("Dropping / Falling ball", "z'' + βz' + αz = 0", "g = α"),
    ("Pendulum",                "θ'' + ζθ' + (g/L)sinθ = 0", "L = g/α"),
    ("Rotating cone",           "φ'' + βφ' + αφ = 0", "α, β direct"),
    ("Sliding cone",            "Constant acceleration block", "μ = β"),
    ("Multi-body",              "Graph ODE + coupling κᵢⱼ", "κᵢⱼ fitted"),
]
ry = Inches(1.27)
for i, (phen, ode, cal) in enumerate(ode_rows):
    bg = LIGHT_BLUE if i % 2 == 0 else WHITE
    add_rect(sl, Inches(6.7), ry, Inches(6.3), Inches(0.52), fill=bg)
    add_text(sl, phen,  Inches(6.8),  ry + Inches(0.06), Inches(2.1), Inches(0.42), size=13, bold=True, color=BLUE)
    add_text(sl, ode,   Inches(9.0),  ry + Inches(0.06), Inches(2.5), Inches(0.42), size=12, color=BLACK, italic=True)
    add_text(sl, cal,   Inches(11.55), ry + Inches(0.06), Inches(1.4), Inches(0.42), size=12, color=GREEN)
    ry += Inches(0.52)


# ── SLIDE 5 — Bug Discovery ───────────────────────────────────────────────────
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, W, H, fill=WHITE)
add_header(sl, "Key Finding: Critical Gradient-Flow Bug in Baseline")

# Left — explanation
add_text(sl, "Original Euler step (Garcia et al. 2025):",
         Inches(0.4), Inches(0.85), Inches(6.0), Inches(0.4),
         size=16, bold=True, color=RED)

add_rect(sl, Inches(0.4), Inches(1.3), Inches(5.9), Inches(1.1), fill=RGBColor(0xFF,0xF0,0xF0), line=RED)
add_text(sl,
         "ż(t+1)  =  ż(t)  +  Δt · z̈(t)\n"
         "z(t+1)  =  z(t)  +  Δt · ż(t)      ← Missing term!",
         Inches(0.55), Inches(1.38), Inches(5.6), Inches(0.95),
         size=15, color=RED, italic=True)

add_text(sl,
         "Missing  Δt² · z̈(t)  →  ∂z(t+1)/∂γ = 0\n"
         "Physics parameters receive ZERO gradient throughout training.",
         Inches(0.4), Inches(2.55), Inches(6.0), Inches(0.8),
         size=15, bold=True, color=RED)

add_text(sl, "Corrected Euler-Cromer step:",
         Inches(0.4), Inches(3.45), Inches(6.0), Inches(0.4),
         size=16, bold=True, color=GREEN)

add_rect(sl, Inches(0.4), Inches(3.9), Inches(5.9), Inches(1.1), fill=RGBColor(0xF0,0xF8,0xF0), line=GREEN)
add_text(sl,
         "ż(t+1)  =  ż(t)  +  Δt · z̈(t)\n"
         "z(t+1)  =  z(t)  +  Δt · ż(t)  +  Δt² · z̈(t)   ✓",
         Inches(0.55), Inches(3.98), Inches(5.6), Inches(0.95),
         size=15, color=GREEN, italic=True)

add_text(sl,
         "Benchmark evaluation exposed this bug — demonstrating the\n"
         "diagnostic value of rigorous real-world benchmarking.",
         Inches(0.4), Inches(5.15), Inches(6.1), Inches(0.7),
         size=14, color=GRAY, italic=True)

# Right — results table
add_rect(sl, Inches(6.7), Inches(0.85), Inches(6.3), Inches(0.45), fill=BLUE)
add_text(sl, "Impact on Delfys75 — Parameter MAE",
         Inches(6.8), Inches(0.9), Inches(6.1), Inches(0.38),
         size=15, bold=True, color=WHITE)

bug_rows = [
    ("pendulum_45",   "L [m]",   "95.07", "3.80",  "-91.3"),
    ("pendulum_90",   "L [m]",   "50.15", "2.93",  "-47.2"),
    ("pendulum_150",  "L [m]",   "29.83", "0.71",  "-29.1"),
    ("LED 2s",        "γ",       "2.30",  "0.40",  "-1.90"),
    ("Torricelli lg", "k",       "6.07",  "2.91",  "-3.16"),
    ("Torricelli sm", "k",       "7.67",  "5.69",  "-1.99"),
]
hdrs = ["Setting", "Param", "Original", "Fixed", "Δ MAE"]
col_x = [Inches(6.75), Inches(8.5), Inches(9.5), Inches(10.6), Inches(11.7)]
col_w = [Inches(1.7),  Inches(1.0), Inches(1.1), Inches(1.1),  Inches(1.2)]

add_rect(sl, Inches(6.7), Inches(1.3), Inches(6.3), Inches(0.38), fill=LIGHT_BLUE)
for cx, cw, h in zip(col_x, col_w, hdrs):
    add_text(sl, h, cx, Inches(1.32), cw, Inches(0.35), size=13, bold=True, color=BLUE)

ry = Inches(1.68)
for i, row in enumerate(bug_rows):
    bg = WHITE if i % 2 == 0 else RGBColor(0xF7,0xF7,0xF7)
    add_rect(sl, Inches(6.7), ry, Inches(6.3), Inches(0.48), fill=bg)
    for cx, cw, val in zip(col_x, col_w, row):
        col_idx = list(row).index(val)
        color = RED if col_idx == 2 else (GREEN if col_idx == 3 else (GREEN if col_idx == 4 else BLACK))
        add_text(sl, val, cx, ry + Inches(0.06), cw, Inches(0.38), size=13, color=color)
    ry += Inches(0.48)


# ── SLIDE 6 — Equation Identification ────────────────────────────────────────
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, W, H, fill=WHITE)
add_header(sl, "Equation Identification: VLM vs. CNN vs. Path-Based")

# Left — motivation
add_text(sl, "Why automatic identification matters:",
         Inches(0.4), Inches(0.85), Inches(6.1), Inches(0.4),
         size=16, bold=True, color=BLUE)
motiv = [
    "•  Garcia et al. use path-based oracle selection",
    "    — requires manual labelling per clip",
    "•  IRIS benchmarks 4 automatic routing strategies",
    "•  Goal: remove human-in-the-loop for equation routing",
]
y = Inches(1.3)
for m in motiv:
    add_text(sl, m, Inches(0.5), y, Inches(6.0), Inches(0.42), size=15)
    y += Inches(0.43)

# Accuracy table
add_rect(sl, Inches(0.4), Inches(3.0), Inches(6.1), Inches(0.42), fill=BLUE)
for cx, cw, h in [(Inches(0.45), Inches(3.5), "Method"),
                   (Inches(4.0),  Inches(1.2), "Delfys75"),
                   (Inches(5.3),  Inches(1.2), "IRIS")]:
    add_text(sl, h, cx, Inches(3.04), cw, Inches(0.35), size=14, bold=True, color=WHITE)

acc_rows = [
    ("CNN (in-distribution)",        "98.4%", "99.3%", True),
    ("VLM temporal reasoning",       "73.3%", "65.0%", False),
    ("VLM describe-then-classify",   "61.1%", "72.9%", False),
    ("Path-based (oracle)",          "100%",  "100%",  False),
]
ry = Inches(3.42)
for i, (method, d75, iris, best) in enumerate(acc_rows):
    bg = LIGHT_BLUE if i % 2 == 0 else WHITE
    add_rect(sl, Inches(0.4), ry, Inches(6.1), Inches(0.48), fill=bg)
    add_text(sl, method, Inches(0.5), ry+Inches(0.06), Inches(3.4), Inches(0.38), size=13, bold=best, color=BLUE if best else BLACK)
    add_text(sl, d75,    Inches(4.0), ry+Inches(0.06), Inches(1.2), Inches(0.38), size=13, color=GREEN if best else BLACK)
    add_text(sl, iris,   Inches(5.3), ry+Inches(0.06), Inches(1.2), Inches(0.38), size=13, color=GREEN if best else BLACK)
    ry += Inches(0.48)

# Right — insights
add_rect(sl, Inches(6.9), Inches(0.85), Inches(6.1), Inches(0.42), fill=BLUE)
add_text(sl, "Key Insight",
         Inches(7.0), Inches(0.89), Inches(5.9), Inches(0.35),
         size=15, bold=True, color=WHITE)
add_rect(sl, Inches(6.9), Inches(1.27), Inches(6.1), Inches(1.5), fill=LIGHT_BLUE)
add_text(sl,
         "VLM ranking REVERSES across benchmarks:\n\n"
         "Temporal reasoning wins on Delfys75\n"
         "(familiar, single-body phenomena)\n\n"
         "Describe-then-classify wins on IRIS\n"
         "(diverse, multi-body phenomena)",
         Inches(7.0), Inches(1.32), Inches(5.9), Inches(1.4),
         size=14, color=BLACK)

add_rect(sl, Inches(6.9), Inches(2.95), Inches(6.1), Inches(0.42), fill=BLUE)
add_text(sl, "CNN vs. VLM Trade-off",
         Inches(7.0), Inches(2.99), Inches(5.9), Inches(0.35),
         size=15, bold=True, color=WHITE)
add_rect(sl, Inches(6.9), Inches(3.37), Inches(6.1), Inches(1.4), fill=LIGHT_BLUE)
add_text(sl,
         "CNN achieves near-perfect accuracy in-distribution\n"
         "but cannot generalise to unseen phenomena\n"
         "without full retraining.\n\n"
         "VLMs operate zero-shot across any phenomenon set.",
         Inches(7.0), Inches(3.42), Inches(5.9), Inches(1.3),
         size=14, color=BLACK)

add_rect(sl, Inches(6.9), Inches(4.95), Inches(6.1), Inches(1.0), fill=RGBColor(0xFF,0xF8,0xE1))
add_text(sl,
         "First systematic comparison of automatic\n"
         "equation routing for physics estimation.",
         Inches(7.0), Inches(5.05), Inches(5.9), Inches(0.8),
         size=14, bold=True, color=RGBColor(0xA0, 0x60, 0x00), italic=True)


# ── SLIDE 7 — IRIS Results ────────────────────────────────────────────────────
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, W, H, fill=WHITE)
add_header(sl, "Results on IRIS: 1-Step vs. Multi-Step Loss")

# Table
add_rect(sl, Inches(0.3), Inches(0.85), Inches(7.8), Inches(0.42), fill=BLUE)
for cx, cw, h in [
    (Inches(0.35), Inches(2.1), "Dynamics"),
    (Inches(2.5),  Inches(1.1), "Setting"),
    (Inches(3.65), Inches(0.9), "Param"),
    (Inches(4.6),  Inches(0.9), "GT"),
    (Inches(5.55), Inches(1.0), "1-step"),
    (Inches(6.6),  Inches(1.0), "Multi"),
    (Inches(7.65), Inches(0.4), "Δ"),
]:
    add_text(sl, h, cx, Inches(0.89), cw, Inches(0.35), size=13, bold=True, color=WHITE)

result_rows = [
    # (dynamics, setting, param, gt, one, multi, delta, one_better, catastrophic)
    ("Dropping ball", "drop_50",  "g [m/s²]", "9.81", "1.04",  "6.88",   "+5.84", True,  False),
    ("Dropping ball", "drop_100", "g [m/s²]", "9.81", "2.26",  "8.28",   "+6.02", True,  False),
    ("Falling ball",  "big",      "g [m/s²]", "9.81", "4.26",  "6.40",   "+2.14", True,  False),
    ("Pendulum",      "pend_20",  "L [m]",    "0.50", "0.56",  "0.40",   "-0.16", False, False),
    ("Pendulum",      "pend_45",  "L [m]",    "0.50", "0.34",  "1.16",   "+0.82", True,  False),
    ("Pendulum",      "pend_90",  "L [m]",    "0.50", "0.60",  "21.95",  "+21.3", True,  True),
    ("Sliding cone",  "cone_45",  "α [deg]",  "45.0", "0.00",  "0.00",   "0.00",  False, False),
    ("Two mov. pend.","pend_20",  "L [m]",    "0.50", "1.14",  "741.1",  "+740",  True,  True),
    ("Two mov. pend.","pend_45",  "L [m]",    "0.50", "1.63",  "164.1",  "+163",  True,  True),
    ("One stat. pend.","pend_20", "L [m]",    "0.50", "1.38",  "65.4",   "+64",   True,  True),
    ("One stat. pend.","pend_90", "L [m]",    "0.50", "1.06",  "164.8",  "+164",  True,  True),
]

ry = Inches(1.27)
prev_dyn = ""
for i, (dyn, sett, param, gt, one, multi, delta, one_better, cat) in enumerate(result_rows):
    bg = LIGHT_BLUE if i % 2 == 0 else WHITE
    add_rect(sl, Inches(0.3), ry, Inches(7.8), Inches(0.44), fill=bg)
    dyn_text = dyn if dyn != prev_dyn else ""
    prev_dyn = dyn
    add_text(sl, dyn_text, Inches(0.35), ry+Inches(0.05), Inches(2.1), Inches(0.36), size=12, bold=True, color=BLUE)
    add_text(sl, sett,     Inches(2.5),  ry+Inches(0.05), Inches(1.1), Inches(0.36), size=12, color=BLACK)
    add_text(sl, param,    Inches(3.65), ry+Inches(0.05), Inches(0.9), Inches(0.36), size=12, color=GRAY)
    add_text(sl, gt,       Inches(4.6),  ry+Inches(0.05), Inches(0.9), Inches(0.36), size=12, color=BLACK)
    one_col = GREEN if one_better else BLACK
    mul_col = RED if cat else (GREEN if not one_better else BLACK)
    add_text(sl, one,   Inches(5.55), ry+Inches(0.05), Inches(1.0), Inches(0.36), size=12, bold=one_better, color=one_col)
    add_text(sl, multi, Inches(6.6),  ry+Inches(0.05), Inches(1.0), Inches(0.36), size=12, bold=cat, color=mul_col)
    add_text(sl, delta, Inches(7.65), ry+Inches(0.05), Inches(0.4), Inches(0.36), size=12, color=RED if cat else BLACK)
    ry += Inches(0.44)

# Right — key findings
add_rect(sl, Inches(8.4), Inches(0.85), Inches(4.7), Inches(0.42), fill=BLUE)
add_text(sl, "Key Findings", Inches(8.5), Inches(0.89), Inches(4.5), Inches(0.35), size=15, bold=True, color=WHITE)

findings = [
    (GREEN, "Multi-step helps on rotation and small-angle pendulum"),
    (RED,   "CATASTROPHIC failure on large-angle pendulum (pend_90)"),
    (RED,   "Multi-body: errors >100m — coupling κᵢⱼ compounds over K steps"),
    (GREEN, "Sliding cone: perfect recovery (metadata-based angle)"),
    (BLUE,  "1-step baseline consistently wins on gravity estimation"),
]
ry2 = Inches(1.35)
for color, text in findings:
    add_rect(sl, Inches(8.4), ry2, Inches(4.7), Inches(0.8), fill=LIGHT_BLUE if color != RED else RGBColor(0xFF,0xF0,0xF0))
    add_text(sl, text, Inches(8.55), ry2+Inches(0.1), Inches(4.4), Inches(0.65), size=13, color=color, bold=(color==RED))
    ry2 += Inches(0.88)

add_text(sl,
         "Failure mode invisible on single-body benchmarks — only exposed by IRIS multi-body scenarios.",
         Inches(8.4), ry2 + Inches(0.1), Inches(4.7), Inches(0.6),
         size=13, color=GRAY, italic=True)


# ── SLIDE 8 — Summary ─────────────────────────────────────────────────────────
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, W, H, fill=WHITE)
add_header(sl, "Summary and Contributions")

contribs = [
    ("1. IRIS Benchmark",
     "220 real-world 4K/60fps videos · 8 dynamical systems · 3 novel multi-body scenarios\n"
     "Independently measured ground truth with uncertainty estimates · 10 trials per setting"),
    ("2. Standardised Protocol",
     "5 evaluation axes (accuracy, equation selection, identifiability, robustness, extrapolation)\n"
     "Train-per-clip · fixed seeds · fully traceable results"),
    ("3. Equation-ID Benchmark",
     "First systematic comparison of 4 routing strategies\n"
     "VLM ranking reverses across benchmarks · CNN generalisation bottleneck identified"),
    ("4. Diagnostic Findings",
     "Gradient-flow bug in state-of-the-art pipeline fixed (+91m improvement on pendulum)\n"
     "Multi-step loss catastrophically unstable on multi-body dynamics"),
]

y = Inches(0.85)
for title, body in contribs:
    add_rect(sl, Inches(0.4), y, Inches(8.5), Inches(0.38), fill=BLUE)
    add_text(sl, title, Inches(0.5), y + Inches(0.04), Inches(8.3), Inches(0.32), size=15, bold=True, color=WHITE)
    add_rect(sl, Inches(0.4), y + Inches(0.38), Inches(8.5), Inches(0.82), fill=LIGHT_BLUE)
    add_text(sl, body, Inches(0.55), y + Inches(0.42), Inches(8.2), Inches(0.75), size=13, color=BLACK)
    y += Inches(1.35)

# Right — open challenges + release
add_rect(sl, Inches(9.2), Inches(0.85), Inches(3.8), Inches(0.42), fill=BLUE)
add_text(sl, "Open Challenges", Inches(9.3), Inches(0.89), Inches(3.6), Inches(0.35), size=15, bold=True, color=WHITE)
challenges = [
    "VLM routing: 65–73% (far from oracle)",
    "Damping poorly identifiable across all methods",
    "Multi-body multi-step training unstable",
    "Latent-to-SI calibration is phenomenon-specific",
]
ry = Inches(1.3)
for c in challenges:
    add_rect(sl, Inches(9.2), ry, Inches(3.8), Inches(0.52), fill=RGBColor(0xFF,0xF0,0xF0))
    add_text(sl, "• " + c, Inches(9.3), ry + Inches(0.06), Inches(3.6), Inches(0.42), size=13, color=RED)
    ry += Inches(0.56)

add_rect(sl, Inches(9.2), Inches(3.75), Inches(3.8), Inches(0.42), fill=BLUE)
add_text(sl, "Release", Inches(9.3), Inches(3.79), Inches(3.6), Inches(0.35), size=15, bold=True, color=WHITE)
add_rect(sl, Inches(9.2), Inches(4.17), Inches(3.8), Inches(1.1), fill=LIGHT_BLUE)
add_text(sl,
         "Dataset · Annotations\nEvaluation toolkit\nAll baseline implementations\nCC BY 4.0 upon acceptance",
         Inches(9.3), Inches(4.22), Inches(3.6), Inches(1.0),
         size=14, color=BLUE)


# ── SLIDE 9 — Thank You ───────────────────────────────────────────────────────
sl = prs.slides.add_slide(BLANK)
add_rect(sl, 0, 0, W, H, fill=WHITE)
add_rect(sl, 0, 0, W, Inches(0.12), fill=BLUE)
add_rect(sl, 0, H - Inches(0.12), W, Inches(0.12), fill=BLUE)

add_text(sl, "Thank You",
         Inches(0.5), Inches(0.3), Inches(12.3), Inches(1.0),
         size=48, bold=True, color=BLUE, align=PP_ALIGN.CENTER)

gif_y = Inches(1.6)
gif_w = Inches(1.7)
total_w = gif_w * len(GIFS) + Inches(0.2) * (len(GIFS) - 1)
gif_x = (W - total_w) / 2
for gname in GIFS:
    h = add_gif(sl, gname, gif_x, gif_y, gif_w)
    gif_x += gif_w + Inches(0.2)

add_text(sl,
         "IRIS  ·  220 videos  ·  8 phenomena  ·  4K/60fps  ·  Open benchmark",
         Inches(0.5), Inches(5.0), Inches(12.3), Inches(0.6),
         size=18, bold=True, color=BLUE, align=PP_ALIGN.CENTER)

add_text(sl, "ECCV 2026  •  Submission #13771",
         Inches(0.5), Inches(5.6), Inches(12.3), Inches(0.5),
         size=15, color=GRAY, align=PP_ALIGN.CENTER)


# ── Save ──────────────────────────────────────────────────────────────────────
out = "IRIS_slides.pptx"
prs.save(out)
print(f"Saved: {out}")
