import pandas as pd
import matplotlib.pyplot as plt

class rpt_ele():
    def __init__(self, rpt_file, ele, var):
        """
        rpt_file (str): the name of the .rpt file you wante to read
        ele (str): the name of the element (link or node). e.g., "Node J2" or "Link C1"
        """
        self.rpt = rpt_file
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
        df["datetime"] = pd.to_datetime(df["Date"] + " " + df["Time"])
        df["datetime"] = df["datetime"].dt.round('min')
        df.set_index("datetime", inplace=True)
        for c in df.columns:
            try:
                df[c] = pd.to_numeric(df[c])
            except:
                pass
        return df

    def get_file_contents(self):
        with open(self.rpt, 'r') as f:
            lines = f.readlines()
            return lines

    def get_ele_line(self):
        start = None
        for i, l in enumerate(self.file_contents):
            la = l.strip().lower()
            if la.startswith("<<< {} >>>".format(self.ele.lower())):
                start = i
            if start and la == "":
                end = i
                return start, end


    
