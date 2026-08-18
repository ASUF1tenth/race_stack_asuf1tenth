#!/usr/bin/env python3
# Copyright 2026 F1TENTH Foundation
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

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64
from sensor_msgs.msg import Imu
from vesc_msgs.msg import VescStateStamped, VescImuStamped


class VescFescBridge(Node):

    def __init__(self):
        super().__init__('vesc_fesc_bridge')
        self.get_logger().info('Initializing VESC/FESC Topic Bridge Node...')

        # Watchdog and connection state tracking
        self.last_fesc_msg_time = None
        self.last_vesc_msg_time = None
        self.fesc_connected = False
        self.vesc_connected = False

        # --- Subscriptions to Global Commands -> Publish to Namespaces ---
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

        self.cmd_servo_sub = self.create_subscription(
            Float64,
            'commands/servo/position',
            self.cmd_servo_callback,
            10
        )
        self.cmd_servo_pub = self.create_publisher(
            Float64,
            '/vesc/commands/servo/position',
            10
        )

        # --- Subscriptions to Namespaced Sensors -> Publish Globally ---
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

        self.sensor_imu_sub = self.create_subscription(
            VescImuStamped,
            '/vesc/sensors/imu',
            self.sensor_imu_callback,
            10
        )
        self.sensor_imu_pub = self.create_publisher(
            VescImuStamped,
            'sensors/imu',
            10
        )

        self.sensor_imu_raw_sub = self.create_subscription(
            Imu,
            '/vesc/sensors/imu/raw',
            self.sensor_imu_raw_callback,
            10
        )
        self.sensor_imu_raw_pub = self.create_publisher(
            Imu,
            'sensors/imu/raw',
            10
        )

        self.sensor_servo_pos_sub = self.create_subscription(
            Float64,
            '/vesc/sensors/servo_position_command',
            self.sensor_servo_pos_callback,
            10
        )
        self.sensor_servo_pos_pub = self.create_publisher(
            Float64,
            'sensors/servo_position_command',
            10
        )

        # Watchdog timer running at 1Hz to monitor driver connection state
        self.watchdog_timer = self.create_timer(1.0, self.watchdog_callback)

        self.get_logger().info('VESC/FESC Topic Bridge Node is running and routing messages.')

    # --- Callbacks for Commands Routing ---
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

    def cmd_servo_callback(self, msg):
        self.cmd_servo_pub.publish(msg)

    # --- Callbacks for Sensors Routing ---
    def sensor_core_callback(self, msg):
        now = self.get_clock().now()
        self.last_fesc_msg_time = now
        if not self.fesc_connected:
            self.fesc_connected = True
            self.get_logger().info('FESC driver telemetry stream connected.')
        self.sensor_core_pub.publish(msg)

    def sensor_imu_callback(self, msg):
        self.sensor_imu_pub.publish(msg)

    def sensor_imu_raw_callback(self, msg):
        now = self.get_clock().now()
        self.last_vesc_msg_time = now
        if not self.vesc_connected:
            self.vesc_connected = True
            self.get_logger().info('VESC driver IMU telemetry stream connected.')
        self.sensor_imu_raw_pub.publish(msg)

    def sensor_servo_pos_callback(self, msg):
        self.sensor_servo_pos_callback_internal(msg)

    def sensor_servo_pos_callback_internal(self, msg):
        self.sensor_servo_pos_pub.publish(msg)

    def watchdog_callback(self):
        now = self.get_clock().now()
        timeout_duration = rclpy.duration.Duration(seconds=3.0)

        # Check FESC status
        if self.last_fesc_msg_time is not None:
            if (now - self.last_fesc_msg_time) > timeout_duration:
                if self.fesc_connected:
                    self.fesc_connected = False
                    self.get_logger().warn('FESC driver telemetry stream lost. Bridge active and waiting for reconnection...')

        # Check VESC status
        if self.last_vesc_msg_time is not None:
            if (now - self.last_vesc_msg_time) > timeout_duration:
                if self.vesc_connected:
                    self.vesc_connected = False
                    self.get_logger().warn('VESC driver telemetry stream lost. Bridge active and waiting for reconnection...')


def main(args=None):
    rclpy.init(args=args)
    node = VescFescBridge()
    try:
        while rclpy.ok():
            try:
                rclpy.spin(node)
            except KeyboardInterrupt:
                break
            except Exception as e:
                node.get_logger().error(f'Spin exception caught in VESC/FESC bridge: {e}')
    finally:
        node.destroy_node()
        if rclpy.ok():
            try:
                rclpy.shutdown()
            except Exception:
                pass


if __name__ == '__main__':
    main()

