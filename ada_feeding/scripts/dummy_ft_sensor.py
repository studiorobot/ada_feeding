#!/usr/bin/env python3
# Copyright (c) 2024-2025, Personal Robotics Laboratory
# License: BSD 3-Clause. See LICENSE.md file in root directory.

"""
This module contains a node, DummyForceTorqueSensor, which publishes sample data
to mimic the force-torque sensor on the robot. By setting parameters, users can
toggle the sensor on and off (i.e., to mimic communication with the sensor
dying) and/or start publishing zero-variance values (i.e., to mimic the sensor
getting corrupted). The node is intended to be used to test the ADAWatchdog
node.

In addition to that baseline noise, this node also approximates real contact
force: it periodically looks up (via TF) the height of a configured contact
link (the fork tine, by default) relative to a configured table surface
height, and if the link has dipped below the table, adds a synthetic force
proportional to the penetration depth. This exists because the mock/kinematic
hardware stack has no physics engine, so nothing else in simulation can
generate a signal that reflects the robot actually touching something.

Note this deliberately does NOT go through MoveIt's collision checker (e.g.
/check_state_validity): AcquireFood's MoveInto motion runs with table
collisions explicitly *allowed* in the Allowed Collision Matrix (see
AllowTable in acquire_food_tree.py), precisely so the fork can approach the
table -- so a check that respects the ACM would never see a "collision"
during the one motion this is meant to guard. A raw TF height comparison is
immune to ACM state.

Usage:
- Run the node: `ros2 run ada_feeding dummy_ft_sensor`
- Subscribe to the sensor data: `ros2 topic echo /wireless_ft/ftSensor1`
- Turn the sensor off: `ros2 param set /dummy_ft_sensor is_on False`
- Start publishing zero-variance data:
    `ros2 param set /dummy_ft_sensor std [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]`
- Start publishing data where one dimension is zero-variance:
    `ros2 param set /dummy_ft_sensor std [0.0, 0.1, 0.1, 0.1, 0.1, 0.1]`
- Disable the collision-based synthetic force:
    `ros2 param set /dummy_ft_sensor collision_stiffness 0.0`
"""

# Standard imports
import threading

# Third-party imports
from geometry_msgs.msg import WrenchStamped
import numpy as np
from rcl_interfaces.msg import ParameterDescriptor, ParameterType
import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from std_srvs.srv import SetBool
import tf2_ros


class DummyForceTorqueSensor(Node):
    """
    The DummyForceTorqueSensor class publishes sample data to mimic the
    force-torque sensor on the robot. By setting parameters, users can toggle
    the sensor on and off (i.e., to mimic communication with the sensor dying)
    and/or start publishing zero-variance values (i.e., to mimic the sensor
    getting corrupted). The node is intended to be used to test the ADAWatchdog
    node.
    """

    # pylint: disable=too-many-instance-attributes
    # Two above is fine for a dummy node.

    def __init__(self, rate_hz: float = 100.0) -> None:
        """
        Initialize the dummy force-torque sensor node.

        Parameters
        ----------
        mean: the mean of the force-torque sensor data
        std: the standard deviation of the force-torque sensor data
        rate_hz: the rate (Hz) at which to publish the force-torque sensor data
        """
        super().__init__("dummy_ft_sensor")

        self._default_callback_group = rclpy.callback_groups.ReentrantCallbackGroup()

        # Get the mean and standard deviaion of the distribution
        self.mean = self.declare_parameter(
            "mean",
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            ParameterDescriptor(
                name="mean",
                type=ParameterType.PARAMETER_DOUBLE_ARRAY,
                description="The mean of the force-torque sensor data",
            ),
        )
        self.std = self.declare_parameter(
            "std",
            [0.1, 0.1, 0.1, 0.1, 0.1, 0.1],
            ParameterDescriptor(
                name="std",
                type=ParameterType.PARAMETER_DOUBLE_ARRAY,
                description="The standard deviation of the force-torque sensor data",
            ),
        )

        # Create a parameter to toggle the sensor on and off
        self.is_on = self.declare_parameter(
            "is_on",
            True,
            ParameterDescriptor(
                name="is_on",
                type=ParameterType.PARAMETER_BOOL,
                description="Whether or not the simulated force-torque sensor is on",
            ),
        )

        # Create a service to (dummy) re-tare the sensor
        self.set_bias_request_time = None
        self.messages_since_bias_request = 0
        self.set_bias_request_time_lock = threading.Lock()
        self.set_bias_service = self.create_service(
            SetBool,
            "/wireless_ft/set_bias",
            self.set_bias_callback,
        )

        # Parameters for the synthetic, contact-based force. The mock
        # hardware stack has no physics engine, so this is the only way to
        # make simulated contact (e.g., the fork touching the table)
        # produce a force signal at all. This is computed from a raw TF
        # height comparison rather than MoveIt collision checking, since the
        # motion this guards (MoveInto) deliberately runs with table
        # collisions allowed in MoveIt's ACM (see module docstring).
        self.contact_link = self.declare_parameter(
            "contact_link",
            "forkTine",
            ParameterDescriptor(
                name="contact_link",
                type=ParameterType.PARAMETER_STRING,
                description=(
                    "The robot link (TF frame) whose height is compared against "
                    "table_top_z to estimate contact."
                ),
            ),
        )
        self.table_frame_id = self.declare_parameter(
            "table_frame_id",
            "root",
            ParameterDescriptor(
                name="table_frame_id",
                type=ParameterType.PARAMETER_STRING,
                description="The TF frame that table_top_z is expressed in.",
            ),
        )
        self.table_top_z = self.declare_parameter(
            "table_top_z",
            -0.615,
            ParameterDescriptor(
                name="table_top_z",
                type=ParameterType.PARAMETER_DOUBLE,
                description=(
                    "m. Height of the table surface in table_frame_id. This is a "
                    "fixed physical quantity (the arm is rigidly mounted to the "
                    "table), so unlike the table's x/y it is not expected to "
                    "change per-scene; keep it in sync with the table object's "
                    "z position in ada_planning_scene_kortex.yaml."
                ),
            ),
        )
        self.collision_stiffness = self.declare_parameter(
            "collision_stiffness",
            2000.0,
            ParameterDescriptor(
                name="collision_stiffness",
                type=ParameterType.PARAMETER_DOUBLE,
                description=(
                    "N/m. Synthetic contact force = stiffness * max(0, table_top_z "
                    "- contact_link height). 0.0 disables this."
                ),
            ),
        )
        self.collision_check_hz = self.declare_parameter(
            "collision_check_hz",
            20.0,
            ParameterDescriptor(
                name="collision_check_hz",
                type=ParameterType.PARAMETER_DOUBLE,
                description="Rate (Hz) at which to look up contact_link's height.",
            ),
        )

        # TF buffer/listener used to look up contact_link's height.
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # Track the latest penetration depth of contact_link below the table.
        self.latest_penetration_depth = 0.0
        self.latest_penetration_depth_lock = threading.Lock()
        self.collision_check_timer = self.create_timer(
            1.0 / self.collision_check_hz.value,
            self.check_collision,
            callback_group=self._default_callback_group,
        )

        # Create the publisher
        self.ft_msg = WrenchStamped()
        self.publisher_ = self.create_publisher(
            WrenchStamped, "/wireless_ft/ftSensor1", 1
        )

        # Publish at the specified rate
        timer_period = 1.0 / rate_hz  # seconds
        self.timer = self.create_timer(timer_period, self.publish_msg)

        self.get_logger().info("Initialized!")

    def check_collision(self) -> None:
        """
        Periodically look up contact_link's height in table_frame_id and, if
        it has dipped below table_top_z, record the penetration depth. Note
        this is independent of MoveIt's Allowed Collision Matrix by design --
        see module docstring -- and does not account for the contact link's
        x/y position, so it treats any dip below table height, anywhere in
        the workspace, as contact. That's an intentional simplification: a
        false positive far from the table is much cheaper than a missed
        collision near it.
        """
        if self.collision_stiffness.value <= 0.0:
            return

        try:
            transform = self.tf_buffer.lookup_transform(
                self.table_frame_id.value,
                self.contact_link.value,
                rclpy.time.Time(),
            )
        except tf2_ros.TransformException as exc:
            # Best-effort: if TF isn't available yet, just fall back to
            # whatever penetration depth was last recorded.
            self.get_logger().warn(
                f"Could not look up '{self.contact_link.value}' in "
                f"'{self.table_frame_id.value}': {exc}",
                throttle_duration_sec=5.0,
            )
            return

        contact_link_z = transform.transform.translation.z
        depth = max(0.0, self.table_top_z.value - contact_link_z)

        with self.latest_penetration_depth_lock:
            self.latest_penetration_depth = depth

    def set_bias_callback(self, request: SetBool.Request, response: SetBool.Response):
        """
        Callback for the set_bias service. In order to mimic the actual service,
        this returns immediately, but then stops publishing data for 0.75 sec
        (handled in `publish_msg`). This is to mimic the time it takes to
        re-tare the sensor.
        """
        response.success = True
        if request.data:
            response.message = "Successfully set the bias"
        else:
            response.message = "Successfully unset the bias"
        with self.set_bias_request_time_lock:
            self.set_bias_request_time = self.get_clock().now()
        self.get_logger().info(response.message)
        return response

    def publish_msg(self) -> None:
        """
        Publish a message to the force-torque sensor topic.
        """
        # Only publish if the sensor is on
        if self.get_parameter("is_on").value:
            # Reduce the publication rate by 10x while retaring
            with self.set_bias_request_time_lock:
                if (
                    self.set_bias_request_time is not None
                    and self.get_clock().now() - self.set_bias_request_time
                    < rclpy.duration.Duration(seconds=0.75)
                ):
                    self.messages_since_bias_request += 1
                    if (self.messages_since_bias_request % 10) != 0:
                        return

            # Get the simulated data
            ft_data = np.random.normal(
                self.get_parameter("mean").value, self.get_parameter("std").value
            )

            # Add a synthetic contact force, proportional to how far
            # contact_link is currently below the table (0.0 if not in
            # contact, or if TF is unavailable).
            with self.latest_penetration_depth_lock:
                penetration_depth = self.latest_penetration_depth
            contact_force_z = self.collision_stiffness.value * penetration_depth

            # Generate the force-torque sensor message
            self.ft_msg.header.stamp = self.get_clock().now().to_msg()
            self.ft_msg.wrench.force.x = ft_data[0]
            self.ft_msg.wrench.force.y = ft_data[1]
            self.ft_msg.wrench.force.z = ft_data[2] + contact_force_z
            self.ft_msg.wrench.torque.x = ft_data[3]
            self.ft_msg.wrench.torque.y = ft_data[4]
            self.ft_msg.wrench.torque.z = ft_data[5]

            # Publish the message
            self.publisher_.publish(self.ft_msg)


def main(args=None):
    """
    Launch the ROS node and spin.
    """
    rclpy.init(args=args)

    dummy_ft_sensor = DummyForceTorqueSensor()
    executor = MultiThreadedExecutor()
    rclpy.spin(dummy_ft_sensor, executor=executor)


if __name__ == "__main__":
    main()
