import pandas as pd
import matplotlib.pyplot as plt

class rpt_ele():
    def __init__(self, rpt_file):
        """
        rpt_file (str): the name of the .rpt file you wante to read
        """
        self.rpt = rpt_file
        self.file_contents = self.get_file_contents()
        self.total_flooding = self.get_total_flooding()
        self.flooding_df = self.get_flooding_df()

    def get_file_contents(self):
        with open(self.rpt, 'r') as f:
            lines = f.readlines()
            return lines

    def get_ele_df(self, ele):
        start_line_no, end_line_no = self.get_ele_lines(ele)
        col_titles = self.file_contents[start_line_no+3].strip().split()[:2]
        col_titles.extend(self.file_contents[start_line_no+2].strip().split())
        content_start = start_line_no + 5
        content_end = end_line_no - 1
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

    def get_start_line(self, start_string, start=0):
        for i in range(len(self.file_contents[start:])):
            line_no = i + start
            line_lower = self.file_contents[line_no].strip().lower()
            start_string_lower = start_string.lower().strip()

            if line_lower.startswith(start_string_lower):
                return i

        # raise error if start line of section not found
        raise ValueError('Start line for string {} not found'.format(start_string))

    def get_end_line(self, start_line):
        for i in range(len(self.file_contents[start_line:])):
            line_no = start_line + i
            if self.file_contents[line_no].strip() == "" and \
            self.file_contents[line_no + 1].strip() == "":
                return line_no
        # raise error if end line of section not found
        raise ValueError('Did not find end of section starting on line {}'.format(start_line))

    def get_ele_lines(self, ele):
        start_line = self.get_start_line("<<< {} >>>".format(ele.lower()))
        end_line = self.get_end_line(start_line)
        return start, end

    def get_total_flooding(self):
        fl_start_line = self.get_start_line("Flooding Loss")
        return float(self.file_contents[fl_start_line].split()[-1])

    def get_flooding_df(self):
        """
        return a dataframe of the data under the "Node Flooding Summary" heading.
        """
        fl_summary_start = self.get_start_line("Node Flooding Summary")
        fl_summary_end = self.get_end_line(fl_summary_start)
        fl_lines = self.file_contents[fl_summary_start:fl_summary_end]
        # reverse the list of strings so data is on top. makes it easier to handle (less skipping)
        fl_lines.reverse()
        first_row = True
        for i, l in enumerate(fl_lines):
            if not l.strip().startswith('---'):
                # add as row to dataframe
                line = l.strip().split()
                if first_row:
                    df = pd.DataFrame(columns = range(len(line)))
                    first_row = False
                df.loc[i] = line
            else:
                return df




    
