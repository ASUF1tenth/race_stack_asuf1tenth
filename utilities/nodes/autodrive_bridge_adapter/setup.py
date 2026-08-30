from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'autodrive_bridge_adapter'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Mohammed159159',
    maintainer_email='mohammedhany300@gmail.com',
    description='Translates between the AutoDRIVE RoboRacer bridge topics and the ForzaETH race-stack topic conventions',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'autodrive_bridge_adapter_node = autodrive_bridge_adapter.autodrive_bridge_adapter_node:main',
            'autodrive_static_frames_node = autodrive_bridge_adapter.autodrive_static_frames_node:main'
        ],
    },
)
