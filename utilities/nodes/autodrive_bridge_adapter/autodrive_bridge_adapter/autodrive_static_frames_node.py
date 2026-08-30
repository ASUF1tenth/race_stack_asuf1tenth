"""Publishes all AutoDRIVE-related static transforms from a single broadcaster.

Three separate `static_transform_publisher` processes each publish their own
lone transient-local message; a late-joining subscriber (e.g. Cartographer's
tf listener) can end up only seeing the most recent one instead of all three.
tf2_ros.StaticTransformBroadcaster.sendTransform() accepts a list and folds
them into one combined /tf_static message, which avoids that.

Child frames are named autodrive_lidar/autodrive_imu rather than lidar/imu:
the (unmodifiable) autodrive_roboracer bridge already publishes dynamic
world->roboracer_1->lidar/imu transforms of its own on /tf. Reusing those
names here would give 'lidar'/'imu' two different parents (base_link here,
roboracer_1 there), splitting the tf tree instead of connecting it.
"""
import rclpy
from rclpy.node import Node
from tf2_ros import StaticTransformBroadcaster
from geometry_msgs.msg import TransformStamped


def _static_tf(node, x, y, z, parent, child):
    t = TransformStamped()
    t.header.stamp = node.get_clock().now().to_msg()
    t.header.frame_id = parent
    t.child_frame_id = child
    t.transform.translation.x = x
    t.transform.translation.y = y
    t.transform.translation.z = z
    t.transform.rotation.w = 1.0
    return t


class AutoDriveStaticFrames(Node):

    def __init__(self):
        super().__init__('autodrive_static_frames')
        self._broadcaster = StaticTransformBroadcaster(self)
        self._broadcaster.sendTransform([
            _static_tf(self, 0.2733, 0.0, 0.096, 'base_link', 'autodrive_lidar'),
            _static_tf(self, 0.08, 0.0, 0.055, 'base_link', 'autodrive_imu'),
            _static_tf(self, 0.0, 0.0, 0.0, 'map', 'odom'),
        ])


def main(args=None):
    rclpy.init(args=args)
    node = AutoDriveStaticFrames()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
