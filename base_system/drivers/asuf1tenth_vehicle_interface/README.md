# ASU F1TENTH Vehicle Interface & FESC Driver

ROS 2 package providing drivers and hardware abstraction for the ASU F1TENTH vehicle.

## Architecture

The hardware interface splits duties across two embedded devices:
1. **FESC (Flipsky / VESC BLDC Controller)**: Controls the main traction brushless motor and publishes motor core telemetry (`/fesc/sensors/core`).
2. **ESP32-C3 SuperMini**: Direct serial hardware bridge reading MPU6500 IMU $v_z$ ($\text{rad/s}$) and driving the high-frequency 14-bit steering servo PWM on GPIO 5.

The **`asuf1tenth_vehicle_interface`** node ties them together:
- Reads the raw $v_z$ stream from the ESP32 over serial, packages it into standard `sensor_msgs/msg/Imu` on `sensors/imu/raw` with proper timestamp, frame ID, and covariance.
- Subscribes to `commands/servo/position` and sends normalized commands `[0.0, 1.0]` over serial to the ESP32.
- Routes global `commands/motor/*` to `/fesc/commands/motor/*`.
- Republishes `/fesc/sensors/core` to `sensors/core` (consumed by downstream odometry).

### Topic Routing Switchboard:

* **Commands ➔ Hardware Drivers**:
  - `/commands/motor/speed` ➔ `/fesc/commands/motor/speed`
  - `/commands/motor/current` ➔ `/fesc/commands/motor/current`
  - `/commands/motor/brake` ➔ `/fesc/commands/motor/brake`
  - `/commands/motor/duty_cycle` ➔ `/fesc/commands/motor/duty_cycle`
  - `/commands/motor/position` ➔ `/fesc/commands/motor/position`
  - `/commands/servo/position` ➔ ESP32 Serial (`<float>\n`)

* **Telemetry ➔ Global Topics**:
  - `/fesc/sensors/core` ➔ `/sensors/core`
  - ESP32 Serial Stream ➔ `/sensors/imu/raw` (`sensor_msgs/msg/Imu`)

---

## How to Run

Launch the FESC driver and ESP32 interface simultaneously:

```bash
ros2 launch asuf1tenth_vehicle_interface asuf1tenth_vehicle_interface.launch.py esp_port:=/dev/esp fesc_port:=/dev/fesc
```

Or bring up all vehicle drivers (including SLLiDAR):

```bash
ros2 launch drivers_bringup drivers_bringup.launch.py esp_port:=/dev/esp fesc_port:=/dev/fesc
```
