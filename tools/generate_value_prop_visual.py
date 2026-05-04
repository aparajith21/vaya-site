#!/usr/bin/env python3
"""
Reproducible marketing illustration (not app screenshots).

Communicates in one frame: local / nearby, meeting people, spontaneous timing,
light social fun — aligned with Vaya’s coral palette.

Usage:
    python3 tools/generate_value_prop_visual.py

Output:
    assets/site/value-prop-explainer.png

Requires Pillow (same as scripts/generate_appstore_previews.py).
"""

from __future__ import annotations

import math
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Pillow is required. Install it with: python3 -m pip install Pillow"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "assets" / "site" / "value-prop-explainer.png"

# Brand-adjacent palette (matches landing gradients)
ORANGE = (255, 90, 61)
ORANGE_MID = (255, 122, 69)
PEACH = (255, 177, 153)
CREAM = (255, 246, 242)
WHITE = (255, 255, 255)
INK = (28, 32, 42)
INK_SOFT = (80, 88, 108)

WIDTH, HEIGHT = 1920, 1080


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/SFNSMono.ttf",
        (
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
            if bold
            else "/System/Library/Fonts/Supplemental/Arial.ttf"
        ),
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def diagonal_gradient(size: tuple[int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(h):
        for x in range(w):
            # Warm diagonal sweep (deterministic)
            t = (x / max(1, w - 1) * 0.45 + y / max(1, h - 1) * 0.55)
            if t < 0.5:
                u = t / 0.5
                c = tuple(round(ORANGE[i] + (ORANGE_MID[i] - ORANGE[i]) * u) for i in range(3))
            else:
                u = (t - 0.5) / 0.5
                c = tuple(round(ORANGE_MID[i] + (PEACH[i] - ORANGE_MID[i]) * u) for i in range(3))
            px[x, y] = c
    return img


def draw_soft_grid_overlay(size: tuple[int, int]) -> Image.Image:
    """Light diagonal grid suggesting a neighborhood map."""
    w, h = size
    grid = Image.new("RGBA", size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(grid)
    stroke = (255, 255, 255, 36)
    spacing = 72
    for x in range(-spacing, w + spacing, spacing):
        gd.line([(x, 0), (x + h // 3, h)], fill=stroke, width=1)
    for y in range(-spacing, h + spacing, spacing):
        gd.line([(0, y), (w, y + w // 5)], fill=stroke, width=1)
    return grid


def draw_pin(
    layer: Image.Image,
    cx: int,
    cy: int,
    scale: int,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int],
) -> None:
    draw = ImageDraw.Draw(layer)
    r = scale // 2
    body_top = cy - scale
    draw.ellipse([cx - r, body_top, cx + r, body_top + 2 * r], fill=fill, outline=outline, width=3)
    tip_y = cy + int(scale * 0.35)
    half_w = int(scale * 0.62)
    shoulder_y = body_top + int(1.55 * r)
    draw.polygon(
        [(cx, tip_y), (cx - half_w, shoulder_y), (cx + half_w, shoulder_y)],
        fill=fill,
        outline=outline,
    )


def draw_avatar_cluster(layer: Image.Image, cx: int, cy: int, radius: int) -> None:
    fills = [
        (*WHITE[:3], 235),
        (*CREAM[:3], 228),
        (*WHITE[:3], 215),
    ]
    offsets = [(-52, 18), (52, 18), (0, -42)]
    for i, (dx, dy) in enumerate(offsets):
        bbox = [
            cx + dx - radius,
            cy + dy - radius,
            cx + dx + radius,
            cy + dy + radius,
        ]
        overlay = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.ellipse(bbox, fill=fills[i], outline=(*WHITE[:3], 200), width=3)
        layer.alpha_composite(overlay)


def draw_simple_faces_hint(layer: Image.Image, cx: int, cy: int, radius: int) -> None:
    """Minimal arcs suggesting smiles inside avatar circles."""
    draw = ImageDraw.Draw(layer)
    positions = [(-52, 18), (52, 18), (0, -42)]
    for dx, dy in positions:
        ox, oy = cx + dx, cy + dy
        eye_r = max(6, radius // 11)
        draw.ellipse([ox - radius // 4 - eye_r, oy - eye_r // 2, ox - radius // 4 + eye_r, oy + eye_r * 3 // 2], fill=INK_SOFT)
        draw.ellipse([ox + radius // 4 - eye_r, oy - eye_r // 2, ox + radius // 4 + eye_r, oy + eye_r * 3 // 2], fill=INK_SOFT)
        draw.arc(
            [ox - radius // 2, oy, ox + radius // 2, oy + radius],
            start=200,
            end=340,
            fill=INK_SOFT,
            width=4,
        )


def draw_clock_badge(layer: Image.Image, cx: int, cy: int, r: int) -> None:
    """Small clock icon = spontaneous / starting soon."""
    draw = ImageDraw.Draw(layer)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*WHITE[:3], 230), outline=(*WHITE[:3], 255), width=4)
    # Hands pointing ~ “soon” (~10:50 aesthetic)
    for angle_deg, length in [(60, int(r * 0.42)), (210, int(r * 0.55))]:
        rad = math.radians(angle_deg - 90)
        x2 = cx + int(length * math.cos(rad))
        y2 = cy + int(length * math.sin(rad))
        draw.line([(cx, cy), (x2, y2)], fill=INK, width=6)


def draw_sparkles(draw: ImageDraw.ImageDraw, centers: list[tuple[int, int]]) -> None:
    for sx, sy in centers:
        for rot in (0, 45):
            pts: list[tuple[float, float]] = []
            arm = 14.0
            for k in range(4):
                ang = math.radians(rot + k * 90)
                pts.append((sx + arm * math.cos(ang), sy + arm * math.sin(ang)))
                mid = math.radians(rot + k * 90 + 45)
                pts.append((sx + arm * 0.35 * math.cos(mid), sy + arm * 0.35 * math.sin(mid)))
            draw.polygon([(int(round(p[0])), int(round(p[1]))) for p in pts], fill=CREAM)


def draw_curved_connector(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]]) -> None:
    """Soft dashed curve through pin anchors suggesting routes/nearby links."""
    if len(points) < 2:
        return
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        steps = 48
        prev = (x1, y1)
        for s in range(1, steps + 1):
            t = s / steps
            mx = x1 + (x2 - x1) * t
            my = y1 + (y2 - y1) * t + int(70 * math.sin(math.pi * t))
            if s % 6 == 0:
                draw.line([prev, (mx, my)], fill=(255, 255, 255, 130), width=8)
            prev = (mx, my)


def compose() -> Image.Image:
    base = diagonal_gradient((WIDTH, HEIGHT)).convert("RGBA")
    base.alpha_composite(draw_soft_grid_overlay((WIDTH, HEIGHT)))

    draw = ImageDraw.Draw(base)

    # Anchor positions for narrative: pins around a gathering (deterministic layout)
    pin_positions = [
        (WIDTH * 22 // 100, HEIGHT * 34 // 100),
        (WIDTH * 76 // 100, HEIGHT * 38 // 100),
        (WIDTH * 52 // 100, HEIGHT * 72 // 100),
        (WIDTH * 42 // 100, HEIGHT * 22 // 100),
    ]

    overlay_pins = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    pin_colors_fill = [(255, 108, 82), (255, 138, 96), (255, 194, 168), (255, 124, 88)]
    for i, (px, py) in enumerate(pin_positions):
        glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(glow)
        for ring in range(4, 0, -1):
            alpha = 18 + ring * 10
            r = 36 + ring * 22
            gdraw.ellipse([px - r, py - r, px + r, py + r], fill=(*WHITE[:3], alpha))
        overlay_pins.alpha_composite(glow)
        draw_pin(
            overlay_pins,
            int(px),
            int(py),
            scale=62,
            fill=pin_colors_fill[i % len(pin_colors_fill)],
            outline=(255, 255, 255),
        )

    draw_curved_connector(draw, [(int(px), int(py)) for px, py in pin_positions[:3]])

    cluster_cx = WIDTH * 50 // 100
    cluster_cy = HEIGHT * 48 // 100
    faces_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_avatar_cluster(faces_layer, cluster_cx, cluster_cy, radius=58)
    draw_simple_faces_hint(faces_layer, cluster_cx, cluster_cy, radius=58)

    clock_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw_clock_badge(clock_layer, WIDTH * 82 // 100, HEIGHT * 20 // 100, r=54)

    base.alpha_composite(overlay_pins)
    base.alpha_composite(faces_layer)
    base.alpha_composite(clock_layer)

    spark_positions = [
        (WIDTH * 12 // 100, HEIGHT * 18 // 100),
        (WIDTH * 90 // 100, HEIGHT * 55 // 100),
        (WIDTH * 68 // 100, HEIGHT * 14 // 100),
        (WIDTH * 30 // 100, HEIGHT * 78 // 100),
    ]
    draw_sparkles(draw, spark_positions)

    # Copy (short lines; visuals carry most of the story)
    title = "Meet nearby. Do something today."
    subtitle = (
        "Small real-world plans with friendly faces: spontaneous, close by, and easy to join."
    )
    margin_x = WIDTH * 8 // 100
    title_font = load_font(76, bold=True)
    sub_font = load_font(34)

    ty = HEIGHT * 76 // 100
    draw.text((margin_x, ty), title, font=title_font, fill=WHITE)

    title_bbox = draw.textbbox((margin_x, ty), title, font=title_font)
    max_sub_w = WIDTH - 2 * margin_x
    lines: list[str] = []
    words = subtitle.split()
    line = ""
    for word in words:
        trial = (line + " " + word).strip()
        if draw.textbbox((0, 0), trial, font=sub_font)[2] <= max_sub_w:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)

    sy = title_bbox[3] + 28
    line_gap = 12
    for ln in lines:
        draw.text((margin_x, sy), ln, font=sub_font, fill=CREAM)
        lb = draw.textbbox((margin_x, sy), ln, font=sub_font)
        sy = lb[3] + line_gap

    return base.convert("RGB")


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    image = compose()
    image.save(OUT_PATH, format="PNG", optimize=True)
    print(f"Wrote {OUT_PATH} ({WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main()
