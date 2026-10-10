import math
import urllib.request
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

ROOT = Path(__file__).parent
OUT = ROOT / "maps"
OUT.mkdir(exist_ok=True)

PLACES = {
    "呼和浩特": (111.7492, 40.8426),
    "北方兵器城": (109.880831, 40.678197),
    "赛汗塔拉": (109.903049, 40.627502),
    "青山区住宿": (109.905, 40.657),
    "包头古城": (110.052355, 40.646601),
    "胡服骑射广场": (110.165, 40.715),
    "五当召": (110.296671, 40.789928),
}

def world_pixel(lon, lat, zoom):
    size = 256 * (2 ** zoom)
    x = (lon + 180.0) / 360.0 * size
    sin_lat = math.sin(math.radians(lat))
    y = (0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi)) * size
    return x, y

def tile(x, y, zoom):
    url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
    req = urllib.request.Request(url, headers={"User-Agent": "LauraLifeOS-TravelPlanner/1.0"})
    with urllib.request.urlopen(req, timeout=20) as response:
        return Image.open(BytesIO(response.read())).convert("RGB")

def label_font(size):
    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            pass
    return ImageFont.load_default()

def render(filename, names, zoom, title, width=1280, height=720):
    points = [PLACES[name] for name in names]
    projected = [world_pixel(lon, lat, zoom) for lon, lat in points]
    center_x = sum(x for x, _ in projected) / len(projected)
    center_y = sum(y for _, y in projected) / len(projected)
    left, top = center_x - width / 2, center_y - height / 2
    first_x, last_x = math.floor(left / 256), math.floor((left + width) / 256)
    first_y, last_y = math.floor(top / 256), math.floor((top + height) / 256)
    canvas = Image.new("RGB", (width, height), "#dce7e3")
    for tx in range(first_x, last_x + 1):
        for ty in range(first_y, last_y + 1):
            try:
                im = tile(tx, ty, zoom)
                canvas.paste(im, (round(tx * 256 - left), round(ty * 256 - top)))
            except Exception:
                continue
    canvas = ImageEnhance.Color(canvas).enhance(0.55)
    canvas = ImageEnhance.Contrast(canvas).enhance(0.92)
    canvas = ImageEnhance.Brightness(canvas).enhance(1.04)
    paper = Image.new("RGB", canvas.size, "#e8dfca")
    canvas = Image.blend(canvas, paper, 0.13)
    draw = ImageDraw.Draw(canvas, "RGBA")
    pixels = [(x - left, y - top) for x, y in projected]
    route_color = (176, 79, 49, 255)
    draw.line(pixels, fill=(255, 248, 232, 230), width=14, joint="curve")
    draw.line(pixels, fill=route_color, width=7, joint="curve")
    font = label_font(23)
    small = label_font(18)
    for index, ((x, y), name) in enumerate(zip(pixels, names), 1):
        draw.ellipse((x - 15, y - 15, x + 15, y + 15), fill=route_color, outline="#fff8e8", width=5)
        number = str(index)
        box = draw.textbbox((0, 0), number, font=small)
        draw.text((x - (box[2]-box[0])/2, y - (box[3]-box[1])/2 - 2), number, font=small, fill="white")
    legend_width = 255
    legend_height = 24 + len(names) * 34
    draw.rounded_rectangle((22, 22, 22 + legend_width, 22 + legend_height), radius=3, fill=(82, 63, 47, 225))
    for index, name in enumerate(names, 1):
        y = 32 + (index - 1) * 34
        draw.ellipse((34, y, 58, y + 24), fill=route_color)
        draw.text((41, y + 1), str(index), font=small, fill="#fff8e8")
        draw.text((68, y - 1), name, font=font, fill="#fff8e8")
    title_box = draw.textbbox((0, 0), title, font=font)
    title_width = title_box[2] - title_box[0]
    draw.rectangle((width - title_width - 50, 22, width - 22, 66), fill=(245, 236, 216, 235))
    draw.text((width - title_width - 36, 29), title, font=font, fill="#513d2e")
    draw.rectangle((8, 8, width - 8, height - 8), outline=(104, 83, 62, 180), width=2)
    draw.rectangle((0, height - 34, width, height), fill=(247,240,223,230))
    draw.text((12, height - 29), "© OpenStreetMap contributors · 路线为行程顺序示意，实际驾驶以实时导航为准", font=small, fill="#51483f")
    canvas.save(OUT / filename, quality=92)

jobs = [
    ("trip-overview.jpg", ["呼和浩特", "北方兵器城", "赛汗塔拉", "包头古城", "胡服骑射广场", "五当召", "呼和浩特"], 8, "呼和浩特—包头 · 两日总览"),
    ("day-01.jpg", ["北方兵器城", "赛汗塔拉"], 13, "DAY 01 · 青山区"),
    ("day-02.jpg", ["包头古城", "胡服骑射广场", "五当召"], 11, "DAY 02 · 石拐文化线"),
]
for filename, names, zoom, title in jobs:
    render(filename, names, zoom, title)
