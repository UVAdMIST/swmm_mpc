from rpt_ele import rpt_ele
import sys
import matplotlib.pyplot as plt

rpt_file = sys.argv[1]
ele = sys.argv[2]
variable = sys.argv[3]

rpt = rpt_ele(rpt_file, ele)

ax = rpt.ele_df[variable].plot()
ax.set_title(ele)
ax.set_ylabel(variable)
plt.tight_layout()
plt.show()
