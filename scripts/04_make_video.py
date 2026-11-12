import subprocess
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from mosaicolabs import MosaicoClient

from config import HOST, PORT, SEQ, ROBOT, CAMERA_TOPIC, SEC, G, RESULTS_DIR, BUILD_DIR
from freefall import free_fall_window

LEAD, TAIL = 11, 4                 # seconds before / after the fall -> 15 s total
WARN, FALL_SHOW, LAND_SHOW = 3.0, 0.5, 1.5
OUT_W = 960                        # upscale small frames so text is readable
OUT_DIR = BUILD_DIR / "video_frames"
OUT_VIDEO = RESULTS_DIR / "spot07_fall_15s.mp4"

OUT_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)
for f in OUT_DIR.iterdir():
    f.unlink()


def font(size):
    try:
        return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def banner(draw, img_w, text, fill, text_fill, y, size):
    f = font(size)
    l, t, r, b = draw.textbbox((0, 0), text, font=f)
    w, h = r - l, b - t
    pad = 14
    x = (img_w - w) // 2
    draw.rectangle([x - pad, y - pad, x + w + pad, y + h + pad], fill=fill)
    draw.text((x - l, y - t), text, font=f, fill=text_fill)


with MosaicoClient.connect(HOST, PORT) as client:
    T_FALL, T_FALL_END = free_fall_window(client)
    T0 = client.sequence_handler(SEQ).timestamp_ns_min   # bag start (ns)
    fall_s = (T_FALL_END - T_FALL) / SEC
    drop_cm = 0.5 * G * fall_s ** 2 * 100                 # d = 1/2 g t^2

    cam = client.topic_handler(topic_name=CAMERA_TOPIC, sequence_name=SEQ)
    n = 0
    for msg in cam.get_data_streamer(start_timestamp_ns=T_FALL - LEAD * SEC,
                                     end_timestamp_ns=T_FALL + TAIL * SEC):
        img = Image.open(BytesIO(msg.data.data)).convert("RGB")
        scale = OUT_W / img.width
        img = img.resize((OUT_W, int(img.height * scale)), Image.LANCZOS)
        W, H = img.size
        d = ImageDraw.Draw(img)

        t_bag = (msg.timestamp_ns - T0) / SEC
        dt = (msg.timestamp_ns - T_FALL) / SEC      # negative = before fall

        # timestamp, always on
        d.text((12, H - 40), f"t = {t_bag:6.3f} s   {ROBOT} / YB-42",
               font=font(22), fill="white", stroke_width=2, stroke_fill="black")

        if -WARN <= dt < 0:
            banner(d, W, f"FALL IN {-dt:.1f} s", (255, 200, 0), "black", 20, 40)
        elif 0 <= dt < FALL_SHOW:
            d.rectangle([0, 0, W - 1, H - 1], outline=(255, 0, 0), width=14)
            banner(d, W, "FREE FALL", (220, 0, 0), "white", 20, 56)
            banner(d, W, f"IMU a_z ~ 0  ({fall_s * 1000:.0f} ms, ~{drop_cm:.1f} cm drop)",
                   (0, 0, 0), "white", 110, 22)
        elif FALL_SHOW <= dt < FALL_SHOW + LAND_SHOW:
            banner(d, W, "LANDED", (0, 160, 0), "white", 20, 40)

        img.save(OUT_DIR / f"{n:04d}.png")
        n += 1
    cam.close()

print(f"Wrote {n} frames ({n / 8:.1f} s at 8 fps)")

subprocess.run([
    "ffmpeg", "-y", "-framerate", "8", "-i", str(OUT_DIR / "%04d.png"),
    "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2",   # libx264 needs even dimensions
    str(OUT_VIDEO),
], check=True)
print(f"Saved {OUT_VIDEO}")
