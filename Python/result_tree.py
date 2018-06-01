import ttk
import Tkinter as tk


class ResultTreeList(ttk.Treeview):
    def __init__(self, parent=None, **kw):
        ttk.Treeview.__init__(self, parent, **kw)
        self.make()

    def make(self):
        #self.column("#0", width=90)
        list_columns = ["pass", "partial", "fail", "total"]
        self['columns'] = ("pass", "partial", "fail", "total")

        for column in list_columns:
            self.column(column, width=40)
            self.heading(column, text=column.capitalize())

    def insert_row(self, item_name, test_desc, res):
        # res has format: ("", "", "", "")
        self.insert("", 'end', item_name, text=test_desc, values=res)

    def update_result(self, item_name, column_name, value):
        self.set(item_name, column_name, value)


if __name__ == "__main__":
    import ttk
    import Tkinter as tk
    root = tk.Tk()