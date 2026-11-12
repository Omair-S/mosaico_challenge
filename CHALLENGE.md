# Mission YB-42

Last night, spot-07 ran a patrol of Yard B. The log is in `spot_yb42.mcap` (ROS 2, ~13 MB, 87 s):
IMU, joint states, odometry, tf, four foot load cells, a front camera, battery and the mission log.

The night-shift operator swears nothing happened.

1. Ingest the recording into Mosaico:
   ```bash
   mosaicolabs.ros_injector spot_yb42.mcap --name spot_yb42 --metadata sequence_metadata.json
   ```
2. With a **single Mosaico query**, find the moment spot-07 was in **free fall**. That's when its IMU measured almost no vertical acceleration.
3. Send us the exact start timestamp of that window (UTC, nanoseconds), plus the query you used.

Bonus: once you know *when*, take a look at *what* the robot saw, and *where* it walked.
