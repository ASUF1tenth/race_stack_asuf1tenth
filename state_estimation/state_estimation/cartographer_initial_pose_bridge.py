#!/usr/bin/env python3
# Copyright 2026 ASUF1tenth / ForzaETH
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
from geometry_msgs.msg import PoseWithCovarianceStamped
from cartographer_ros_msgs.srv import FinishTrajectory, StartTrajectory


class CartographerInitialPoseBridge(Node):
    """
    ROS 2 Bridge Node that subscribes to /initialpose (geometry_msgs/PoseWithCovarianceStamped)
    and resets Google Cartographer localization by finishing the active trajectory and starting
    a new trajectory seeded at the requested 2D pose relative to the frozen map trajectory (0).
    """

    def __init__(self):
        super().__init__('cartographer_initial_pose_bridge')
        
        # Declare parameters
        self.declare_parameter('configuration_directory', '')
        self.declare_parameter('configuration_basename', 'f110_2d_loc.lua')
        self.declare_parameter('initial_pose_topic', '/initialpose')
        self.declare_parameter('initial_trajectory_id', 1)

        self.config_dir = self.get_parameter('configuration_directory').value
        self.config_basename = self.get_parameter('configuration_basename').value
        pose_topic = self.get_parameter('initial_pose_topic').value
        self.current_trajectory_id = self.get_parameter('initial_trajectory_id').value

        # Create service clients
        self.finish_client = self.create_client(FinishTrajectory, '/finish_trajectory')
        self.start_client = self.create_client(StartTrajectory, '/start_trajectory')

        # Subscribe to RViz initialpose
        self.pose_sub = self.create_subscription(
            PoseWithCovarianceStamped,
            pose_topic,
            self.initial_pose_callback,
            10
        )

        self.is_resetting = False
        self.get_logger().info(
            f"Cartographer Initial Pose Bridge active on topic '{pose_topic}'. "
            f"Config: dir='{self.config_dir}', base='{self.config_basename}'"
        )

    def initial_pose_callback(self, msg: PoseWithCovarianceStamped):
        """Callback triggered when RViz 2D Pose Estimate is published."""
        if self.is_resetting:
            self.get_logger().warn("Initial pose reset already in progress. Ignoring duplicate request.")
            return

        self.is_resetting = True
        self.get_logger().info(
            f"Received 2D Pose Estimate [x: {msg.pose.pose.position.x:.2f}, "
            f"y: {msg.pose.pose.position.y:.2f}]. Resetting Cartographer trajectory..."
        )

        # 1. Call finish_trajectory asynchronously for current trajectory
        if not self.finish_client.service_is_ready():
            self.get_logger().warn("Cartographer service '/finish_trajectory' is not ready yet.")
            self.is_resetting = False
            return

        req_finish = FinishTrajectory.Request()
        req_finish.trajectory_id = self.current_trajectory_id

        finish_future = self.finish_client.call_async(req_finish)
        finish_future.add_done_callback(
            lambda future: self._finish_trajectory_done(future, msg.pose.pose)
        )

    def _finish_trajectory_done(self, future, target_pose):
        """Callback executed after /finish_trajectory completes."""
        try:
            res = future.result()
            self.get_logger().info(f"Finished trajectory {self.current_trajectory_id} (status: {res.status.message})")
        except Exception as e:
            self.get_logger().error(f"Failed to finish trajectory {self.current_trajectory_id}: {e}")

        # Wait 300ms before starting new trajectory to allow ROS sensor queues (odom/scan) to flush
        # This prevents Cartographer OrderedMultiQueue timestamp out-of-order crashes.
        self.settle_timer = self.create_timer(
            0.3, lambda: self._delayed_start_trajectory(target_pose)
        )

    def _delayed_start_trajectory(self, target_pose):
        """Starts new trajectory after ROS sensor queues have flushed."""
        if hasattr(self, 'settle_timer') and self.settle_timer is not None:
            self.settle_timer.cancel()
            self.destroy_timer(self.settle_timer)

        if not self.start_client.service_is_ready():
            self.get_logger().error("Cartographer service '/start_trajectory' is not ready.")
            self.is_resetting = False
            return

        req_start = StartTrajectory.Request()
        req_start.configuration_directory = self.config_dir
        req_start.configuration_basename = self.config_basename
        req_start.use_initial_pose = True
        req_start.initial_pose = target_pose
        req_start.relative_to_trajectory_id = 0  # Frozen map trajectory

        start_future = self.start_client.call_async(req_start)
        start_future.add_done_callback(self._start_trajectory_done)

    def _start_trajectory_done(self, future):
        """Callback executed after /start_trajectory completes."""
        try:
            res = future.result()
            self.current_trajectory_id = res.trajectory_id
            self.get_logger().info(
                f"Successfully started new Cartographer localization trajectory ID: {self.current_trajectory_id}"
            )
        except Exception as e:
            self.get_logger().error(f"Failed to start new trajectory: {e}")
        finally:
            self.is_resetting = False


def main(args=None):
    rclpy.init(args=args)
    node = CartographerInitialPoseBridge()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.get_logger().info("Shutting down Cartographer Initial Pose Bridge node cleanly.")
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
