from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch.conditions import IfCondition, UnlessCondition


def generate_launch_description():
    repeat_rate_arg = DeclareLaunchArgument(
        'repeat_rate',
        default_value='20.0',
        description='Publication frequency in Hz for continuous teleop stream'
    )
    max_speed_arg = DeclareLaunchArgument(
        'max_speed',
        default_value='2.0',
        description='Maximum speed limit in m/s'
    )
    max_steering_arg = DeclareLaunchArgument(
        'max_steering',
        default_value='0.34',
        description='Maximum steering angle in radians'
    )
    topic_name_arg = DeclareLaunchArgument(
        'topic_name',
        default_value='/teleop',
        description='Output topic for high priority AckermannDriveStamped messages'
    )
    use_standard_teleop_arg = DeclareLaunchArgument(
        'use_standard_teleop',
        default_value='False',
        description='Whether to launch standard ROS teleop_twist_keyboard alongside kill_switch_node'
    )

    # 1. Primary Interactive Keyboard Teleop & Kill Switch Node
    interactive_keyboard_teleop_node = Node(
        package='stack_master',
        executable='keyboard_teleop',
        name='keyboard_teleop',
        output='screen',
        emulate_tty=True,
        parameters=[{
            'topic_name': LaunchConfiguration('topic_name'),
            'max_speed': LaunchConfiguration('max_speed'),
            'max_steering': LaunchConfiguration('max_steering'),
            'repeat_rate': LaunchConfiguration('repeat_rate'),
            'mode': 'interactive'
        }],
        condition=UnlessCondition(LaunchConfiguration('use_standard_teleop'))
    )

    # 2. Optional: Standard ROS teleop_twist_keyboard with repeat_rate continuous streaming
    standard_teleop_node = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_twist_keyboard',
        output='screen',
        emulate_tty=True,
        parameters=[{
            'repeat_rate': LaunchConfiguration('repeat_rate')
        }],
        condition=IfCondition(LaunchConfiguration('use_standard_teleop'))
    )

    # 3. Optional: Passthrough Keyboard Teleop Node when standard teleop is active
    passthrough_keyboard_teleop_node = Node(
        package='stack_master',
        executable='keyboard_teleop',
        name='keyboard_teleop_interceptor',
        output='screen',
        emulate_tty=True,
        parameters=[{
            'topic_name': LaunchConfiguration('topic_name'),
            'max_speed': LaunchConfiguration('max_speed'),
            'max_steering': LaunchConfiguration('max_steering'),
            'repeat_rate': LaunchConfiguration('repeat_rate'),
            'mode': 'passthrough'
        }],
        condition=IfCondition(LaunchConfiguration('use_standard_teleop'))
    )

    return LaunchDescription([
        repeat_rate_arg,
        max_speed_arg,
        max_steering_arg,
        topic_name_arg,
        use_standard_teleop_arg,
        interactive_keyboard_teleop_node,
        standard_teleop_node,
        passthrough_keyboard_teleop_node,
    ])
