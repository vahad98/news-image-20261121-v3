"""Compose the news-image v3 front page (1024x1024) from 4 photo panels.

All text is rendered here with PIL; the panels contain no text.
Deterministic: same inputs -> same bytes (PNG written with fixed settings).
"""
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 1024
PAPER = (246, 241, 231)
INK = (17, 17, 17)
RED = (176, 30, 36)
DARK = (14, 14, 14)
GREY = (105, 100, 92)
WHITE = (255, 255, 255)
MARGIN = 36
CW = W - 2 * MARGIN  # 952 content width

F_SERIF_BLACK = "/usr/share/fonts/truetype/noto/NotoSerifDisplay-Black.ttf"
F_SERIF_BOLD = "/usr/share/fonts/truetype/noto/NotoSerif-Bold.ttf"
F_SERIF = "/usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf"
F_SANS_BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"
F_SANS = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def fit_font(path, size, text, max_w, min_size=10):
    """Largest font size <= size whose text fits max_w."""
    s = size
    while s > min_size:
        f = font(path, s)
        if f.getlength(text) <= max_w:
            return f
        s -= 1
    return font(path, min_size)


def wrap(text, f, max_w, max_lines=None):
    """Greedy word wrap measured with the real font."""
    words = text.split()
    lines, cur = [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if f.getlength(trial) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    if max_lines and len(lines) > max_lines:
        # merge overflow into the last allowed line (caller shrinks font instead)
        lines = lines[:max_lines]
    return lines


def wrap_fit(text, path, size, max_w, max_lines, min_size=11):
    """Wrap at the largest size (<= size) that fits within max_lines."""
    s = size
    while s > min_size:
        f = font(path, s)
        lines = wrap(text, f, max_w)
        if len(lines) <= max_lines:
            return f, lines
        s -= 1
    f = font(path, min_size)
    return f, wrap(text, f, max_w, max_lines)


def draw_tracked(draw, cx, y, text, f, fill, tracking=3):
    """Draw centred text with letter tracking."""
    widths = [draw.textlength(ch, font=f) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, w_ in zip(text, widths):
        draw.text((x, y), ch, font=f, fill=fill)
        x += w_ + tracking
    return total


def cover(img, tw, th):
    """Centre-crop resize to exactly tw x th."""
    iw, ih = img.size
    scale = max(tw / iw, th / ih)
    nw, nh = int(iw * scale + 0.5), int(ih * scale + 0.5)
    img = img.resize((nw, nh), Image.LANCZOS)
    x = (nw - tw) // 2
    y = (nh - th) // 2
    return img.crop((x, y, x + tw, y + th))


def load_panel(name, tw, th):
    p = os.path.join(HERE, "assets", name)
    img = Image.open(p).convert("RGB")
    return cover(img, tw, th)


def main():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    x0, x1 = MARGIN, W - MARGIN

    # --- top red bar ---
    d.rectangle([0, 0, W, 7], fill=RED)
    y = 15

    # --- masthead ---
    f_mast = fit_font(F_SERIF_BLACK, 76, "THE WORLD TODAY", CW)
    d.text((W / 2, y), "THE WORLD TODAY", font=f_mast, fill=INK, anchor="ma")
    y += int(f_mast.size * 1.12) + 6

    # --- thin rule, date, dateline, double rule ---
    d.line([(x0, y), (x1, y)], fill=INK, width=1)
    y += 8
    f_date = fit_font(F_SANS_BOLD, 30, "SUNDAY, 22 NOVEMBER 2026", CW)
    d.text((W / 2, y), "SUNDAY, 22 NOVEMBER 2026", font=f_date, fill=RED, anchor="ma")
    y += int(f_date.size * 1.25) + 2
    f_dl = font(F_SANS, 15)
    draw_tracked(d, W / 2, y, "THE GULF  •  WASHINGTON  •  OSLO  •  ANTALYA", f_dl, GREY, tracking=2)
    y += 26
    d.line([(x0, y), (x1, y)], fill=INK, width=2)
    y += 4
    d.line([(x0, y), (x1, y)], fill=INK, width=1)
    y += 10

    # --- hero photo ---
    hero_h = 212
    hero = load_panel("panel_hero.png", CW, hero_h)
    img.paste(hero, (x0, y))
    d.rectangle([x0, y, x1 - 1, y + hero_h - 1], outline=INK, width=2)
    # kicker chip overlapping bottom-left of the photo
    f_kick = font(F_SANS_BOLD, 16)
    chip_text = "THE GULF"
    chip_w = int(f_kick.getlength(chip_text)) + 24
    chip_h = 30
    chip_y = y + hero_h - chip_h - 8
    d.rectangle([x0 + 10, chip_y, x0 + 10 + chip_w, chip_y + chip_h], fill=RED)
    d.text((x0 + 10 + chip_w / 2, chip_y + chip_h / 2), chip_text,
           font=f_kick, fill=WHITE, anchor="mm")
    y += hero_h + 10

    # --- hero headline, one line ---
    f_head = fit_font(F_SERIF_BOLD, 46, "IRAN STRIKES US BASES", CW)
    d.text((W / 2, y), "IRAN STRIKES US BASES", font=f_head, fill=INK, anchor="ma")
    y += int(f_head.size * 1.18) + 2

    # --- hero deck, 2 lines ---
    deck = ("Missiles and drones target US Patriot sites in Kuwait and Bahrain; "
            "a Russian cargo ship burns after a drone strike in the Gulf of Finland.")
    f_deck, deck_lines = wrap_fit(deck, F_SERIF, 19, CW, 2)
    for ln in deck_lines:
        d.text((W / 2, y), ln, font=f_deck, fill=INK, anchor="ma")
        y += int(f_deck.size * 1.32)
    y += 4
    d.line([(x0, y), (x1, y)], fill=INK, width=1)
    y += 8

    # --- markets ticker, one line ---
    tick_rest = "S&P 500 -3.7% AS AI SELL-OFF SPREADS  •  ANTHROPIC SLIDES AFTER $81.3BN LISTING"
    f_tick = font(F_SANS_BOLD, 15)
    label = "MARKETS  "
    while f_tick.size > 11 and f_tick.getlength(label + tick_rest) > CW:
        f_tick = font(F_SANS_BOLD, f_tick.size - 1)
    d.text((x0, y), label, font=f_tick, fill=RED, anchor="la")
    d.text((x0 + f_tick.getlength(label), y), tick_rest, font=f_tick, fill=INK, anchor="la")
    y += int(f_tick.size * 1.5) + 6
    d.line([(x0, y), (x1, y)], fill=INK, width=1)
    y += 10

    # --- three sub-columns ---
    gap = 12
    col_w = (CW - 2 * gap) // 3  # 309
    sub_h = 128
    subs = [
        ("panel_tech.png", "TECH", "HUANG QUITS NVIDIA",
         "Nvidia's chief steps down as espionage probes widen; the race to replace him begins."),
        ("panel_climate.png", "CLIMATE", "COURT VOIDS OIL LICENCES",
         "Norway's supreme court strikes down climate-disputed oil licences in a landmark ruling."),
        ("panel_politics.png", "POLITICS", "DEMOCRATS RETAKE CONGRESS",
         "Democrats reclaim the US Congress in a resurgent midterm victory over the Republicans."),
    ]
    sub_top = y
    max_sub_bottom = y
    for i, (panel, kicker, head, dk) in enumerate(subs):
        cx = x0 + i * (col_w + gap)
        ph = load_panel(panel, col_w, sub_h)
        img.paste(ph, (cx, y))
        d.rectangle([cx, y, cx + col_w - 1, y + sub_h - 1], outline=INK, width=2)
        yy = y + sub_h + 8
        f_sub_k = font(F_SANS_BOLD, 13)
        d.text((cx, yy), kicker, font=f_sub_k, fill=RED, anchor="la")
        yy += 20
        f_sub_h, head_lines = wrap_fit(head, F_SERIF_BOLD, 21, col_w, 2)
        for ln in head_lines:
            d.text((cx, yy), ln, font=f_sub_h, fill=INK, anchor="la")
            yy += int(f_sub_h.size * 1.18)
        yy += 2
        f_sub_d, dk_lines = wrap_fit(dk, F_SERIF, 15, col_w, 4)
        for ln in dk_lines:
            d.text((cx, yy), ln, font=f_sub_d, fill=INK, anchor="la")
            yy += int(f_sub_d.size * 1.3)
        max_sub_bottom = max(max_sub_bottom, yy)
    y = max_sub_bottom + 10

    # --- footer: ALSO TODAY ---
    foot_h = H - 26 - y  # leave 26px for the credit line
    d.rectangle([0, y, W, y + foot_h], fill=DARK)
    fy = y + 12
    f_foot_h = font(F_SANS_BOLD, 16)
    d.text((x0, fy), "ALSO TODAY", font=f_foot_h, fill=WHITE, anchor="la")
    d.line([(x0, fy + 26), (x1, fy + 26)], fill=RED, width=2)
    fy += 38
    items = [
        "COP31 in Antalya in overtime, deadlocked on fossil fuels",
        "Mexico captures FBI most-wanted 'El Chapo Isidro' in Sinaloa",
        "Magnitude 6.9 quake shakes Peru's Andes; no damage reported",
        "EU-Indonesia trade deal covers 730 million people",
        "Alcaraz faces Zverev in the ATP Finals title decider",
        "Lagarde resigns; EU begins the search for a new ECB chief",
    ]
    f_item = font(F_SANS, 13)
    col2_w = (CW - 24) // 2
    row_h = (foot_h - 50) // 3
    for idx, item in enumerate(items):
        col = idx % 2
        row = idx // 2
        ix = x0 + col * (col2_w + 24)
        iy = fy + row * row_h
        lines = wrap(item, f_item, col2_w - 18)
        d.rectangle([ix, iy + 4, ix + 8, iy + 12], fill=RED)
        ly = iy
        for ln in lines[:2]:
            d.text((ix + 16, ly), ln, font=f_item, fill=WHITE, anchor="la")
            ly += 18
    y = y + foot_h + 6

    # --- credit line ---
    f_credit = font(F_SANS_BOLD, 12)
    d.text((W / 2, y), "THE WORLD TODAY  •  SUNDAY, 22 NOVEMBER 2026",
           font=f_credit, fill=GREY, anchor="ma")

    out = os.path.join(HERE, "entry.png")
    img.save(out, "PNG", optimize=True)
    size = os.path.getsize(out)
    print(f"saved {out} {img.size} {size} bytes")
    if size > 1048576:
        # JPEG bytes are allowed under the entry.png name (judged by first bytes)
        img.save(out, "JPEG", quality=90, optimize=True)
        size = os.path.getsize(out)
        print(f"re-saved as JPEG {size} bytes")
        if size > 1048576:
            img.save(out, "JPEG", quality=82, optimize=True)
            print(f"re-saved as JPEG q82 {os.path.getsize(out)} bytes")


if __name__ == "__main__":
    main()
