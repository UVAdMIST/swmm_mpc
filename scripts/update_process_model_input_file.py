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
