#!/usr/bin/env python3

import os
import sys
import select
import termios
import tty
import threading
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from ackermann_msgs.msg import AckermannDriveStamped

# Key mappings matching standard teleop_twist_keyboard
MOVE_BINDINGS = {
    'i': (1.0, 0.0),   # Forward
    'o': (1.0, -1.0),  # Forward Right
    'j': (0.0, 1.0),   # Turn Left
    'l': (0.0, -1.0),  # Turn Right
    'u': (1.0, 1.0),   # Forward Left
    ',': (-1.0, 0.0),  # Reverse
    '.': (-1.0, -1.0), # Reverse Right
    'm': (-1.0, 1.0),  # Reverse Left
    'k': (0.0, 0.0),   # Stop
}

SPEED_BINDINGS = {
    'w': (1.1, 1.0),  # Increase linear max
    'x': (0.9, 1.0),  # Decrease linear max
    'e': (1.0, 1.1),  # Increase angular max
    'c': (1.0, 0.9),  # Decrease angular max
    'q': (1.1, 1.1),  # Increase both
    'z': (0.9, 0.9),  # Decrease both
}

# ANSI colors
COLOR_RESET = "\033[0m"
COLOR_RED_BG = "\033[41m\033[1;37m"
COLOR_GREEN_BG = "\033[42m\033[1;37m"
COLOR_YELLOW = "\033[1;33m"
COLOR_CYAN = "\033[1;36m"
COLOR_BOLD = "\033[1m"


class KillSwitchTeleopNode(Node):

    def __init__(self):
        super().__init__('kill_switch_teleop')

        self.declare_parameter('topic_name', '/teleop')
        self.declare_parameter('max_speed', 2.0)
        self.declare_parameter('max_steering', 0.34)  # ~20 degrees in radians
        self.declare_parameter('repeat_rate', 20.0)    # Hz
        self.declare_parameter('mode', 'interactive')   # 'interactive' or 'passthrough'

        self.topic_name = self.get_parameter('topic_name').value
        self.max_speed = float(self.get_parameter('max_speed').value)
        self.max_steering = float(self.get_parameter('max_steering').value)
        self.repeat_rate = float(self.get_parameter('repeat_rate').value)
        self.mode = self.get_parameter('mode').value

        # Speed scaling factors
        self.speed_scale = 0.5
        self.turn_scale = 1.0

        # Motion state
        self.target_linear = 0.0
        self.target_angular = 0.0

        # Emergency Kill Switch State
        self.is_killed = False

        # Publisher to /teleop (Ackermann Mux input, priority 100)
        self.pub_teleop = self.create_publisher(AckermannDriveStamped, self.topic_name, 10)

        # Subscriber to /cmd_vel (for passthrough mode or external twist input)
        self.sub_cmd_vel = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        # Timer for continuous streaming to /teleop
        timer_period = 1.0 / self.repeat_rate if self.repeat_rate > 0 else 0.05
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.get_logger().info(f"Kill Switch Teleop Node started on {self.topic_name} at {self.repeat_rate} Hz.")

    def cmd_vel_callback(self, msg: Twist):
        """Called when /cmd_vel receives a message (used in passthrough mode)."""
        if not self.is_killed and self.mode == 'passthrough':
            self.target_linear = msg.linear.x
            self.target_angular = msg.angular.z

    def timer_callback(self):
        """Continuously streams AckermannDriveStamped messages to /teleop at repeat_rate Hz."""
        drive = AckermannDriveStamped()
        drive.header.stamp = self.get_clock().now().to_msg()

        if self.is_killed:
            # Emergency Stop Signal: Force speed=0 and steering=0
            drive.drive.speed = 0.0
            drive.drive.steering_angle = 0.0
        else:
            # Normal velocity conversion with safety max bounds clamping
            speed = self.target_linear * self.speed_scale * self.max_speed
            if speed > 0:
                speed = min(speed, self.max_speed)
            elif speed < 0:
                speed = max(speed, -self.max_speed)

            steering = self.target_angular * self.turn_scale * self.max_steering
            if steering > 0:
                steering = min(steering, self.max_steering)
            elif steering < 0:
                steering = max(steering, -self.max_steering)

            drive.drive.speed = float(speed)
            drive.drive.steering_angle = float(steering)

        self.pub_teleop.publish(drive)

    def print_status(self):
        """Prints terminal banner and instructions."""
        os.system('clear')
        print("=" * 65)
        print(f"{COLOR_CYAN}{COLOR_BOLD}  F1TENTH KEYBOARD TELEOP & KILL SWITCH NODE {COLOR_RESET}")
        print("=" * 65)

        if self.is_killed:
            print(f"\n   STATUS:  {COLOR_RED_BG}  🚨 EMERGENCY KILL SWITCH ENGAGED - CAR HALTED  {COLOR_RESET}\n")
            print(f"   {COLOR_YELLOW}Press [SPACEBAR] to DISENGAGE Kill Switch and resume control.{COLOR_RESET}")
        else:
            print(f"\n   STATUS:  {COLOR_GREEN_BG}  ✅ RELEASED - TELEOP / NAVIGATION ACTIVE  {COLOR_RESET}\n")
            print(f"   {COLOR_YELLOW}Press [SPACEBAR] to IMMEDIATELY ENGAGE EMERGENCY KILL SWITCH.{COLOR_RESET}")

        print("-" * 65)
        print("   Moving Around:             Speed Limits:")
        print("      u    i    o               w/x : increase/decrease max speed")
        print("      j    k    l               e/c : increase/decrease max turn")
        print("      m    ,    .               q/z : increase/decrease both")
        print()
        print("   Key details:")
        print("   - 'i': Forward        - ',': Reverse        - 'k': Stop motion")
        print("   - 'j': Left           - 'l': Right          - 'u'/'o': Fwd L/R")
        print("   - 'm'/'.': Rev L/R    - [SPACEBAR]: Toggle Emergency Kill Switch")
        print("   - CTRL-C to quit")
        print("-" * 65)
        print(f"   Current Speed Scale: {self.speed_scale:.2f} | Turn Scale: {self.turn_scale:.2f}")
        print(f"   Target Linear: {self.target_linear:.2f} | Target Angular: {self.target_angular:.2f}")
        print("=" * 65)


def get_tty_device():
    """Returns a valid TTY file object if available (sys.stdin or /dev/tty fallback)."""
    if sys.stdin.isatty():
        return sys.stdin
    try:
        tty_file = open('/dev/tty', 'r')
        if tty_file.isatty():
            return tty_file
    except Exception:
        pass
    return None


def get_key(tty_device, settings):
    """Reads a single keypress from TTY without waiting for Enter."""
    fd = tty_device.fileno()
    tty.setraw(fd)
    rlist, _, _ = select.select([tty_device], [], [], 0.1)
    if rlist:
        key = tty_device.read(1)
    else:
        key = ''
    termios.tcsetattr(fd, termios.TCSADRAIN, settings)
    return key


def main(args=None):
    rclpy.init(args=args)
    node = KillSwitchTeleopNode()

    tty_device = get_tty_device()

    if tty_device is None:
        node.get_logger().warn(
            "No interactive TTY terminal detected. Running in ROS-only mode without keyboard input."
        )
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            pass
        finally:
            node.destroy_node()
            rclpy.shutdown()
        return

    fd = tty_device.fileno()
    try:
        settings = termios.tcgetattr(fd)
    except Exception as e:
        node.get_logger().error(f"Failed to get TTY attributes: {e}")
        try:
            rclpy.spin(node)
        except KeyboardInterrupt:
            pass
        finally:
            node.destroy_node()
            rclpy.shutdown()
        return

    # Spin ROS 2 callbacks in a separate thread so timer keeps publishing at 20Hz
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()

    node.print_status()

    try:
        while rclpy.ok():
            key = get_key(tty_device, settings)

            if key == ' ':
                # Toggle Emergency Kill Switch
                node.is_killed = not node.is_killed
                if node.is_killed:
                    node.target_linear = 0.0
                    node.target_angular = 0.0
                node.print_status()

            elif key in MOVE_BINDINGS:
                lin, ang = MOVE_BINDINGS[key]
                if not node.is_killed:
                    node.target_linear = lin
                    node.target_angular = ang
                node.print_status()

            elif key in SPEED_BINDINGS:
                sp_mult, ang_mult = SPEED_BINDINGS[key]
                node.speed_scale = max(0.1, min(2.0, node.speed_scale * sp_mult))
                node.turn_scale = max(0.1, min(2.0, node.turn_scale * ang_mult))
                node.print_status()

            elif key == '\x03':  # CTRL-C
                break

    except Exception as e:
        node.get_logger().error(f"Error in keyboard reader loop: {e}")

    finally:
        try:
            termios.tcsetattr(fd, termios.TCSADRAIN, settings)
        except Exception:
            pass
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
