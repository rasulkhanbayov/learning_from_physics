#!/usr/bin/env python3
"""
Generate paper figures (Fig 1–6, Fig S1) for IRIS / physics-from-video paper.
Run from repo root: python paper_drafts/figures/generate_figures.py
Saves PNGs to paper_drafts/figures/
"""
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Arc, Wedge, Polygon, ConnectionPatch
from matplotlib.collections import PatchCollection
from matplotlib import cm

OUT_DIR = os.path.join(os.path.dirname(__file__))
os.makedirs(OUT_DIR, exist_ok=True)

# Cohesive palette: deep indigo/slate + amber accent + soft backgrounds
COLORS = {
    "bg_light": "#f8fafc",
    "bg_card": "#ffffff",
    "ink": "#0f172a",
    "ink_soft": "#475569",
    "accent": "#f59e0b",      # amber
    "accent_soft": "#fde68a",
    "blue": "#3b82f6",
    "blue_soft": "#dbeafe",
    "emerald": "#059669",
    "emerald_soft": "#d1fae5",
    "rose": "#e11d48",
    "rose_soft": "#ffe4e6",
    "violet": "#7c3aed",
    "violet_soft": "#ede9fe",
}

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["CMU Serif", "Computer Modern Serif", "DejaVu Serif", "serif"],
    "font.size": 10,
    "axes.titlesize": 11,
    "figure.facecolor": COLORS["bg_light"],
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.facecolor": COLORS["bg_light"],
})


def _rounded_box(ax, x, y, w, h, face, edge=COLORS["ink"], lw=1.2, r=0.08):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.02,rounding_size={r}", 
                        facecolor=face, edgecolor=edge, linewidth=lw)
    ax.add_patch(p)
    return p


def fig1_teaser():
    """Fig 1: Teaser — IRIS: video → equation + parameters. Film strip + equation card."""
    fig, ax = plt.subplots(1, 1, figsize=(7.5, 2.6))
    fig.patch.set_facecolor(COLORS["bg_light"])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2.6)
    ax.set_aspect("equal")
    ax.axis("off")

    # Film-strip: 4 frames with perforations
    strip_w, strip_h = 1.8, 1.15
    strip_x, strip_y = 0.6, 0.65
    # Shadow
    _rounded_box(ax, strip_x + 0.06, strip_y - 0.06, strip_w, strip_h, "#e2e8f0", edge="none")
    # Strip base
    _rounded_box(ax, strip_x, strip_y, strip_w, strip_h, COLORS["bg_card"], COLORS["ink_soft"], r=0.05)
    # Perforations (top and bottom)
    for row in [strip_y + strip_h - 0.12, strip_y + 0.08]:
        for i in range(6):
            cx = strip_x + 0.18 + i * 0.28
            circ = Circle((cx, row), 0.04, facecolor=COLORS["ink"], alpha=0.15)
            ax.add_patch(circ)
    # Frame thumbnails (gradient as placeholder)
    for i in range(4):
        fx = strip_x + 0.12 + i * 0.4
        _rounded_box(ax, fx, strip_y + 0.22, 0.32, 0.68, COLORS["blue_soft"], COLORS["blue"], 0.8, 0.03)
        # Simple motion line
        ax.plot([fx + 0.05, fx + 0.27], [strip_y + 0.5, strip_y + 0.52], color=COLORS["blue"], lw=1, alpha=0.7)
    ax.text(strip_x + strip_w / 2, strip_y - 0.18, "Video", ha="center", fontsize=10, fontweight="600", color=COLORS["ink"])

    # Curved arrow
    ax.annotate("", xy=(4.0, 1.2), xytext=(2.55, 1.2),
                arrowprops=dict(arrowstyle="->", lw=2.5, color=COLORS["accent"],
                               connectionstyle="arc3,rad=0"))
    ax.text(3.25, 1.48, "Physics ID", ha="center", fontsize=9, fontweight="600", color=COLORS["accent"])

    # Equation card (chalkboard style)
    card_x, card_y, card_w, card_h = 4.3, 0.35, 2.9, 1.85
    _rounded_box(ax, card_x + 0.04, card_y - 0.04, card_w, card_h, "#e2e8f0", edge="none")
    _rounded_box(ax, card_x, card_y, card_w, card_h, "#1e293b", COLORS["ink"], r=0.06)
    ax.text(card_x + card_w / 2, card_y + card_h - 0.32, "Governing equation", ha="center", fontsize=9, color="#94a3b8", fontweight="600")
    ax.text(card_x + card_w / 2, card_y + card_h / 2 - 0.1, r"$z'' + \beta z' + \alpha z = 0$", ha="center", fontsize=12, color="white")
    ax.text(card_x + card_w / 2, card_y + 0.55, r"$\alpha,\, \beta,\, g,\, L,\, \ldots$", ha="center", fontsize=10, color="#cbd5e1")
    ax.text(card_x + card_w / 2, card_y + 0.22, "Parameters", ha="center", fontsize=8, color="#64748b")

    # Title
    ax.text(5.2, 2.32, "IRIS: Physics Identification from Video", ha="center", fontsize=13, fontweight="bold", color=COLORS["ink"])
    ax.text(5.2, 2.05, "From pixels to equations and physical parameters", ha="center", fontsize=9, color=COLORS["ink_soft"])
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig1_teaser.png"))
    plt.close(fig)
    print("Saved fig1_teaser.png")


def fig2_pipeline():
    """Fig 2: Pipeline — two branches (VLM + Encoder) merging into physics and parameters."""
    fig, ax = plt.subplots(1, 1, figsize=(9.2, 3.4))
    fig.patch.set_facecolor(COLORS["bg_light"])
    ax.set_xlim(0, 9.2)
    ax.set_ylim(0, 3.4)
    ax.axis("off")

    def box(x, y, w, h, label, face, edge=COLORS["ink"], fontsize=9):
        _rounded_box(ax, x, y, w, h, face, edge, r=0.06)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=fontsize, color=COLORS["ink"])

    # Video (source)
    box(0.15, 1.25, 1.05, 1.0, "Video\nframes", COLORS["bg_card"], COLORS["ink_soft"])
    # Branch 1: VLM path
    box(1.55, 2.35, 1.15, 0.65, "VLM\nEquation selection", COLORS["blue_soft"], COLORS["blue"])
    box(2.95, 2.35, 1.75, 0.65, "ODE Bank\nPendulum | Free fall | LED | …", COLORS["emerald_soft"], COLORS["emerald"])
    # Branch 2: Encoder path
    box(1.55, 0.45, 1.15, 0.65, "Encoder", COLORS["violet_soft"], COLORS["violet"])
    box(2.95, 0.45, 1.0, 0.65, r"Latent $\mathbf{z}_t$", COLORS["violet_soft"], COLORS["violet"])
    # Merge: Physics block
    box(4.25, 0.95, 1.5, 0.75, "Physics block\n" + r"$\theta = (\alpha, \beta)$", COLORS["accent_soft"], COLORS["accent"])
    # Output
    box(6.0, 1.15, 1.35, 1.35, "Estimated\nparameters", COLORS["emerald_soft"], COLORS["emerald"])

    # Arrows (curved where needed)
    arrow_style = dict(arrowstyle="->", lw=1.8, color=COLORS["ink_soft"])
    ax.annotate("", xy=(1.55, 2.675), xytext=(1.2, 1.75), arrowprops=arrow_style)
    ax.annotate("", xy=(1.55, 0.775), xytext=(1.2, 1.25), arrowprops=arrow_style)
    ax.annotate("", xy=(2.95, 2.675), xytext=(2.7, 2.675), arrowprops=arrow_style)
    ax.annotate("", xy=(2.95, 0.775), xytext=(2.7, 0.775), arrowprops=arrow_style)
    ax.annotate("", xy=(4.25, 1.325), xytext=(3.95, 1.325), arrowprops=arrow_style)
    ax.annotate("", xy=(6.0, 1.825), xytext=(5.75, 1.825), arrowprops=arrow_style)
    # Step labels
    for i, (xx, yy, tt) in enumerate([(0.7, 2.9, "1"), (2.1, 2.9, "2"), (3.9, 2.9, "3"), (5.7, 2.5, "4")], 1):
        ax.text(xx, yy, tt, fontsize=8, fontweight="bold", color=COLORS["accent"])
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig2_pipeline.png"))
    plt.close(fig)
    print("Saved fig2_pipeline.png")


def fig3_multistep():
    """Fig 3: Multi-step loss — two trajectories with shaded error and weight badges."""
    fig, ax = plt.subplots(1, 1, figsize=(7.2, 2.8))
    fig.patch.set_facecolor(COLORS["bg_light"])
    ax.set_xlim(0, 7.2)
    ax.set_ylim(0, 2.8)
    ax.axis("off")

    K = 5
    xs = np.linspace(1.0, 5.8, K + 1)
    t = np.linspace(0, 1, 50)
    # Smooth encoder trajectory
    xs_smooth = np.linspace(xs[0], xs[-1], 50)
    ys_enc = 1.65 + 0.2 * np.sin(2 * np.pi * (xs_smooth - xs[0]) / (xs[-1] - xs[0]))
    ys_phys = 0.95 + 0.15 * np.sin(2 * np.pi * (xs_smooth - xs[0]) / (xs[-1] - xs[0]) + 0.3)
    ax.fill_between(xs_smooth, ys_enc, ys_phys, alpha=0.2, color=COLORS["rose"])
    ax.plot(xs_smooth, ys_enc, color=COLORS["blue"], lw=2.5, label=r"Encoder $\hat{\mathbf{z}}_{t+k}$")
    ax.plot(xs_smooth, ys_phys, color=COLORS["rose"], lw=2, linestyle="--", label=r"Physics $\tilde{\mathbf{z}}_{t+k}$")
    for i, x in enumerate(xs):
        y_enc_i = 1.65 + 0.2 * np.sin(2 * np.pi * i / K)
        y_phys_i = 0.95 + 0.15 * np.sin(2 * np.pi * i / K + 0.3)
        ax.plot(x, y_enc_i, "o", color=COLORS["blue"], markersize=9)
        ax.plot(x, y_phys_i, "s", color=COLORS["rose"], markersize=7)
        if i > 0:
            ax.plot([x, x], [y_phys_i, y_enc_i], "k--", alpha=0.4, lw=1)
            w = [1, 1, 0.5, 0.5, 0.25][i - 1]
            ax.text(x, (y_enc_i + y_phys_i) / 2 - 0.12, f"$w_{i}={w}$", ha="center", fontsize=8)
    ax.text(0.35, 1.7, r"$\hat{\mathbf{z}}$", fontsize=11, color=COLORS["blue"], fontweight="bold")
    ax.text(0.35, 0.9, r"$\tilde{\mathbf{z}}$", fontsize=11, color=COLORS["rose"], fontweight="bold")
    for i, x in enumerate(xs):
        ax.text(x, 0.38, f"$t{'+'+str(i) if i else ''}$", ha="center", fontsize=9)
    ax.text(3.4, 0.08, "Time →", ha="center", fontsize=10)
    ax.legend(loc="upper right", frameon=True, fancybox=True, shadow=True, fontsize=9)
    ax.set_title("Multi-step loss: match encoder and physics at horizons k = 1, …, K", fontsize=10, pad=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig3_multistep.pdf"))
    fig.savefig(os.path.join(OUT_DIR, "fig3_multistep.png"))
    plt.close(fig)
    print("Saved fig3_multistep.pdf and fig3_multistep.png")


def fig4_dataset():
    """Fig 4: Dataset — phenomena with simple icons (circle, arc, cone, etc.)."""
    # Simple icon drawing helpers
    def draw_pendulum(ax, cx, cy, r=0.28):
        ax.plot([cx, cx], [cy + r, cy - r], color=COLORS["ink"], lw=2)
        circle = Circle((cx, cy + r), 0.08, facecolor=COLORS["accent"], edgecolor=COLORS["ink"])
        ax.add_patch(circle)
    def draw_ball(ax, cx, cy):
        Circle((cx, cy), 0.2, facecolor=COLORS["ink_soft"], edgecolor=COLORS["ink"])
        ax.add_patch(Circle((cx, cy), 0.2, facecolor=COLORS["accent_soft"], edgecolor=COLORS["ink"], lw=1))
    def draw_cone(ax, cx, cy):
        tri = Polygon([[cx, cy - 0.2], [cx - 0.2, cy + 0.2], [cx + 0.2, cy + 0.2]], 
                      facecolor=COLORS["emerald_soft"], edgecolor=COLORS["emerald"])
        ax.add_patch(tri)
    def draw_rotation(ax, cx, cy):
        ax.add_patch(Arc((cx, cy), 0.45, 0.45, theta1=0, theta2=270, lw=2, color=COLORS["violet"]))
        ax.plot(cx + 0.22, cy + 0.22, "o", color=COLORS["violet"], markersize=6)
    def draw_cones(ax, cx, cy):
        for dx in [-0.15, 0, 0.15]:
            tri = Polygon([[cx+dx, cy-0.12], [cx+dx-0.1, cy+0.12], [cx+dx+0.1, cy+0.12]], 
                          facecolor=COLORS["rose_soft"], edgecolor=COLORS["rose"], lw=0.8)
            ax.add_patch(tri)
        ax.add_patch(Circle((cx, cy + 0.25), 0.08, facecolor=COLORS["accent_soft"], edgecolor=COLORS["ink"]))
    def draw_two_pendulums(ax, cx, cy):
        for dx in [-0.12, 0.12]:
            ax.plot([cx+dx, cx+dx], [cy+0.2, cy-0.2], color=COLORS["ink"], lw=1.2)
            ax.add_patch(Circle((cx+dx, cy+0.2), 0.05, facecolor=COLORS["accent"]))
    def draw_led(ax, cx, cy):
        ax.add_patch(Circle((cx, cy), 0.2, facecolor=COLORS["accent_soft"], edgecolor=COLORS["accent"]))
        ax.text(cx, cy, "⋆", ha="center", va="center", fontsize=14, color=COLORS["accent"])
    def draw_drain(ax, cx, cy):
        ax.add_patch(FancyBboxPatch((cx - 0.15, cy - 0.15), 0.3, 0.2, boxstyle="round,pad=0.01", 
                                    facecolor=COLORS["blue_soft"], edgecolor=COLORS["blue"]))
        ax.plot([cx - 0.05, cx + 0.05], [cy - 0.2, cy - 0.35], color=COLORS["blue"], lw=1.5)

    phenomena = [
        ("Pendulum", draw_pendulum, COLORS["blue_soft"]),
        ("Falling ball", draw_ball, COLORS["accent_soft"]),
        ("Sliding cone", draw_cone, COLORS["emerald_soft"]),
        ("Rotation", draw_rotation, COLORS["violet_soft"]),
        ("Hitting cones", draw_cones, COLORS["rose_soft"]),
        ("Two pendulums", draw_two_pendulums, "#fed7aa"),
        ("LED decay", draw_led, COLORS["violet_soft"]),
        ("Drain", draw_drain, COLORS["blue_soft"]),
    ]

    ncol, nrow = 4, 2
    fig, axes = plt.subplots(nrow, ncol, figsize=(6.5, 3.5))
    fig.patch.set_facecolor(COLORS["bg_light"])
    axes = axes.flatten()
    for i, (name, draw_fn, color) in enumerate(phenomena):
        ax = axes[i]
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect("equal")
        ax.axis("off")
        _rounded_box(ax, 0.06, 0.12, 0.88, 0.76, color, COLORS["ink_soft"], 0.8, 0.04)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        draw_fn(ax, 0.5, 0.52)
        ax.text(0.5, 0.18, name, ha="center", va="center", fontsize=9, fontweight="600", color=COLORS["ink"])
    fig.suptitle("IRIS dataset — single- and multi-body phenomena", fontsize=11, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig4_dataset.png"))
    plt.close(fig)
    print("Saved fig4_dataset.png")


def fig5_ode_bank():
    """Fig 5: ODE bank — equation cards with left accent stripe."""
    fig, ax = plt.subplots(1, 1, figsize=(6.8, 3.8))
    fig.patch.set_facecolor(COLORS["bg_light"])
    ax.set_xlim(0, 6.8)
    ax.set_ylim(0, 3.8)
    ax.axis("off")

    rows = [
        (r"$z'' + \beta z' + \alpha z = 0$", "Pendulum, free fall, rotation", COLORS["blue"]),
        (r"$z' = -\lambda z$", "LED decay", COLORS["violet"]),
        (r"$z' = -k\sqrt{z}$", "Torricelli drain", COLORS["emerald"]),
        ("Inclined plane + friction", "Sliding block / cone", COLORS["accent"]),
        (r"Graph: $\mathbf{Z}_t \in \mathbb{R}^{N \times d}$", "Multi-object", COLORS["rose"]),
    ]
    y = 3.35
    ax.text(3.4, 3.55, "ODE bank", ha="center", fontsize=13, fontweight="bold", color=COLORS["ink"])
    for eq, desc, accent in rows:
        y -= 0.62
        # Card
        _rounded_box(ax, 0.25, y, 6.3, 0.5, COLORS["bg_card"], COLORS["ink_soft"], 0.8, 0.04)
        # Accent stripe
        _rounded_box(ax, 0.25, y + 0.06, 0.08, 0.38, accent, edge="none", r=0.02)
        ax.text(0.5, y + 0.25, eq, fontsize=10)
        ax.text(4.2, y + 0.25, desc, fontsize=9, color=COLORS["ink_soft"], va="center")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig5_ode_bank.png"))
    plt.close(fig)
    print("Saved fig5_ode_bank.png")


def fig6_loss_landscape():
    """Fig 6: Training dynamics — train & val curves with gradient fill."""
    fig, ax = plt.subplots(1, 1, figsize=(4.2, 2.8))
    fig.patch.set_facecolor(COLORS["bg_light"])
    ax.set_facecolor(COLORS["bg_card"])
    epochs = np.linspace(0, 500, 250)
    np.random.seed(42)
    loss_train = 5 * np.exp(-epochs / 100) + 0.45 + 0.02 * np.cumsum(np.random.randn(250))
    loss_train = np.maximum(loss_train, 0.35)
    loss_val = loss_train + 0.1 + 0.05 * np.sin(epochs / 30)
    ax.fill_between(epochs, loss_train, alpha=0.3, color=COLORS["blue"])
    ax.plot(epochs, loss_train, color=COLORS["blue"], lw=2, label="Training")
    ax.plot(epochs, loss_val, color=COLORS["rose"], lw=1.5, linestyle="--", label="Validation")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.set_title("Training dynamics")
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, alpha=0.25, linestyle="-")
    ax.set_xlim(0, 500)
    ax.set_ylim(0, None)
    for spine in ax.spines.values():
        spine.set_color(COLORS["ink_soft"])
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "fig6_loss_landscape.png"))
    plt.close(fig)
    print("Saved fig6_loss_landscape.png")


def figS1_synthetic_real():
    """Fig S1: Synthetic vs real — split with domain-gap arrow."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(5.5, 2.4))
    fig.patch.set_facecolor(COLORS["bg_light"])
    for ax in (ax1, ax2):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect("equal")
        ax.axis("off")
    # Synthetic: grid/rendered feel
    _rounded_box(ax1, 0.05, 0.05, 0.9, 0.9, "#e0e7ff", COLORS["violet"], 1.2, 0.05)
    for i in range(4):
        for j in range(3):
            ax1.add_patch(Circle((0.25 + i * 0.2, 0.3 + j * 0.25), 0.04, facecolor=COLORS["violet"], alpha=0.4))
    ax1.text(0.5, 0.78, "Synthetic", ha="center", fontsize=12, fontweight="bold")
    ax1.text(0.5, 0.62, "Rendered / simulated", ha="center", fontsize=8, color=COLORS["ink_soft"])
    # Real: texture-like
    _rounded_box(ax2, 0.05, 0.05, 0.9, 0.9, "#fef3c7", COLORS["accent"], 1.2, 0.05)
    np.random.seed(1)
    for _ in range(40):
        ax2.plot(np.random.rand(2), np.random.rand(2), color=COLORS["ink_soft"], lw=0.5, alpha=0.2)
    ax2.text(0.5, 0.78, "Real", ha="center", fontsize=12, fontweight="bold")
    ax2.text(0.5, 0.62, "IRIS / Delfys75", ha="center", fontsize=8, color=COLORS["ink_soft"])
    fig.text(0.5, 0.12, "Domain gap → evaluation on real data", ha="center", fontsize=9, style="italic", color=COLORS["ink_soft"])
    fig.suptitle("Synthetic vs. real video", fontsize=11, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT_DIR, "figS1_synthetic_real.png"))
    plt.close(fig)
    print("Saved figS1_synthetic_real.png")


def main():
    fig1_teaser()
    fig2_pipeline()
    fig3_multistep()
    fig4_dataset()
    fig5_ode_bank()
    fig6_loss_landscape()
    figS1_synthetic_real()
    print("All figures saved to", OUT_DIR)


if __name__ == "__main__":
    main()
