from rpt_ele import rpt_ele
from update_process_model_input_file import update_controls_with_resulting_policy
import sys
import matplotlib.pyplot as plt
import subprocess
import os

inp_file = sys.argv[1]
policy_file = sys.argv[2]
control_time_step = float(sys.argv[3])

policy_id = policy_file.split("/")[-1].split("_")[-1]

update_controls_with_resulting_policy(inp_file, control_time_step, policy_file)

# run swmm
rpt_file = inp_file.replace(".inp", ".rpt") 
cmd = "swmm5 {} {}".format(inp_file, rpt_file)
subprocess.call(cmd, shell=True, stderr=subprocess.STDOUT)

rpt_obj = rpt_ele(rpt_file, "NODE J3")
variable = 'Depth'
ax = rpt_obj.ele_df[variable].plot(label=variable+" (ft)")
variable = 'Flooding'
ax = rpt_obj.ele_df[variable].plot(ax=ax, label=variable+" (million gallons)")
ax.set_title("NODE J3 results from {}".format(policy_id))
ax.legend()
plt.tight_layout()
plt.show()

rpt_obj = rpt_ele(rpt_file, "NODE ST1")
variable = 'Depth'
ax = rpt_obj.ele_df[variable].plot(label=variable+" (ft)")
ax.set_title("NODE ST1 results from {}".format(policy_id))
plt.tight_layout()
plt.show()
