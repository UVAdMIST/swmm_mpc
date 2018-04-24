from shutil import copyfile
from get_contributing_area import get_upstream_nodes
from swmmio import swmmio
model_input_file = "../hague_model/v2014_Hague_EX_10yr_MHHW_mod2_trim.inp"
model_input_file_tmp = model_input_file.replace(".inp", "_tmp.inp")
copyfile(model_input_file, model_input_file.replace(".inp", "_tmp.inp"))
mymodel = swmmio.Model(model_input_file)
nodes = mymodel.nodes()
cons = mymodel.conduits()
subs = mymodel.subcatchments()

non_important_outfalls = ['D14200', 'D143000', 'D14860', 'D1489', 'D14240', 'D14153', 'D14110', 
            'E14310', 'E145200', 'E14330', 'D14165', 'D14124', 'D14300']
non_rel_nodes = []
for out in non_important_outfalls:
    us_nodes = get_upstream_nodes(out, cons)
    non_rel_nodes.extend(us_nodes)
    non_rel_nodes.append(out)

relevant_lines = []
with open(model_input_file_tmp, 'r') as inpfile:
    for line in inpfile:
        if all(node not in line for node in non_rel_nodes):
            relevant_lines.append(line)

with open(model_input_file_tmp, 'w') as inpfile:
    inpfile.writelines(relevant_lines)
