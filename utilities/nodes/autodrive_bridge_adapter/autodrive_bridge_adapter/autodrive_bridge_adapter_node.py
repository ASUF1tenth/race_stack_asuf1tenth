"""AutoDRIVE RoboRacer bridge <-> ForzaETH race-stack topic adapter.

Only consumes AutoDRIVE topics that are runtime-permitted under the
competition rules (lidar, imu, encoders, steering feedback), plus our own
/drive command input. Never touches /autodrive/roboracer_1/odom, /tf,
/autodrive/roboracer_1/ips, or any lap/collision/reset topic.

    /drive (AckermannDriveStamped)          -> throttle_command / steering_command
    /autodrive/roboracer_1/lidar            -> /scan
    /autodrive/roboracer_1/imu              -> /sensors/imu/raw
    left_encoder + right_encoder + steering -> /odom (wheel odometry, bicycle model)

The /odom synthesis mirrors vesc_to_odom.cpp's approach on real hardware:
wheel speed from a real sensor, yaw rate from speed * tan(steering) / wheelbase,
dead-reckoned into x/y/yaw.
"""
import math

import rclpy
from rclpy.node import Node
from rclpy.time import Time
from std_msgs.msg import Float32
from sensor_msgs.msg import JointState, Imu, LaserScan
from nav_msgs.msg import Odometry
from ackermann_msgs.msg import AckermannDriveStamped


def _unwrap_delta(delta):
    if delta > math.pi:
        delta -= 2.0 * math.pi
    elif delta < -math.pi:
        delta += 2.0 * math.pi
    return delta


class AutoDriveBridgeAdapter(Node):

    def __init__(self):
        super().__init__('autodrive_bridge_adapter')

        self.declare_parameter('wheel_radius', 0.059)
        self.declare_parameter('wheelbase', 0.324)
        self.declare_parameter('max_speed', 10.0)
        self.declare_parameter('max_steer', 0.5236)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')

        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.wheelbase = self.get_parameter('wheelbase').value
        self.max_speed = self.get_parameter('max_speed').value
        self.max_steer = self.get_parameter('max_steer').value
        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value

        self._drive_sub = self.create_subscription(AckermannDriveStamped, '/drive', self._drive_cb, 5)
        self._throttle_pub = self.create_publisher(Float32, '/autodrive/roboracer_1/throttle_command', 5)
        self._steering_pub = self.create_publisher(Float32, '/autodrive/roboracer_1/steering_command', 5)

        self._lidar_sub = self.create_subscription(
            LaserScan, '/autodrive/roboracer_1/lidar', self._lidar_cb, 5)
        self._scan_pub = self.create_publisher(LaserScan, '/scan', 5)

        self._imu_sub = self.create_subscription(
            Imu, '/autodrive/roboracer_1/imu', self._imu_cb, 5)
        self._imu_pub = self.create_publisher(Imu, '/sensors/imu/raw', 5)

        self._left_encoder_sub = self.create_subscription(
            JointState, '/autodrive/roboracer_1/left_encoder', self._left_encoder_cb, 5)
        self._right_encoder_sub = self.create_subscription(
            JointState, '/autodrive/roboracer_1/right_encoder', self._right_encoder_cb, 5)
        self._steering_sub = self.create_subscription(
            Float32, '/autodrive/roboracer_1/steering', self._steering_cb, 5)
        self._odom_pub = self.create_publisher(Odometry, '/odom', 5)

        self._last_left_angle = None
        self._last_left_stamp = None
        self._last_right_angle = None
        self._last_right_stamp = None
        self._left_speed = 0.0
        self._right_speed = 0.0
        self._current_steering = 0.0
        self._last_odom_stamp = None
        self._x = 0.0
        self._y = 0.0
        self._yaw = 0.0

        self.get_logger().info('autodrive_bridge_adapter started')

    def _drive_cb(self, msg):
        throttle = max(-1.0, min(1.0, msg.drive.speed / self.max_speed))
        steer = max(-1.0, min(1.0, msg.drive.steering_angle / self.max_steer))
        self._throttle_pub.publish(Float32(data=float(throttle)))
        self._steering_pub.publish(Float32(data=float(steer)))

    def _lidar_cb(self, msg):
        # Overwrite frame_id: the incoming 'lidar' frame is a child of
        # roboracer_1 in the bridge's own /tf tree, not of our base_link.
        msg.header.frame_id = 'autodrive_lidar'
        self._scan_pub.publish(msg)

    def _imu_cb(self, msg):
        msg.header.frame_id = 'autodrive_imu'
        self._imu_pub.publish(msg)

    def _steering_cb(self, msg):
        self._current_steering = msg.data

    def _left_encoder_cb(self, msg):
        speed = self._wheel_speed(msg, self._last_left_angle, self._last_left_stamp)
        self._last_left_angle = msg.position[0]
        self._last_left_stamp = msg.header.stamp
        if speed is not None:
            self._left_speed = speed
            self._publish_odom(msg.header.stamp)

    def _right_encoder_cb(self, msg):
        speed = self._wheel_speed(msg, self._last_right_angle, self._last_right_stamp)
        self._last_right_angle = msg.position[0]
        self._last_right_stamp = msg.header.stamp
        if speed is not None:
            self._right_speed = speed

    def _wheel_speed(self, msg, last_angle, last_stamp):
        if last_angle is None or last_stamp is None:
            return None
        dt = (Time.from_msg(msg.header.stamp) - Time.from_msg(last_stamp)).nanoseconds / 1e9
        if dt <= 0.0:
            return None
        delta = _unwrap_delta(msg.position[0] - last_angle)
        return (delta / dt) * self.wheel_radius

    def _publish_odom(self, stamp):
        speed = 0.5 * (self._left_speed + self._right_speed)
        angular_velocity = speed * math.tan(self._current_steering) / self.wheelbase

        if self._last_odom_stamp is not None:
            dt = (Time.from_msg(stamp) - Time.from_msg(self._last_odom_stamp)).nanoseconds / 1e9
            if dt > 0.0:
                self._x += speed * math.cos(self._yaw) * dt
                self._y += speed * math.sin(self._yaw) * dt
                self._yaw += angular_velocity * dt
        self._last_odom_stamp = stamp

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame
        odom.pose.pose.position.x = self._x
        odom.pose.pose.position.y = self._y
        odom.pose.pose.orientation.z = math.sin(self._yaw / 2.0)
        odom.pose.pose.orientation.w = math.cos(self._yaw / 2.0)
        odom.pose.covariance[0] = 0.2
        odom.pose.covariance[7] = 0.2
        odom.pose.covariance[35] = 0.4
        odom.twist.twist.linear.x = speed
        odom.twist.twist.angular.z = angular_velocity
        self._odom_pub.publish(odom)


def main(args=None):
    rclpy.init(args=args)
    node = AutoDriveBridgeAdapter()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
