import os
from PIL import Image, ImageDraw

W = 512
BG_TOP = (26, 16, 64)
BG_BOT = (13, 17, 23)
RING = (88, 166, 255)
RING_DIM = (49, 94, 148)
ARROW = (63, 185, 80)
ARROW_DIM = (35, 115, 52)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)))


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rounded_gradient(size, radius, top, bottom):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for y in range(size):
        draw = ImageDraw.Draw(img)
        draw.line([(0, y), (size, y)], fill=lerp(top, bottom, y / size))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [(8, 8), (size - 8, size - 8)], radius=radius, fill=255)
    img.putalpha(mask)
    return img


def build():
    img = rounded_gradient(W, 110, BG_TOP, BG_BOT)
    d = ImageDraw.Draw(img)
    cx = cy = W // 2

    d.ellipse([cx - 190, cy - 190, cx + 190, cy + 190],
              outline=RING_DIM, width=34)
    d.ellipse([cx - 178, cy - 178, cx + 178, cy + 178],
              outline=RING, width=18)
    d.arc([cx - 178, cy - 178, cx + 178, cy + 178], start=200, end=290,
          fill=(136, 195, 255), width=18)

    d.rounded_rectangle([cx - 34, cy - 130, cx + 34, cy + 20],
                        radius=17, fill=ARROW_DIM)
    d.rounded_rectangle([cx - 30, cy - 126, cx + 30, cy + 16],
                        radius=15, fill=ARROW)
    d.polygon([(cx - 118, cy + 8), (cx + 118, cy + 8),
               (cx, cy + 118)], fill=ARROW_DIM)
    d.polygon([(cx - 106, cy + 8), (cx + 106, cy + 8),
               (cx, cy + 104)], fill=ARROW)

    d.rounded_rectangle([cx - 210, cy + 190, cx + 210, cy + 234],
                        radius=22, fill=(210, 217, 228, 26))

    img.save(os.path.join(OUT, "icon.png"))
    img.save(os.path.join(OUT, "icon.ico"),
             sizes=[(16, 16), (24, 24), (32, 32), (48, 48),
                    (64, 64), (128, 128), (256, 256)])
    print("media/icon.png and media/icon.ico written")


if __name__ == "__main__":
    build()
