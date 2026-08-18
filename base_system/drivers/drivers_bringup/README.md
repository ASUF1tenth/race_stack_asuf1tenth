# drivers_bringup

ROS 2 launch aggregator for ASU F1TENTH low-level hardware drivers. Provides a single entry point to bring up all onboard hardware:

- **ESP32-C3 & FESC (`asuf1tenth_vehicle_interface`)** — High-rate MPU6500 IMU $v_z$ telemetry, 14-bit steering servo PWM, and BLDC traction motor control.
- **SLLiDAR A1 (`sllidar_ros2`)** — 2D laser scan rangefinder.

---

## Hardware Setup & Udev Rules (One-Time Setup)

Before running the driver stack, install the hardware udev rules on the host OS so persistent symlinks (`/dev/esp`, `/dev/fesc`, and `/dev/rplidar`) are created automatically:

```bash
# Run from drivers_bringup package directory:
./scripts/create_udev_rules.sh
```

Check that the symlinks are active:
```bash
ls -l /dev/esp /dev/fesc /dev/rplidar
```

---

## Usage

Bring up all vehicle drivers with default persistent ports:

```bash
ros2 launch drivers_bringup drivers_bringup.launch.py
```

### Configurable Arguments

| Argument | Default | Description |
|---|---|---|
| `esp_port` | `/dev/esp` | ESP32 (Steering Servo + IMU) serial port |
| `fesc_port` | `/dev/fesc` | FESC (BLDC motor) serial port |
| `serial_port` | `/dev/rplidar` | SLLiDAR serial port |
| `serial_baudrate` | `115200` | SLLiDAR baud rate |
| `frame_id` | `laser` | TF frame ID for scan data |
| `inverted` | `false` | Invert scan data |
| `angle_compensate` | `true` | Enable angle compensation |
| `vesc_config` | *(asuf1tenth_vehicle_interface default)* | Path to VESC configuration YAML |

Override arguments if needed:

```bash
ros2 launch drivers_bringup drivers_bringup.launch.py esp_port:=/dev/ttyACM0 fesc_port:=/dev/ttyACM1
```

## License

Apache-2.0
