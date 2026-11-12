"""Shared constants and paths. All paths are relative to the repo root, not the cwd."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
BUILD_DIR = ROOT / "build"          # intermediate frames, gitignored

HOST, PORT = "localhost", 6726
SEQ = "spot_yb42"
ROBOT = "spot-07"
IMU_TOPIC = "/imu/body"
CAMERA_TOPIC = "/camera/front/image"
ODOM_TOPIC = "/robot/odom"

FREE_FALL_AZ = 0.1                  # m/s^2, a_z below this counts as free fall
CLUSTER_GAP_NS = int(1e8)           # gaps > 100 ms start a new window
SEC = 1_000_000_000
G = 9.81

# LaTeX-style fonts (Computer Modern), no TeX install needed
PLOT_STYLE = {
    "font.family": "serif",
    "mathtext.fontset": "cm",
    "font.serif": ["cmr10", "DejaVu Serif"],
    "axes.formatter.use_mathtext": True,
}
