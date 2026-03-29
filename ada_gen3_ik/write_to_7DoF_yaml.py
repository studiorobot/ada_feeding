import yaml

def write_to_7DoF_def_yaml(action_name,jnt_val):
    """
    Write 7 DoF joint values to default yaml file

    Loads in the ada_feeding_action_servers_default_gen3.yaml file and updates the joint values for the given action with the new 
    7 DoF joints values for use on the Gen3 Kinova Arm 

    Args: 
        action_name (string): The action that corresponds to where the joint values will locate the end effector, from YAML
        jnt_val (list): 7 joint values in a list in radians to be written into the new file
        
    Returns:
        No return variables. Saves joint values to ada_feeding_action_servers_default_gen3.yaml
        
    """
    # Reading nested data from a YAML file
    with open("src/ada_feeding/config/ada_feeding_action_servers_default_gen3.yaml", 'r') as file:
        action_servers_default = yaml.safe_load(file)
    
    # update the dict with the new joint values
    action_servers_default.get('ada_feeding_action_servers').get('ros__parameters').get('default').get(action_name).get('tree_kwargs').update({"joint_positions": jnt_val})

    # Writing the data to a YAML file
    with open("src/ada_feeding/config/ada_feeding_action_servers_default_gen3.yaml", 'w') as file:
        yaml.dump(action_servers_default, file)

def write_to_7DoF_custom_yaml(scene,action_name,jnt_val):
    """
    Write 7 DoF joint values to custom yaml file

    Loads in the ada_feeding_action_servers_custom_gen3.yaml file and updates the joint values for the given action with the new 
    7 DoF joints values for use on the Gen3 Kinova Arm 

    Args: 
        scene (string): the planning scene for the ada configuration
        action_name (string): The action that corresponds to where the joint values will locate the end effector, from YAML
        jnt_val (list): 7 joint values in a list in radians to be written into the new file
        
    Returns:
        No return variables. Saves joint values to ada_feeding_action_servers_custom_gen3.yaml
        
    """
    # Reading nested data from a YAML file
    with open("src/ada_feeding/config/ada_feeding_action_servers_custom_gen3.yaml", 'r') as file:
        action_servers_custom = yaml.safe_load(file)
    
    # update the dict with the new joint values
    action_servers_custom.get('ada_feeding_action_servers').get('ros__parameters').get(scene).update({action_name: jnt_val})
 
    # Writing the data to a YAML file
    with open("src/ada_feeding/config/ada_feeding_action_servers_custom_gen3.yaml", 'w') as file:
        yaml.dump(action_servers_custom, file)