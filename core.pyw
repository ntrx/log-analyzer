# #!/usr/bin/env python

# python 3.7 last version 12:30 03072019
# use libs: PIP: pyqt5->pyiuc5 (for GUI
# xlswriter (for EXCEL
# pyinstaller (for executable

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import pyqtSlot
from analyzer import Ui_MainWindow
from xlsxwriter import Workbook  # before import xlswriter
from os import path
import struct
import math

struct_file = "log1.dat"
xls_name = "log-export.xlsx"

elements = 100
max_elements = int(elements)
max_sessions = max_elements*10

data_type = ["" for i in range(max_elements)]
data_name = ["" for i in range(max_elements)]
data_size = ["" for i in range(max_elements)]
data_print = ["0" for i in range(max_elements)]
data_view = ["" for i in range(max_elements)]
data_sessions_print = ["0" for i in range(max_sessions-1)]


class MainWindow(QtWidgets. QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        # gui init
        super(MainWindow, self).__init__(parent)
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)

        # init text labels and 'end' panel
        self.label.setText("Select fields to be extracted")
        self.label_2.setText("Select session to display")
        self.label_5.setVisible(False)
        self.textBrowser.setVisible(False)
        self.textBrowser_2.setVisible(False)
        self.textBrowser_3.setVisible(False)
        self.progressBar.setVisible(False)
        self.progressBar.setValue(0)

        self.load_file()

        self.pushButton.clicked.connect(self.on_list_clicked)  # button 'EXTRACT' push all code to Excel
        self.pushButton_4.clicked.connect(self.on_list_clear)  # button 'NONE' clear all selection on lists
        self.pushButton_2.clicked.connect(self.on_list_all)  # button 'ALL' select all fields in both lists
        self.pushButton_5.clicked.connect(self.on_button_open)

    def load_file(self):
        global data_type
        global data_name
        global data_size
        global data_print
        global data_view
        global data_sessions_print
        global data_values_sessions

        self.label_5.setVisible(True)
        self.label_5.setText("Loading log....")
        self.textBrowser.setVisible(False)
        self.textBrowser_2.setVisible(False)
        self.textBrowser_3.setVisible(False)
        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)
        # msg if no file
        if not path.exists(struct_file):
            self.label_5.setText("Error while loading file.")
            return  # sys.exit()
        self.progressBar.setValue(5)
        # try to open file
        fp = open(struct_file, "rb")
        self.progressBar.setValue(10)
        arr_header_size = fp.read(16)
        arr_records_n = fp.read(16)
        fp.close()

        global records_n
        global sessions_n
        global dt_ind
        global dn_ind
        global ds_ind
        global dp_ind
        global error

        byte_str = str(arr_header_size, 'utf-8', errors='ignore')
        for i in range(0, len(byte_str)):
            if byte_str[i] == '=' and byte_str[i + 1] == '[':
                j = i + 2
                tmp_name = ""
                while byte_str[j] != ']':
                    tmp_name += byte_str[j]
                    j = j + 1
        header_size = int(tmp_name)
        print("File HEADER size: ", header_size)
        self.progressBar.setValue(20)
        byte_str = str(arr_records_n, 'utf-8', errors='ignore')
        for i in range(0, len(byte_str)):
            if byte_str[i] == '=' and byte_str[i + 1] == '[':
                j = i + 2
                tmp_name = ""
                while byte_str[j] != ']':
                    tmp_name += byte_str[j]
                    j = j + 1
        records_n = int(tmp_name)
        self.progressBar.setValue(30)
        print("Records available: ", records_n)

        fp = open(struct_file, "rb")
        fp.seek(16 + 16, 0)
        data = fp.read(header_size)
        data = str(data, 'utf-8', errors='ignore')
        fp.close()

        error = 0
        dt_ind = 0
        dn_ind = 0
        ds_ind = 0
        dp_ind = 0
        index = 0
        while index != len(data):
            # reading data type
            if data[index] == '$' and data[index + 1] == '[':
                index += 2
                data_type[dt_ind] = ""
                for j in range(index, index + 16):
                    if data[j] == ']':
                        break
                    data_type[dt_ind] += data[j]
                dt_ind += 1

            # reading data type name
            if data[index] == '!' and data[index + 1] == '[':
                index += 2
                data_name[dn_ind] = ""
                for j in range(index, index + 16):
                    if data[j] == ']':
                        break
                    data_name[dn_ind] += data[j]
                dn_ind += 1

            # reading data type size
            if data[index] == '=' and data[index + 1] == '[':
                index += 2
                data_size[ds_ind] = ""
                for j in range(index, index + 16):
                    if data[j] == ']':
                        break
                    data_size[ds_ind] += data[j]
                ds_ind += 1

            index += 1
        self.progressBar.setValue(50)
        if dt_ind == dn_ind == ds_ind:
            print("Read OK", dt_ind)
        else:
            print("Read ERROR", dt_ind, dn_ind, ds_ind)

        global data_values
        global data_values_sessions
        data_values = [["" for i in range(dt_ind + 1)] for j in range(int(records_n))]
        data_values_sessions = [["" for i in range(2)] for j in range(int(records_n))]

        data_size_total = 0
        for i in range(0, dt_ind):
            data_size_total += int(data_size[i])

        print("Struct size %d\n" % data_size_total)
        self.progressBar.setValue(60)
        fp = open(struct_file, "rb")

        fp.seek(32 + header_size, 0)

        for k in range(0, records_n):
            for i in range(dt_ind):
                byte_arr = fp.read(int(data_size[i]))

                if data_type[i] == "unsigned int":
                    binary_id = 0
                    j = 0
                    for c in range(0, len(byte_arr)):
                        binary_id |= byte_arr[c] << j
                        j = j + int(data_size[i]) * 2
                    if math.isnan(binary_id):
                        binary_id = -1
                        error = 1
                    data_values[k][i] = binary_id

                if data_type[i] == "char":
                    char_id = ""
                    for c in range(0, len(byte_arr)):
                        if byte_arr[c] == 0x00:
                            break
                        if byte_arr[c] == 0x09:
                            break
                        char_id += chr(byte_arr[c])
                    data_values[k][i] = char_id

                if data_type[i] == "double":
                    binary_id = struct.unpack_from('d', byte_arr)[0]
                    if math.isnan(binary_id):
                        binary_id = -1
                        error = 1
                    data_values[k][i] = binary_id

                if data_type[i] == "float":
                    binary_id = struct.unpack_from('f', byte_arr)[0]
                    if math.isnan(binary_id):
                        binary_id = -1
                        error = 1
                    data_values[k][i] = binary_id

        fp.close()
        self.progressBar.setValue(75)
        for i in range(0, dt_ind):
            data_view[i] = data_type[i] + "\t" + data_name[i] + " " + data_size[i]

        second = False
        j = 0
        for i in range(0, records_n):
            if data_values[i][2] != data_values[i - 1][2]:
                if second:
                    data_values_sessions[j][1] = i
                    j = j + 1
                second = True
                data_values_sessions[j][0] = i
        data_values_sessions[j][1] = records_n
        self.progressBar.setValue(85)
        sessions_n = j  # number of sessions found
        print("Session found: ", sessions_n)
        if sessions_n == 0:
            print("No session found, exit.")
            return
        data_sessions = ["" for i in range(sessions_n + 1)]

        for i in range(sessions_n + 1):
            session_records = 0
            print("Session %d started at %s" % (i, data_values[data_values_sessions[i][0]][5]))
            for n in range(data_values_sessions[i][0], data_values_sessions[i][1]):
                session_records += 1
            print("records found: %d" % session_records)
            print("Session %d ended at %s" % (i, data_values[data_values_sessions[i][1] - 1][5]))
            data_sessions[i] = "launch " + str(i) + " at " + data_values[data_values_sessions[i][0]][4] + " " + \
                               data_values[data_values_sessions[i][1] - 1][5] + " recs " + str(session_records)
        self.progressBar.setValue(90)
        list_of_fields = list(data_view)
        model = QtGui.QStandardItemModel()
        self.listView.setModel(model)
        for i in range(0, dt_ind):
            item = QtGui.QStandardItem(list_of_fields[i])
            model.appendRow(item)
        self.label_3.setText("Selected: %d of %d" % (0, max_elements))

        list_of_sessions = list(data_sessions)
        model2 = QtGui.QStandardItemModel()
        self.listView_2.setModel(model2)
        for i in range(0, sessions_n + 1):
            item = QtGui.QStandardItem(list_of_sessions[i])
            model2.appendRow(item)
        self.label_4.setText("Selected: %d of %d" % (0, max_sessions))
        self.progressBar.setValue(100)
        self.label_5.setText("Log loaded.")
        self.progressBar.setValue(0)

        self.listView.selectionModel().selectionChanged.connect(self.elements_list_change)
        self.listView_2.selectionModel().selectionChanged.connect(self.session_list_change)

    def elements_list_change(self):
        self.textBrowser_2.setVisible(False)
        selected = self.listView.selectedIndexes()
        select = 0
        self.label_3.setText("Selected: %d of %d" % (select, max_elements))
        for it in selected:
            select += 1
            self.label_3.setText("Selected: %d of %d" % (select, max_elements))

    def session_list_change(self):
        self.textBrowser_3.setVisible(False)
        selected = self.listView_2.selectedIndexes()
        select = 0
        self.label_4.setText("Selected: %d of %d" % (select, max_sessions))
        for it in selected:
            select += 1
            self.label_4.setText("Selected: %d of %d" % (select, max_sessions))

    @pyqtSlot()
    def on_button_open(self):
        global struct_file
        tmp = QFileDialog.getOpenFileName()
        struct_file = tmp[0]
        self.load_file()

    @pyqtSlot()
    def on_list_all(self):
        self.listView.selectAll()

    @pyqtSlot()
    def on_list_clear(self):
        self.listView.clearSelection()
        self.listView_2.clearSelection()

    @pyqtSlot()
    def on_list_clicked(self):
        global data_print
        global data_sessions_print

        self.textBrowser.setVisible(False)
        self.textBrowser_2.setVisible(False)
        self.textBrowser_3.setVisible(False)
        self.progressBar.setVisible(True)
        # self.progressBar.value(0)

        wbook = Workbook(xls_name)
        wsheet = wbook.add_worksheet()
        itms = self.listView.selectedIndexes()
        for it in itms:
            # print('selected item index found at %s with data: %s' % (it.row(), it.data()))
            data_print[int(it.row())] = "1"
        if len(itms) == 0:
            self.label_5.setText('nothing selected in data types list')
            return

        itms2 = self.listView_2.selectedIndexes()
        for it in itms2:
            # print('selected item index found at %s with data: %s' % (it.row(), it.data()))
            data_sessions_print[int(it.row())] = "1"
        if itms2 == 0:
            self.label_5.setText('nothing selected in session list ')
            return

        print("hello, its me")
        row = 0
        for rw_ind in range(dt_ind):
            if data_print[rw_ind] == '1':
                wsheet.write(0, row, str(data_name[rw_ind]))
                wsheet.set_column(row, row, len(str(data_name[rw_ind]))+1)
                row += 1
        if data_print[0] == '1':
            wsheet.set_column(0, 0, 6)  # first 10601
        wsheet.freeze_panes(1, 0)  # freeze first row

        row = 1
        xlsx_write = (sessions_n + 1) if (sessions_n + 1) < max_sessions else max_sessions
        proc100 = float(xlsx_write)
        for i in range(xlsx_write):
            for cl_ind in range(int(data_values_sessions[i][0]), int(data_values_sessions[i][1])):
                if data_sessions_print[i] == '1':
                    col = 0
                    for rw_ind in range(dt_ind):
                        if data_print[rw_ind] == '1':
                            wsheet.write(row, col, data_values[cl_ind][rw_ind])
                            col += 1
                            self.progressBar.setValue(int((int(i)/proc100)*100))
                    row += 1
        self.label_5.setVisible(True)
        self.label_5.setText("Saving file.")
        wbook.close()
        self.progressBar.setValue(int(100))
        print("bye")
        self.textBrowser.setVisible(True)
        if error == 1:
            self.label_5.setText("File corrupted, finished with errors")
        else:
            self.label_5.setText("No errors found.")
        data_sessions_print = ["0" for i in range(max_sessions - 1)]


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
