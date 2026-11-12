import matplotlib.pyplot as plt
import numpy as np
from mosaicolabs import MosaicoClient

from config import HOST, PORT, SEQ, IMU_TOPIC, FREE_FALL_AZ, PLOT_STYLE, RESULTS_DIR

with MosaicoClient.connect(HOST, PORT) as client:
    topic_handler = client.topic_handler(topic_name=IMU_TOPIC, sequence_name=SEQ)
    data_streamer = topic_handler.get_data_streamer()
    z_accelerations = []
    timestamps = []
    freefall_timestamps = []
    for msg in data_streamer:
        z_accelerations.append(msg.data.acceleration.z)
        timestamps.append(msg.timestamp_ns)
        if msg.data.acceleration.z < FREE_FALL_AZ:  # free fall
            print(f"Free fall detected at timestamp {msg.timestamp_ns} ns")
            freefall_timestamps.append(msg.timestamp_ns)
    data_streamer.close()

print(len(freefall_timestamps))
plt.rcParams.update({**PLOT_STYLE, "font.size": 13})

t = (np.array(timestamps) - timestamps[0]) / 1e9   # seconds from start
az = np.array(z_accelerations)

fig, ax = plt.subplots(figsize=(8, 3.5))
ax.plot(t, az, linewidth=0.6, label=r"$a_z$")
ax.axhline(9.81, color="gray", linestyle="--", linewidth=0.8, label=r"$g = 9.81\ \mathrm{m/s^2}$")
ax.axhline(0, color="red", linestyle=":", linewidth=0.8, label=r"free fall ($a_z \approx 0$)")

ax.set_xlabel(r"Time $t$(s)")
ax.set_ylabel(r"Vertical acceleration $a_z$ ($\mathrm{m/s^2}$)")
ax.set_title(r"\texttt{/imu/body} vertical acceleration, \texttt{spot\_yb42}" if plt.rcParams["text.usetex"]
             else r"/imu/body vertical acceleration, spot$\_$yb42")  # cmr10 has no "_" glyph
ax.legend(loc="upper right", fontsize=9)
ax.grid(alpha=0.3)
fig.tight_layout()

RESULTS_DIR.mkdir(exist_ok=True)
fig.savefig(RESULTS_DIR / "imu_z.png", dpi=200)
print(f"Saved {RESULTS_DIR / 'imu_z.png'}")
plt.show()
