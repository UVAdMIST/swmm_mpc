import re

def update_depths_or_flows(lines, i, depths_or_flows, col_name):
    init_depth_loc = lines[i+1].find(col_name)
    for obj_id in depths_or_flows:
        for j, l in enumerate(lines[i:]):
            if l.startswith(obj_id):
                new_value_string = "{: <11.4f}".format(depths_or_flows[obj_id]) 
                new_string = l[:init_depth_loc] + new_value_string + l[init_depth_loc+11: ]
                lines[i+j] = new_string
                break 
    return lines

def update_simulation_date_time(lines, i, new_datetime):
    new_date = new_datetime.strftime("%m/%d/%Y")
    new_time = new_datetime.strftime("%H:%M:%S")
    lines[i] = re.sub(r'\d{2}\\\d{2}\\\d{2}', new_date, lines[i])
    lines[i+1] = re.sub(r'\d{2}:\d{2}:\d{2}', new_time, lines[i+1])
    return lines

def update_process_model_file(inp_file, new_date_time, new_depths, new_flows):
    with open(inp_file, 'r') as tmp_file:
        lines = tmp_file.readlines()

    for i,l in enumerate(lines):
        if l.startswith("START_DATE"):
            new_lines = update_simulation_date_time(lines, i, new_date_time)
        elif l.startswith("[JUNCTIONS]"):
            new_lines  = update_depths_or_flows(lines, i, new_depths['junctions'], "InitDepth")
        elif l.startswith("[STORAGE]"):
            new_lines = update_depths_or_flows(lines, i, new_depths['storage'], "InitDepth")
        elif l.startswith("[CONDUITS]"):
            new_lines = update_depths_or_flows(lines, i, new_flows, "InitFlow")

    with open(inp_file, 'w') as tmp_file:
        tmp_file.writelines(lines)

def find_control_section(lines):
    # check if CONTROL section is in the input file
    control_line = None
    end_control_section = None
    for i, l in enumerate(lines):
        if l.startswith("[CONTROLS]"):
           control_line = i 
           for j, ll in enumerate(lines[i+1:]):
               if ll.startswith("["):
                   end_control_section = j + i
                   break
    return control_line, end_control_section

def get_control_rule_string(control_time_step, policies):
    new_lines = ["[CONTROLS] \n"]
    rule_number = 0
    # control_time_step is in seconds. convert to hours
    control_time_step_hours = control_time_step/3600.
    for structure_id in policies:
        for i, policy_step in enumerate(policies[structure_id]):
            l1 = "RULE R{} \n".format(rule_number)
            l2 = "IF SIMULATION TIME < {:.3f} \n".format((i+1) * control_time_step_hours)
            l3 = "THEN {} SETTING = {} \n".format(structure_id, policy_step) 
            l4 = "\n"
            new_lines.extend([l1, l2, l3, l4])
            rule_number += 1
    return new_lines

def update_controls(inp_file, control_time_step, policies):
    """
    policies: dict; structure id (e.g., ORIFICE R1) as key, list of settings as value; 

    """
    with open(inp_file, 'r') as inpfile:
        lines = inpfile.readlines()
    
    control_line, end_control_line = find_control_section(lines)
    if control_line and end_control_line:
        del lines[control_line: end_control_line]
    else:
        control_line = len(lines)

    control_rule_string = get_control_rule_string(control_time_step, policies)
    lines[control_line: control_line] = control_rule_string
    
    with open(inp_file, 'w') as inpfile:
        inpfile.writelines(lines)
