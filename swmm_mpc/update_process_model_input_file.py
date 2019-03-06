import re
import pandas as pd


def update_simulation_date_time(lines, start_line, new_datetime):
    """
    replace both the analysis and reporting start date and times
    """
    new_date = new_datetime.strftime("%m/%d/%Y")
    new_time = new_datetime.strftime("%H:%M:%S")
    lines[start_line] = re.sub(r'\d{2}\\\d{2}\\\d{2}', new_date,
                               lines[start_line])
    lines[start_line+1] = re.sub(r'\d{2}:\d{2}:\d{2}', new_time,
                                 lines[start_line+1])
    lines[start_line+2] = re.sub(r'\d{2}\\\d{2}\\\d{2}', new_date,
                                 lines[start_line+2])
    lines[start_line+3] = re.sub(r'\d{2}:\d{2}:\d{2}', new_time,
                                 lines[start_line+3])
    return lines


def update_process_model_file(inp_file, new_date_time, hs_file):
    with open(inp_file, 'r') as tmp_file:
        lines = tmp_file.readlines()

    # update date and times
    date_section_start, date_section_end = find_section(lines, "START_DATE")
    update_simulation_date_time(lines, date_section_start, new_date_time)

    # update to use hotstart file
    file_section_start, file_section_end = find_section(lines, "[FILES]")
    new_hotstart_string = get_file_section_string(hs_file)
    lines = update_section(lines, new_hotstart_string, file_section_start,
                           file_section_end)

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


def update_section(lines, new_lines, old_section_start=None,
                   old_section_end=None):
    """
    lines: list of strings; text of .inp file read into list of strings
    new_lines: list of strings; list of strings for replacing old section
    old_section_start: int; position of line where replacing should start
                       (will append to end of file if 'None' and section end
                       is 'None' passed as argument)
    old_section_end: int; position of line where replacing should end

    """
    if old_section_start and old_section_end:
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
    """
    Write control rules from the policies.
    """
    new_lines = ["[CONTROLS]\n"]
    rule_number = 0
    # control_time_step is in seconds. convert to hours
    control_time_step_hours = control_time_step/3600.
    for structure_id in policies:
        structure_type = structure_id.split()[0]
        for i, policy_step in enumerate(policies[structure_id]):
            l1 = "RULE R{}\n".format(rule_number)
            l2 = "IF SIMULATION TIME < {:.3f}\n".format(
                    (i+1) * control_time_step_hours)
            # check the structure type to write 'SETTINGS' or 'STATUS'
            if structure_type == 'ORIFICE' or structure_type == 'WEIR':
                sttg_or_status = 'SETTING'
            elif structure_type == 'PUMP':
                sttg_or_status = 'STATUS'
            l3 = "THEN {} {} = {}\n".format(structure_id, sttg_or_status,
                                             policy_step)
            l4 = "\n"
            new_lines.extend([l1, l2, l3, l4])
            rule_number += 1
    return new_lines


def update_controls_and_hotstart(inp_file, control_time_step, policies,
                                 hs_file=None):
    """
    control_time_step: number; in seconds
    policies: dict; structure id (e.g., ORIFICE R1) as key, list of settings
              as value;

    """
    with open(inp_file, 'r') as inpfile:
        lines = inpfile.readlines()

    control_line, end_control_line = find_section(lines, "[CONTROLS]")

    control_rule_string = get_control_rule_string(control_time_step, policies)
    updated_lines = update_section(lines, control_rule_string, control_line,
                                   end_control_line)

    if hs_file:
        file_section_start, file_section_end = find_section(updated_lines,
                                                            "[FILES]")
        hs_lines = get_file_section_string(hs_file)
        updated_lines = update_section(updated_lines, hs_lines,
                                       file_section_start,
                                       file_section_end)

    with open(inp_file, 'w') as inpfile:
        inpfile.writelines(updated_lines)


def update_controls_with_policy(inp_file, policy_file):
    policy_df = pd.read_csv(policy_file)
    control_time_step = get_control_time_step(policy_df)
    policy_columns = [col for col in policy_df.columns if "setting" in col]
    policy_dict = {}
    for policy_col in policy_columns:
        structure_id = policy_col.split("_")[-1]
        policy_dict[structure_id] = policy_df[policy_col].tolist()

    update_controls_and_hotstart(inp_file, control_time_step, policy_dict)


def remove_control_section(inp_file):
    with open(inp_file, 'r') as inpfile:
        lines = inpfile.readlines()

    control_line, end_control_line = find_section(lines, "[CONTROLS]")
    if control_line and end_control_line:
        del lines[control_line: end_control_line]

    with open(inp_file, 'w') as inpfile:
        inpfile.writelines(lines)


def read_hs_filename(inp_file):
    with open(inp_file, 'r') as f:
        for line in f:
            if line.startswith("USE HOTSTART"):
                hs_filename = line.split()[-1].replace('"', '')
                return hs_filename


def get_control_time_step(df, dt_col="datetime"):
    times = (pd.to_datetime(df[dt_col]))
    delta_times = times.diff()
    time_step = delta_times.mean().seconds
    if time_step % 60:
        raise Exception("The time step in your file is in between minutes")
    else:
        return time_step
