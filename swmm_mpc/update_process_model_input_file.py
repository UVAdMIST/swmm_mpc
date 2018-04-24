import re
import pandas as pd


def update_simulation_date_time(lines, i, new_datetime):
    """
    replace both the analysis and reporting start date and times
    """
    new_date = new_datetime.strftime("%m/%d/%Y")
    new_time = new_datetime.strftime("%H:%M:%S")
    lines[i] = re.sub(r'\d{2}\\\d{2}\\\d{2}', new_date, lines[i])
    lines[i+1] = re.sub(r'\d{2}:\d{2}:\d{2}', new_time, lines[i+1])
    lines[i+2] = re.sub(r'\d{2}\\\d{2}\\\d{2}', new_date, lines[i+2])
    lines[i+3] = re.sub(r'\d{2}:\d{2}:\d{2}', new_time, lines[i+3])
    return lines

def update_process_model_file(inp_file, new_date_time, hs_file):
    with open(inp_file, 'r') as tmp_file:
        lines = tmp_file.readlines()

    # update date and times 
    date_section_start, date_section_end = find_section(lines, "START_DATE")
    new_lines = update_simulation_date_time(lines, date_section_start, new_date_time)

    # update to use hotstart file
    file_section_start, file_section_end = find_section(lines, "[FILES]")
    new_hotstart_string = get_file_section_string(hs_file)
    lines = update_section(lines, new_hotstart_string, file_section_start, file_section_end)

    new_date_time_string = new_date_time.strftime("%Y.%m.%d_%H.%M.%S")
    new_file_end = "{}.inp".format(new_date_time_string)
    new_file_name = inp_file.replace(".inp", new_file_end)
    with open(inp_file, 'w') as tmp_file:
        tmp_file.writelines(lines)

def find_section(lines, section_name):
    # check if CONTROL section is in the input file
    start_line = None
    end_line = None
    for i, l in enumerate(lines):
        if l.startswith("{}".format(section_name)):
           start_line = i 
           for j, ll in enumerate(lines[i+1:]):
               if ll.startswith("["):
                   end_line = j + i
                   break
           if not end_line:
               end_line = len(lines) 
    return start_line, end_line

def update_section(lines, new_lines, old_section_start=None, old_section_end=None):
    """
    lines: list of strings; text of .inp file read into list of strings
    new_lines: list of strings; list of strings for replacing old section
    old_section_start: int; position of line where replacing should start (will append to end of 
    file if 'None' and section end is 'None' passed as argument)
    old_section_end: int; position of line where replacing should end

    """
    if  old_section_start and old_section_end:
        del lines[old_section_start: old_section_end]
    else:
        old_section_start = len(lines)

    lines[old_section_start: old_section_start] = new_lines
    return lines 

def get_file_section_string(hs_filename):
    new_lines = ["[FILES] \n"]
    new_lines.append('USE HOTSTART "{}"\n \n'.format(hs_filename))
    return new_lines

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

    

def update_controls_and_hotstart(inp_file, control_time_step, policies, hs_file=None):
    """
    control_time_step: number; in seconds
    policies: dict; structure id (e.g., ORIFICE R1) as key, list of settings as value; 

    """
    with open(inp_file, 'r') as inpfile:
        lines = inpfile.readlines()
    
    control_line, end_control_line = find_section(lines, "[CONTROLS]")

    control_rule_string = get_control_rule_string(control_time_step, policies)
    updated_lines = update_section(lines, control_rule_string, control_line, end_control_line)
    
    if hs_file:
        file_section_start, file_section_end = find_section(updated_lines, "[FILES]")
        hs_lines = get_file_section_string(hs_file)
        updated_lines = update_section(updated_lines, hs_lines, file_section_start, file_section_end)

    with open(inp_file, 'w') as inpfile:
        inpfile.writelines(updated_lines)

def update_controls_with_resulting_policy(inp_file, control_time_step, policy_file):
    policy_df = pd.read_csv(policy_file)
    policy_columns = [col for col in policy_df.columns if "setting" in col]
    policy_dict = {}
    for policy_col in policy_columns:
        structure_id = policy_col.split("_")[-1]
        policy_dict[structure_id] = policy_df[policy_col].tolist()

    update_controls_and_hotstart(inp_file, control_time_step, policy_dict)   
    
def read_hs_filename(inp_file):
    with open(inp_file, 'r') as f:
        for line in f:
            if line.startswith("USE HOTSTART"):
                hs_filename = line.split()[-1].replace('"', '')
                return hs_filename
