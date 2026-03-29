import PyKDL as kdl
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kdl_parser'))

from PyKDL import Chain, Segment, Joint, Frame, Vector, Rotation
from PyKDL import ChainFkSolverPos_recursive, ChainIkSolverVel_pinv, ChainIkSolverPos_NR, ChainIkSolverPos_LMA
from PyKDL import JntArray

import tempfile
from urdf_parser_py.urdf import URDF
from kdl_parser import urdf

def output_7dof_value(gen2_urdf_string,gen3_urdf_string, six_jnt_val):
    """
    Convert Gen2 6DoF joint values to Gen3 7DoF joint values

    Uses the PyKDL library to convert the 6DoF joint values for a Gen2 Kinova Arm to an XYZ position
    using FK. Then uses IK to convert the XYZ position into 7 joint values for the
    Gen3 Kinova Arm

    Args:
        gen2_urdf_string (string): urdf_style string description of the Gen2 Kionova Arm
        gen3_urdf_string (string): urdf_style string description of the Gen3 Kionova Arm
        six_jnt_val (list): list of 6 joint values for 6DoF Gen2 arm to be fed into FK

    Returns:
        q_sol_list (list): list of 7 joint values returned from IK solver for Gen3 arm

    """

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', delete=False) as f:
        f.write(gen2_urdf_string)
    temp_gen2_urdf_path = f.name
    with tempfile.NamedTemporaryFile(mode='w', suffix='.urdf', delete=False) as f:
        f.write(gen3_urdf_string)
    temp_gen3_urdf_path = f.name

    # Load URDF file
    gen2_robot = URDF.from_xml_file(temp_gen2_urdf_path)
    gen3_robot = URDF.from_xml_file(temp_gen3_urdf_path)

    # Parse to KDL tree
    ok2, tree_gen2 = urdf.treeFromUrdfModel(gen2_robot)
    ok3, tree_gen3 = urdf.treeFromUrdfModel(gen3_robot)

    if not ok2:
        print("Failed to parse Gen2 URDF")
    elif not ok3:
        print("Failed to parse Gen3 URDF")
    else:
        # Extract chain from tree
        gen2_chain = tree_gen2.getChain("root", "j2n6s200_end_effector")
        gen3_chain = tree_gen3.getChain("ada_base_link", "ada_end_effector_link")

        #Create solvers
        fk_solver_gen2 = ChainFkSolverPos_recursive(gen2_chain)
        fk_solver_gen3 = ChainFkSolverPos_recursive(gen3_chain)
        ik_vel_solver = ChainIkSolverVel_pinv(gen3_chain)
        #ik_solver = ChainIkSolverPos_NR(gen3_chain, fk_solver_gen3, ik_vel_solver)
        ik_solver = ChainIkSolverPos_LMA(gen3_chain) #much better solver than NR

        # Forward kinematics
        q = JntArray(gen2_chain.getNrOfJoints())  # 6 joints
        q[0] = six_jnt_val[0]
        q[1] = six_jnt_val[1]
        q[2] = six_jnt_val[2]
        q[3] = six_jnt_val[3]
        q[4] = six_jnt_val[4]
        q[5] = six_jnt_val[5]

        # Calculate end effector position
        end_frame = Frame()
        fk_solver_gen2.JntToCart(q, end_frame)
        print("End effector position:", end_frame.p)

        # Inverse kinematics
        target_frame = Frame()
        target_frame.p = end_frame.p #Target position from Gen 2

        q_init = JntArray(gen3_chain.getNrOfJoints())  # Initial guess
        q_sol = JntArray(gen3_chain.getNrOfJoints())   # Solution

        ik_solver.CartToJnt(q_init, target_frame, q_sol)
        print("Joint solution:", [q_sol[i] for i in range(q_sol.rows())])

        # Verify the solution
        result_frame = Frame()
        fk_solver_gen3.JntToCart(q_sol, result_frame)
        print("Resulting position:", result_frame.p)

        q_sol_list = list(map(float, q_sol))

        return q_sol_list
