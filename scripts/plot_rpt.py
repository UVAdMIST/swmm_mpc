import pandas as pd
import matplotlib.pyplot as plt

class rpt_ele():
    def __init__(self, inp_file, ele, var):
        self.inp = inp_file
        self.ele = ele
        self.var = var
        self.file_contents = self.get_file_contents()
        self.start_line_no, self.end_line_no = self.get_ele_line()
        self.ele_df = self.get_ele_df()


    def get_ele_df(self):
        col_titles = self.file_contents[self.start_line_no+3].strip().split()[:2]
        col_titles.extend(self.file_contents[self.start_line_no+2].strip().split())
        content_start = self.start_line_no + 5
        content_end = self.end_line_no - 1
        content_list = []
        for i in range(content_start, content_end):
            content_list.append(self.file_contents[i].split())
        df =  pd.DataFrame(content_list, columns=col_titles)
        df['Time'] = pd.to_datetime(df['Time'])
        df.set_index("Time", inplace=True)
        for c in df.columns:
            try:
                df[c] = pd.to_numeric(df[c])
            except:
                pass
        return df

    def get_file_contents(self):
        with open(self.inp, 'r') as f:
            lines = f.readlines()
            return lines

    def get_ele_line(self):
        start = None
        for i, l in enumerate(self.file_contents):
            la = l.strip()
            if la.startswith("<<< {} >>>".format(self.ele)):
                start = i
            if start and la == "":
                end = i
                return start, end


    
    # def plot_ts(inp_file, ele, var):


inp_file = ('../simple_model/s_s_b_50.rpt')
inp_file2 = ('../simple_model/s_s_b.rpt')
rpt = rpt_ele(inp_file, "Node J1", "Inflow")
rpt2 = rpt_ele(inp_file2, "Node J1", "Inflow")

# ax = rpt2.ele_df['Inflow'].plot()
rpt.ele_df['Inflow'].plot()
plt.show()
