#!/usr/bin/env python3
# Copyright 2026 ASU F1TENTH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
asuf1tenth_vehicle_interface.py

Hardware bridge node for the F1TENTH vehicle:
  1. Communicates directly with ESP32-C3 over Serial:
     - Streams IMU vz (rad/s) and packages it into sensor_msgs/msg/Imu.
     - Receives normalized servo commands and writes them to the ESP32.
  2. Bridges standard motor command topics to the FESC namespace (/fesc/...).
  3. Republishes FESC telemetry (/fesc/sensors/core) to standard sensors/core.
"""

import os
import threading
import time
import serial
import serial.tools.list_ports
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from sensor_msgs.msg import Imu, LaserScan
from vesc_msgs.msg import VescStateStamped


class AsuF1tenthVehicleInterface(Node):

    def __init__(self):
        super().__init__('asuf1tenth_vehicle_interface')
        self.get_logger().info('Initializing ASU F1TENTH Vehicle Interface Node...')

        # --- Parameters ---
        self.declare_parameter('esp_port', '/dev/esp')
        self.declare_parameter('esp_baudrate', 115200)
        self.declare_parameter('imu_frame_id', 'imu')
        self.declare_parameter('imu_topic', 'sensors/imu/raw')
        self.declare_parameter('servo_cmd_topic', 'commands/servo/position')
        self.declare_parameter('lidar_topic', 'scan')
        self.declare_parameter('imu_cov_z', 0.0001)

        self.esp_port = self.get_parameter('esp_port').get_parameter_value().string_value
        self.esp_baudrate = self.get_parameter('esp_baudrate').get_parameter_value().integer_value
        self.imu_frame_id = self.get_parameter('imu_frame_id').get_parameter_value().string_value
        self.imu_topic = self.get_parameter('imu_topic').get_parameter_value().string_value
        self.servo_cmd_topic = self.get_parameter('servo_cmd_topic').get_parameter_value().string_value
        self.lidar_topic = self.get_parameter('lidar_topic').get_parameter_value().string_value
        self.imu_cov_z = self.get_parameter('imu_cov_z').get_parameter_value().double_value

        # --- Connection State Flags ---
        self.fesc_connected = False
        self.lidar_connected = False

        # --- Serial Connection & Threading ---
        self.serial_conn = None
        self.serial_lock = threading.Lock()
        self.running = True

        # --- IMU Publisher ---
        self.imu_pub = self.create_publisher(Imu, self.imu_topic, 10)

        # --- Servo Command Subscriber ---
        self.servo_sub = self.create_subscription(
            Float64,
            self.servo_cmd_topic,
            self.servo_cmd_callback,
            10
        )

        # --- FESC Motor Command Publishers & Subscribers ---
        self.cmd_speed_sub = self.create_subscription(
            Float64,
            'commands/motor/speed',
            self.cmd_speed_callback,
            10
        )
        self.cmd_speed_pub = self.create_publisher(
            Float64,
            '/fesc/commands/motor/speed',
            10
        )

        self.cmd_current_sub = self.create_subscription(
            Float64,
            'commands/motor/current',
            self.cmd_current_callback,
            10
        )
        self.cmd_current_pub = self.create_publisher(
            Float64,
            '/fesc/commands/motor/current',
            10
        )

        self.cmd_brake_sub = self.create_subscription(
            Float64,
            'commands/motor/brake',
            self.cmd_brake_callback,
            10
        )
        self.cmd_brake_pub = self.create_publisher(
            Float64,
            '/fesc/commands/motor/brake',
            10
        )

        self.cmd_duty_cycle_sub = self.create_subscription(
            Float64,
            'commands/motor/duty_cycle',
            self.cmd_duty_cycle_callback,
            10
        )
        self.cmd_duty_cycle_pub = self.create_publisher(
            Float64,
            '/fesc/commands/motor/duty_cycle',
            10
        )

        self.cmd_position_sub = self.create_subscription(
            Float64,
            'commands/motor/position',
            self.cmd_position_callback,
            10
        )
        self.cmd_position_pub = self.create_publisher(
            Float64,
            '/fesc/commands/motor/position',
            10
        )

        # --- FESC Telemetry Bridging ---
        self.sensor_core_sub = self.create_subscription(
            VescStateStamped,
            '/fesc/sensors/core',
            self.sensor_core_callback,
            10
        )
        self.sensor_core_pub = self.create_publisher(
            VescStateStamped,
            'sensors/core',
            10
        )
        # Also publish on /vesc/sensors/core for legacy nodes (e.g. state_machine battery check)
        self.sensor_core_vesc_pub = self.create_publisher(
            VescStateStamped,
            '/vesc/sensors/core',
            10
        )

        # --- Servo Telemetry Feedback for Odometry (vesc_to_odom) ---
        self.servo_sensor_pub = self.create_publisher(
            Float64,
            'sensors/servo_position_command',
            10
        )
        self.last_servo_cmd = Float64()
        self.last_servo_cmd.data = 0.5  # Neutral center default

        # Periodic timer (20 Hz) to keep servo feedback alive for vesc_to_odom
        self.servo_feedback_timer = self.create_timer(0.05, self.publish_servo_feedback)

        # --- LiDAR Monitor Subscription ---
        self.lidar_sub = self.create_subscription(
            LaserScan,
            self.lidar_topic,
            self.lidar_scan_callback,
            10
        )

        # Check hardware port availability on startup
        self.check_hardware_devices()

        # Start Serial Reader Thread for ESP32 IMU Stream
        self.reader_thread = threading.Thread(target=self.serial_read_loop, daemon=True)
        self.reader_thread.start()

        self.get_logger().info(
            f'ASU F1TENTH Vehicle Interface active. ESP32 on {self.esp_port} @ {self.esp_baudrate} baud.'
        )

    def check_hardware_devices(self):
        fesc_exists = os.path.exists('/dev/fesc')
        lidar_exists = os.path.exists('/dev/rplidar')
        esp_exists = os.path.exists(self.esp_port)

        status = []
        status.append(f"ESP32: {self.esp_port} [{'FOUND' if esp_exists else 'SEARCHING'}]")
        status.append(f"FESC: /dev/fesc [{'FOUND' if fesc_exists else 'NOT FOUND'}]")
        status.append(f"LiDAR: /dev/rplidar [{'FOUND' if lidar_exists else 'NOT FOUND'}]")

        self.get_logger().info("Hardware Port Check: " + " | ".join(status))

    # --- ESP32 Serial Communication Loop ---
    def resolve_port(self, target_port):
        if os.path.exists(target_port):
            return target_port

        # Search for Espressif VID 0x303A or description
        self.get_logger().warn(
            f"Configured port '{target_port}' does not exist! "
            f"(Ensure udev rules are installed on the host: 'create_udev_rules.sh'). "
            f"Scanning USB devices for auto-fallback..."
        )
        for p in serial.tools.list_ports.comports():
            if p.vid == 0x303A or "Espressif" in (p.description or "") or "USB JTAG" in (p.description or ""):
                self.get_logger().info(f"Auto-detected ESP32 at '{p.device}'. Fallback successful.")
                return p.device

        self.get_logger().error(
            f"Could not auto-detect ESP32. Retrying '{target_port}'..."
        )
        return target_port

    def connect_serial(self):
        active_port = self.resolve_port(self.esp_port)
        try:
            self.serial_conn = serial.Serial(active_port, self.esp_baudrate, timeout=1.0)
            self.get_logger().info(f'Connected to ESP32 on {active_port}')
            return True
        except serial.SerialException as e:
            self.get_logger().warn(f'Waiting for ESP32 on {active_port}... ({e})')
            self.serial_conn = None
            return False

    def serial_read_loop(self):
        while self.running and rclpy.ok():
            if self.serial_conn is None or not self.serial_conn.is_open:
                if not self.connect_serial():
                    time.sleep(2.0)
                    continue

            try:
                line = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue

                # Parse float vz (rad/s)
                try:
                    vz = float(line)
                except ValueError:
                    # Ignore non-numeric lines (e.g. startup banners if any)
                    continue

                # Package and publish Imu message
                imu_msg = Imu()
                imu_msg.header.stamp = self.get_clock().now().to_msg()
                imu_msg.header.frame_id = self.imu_frame_id

                # Set angular velocity Z
                imu_msg.angular_velocity.x = 0.0
                imu_msg.angular_velocity.y = 0.0
                imu_msg.angular_velocity.z = vz

                # Set covariances
                imu_msg.orientation_covariance[0] = -1.0  # Signifies no orientation estimation
                imu_msg.linear_acceleration_covariance[0] = -1.0
                imu_msg.angular_velocity_covariance[0] = 0.0
                imu_msg.angular_velocity_covariance[4] = 0.0
                imu_msg.angular_velocity_covariance[8] = self.imu_cov_z

                self.imu_pub.publish(imu_msg)

            except serial.SerialException as e:
                self.get_logger().error(f'Serial read error: {e}. Reconnecting...')
                with self.serial_lock:
                    if self.serial_conn:
                        try:
                            self.serial_conn.close()
                        except Exception:
                            pass
                        self.serial_conn = None
                time.sleep(1.0)
            except Exception as e:
                self.get_logger().error(f'Unexpected error in serial thread: {e}')

    # --- Servo Feedback Loop ---
    def publish_servo_feedback(self):
        self.servo_sensor_pub.publish(self.last_servo_cmd)

    # --- Servo Command Callback ---
    def servo_cmd_callback(self, msg: Float64):
        # Clamp command to [0.0, 1.0]
        norm_val = max(0.0, min(1.0, float(msg.data)))
        self.last_servo_cmd.data = norm_val
        self.servo_sensor_pub.publish(self.last_servo_cmd)

        cmd_str = f"{norm_val:.3f}\n"

        with self.serial_lock:
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.write(cmd_str.encode('utf-8'))
                except serial.SerialException as e:
                    self.get_logger().warn(f'Failed to send servo command to ESP32: {e}')

    # --- FESC Motor Routing Callbacks ---
    def cmd_speed_callback(self, msg):
        self.cmd_speed_pub.publish(msg)

    def cmd_current_callback(self, msg):
        self.cmd_current_pub.publish(msg)

    def cmd_brake_callback(self, msg):
        self.cmd_brake_pub.publish(msg)

    def cmd_duty_cycle_callback(self, msg):
        self.cmd_duty_cycle_pub.publish(msg)

    def cmd_position_callback(self, msg):
        self.cmd_position_pub.publish(msg)

    def sensor_core_callback(self, msg):
        if not self.fesc_connected:
            self.fesc_connected = True
            self.get_logger().info(
                f'FESC connected & active on /fesc/sensors/core (Battery: {msg.state.voltage_input:.2f} V)'
            )
        self.sensor_core_pub.publish(msg)
        self.sensor_core_vesc_pub.publish(msg)

    def lidar_scan_callback(self, msg):
        if not self.lidar_connected:
            self.lidar_connected = True
            self.get_logger().info(
                f'SLLiDAR connected & active on {self.lidar_topic} (Frame: {msg.header.frame_id}, Beams: {len(msg.ranges)})'
            )

    def destroy_node(self):
        self.running = False
        with self.serial_lock:
            if self.serial_conn and self.serial_conn.is_open:
                try:
                    self.serial_conn.close()
                except Exception:
                    pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = AsuF1tenthVehicleInterface()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            try:
                rclpy.shutdown()
            except Exception:
                pass


if __name__ == '__main__':
    main()
