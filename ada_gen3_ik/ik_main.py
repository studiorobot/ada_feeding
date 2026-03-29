import yaml
import subprocess
from kinova_gen3_ik import output_7dof_value
from write_to_7DoF_yaml import write_to_7DoF_def_yaml, write_to_7DoF_custom_yaml

##TODO: Investigate hardwareInterface unknown tag error
#Convert xacro to URDF
gen2_xacro_file = "src/ada_ros2/ada_description/urdf/ada.jaco2.xacro"
gen3_xacro_file = "src/ada_ros2/ada_description/urdf/ada.gen3.xacro"
gen2_result = subprocess.run(
    ['xacro', gen2_xacro_file],
    capture_output=True,
    text=True
)
gen3_result = subprocess.run(
    ['xacro', gen3_xacro_file],
    capture_output=True,
    text=True
)

# Read in nested data from the default YAML file
with open('src/ada_feeding/config/ada_feeding_action_servers_default.yaml', 'r') as file:
    action_servers_default = yaml.safe_load(file)

# extract 6DoF joint values from default dictionary
action_jnt_pairs = {}
action_resting_jnt_pairs = {}
action_goal_config_pairs = {}
start_key = action_servers_default.get('ada_feeding_action_servers').get('ros__parameters').get('default')
server_names = start_key.get('server_names')
for key in start_key.keys():
    for action in server_names:
        if key == action:
            if start_key[key].get('tree_kwargs') != None:
                jnt_pos = start_key[key].get('tree_kwargs').get('joint_positions')
                if jnt_pos != None:
                    action_jnt_pairs[key] = jnt_pos
                resting_jnt_pos = start_key[key].get('tree_kwargs').get('resting_joint_positions')
                if resting_jnt_pos != None:
                    action_resting_jnt_pairs[key] = resting_jnt_pos
                goal_config = start_key[key].get('tree_kwargs').get('goal_configuration')
                if goal_config != None:
                    action_goal_config_pairs[key] = goal_config

# Read in nested data into a dictionary from the custom YAML file
with open('src/ada_feeding/config/ada_feeding_action_servers_custom.yaml', 'r') as file:
    action_servers_custom = yaml.safe_load(file)

# extract 6DoF joint values from custom dictionary
scenes = {}
scene_list = action_servers_custom.get('ada_feeding_action_servers').get('ros__parameters')
for scene in scene_list:
    custom_action_jnt_pairs = {}
    custom_action_resting_jnt_pairs = {}
    custom_action_goal_config_pairs = {}
    custom_actions = {}
    start_key = scene_list[scene]
    if hasattr(start_key, 'keys'):
        for key in start_key.keys():
            if "resting_joint_positions" in key:
                custom_actions[key] = scene_list[scene].get(key)
            elif "joint_positions" in key:
                custom_actions[key] = scene_list[scene].get(key)
            elif "goal_configuration" in key:
                custom_actions[key] = scene_list[scene].get(key)
        scenes[scene] = custom_actions

#check if conversion from xacro to URDF was successful
#if it was, 
if gen2_result.returncode != 0:
    print(f" Gen2 Xacro processing failed: {gen2_result.stderr}")
else:
    if gen3_result.returncode != 0:
        print(f" Gen3 Xacro processing failed: {gen3_result.stderr}")
    else:
        gen2_urdf_string = gen2_result.stdout
        gen3_urdf_string = gen3_result.stdout

        # loop through each of the dict where joint values are stored from the YAML files
        for action_names,jnt_val in action_jnt_pairs.items():
            #calculate new 7 DoF joint values q_sol
            q_sol = output_7dof_value(gen2_urdf_string,gen3_urdf_string,jnt_val)
            #write new joint values to a new default YAML file
            write_to_7DoF_def_yaml(action_names,q_sol)
        for action_names,jnt_val in action_resting_jnt_pairs.items():
            #calculate new 7 DoF joint values q_sol
            q_sol = output_7dof_value(gen2_urdf_string,gen3_urdf_string,jnt_val)
            #write new joint values to a new default YAML file
            write_to_7DoF_def_yaml(action_names,q_sol)
        for action_names,jnt_val in action_goal_config_pairs.items():
            #calculate new 7 DoF joint values q_sol
            q_sol = output_7dof_value(gen2_urdf_string,gen3_urdf_string,jnt_val)
            #write new joint values to a new default YAML file
            write_to_7DoF_def_yaml(action_names,q_sol)

        for scene in scenes:
            for action_name,jnt_val in scenes[scene].items():
                #calculate new 7 DoF joint values q_sol
                q_sol = output_7dof_value(gen2_urdf_string,gen3_urdf_string,jnt_val)
                #write new joint values to a new default YAML file
                write_to_7DoF_custom_yaml(scene,action_name,q_sol)

