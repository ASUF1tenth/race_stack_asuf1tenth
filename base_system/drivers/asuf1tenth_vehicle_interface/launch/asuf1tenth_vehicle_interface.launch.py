import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    fesc_port_val = LaunchConfiguration('fesc_port').perform(context)
    esp_port_val = LaunchConfiguration('esp_port').perform(context)
    config_val = LaunchConfiguration('config').perform(context)

    # 1. FESC C++ Driver Node (BLDC Motor Control in /fesc namespace)
    fesc_params = [config_val]
    if fesc_port_val:
        fesc_params.append({'port': fesc_port_val})

    fesc_driver_node = Node(
        package='vesc_driver',
        executable='vesc_driver_node',
        name='vesc_driver_node',
        namespace='fesc',
        parameters=fesc_params,
        output='screen'
    )

    # 2. ESP32 Python Vehicle Interface Node (IMU & Steering Servo + Motor Topic Router)
    asuf1tenth_vehicle_interface_node = Node(
        package='asuf1tenth_vehicle_interface',
        executable='asuf1tenth_vehicle_interface.py',
        name='asuf1tenth_vehicle_interface',
        output='screen',
        parameters=[{
            'esp_port': esp_port_val,
            'esp_baudrate': 115200,
            'imu_frame_id': 'imu',
            'imu_topic': 'sensors/imu/raw',
            'servo_cmd_topic': 'commands/servo/position',
            'imu_cov_z': 0.0001,
        }]
    )

    return [fesc_driver_node, asuf1tenth_vehicle_interface_node]


def generate_launch_description():
    pkg_dir = get_package_share_directory('asuf1tenth_vehicle_interface')
    vesc_config_default = os.path.join(pkg_dir, 'params', 'vesc_config.yaml')

    declare_fesc_port_arg = DeclareLaunchArgument(
        'fesc_port',
        default_value='/dev/fesc',
        description='Serial port for the FESC (BLDC motor control and feedback)'
    )

    declare_esp_port_arg = DeclareLaunchArgument(
        'esp_port',
        default_value='/dev/esp',
        description='Serial port for the ESP32 (Steering Servo control and IMU telemetry)'
    )

    declare_config_arg = DeclareLaunchArgument(
        'config',
        default_value=vesc_config_default,
        description='Path to VESC configuration YAML file'
    )

    return LaunchDescription([
        declare_fesc_port_arg,
        declare_esp_port_arg,
        declare_config_arg,
        OpaqueFunction(function=launch_setup)
    ])
