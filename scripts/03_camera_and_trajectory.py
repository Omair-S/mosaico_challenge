import io
import numpy as np
import matplotlib.pyplot as plt
from pydantic import BaseModel
from PIL import Image
from mosaicolabs import MosaicoClient

from config import (HOST, PORT, SEQ, CAMERA_TOPIC, ODOM_TOPIC, SEC, PLOT_STYLE,
                    RESULTS_DIR, BUILD_DIR)
from freefall import free_fall_window

FRAMES_DIR = BUILD_DIR / "frames"

plt.rcParams.update({**PLOT_STYLE, "axes.unicode_minus": False})


def walk(obj, path=""):
    """Yield (path, value) for every field inside a pydantic model, recursively."""
    if isinstance(obj, BaseModel):
        for name in type(obj).model_fields:
            val = getattr(obj, name)
            p = f"{path}.{name}" if path else name
            yield p, val
            yield from walk(val, p)


def find_bytes(data):
    for p, v in walk(data):
        if isinstance(v, (bytes, bytearray)) and len(v) > 100:
            return p, bytes(v)
    return None, None


def find_position(data):
    for p, v in walk(data):
        if p.split(".")[-1] == "position" and all(hasattr(v, a) for a in "xyz"):
            return p, (v.x, v.y, v.z)
    return None, None


def dump_fields(data):
    for p, v in walk(data):
        s = f"<{len(v)} bytes>" if isinstance(v, (bytes, bytearray)) else str(v)[:80]
        print(f"  {p}: {s}")


with MosaicoClient.connect(HOST, PORT) as client:
    T_FALL, T_FALL_END = free_fall_window(client)
    T0 = client.sequence_handler(SEQ).timestamp_ns_min   # bag start (ns)

    # ---------- 1. What it saw: camera frames from 1 s before to 2 s after the fall ----------
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    cam = client.topic_handler(topic_name=CAMERA_TOPIC, sequence_name=SEQ)
    frames = []
    for msg in cam.get_data_streamer(start_timestamp_ns=T_FALL - 1 * SEC,
                                     end_timestamp_ns=T_FALL + 2 * SEC):
        path, raw = find_bytes(msg.data)
        if raw is None:
            print("No image bytes found. Fields:"); dump_fields(msg.data); break
        try:
            img = Image.open(io.BytesIO(raw)).convert("RGB")
        except Exception as e:
            print(f"Could not decode bytes at '{path}' ({e}). Fields:"); dump_fields(msg.data); break
        t = (msg.timestamp_ns - T0) / SEC
        img.save(FRAMES_DIR / f"frame_{t:07.3f}s.png")
        frames.append((t, msg.timestamp_ns, img))
    cam.close()
    print(f"Saved {len(frames)} frames to {FRAMES_DIR}")

    # ---------- 2. Where it walked: full odometry ----------
    odom = client.topic_handler(topic_name=ODOM_TOPIC, sequence_name=SEQ)
    ts, xs, ys, zs = [], [], [], []
    for msg in odom.get_data_streamer():
        path, pos = find_position(msg.data)
        if pos is None:
            print("No position found. Fields:"); dump_fields(msg.data); break
        ts.append((msg.timestamp_ns - T0) / SEC)
        xs.append(pos[0]); ys.append(pos[1]); zs.append(pos[2])
    odom.close()
    print(f"Read {len(ts)} odom samples")

t_fall_s = (T_FALL - T0) / SEC
t_fall_end_s = (T_FALL_END - T0) / SEC
RESULTS_DIR.mkdir(exist_ok=True)

# ---------- Contact sheet of the frames ----------
if frames:
    n = len(frames)
    cols = 6
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(2.6 * cols, 2.2 * rows))
    for ax in np.atleast_1d(axes).ravel():
        ax.axis("off")
    for ax, (t, t_ns, img) in zip(np.atleast_1d(axes).ravel(), frames):
        ax.imshow(img)
        falling = T_FALL <= t_ns < T_FALL_END + SEC // 8   # frame during/just after fall
        ax.set_title(rf"$t = {t:.3f}$ s", fontsize=9, color="red" if falling else "black")
    fig.suptitle(rf"Front camera, ${t_fall_s - 1:.0f}$ to ${t_fall_s + 2:.0f}$ s (red = free-fall window)")
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "camera_contact_sheet.png", dpi=150)

# ---------- Trajectory plots ----------
if ts:
    t = np.array(ts); x = np.array(xs); y = np.array(ys); z = np.array(zs)
    i_fall = np.argmin(np.abs(t - t_fall_s))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    sc = ax1.scatter(x, y, c=t, s=3, cmap="viridis")
    ax1.plot(x[0], y[0], "go", label="start")
    ax1.plot(x[-1], y[-1], "ks", label="end")
    ax1.plot(x[i_fall], y[i_fall], "r*", markersize=14, label=rf"free fall ($t = {t_fall_s:.0f}$ s)")
    ax1.set_xlabel(r"$x$ (m)"); ax1.set_ylabel(r"$y$ (m)")
    ax1.set_title("Top-down path (odom frame)")
    ax1.set_aspect("equal", adjustable="datalim")
    ax1.legend(fontsize=8); ax1.grid(alpha=0.3)
    fig.colorbar(sc, ax=ax1, label=r"$t$ (s)")

    ax2.plot(t, z, linewidth=0.8)
    ax2.axvspan(t_fall_s, t_fall_end_s, color="red", alpha=0.3, label="free-fall window")
    ax2.set_xlabel(r"$t$ (s)"); ax2.set_ylabel(r"$z$ (m)")
    ax2.set_title("Body height over time")
    ax2.legend(fontsize=8); ax2.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(RESULTS_DIR / "trajectory.png", dpi=150)

print(f"Saved {RESULTS_DIR / 'camera_contact_sheet.png'} and {RESULTS_DIR / 'trajectory.png'}")
plt.show()
