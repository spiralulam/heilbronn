"""
Smallest Triangle Finder  –  Heilbronn edition
- Points start at best-known Heilbronn configurations (n=3..16)
- Drag any point with the mouse
- The smallest-area triangle among all triples is highlighted
- Use the spinbox to switch n (resets to the best-known config)
"""

import tkinter as tk
import math
import itertools
from PIL import Image, ImageDraw, ImageTk

# ── constants ──────────────────────────────────────────────────────────────────
CANVAS_SIZE   = 600
PADDING       = 40
POINT_RADIUS  = 8
BG_COLOR      = "#ffffff"
GRID_COLOR    = "#e0e0e0"
POINT_COLOR   = "#333333"
POINT_HOVER   = "#000000"
TEXT_COLOR    = "#666666"
LABEL_COLOR   = "#222222"

# matplotlib tab10 palette (C0–C9) — matches the paper figures
TAB10 = [
    "#1f77b4",  # C0  blue
    "#ff7f0e",  # C1  orange
    "#2ca02c",  # C2  green
    "#d62728",  # C3  red
    "#9467bd",  # C4  purple
    "#8c564b",  # C5  brown
    "#e377c2",  # C6  pink
    "#7f7f7f",  # C7  gray
    "#bcbd22",  # C8  olive
    "#17becf",  # C9  cyan
]

TRI_ALPHA     = 64     # 0–255, triangle fill opacity (25 %)
TRI_OUTLINE_A = 200    # outline opacity
HEILBRONN_CONFIGS = {
    3:  [[0,0],[1,0],[0,1]],
    4:  [[0,0],[1,0],[1,1],[0,1]],
    5:  [[0,0.333333],[0.577350,0],[1,0.422650],[0.666667,1],[0,1]],
    6:  [[0,0],[0.5,0],[1,0.5],[0.5,1],[0,0.5],[1,1]],
    7:  [[0,0],[0.819173,0],[1,0.287258],[0.864809,1],[0,1],
         [0.416141,0.287258],[0.507413,0.806063]],
    8:  [[0,0],[0.767592,0],[1,0.188580],[1,1],[0,0.811420],
         [0.232408,1],[0.232408,0.377161],[0.767592,0.622839]],
    9:  [[0,0.193774],[0.173444,0],[1,0.260165],[0.173444,1],[0,0.826556],
         [0.653113,0.346887],[0.739835,0],[0.806226,1],[1,0.826556]],
    10: [[0.157806,0],[0.747613,0],[0,0.157806],[1,0.252387],
         [0.684389,0.315611],[0.315611,0.684389],[0,0.747613],
         [1,0.842194],[0.252387,1],[0.842194,1]],
    11: [[0.333333,0],[0.666667,0],[0,0.222222],[1,0.222222],
         [0.333333,0.444444],[0.666667,0.444444],[0,0.666667],[1,0.666667],
         [0.5,0.777778],[0.166667,1],[0.833333,1]],
    12: [[0.115354,0],[0.884646,0],[0,0.115354],[1,0.115354],
         [0.5,0.180552],[0.180552,0.5],[0.819448,0.5],[0.5,0.819448],
         [0,0.884646],[1,0.884646],[0.115354,1],[0.884646,1]],
    13: [[0.964815,0.08763],[0,1],[0.896939,0.902546],[0.761346,0.441996],
         [0.655161,1],[0.748551,0],[0,0.09925],[1,0.461332],
         [0.32849,0.633357],[0.087939,0.614507],[0.345014,0.901507],
         [0.087938,0],[0.500181,0.149235]],
    14: [[0.07762,0],[0.92238,1],[0.92238,0],[0.07762,1],
         [0,0.186886],[1,0.813114],[1,0.186886],[0,0.813114],
         [0.292333,0.321345],[0.707667,0.678655],[0.707667,0.321345],
         [0.292333,0.678655],[0.5,0.138278],[0.5,0.861722]],
    15: [[0.934094,1],[0.287119,0.302829],[0.342286,0.701349],[0.963064,0.09573],
         [0.06663,0.633568],[0.648909,0],[0.277707,1],[0.066641,0],
         [0.589972,0.272487],[0.603055,0.928222],[0.895664,0.68429],
         [0,0.192215],[0.670814,0.614942],[0,0.924975],[1,0.399875]],
    16: [[0.064516,0],[0.935484,1],[0.741935,0],[0.258065,1],
         [0,0.303030],[1,0.696970],[1,0.060606],[0,0.939394],
         [0.258065,0.363636],[0.741935,0.636364],[0.322581,0.060606],
         [0.677419,0.939394],[0.677419,0.303030],[0.322581,0.696970],
         [0.935484,0.363636],[0.064516,0.636364]],
}

DELTA_N = {
    3:0.5, 4:0.5, 5:0.19245, 6:0.125, 7:0.08386, 8:0.07238,
    9:0.05488, 10:0.04654, 11:0.03704, 12:0.03260, 13:0.027,
    14:0.0243, 15:0.0211, 16:0.02053,
}

# ── coordinate helpers ─────────────────────────────────────────────────────────
def to_canvas(x, y):
    cx = PADDING + x * (CANVAS_SIZE - 2 * PADDING)
    cy = CANVAS_SIZE - PADDING - y * (CANVAS_SIZE - 2 * PADDING)
    return cx, cy

def to_unit(cx, cy):
    x = (cx - PADDING) / (CANVAS_SIZE - 2 * PADDING)
    y = (CANVAS_SIZE - PADDING - cy) / (CANVAS_SIZE - 2 * PADDING)
    return max(0.0, min(1.0, x)), max(0.0, min(1.0, y))

# ── geometry ───────────────────────────────────────────────────────────────────
def triangle_area(p1, p2, p3):
    return abs(
        (p2[0] - p1[0]) * (p3[1] - p1[1]) -
        (p3[0] - p1[0]) * (p2[1] - p1[1])
    ) / 2.0

AREA_THRESHOLD = 1e-4   # areas within this tolerance are considered equal

def find_all_smallest_triangles(points):
    """Return (min_area, [(i,j,k), ...]) for all triangles tied at the minimum.
    Returns (None, []) if no non-degenerate triangle exists."""
    min_area   = None
    candidates = []
    for i, j, k in itertools.combinations(range(len(points)), 3):
        a = triangle_area(points[i], points[j], points[k])
        if a < 1e-12:           # degenerate / collinear — skip
            continue
        if min_area is None or a < min_area - AREA_THRESHOLD:
            min_area   = a
            candidates = [(i, j, k)]
        elif abs(a - min_area) <= AREA_THRESHOLD:
            candidates.append((i, j, k))
    return min_area, candidates

def default_points(n):
    return [list(p) for p in HEILBRONN_CONFIGS[n]]

# ── main application ───────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smallest Triangle Finder  –  Heilbronn")
        self.resizable(False, False)
        self.configure(bg=BG_COLOR)

        self.points   = default_points(6)
        self.dragging = None
        self.hover    = None

        self._build_ui()
        self._bind_events()
        self._redraw()

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        top = tk.Frame(self, bg=BG_COLOR, pady=8, padx=12)
        top.pack(fill="x")

        self.heading = tk.Label(top, text="Smallest Triangle Finder",
                 font=("Courier", 15, "bold"),
                 fg=LABEL_COLOR, bg=BG_COLOR)
        self.heading.pack(side="left")

        ctrl = tk.Frame(top, bg=BG_COLOR)
        ctrl.pack(side="right")

        tk.Label(ctrl, text="Points:", font=("Courier", 11),
                 fg=TEXT_COLOR, bg=BG_COLOR).pack(side="left", padx=(0, 6))

        self.n_var = tk.IntVar(value=len(self.points))
        spin = tk.Spinbox(
            ctrl, from_=3, to=16, width=4,
            textvariable=self.n_var,
            font=("Courier", 11), justify="center",
            bg="#f0f0f0", fg=LABEL_COLOR,
            buttonbackground="#d0d0d0",
            relief="flat", bd=0,
            highlightthickness=1, highlightcolor="#1f77b4",
            command=self._on_n_change
        )
        spin.pack(side="left")
        spin.bind("<Return>", lambda _: self._on_n_change())

        self.canvas = tk.Canvas(
            self, width=CANVAS_SIZE, height=CANVAS_SIZE,
            bg=BG_COLOR, highlightthickness=0
        )
        self.canvas.pack(padx=12, pady=(0, 4))

        self.status = tk.Label(
            self, text="", font=("Courier", 10),
            fg=TEXT_COLOR, bg=BG_COLOR, anchor="w", padx=14
        )
        self.status.pack(fill="x", pady=(0, 8))

    # ── events ─────────────────────────────────────────────────────────────────
    def _bind_events(self):
        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Motion>",          self._on_motion)

    def _hit_test(self, cx, cy):
        for i, (ux, uy) in enumerate(self.points):
            px, py = to_canvas(ux, uy)
            if math.hypot(cx - px, cy - py) <= POINT_RADIUS + 4:
                return i
        return None

    def _on_press(self, e):
        self.dragging = self._hit_test(e.x, e.y)

    def _on_drag(self, e):
        if self.dragging is not None:
            self.points[self.dragging] = list(to_unit(e.x, e.y))
            self._redraw()

    def _on_release(self, e):
        self.dragging = None

    def _on_motion(self, e):
        idx = self._hit_test(e.x, e.y)
        if idx != self.hover:
            self.hover = idx
            self.canvas.config(cursor="hand2" if idx is not None else "")
            self._redraw()

    def _on_n_change(self):
        try:
            n = int(self.n_var.get())
        except ValueError:
            return
        n = max(3, min(16, n))
        self.n_var.set(n)
        self.points = default_points(n)
        self._redraw()

    # ── drawing ────────────────────────────────────────────────────────────────
    def _redraw(self):
        c = self.canvas
        c.delete("all")

        # grid
        steps = 10
        for i in range(steps + 1):
            t = i / steps
            x0, y0 = to_canvas(t, 0); x1, y1 = to_canvas(t, 1)
            c.create_line(x0, y0, x1, y1, fill=GRID_COLOR, width=1)
            x0, y0 = to_canvas(0, t); x1, y1 = to_canvas(1, t)
            c.create_line(x0, y0, x1, y1, fill=GRID_COLOR, width=1)

        # axis tick labels
        for i in range(steps + 1):
            t = i / steps
            lx, ly = to_canvas(t, 0)
            c.create_text(lx, ly + 14, text=f"{t:.1f}",
                          font=("Courier", 7), fill=GRID_COLOR)
            lx, ly = to_canvas(0, t)
            c.create_text(lx - 18, ly, text=f"{t:.1f}",
                          font=("Courier", 7), fill=GRID_COLOR)

        # smallest triangles — rendered via Pillow for true alpha (supersampled)
        area, triangles = find_all_smallest_triangles(self.points)
        tri_indices = set()
        tri_colors = {}   # point index → first triangle color it appears in
        if triangles:
            # render at 3× resolution for crisp anti-aliased edges
            SS = 3
            hi = CANVAS_SIZE * SS
            overlay = Image.new("RGBA", (hi, hi), (0, 0, 0, 0))
            for ti, (i, j, k) in enumerate(triangles):
                col = TAB10[ti % len(TAB10)]
                r, g, b = int(col[1:3], 16), int(col[3:5], 16), int(col[5:7], 16)
                for idx in (i, j, k):
                    if idx not in tri_colors:
                        tri_colors[idx] = col
                tri_indices |= {i, j, k}
                pts = [
                    (int(round(to_canvas(*self.points[v])[0] * SS)),
                     int(round(to_canvas(*self.points[v])[1] * SS)))
                    for v in (i, j, k)
                ]
                layer = Image.new("RGBA", (hi, hi), (0, 0, 0, 0))
                ld = ImageDraw.Draw(layer)
                ld.polygon(pts, fill=(r, g, b, TRI_ALPHA),
                           outline=(r, g, b, TRI_OUTLINE_A), width=2 * SS)
                overlay = Image.alpha_composite(overlay, layer)
            # composite onto white, downsample with Lanczos
            bg_img = Image.new("RGBA", (hi, hi), (255, 255, 255, 255))
            bg_img = Image.alpha_composite(bg_img, overlay)
            bg_img = bg_img.resize((CANVAS_SIZE, CANVAS_SIZE), Image.LANCZOS)
            self._tri_photo = ImageTk.PhotoImage(bg_img)
            c.create_image(0, 0, anchor="nw", image=self._tri_photo)
            # re-draw grid on top so it's visible through light fills
            for gi in range(steps + 1):
                t = gi / steps
                x0, y0 = to_canvas(t, 0); x1, y1 = to_canvas(t, 1)
                c.create_line(x0, y0, x1, y1, fill=GRID_COLOR, width=1)
                x0, y0 = to_canvas(0, t); x1, y1 = to_canvas(1, t)
                c.create_line(x0, y0, x1, y1, fill=GRID_COLOR, width=1)

            n   = len(self.points)
            ref = DELTA_N.get(n, 0)
            count = len(triangles)
            self.heading.config(
                text=f"Smallest Triangle{'s' if count > 1 else ''} ({count}):  A = {area:.6f}"
            )
            self.status.config(
                text=f"  best known δ = {ref}"
            )
        else:
            self.heading.config(text="Smallest Triangle Finder")
            self.status.config(text="  All points are collinear — no triangle.")

        # points
        for idx, (ux, uy) in enumerate(self.points):
            px, py = to_canvas(ux, uy)
            is_tri  = idx in tri_indices
            is_hov  = idx == self.hover
            is_drag = idx == self.dragging

            color = POINT_HOVER if (is_hov or is_drag) else POINT_COLOR
            r = POINT_RADIUS + (2 if is_drag else 0)
            c.create_oval(px - r, py - r, px + r, py + r,
                          fill=color,
                          outline="#999999" if is_hov else BG_COLOR, width=2)

            c.create_text(px + POINT_RADIUS + 10, py - POINT_RADIUS - 2,
                          text=f"P{idx+1}", font=("Courier", 9),
                          fill=tri_colors.get(idx, TEXT_COLOR) if is_tri else TEXT_COLOR)

        # tooltip for hovered or dragged point
        tip_idx = self.dragging if self.dragging is not None else self.hover
        if tip_idx is not None:
            ux, uy = self.points[tip_idx]
            px, py = to_canvas(ux, uy)
            label  = f"P{tip_idx+1}  ({ux:.4f}, {uy:.4f})"
            pad    = 5
            tw     = len(label) * 6 + pad * 2   # approximate text width
            th     = 14 + pad * 2
            # position: prefer right of point, flip if too close to edge
            tx = px + POINT_RADIUS + 14
            if tx + tw > CANVAS_SIZE - PADDING // 2:
                tx = px - POINT_RADIUS - 14 - tw
            ty = py - POINT_RADIUS - 14
            if ty - th < 0:
                ty = py + POINT_RADIUS + 14
            c.create_rectangle(tx - pad, ty - th // 2 - pad,
                                tx + tw - pad, ty + th // 2,
                                fill="#f5f5f5", outline="#999999", width=1)
            c.create_text(tx + tw // 2 - pad, ty - pad // 2,
                          text=label, font=("Courier", 9),
                          fill=LABEL_COLOR)

    @staticmethod
    def _blend(hex_color, alpha):
        """Blend hex_color toward white by (1-alpha)."""
        bg = (255, 255, 255)
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r2 = int(r * alpha + bg[0] * (1 - alpha))
        g2 = int(g * alpha + bg[1] * (1 - alpha))
        b2 = int(b * alpha + bg[2] * (1 - alpha))
        return f"#{r2:02x}{g2:02x}{b2:02x}"

# ── entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
