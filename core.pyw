# #!/usr/bin/env python

# python 3.7 last version 09:15 13042020
# use libs: PIP: pyqt5->pyiuc5 (for GUI
# xlswriter (for EXCEL
# pyinstaller (for executable

from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import pyqtSlot
from analyzer import Ui_MainWindow
from xlsxwriter import Workbook  # before import xlsxwriter
from os import path
import struct
import math
from datetime import datetime
from typing import Final  # C-like const variable

PROG_NAME = "Log Analyzer"
VERSION = "1.3.2"
RELEASE = " "

_HEADER_SIZE_: Final[int] = 16  # Размер заголовка в файле (байтов)
_HEADER_RECORDS_SIZE_: Final[int] = 16  # Размер строки с количеством записей у файле


struct_file = "log1.dat"
xls_name = "log-export"
xls_format = ".xlsx"

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
        self.setWindowTitle("%s %s %s" % (PROG_NAME, VERSION, RELEASE))

        # init text labels and 'end' panel
        self.label.setText("Select fields to be extracted")
        self.label_2.setText("Select session to display")
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

    # Ядро программы
    def load_file(self):
        global data_type  # тип переменной (int, float, char)
        global data_name  # имя переменной в исходниках СН-3307х / СН-4308х
        global data_size  # размер переменной, в байтах
        global data_print  # флаг какой то
        global data_view  # строка для отображения в окне Qt
        global data_sessions_print
        global data_values_sessions

        self.label_5.setText("Loading log....")  # Текст в строку состояния
        self.textBrowser.setVisible(False)
        self.textBrowser_2.setVisible(False)  # Текст 'SELECT SOMETHING' left panel
        self.textBrowser_3.setVisible(False)  # Текст 'SELECT SOMETHING' right panel
        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)  # Обнуление значений строки прогрес бара
        # Выдать сообщение об
        if not path.exists(struct_file):
            self.label_5.setText("Error while loading file.")
            return  # sys.exit()
        self.progressBar.setValue(5)  # 5%
        # Попытка открыть файл в бинарном режиме
        # для считывания размера структуры записи, и количества записей
        fp = open(struct_file, "rb")
        self.progressBar.setValue(10)  # 10%
        # Считывание размера заголовка (текст)
        arr_header_size = fp.read(_HEADER_SIZE_)
        # Считывание количества записей (текст)
        arr_records_n = fp.read(_HEADER_RECORDS_SIZE_)
        fp.close()

        global records_n
        global sessions_n
        global dt_ind
        global dn_ind
        global ds_ind
        global dp_ind
        global error

        # Конвертация размера заголовка с string у int
        # Запись строки находится в формате "=[3500]...
        header_size = extract_string(arr_header_size)
        print("File HEADER size: ", header_size)

        self.progressBar.setValue(20)  # 20%
        # Конвертация количества записей с string у int
        # Запись строки находится в формате "=[3500]...
        records_n = extract_string(arr_records_n)
        print("Records available: ", records_n)
        self.progressBar.setValue(30)  # 30%

        # Открытие файла для считывания структуры записей, размер которой извлекли ранее
        fp = open(struct_file, "rb")
        # Пропуск заголовочной информации
        fp.seek(_HEADER_SIZE_ + _HEADER_RECORDS_SIZE_, 0)
        # Считывание данных с файла зармером header_size
        data = fp.read(header_size)
        data = str(data, 'utf-8', errors='ignore')
        fp.close()

        error = 0
        dt_ind = 0  # Номер в массиве для типа данных переменной
        dn_ind = 0  # Номер в массиве для имени переменной
        ds_ind = 0  # Номер в массиве для размера переменной
        dp_ind = 0
        index = 0  # Номер байта с которым работаем

        # Обработчик структуры записей
        while index != len(data):
            # Считывание типа переменной
            # Пример: $[unsigned char]
            if data[index] == '$' and data[index + 1] == '[':
                index += 2
                data_type[dt_ind] = ""
                # на всякий случай, макс до 16 символа производить поиск
                for j in range(index, index + 16):
                    if data[j] == ']':
                        break
                    # Заполнение массива
                    data_type[dt_ind] += data[j]
                dt_ind += 1

            # Считывание имени переменной
            # Пример: ![current_data]
            if data[index] == '!' and data[index + 1] == '[':
                index += 2
                data_name[dn_ind] = ""
                # на всякий случай, макс до 16 символа производить поиск
                for j in range(index, index + 16):
                    if data[j] == ']':
                        break
                    # Заполнение массива
                    data_name[dn_ind] += data[j]
                dn_ind += 1

            # Считывание размера переменной
            # Пример: =[4]
            if data[index] == '=' and data[index + 1] == '[':
                index += 2
                data_size[ds_ind] = ""
                # на всякий случай, макс до 16 символа производить поиск
                for j in range(index, index + 16):
                    if data[j] == ']':
                        break
                    # Заполнение массива
                    data_size[ds_ind] += data[j]
                ds_ind += 1
            index += 1

        self.progressBar.setValue(50)  # 50%
        # Количеств совпадений (тип, имя, размер) должно совпасть
        if dt_ind == dn_ind == ds_ind:
            print("Read OK", dt_ind)
        else:
            print("Read ERROR", dt_ind, dn_ind, ds_ind)

        global data_values
        global data_values_sessions
        # Массив для списка 'тип переменной имя переменной размер'
        data_values = [["" for i in range(dt_ind + 1)] for j in range(int(records_n))]
        # Массив для отображения считанных с файла сессий
        data_values_sessions = [["" for i in range(2)] for j in range(int(records_n))]

        # Подсчёт размеров переменных
        data_size_total = 0
        for i in range(0, dt_ind):
            data_size_total += int(data_size[i])

        print("Struct size %d\n" % data_size_total)

        self.progressBar.setValue(60)  # 60%

        # Открытие файла для считывания записей
        fp = open(struct_file, "rb")
        # Перескакиваем на нужную позицию
        fp.seek(_HEADER_SIZE_ + _HEADER_RECORDS_SIZE_ + header_size, 0)

        # Основной цикл для считывания данных
        # Данные тут записаны в бинарном виде
        # Цикл по количеству записей в файле
        for k in range(0, records_n):
            # цикл по количеству переменных в структуре
            for i in range(dt_ind):
                # Последовательное считывание памяти размер с переменной структуры
                byte_arr = fp.read(int(data_size[i]))

                # Типы данных тут, должны соотвествовать типам данных в Logger модуле
                # Разбор целочисельной переменной
                if data_type[i] == "unsigned int":
                    binary_id = 0  # для хранения значения
                    j = 0
                    # Конвертация в стиле С
                    for c in range(0, len(byte_arr)):
                        binary_id |= byte_arr[c] << j
                        j = j + int(data_size[i]) * 2
                    # проверка на число
                    if math.isnan(binary_id):
                        binary_id = -1
                        error = 1
                    # сохранение в глобальную переменную
                    data_values[k][i] = binary_id

                # Разбор байтовой переменной
                if data_type[i] == "char":
                    char_id = ""
                    for c in range(0, len(byte_arr)):
                        # пропуск 0
                        if byte_arr[c] == 0x00:
                            break
                        # пропуск <TAB>
                        if byte_arr[c] == 0x09:
                            break
                        char_id += chr(byte_arr[c])
                    # Решение проблемы с кодировкой, когда русский текст отображался крякозябрами
                    encoded_string = str(char_id.encode('utf-8'), encoding='cp866')
                    if not char_id.isascii():  # Если байт не принадлежит диапазону ASCII то запись через 2 символа
                        data_values[k][i] = encoded_string[1:len(encoded_string)-1:2]
                    else:
                        data_values[k][i] = encoded_string

                # Разбор double переменной
                if data_type[i] == "double":
                    if len(byte_arr) > 0:
                        # Конвертация в стиле Python
                        binary_id = struct.unpack_from('d', byte_arr)[0]
                        if math.isnan(binary_id):
                            binary_id = -1
                            error = 1
                        data_values[k][i] = binary_id

                # Разбор float переменной
                if data_type[i] == "float":
                    if len(byte_arr) > 0:
                        binary_id = struct.unpack_from('f', byte_arr)[0]
                        if math.isnan(binary_id):
                            binary_id = -1
                            error = 1
                        data_values[k][i] = binary_id
        fp.close()

        self.progressBar.setValue(75)  # 75%
        # Форматирование строки для отображение в окне
        for i in range(0, dt_ind):
            data_view[i] = data_type[i] + "\t" + data_name[i] + " " + data_size[i]

        second = False  # TODO
        j = 0
        # Подсчет количества сессий
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

        # Отображение сессий для отладки в консоли
        for i in range(sessions_n + 1):
            session_records = 0
            print("Session %d started at %s" % (i, data_values[data_values_sessions[i][0]][5]))
            for n in range(data_values_sessions[i][0], data_values_sessions[i][1]):
                session_records += 1
            print("records found: %d" % session_records)
            print("Session %d ended at %s" % (i, data_values[data_values_sessions[i][1] - 1][5]))
            data_sessions[i] = str(i) + " at " + data_values[data_values_sessions[i][0]][4] + " " + \
                               data_values[data_values_sessions[i][1] - 1][5] + " recs " + str(session_records)
        self.progressBar.setValue(90)  # 90%

        # Формирование окна для Qt
        # поля структуры
        list_of_fields = list(data_view)
        model = QtGui.QStandardItemModel()
        self.listView.setModel(model)
        for i in range(0, dt_ind):
            item = QtGui.QStandardItem(list_of_fields[i])
            model.appendRow(item)
        self.label_3.setText("Selected: %d of %d" % (0, max_elements))

        # Поля сессий
        list_of_sessions = list(data_sessions)
        model2 = QtGui.QStandardItemModel()
        self.listView_2.setModel(model2)
        for i in range(0, sessions_n + 1):
            item = QtGui.QStandardItem(list_of_sessions[i])
            model2.appendRow(item)
        self.label_4.setText("Selected: %d of %d" % (0, max_sessions))
        self.progressBar.setValue(100)  # 100%
        successfull_load = "Log loaded. Fields="+str(dt_ind)+", sessions="+str(sessions_n)+", records="+str(records_n)
        self.label_5.setText(successfull_load)
        self.progressBar.setValue(0)  # 0% - обнуление прогресса

        # Обработчики нажатий по спискам
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

    # Открыть новый файл
    @pyqtSlot(name='on_button_open')
    def on_button_open(self):
        global struct_file
        tmp = QFileDialog.getOpenFileName(filter=struct_file)
        struct_file = tmp[0]
        self.load_file()

    # Выделить всё на панели типов переменных в структуре
    @pyqtSlot(name='on_list_all')
    def on_list_all(self):
        self.listView.selectAll()

    # Снять выделение с двух панелей
    @pyqtSlot(name='on_list_clear')
    def on_list_clear(self):
        self.listView.clearSelection()
        self.listView_2.clearSelection()

    # Кнопка извлечь данные в Excel (EXTRACT)
    @pyqtSlot(name='on_list_clicked')
    def on_list_clicked(self):
        global data_print
        global data_sessions_print

        self.textBrowser.setVisible(False)
        self.textBrowser_2.setVisible(False)
        self.textBrowser_3.setVisible(False)
        self.progressBar.setVisible(True)
        # self.progressBar.value(0)
        # Сохранение времени для формирования имени файла с датой и временем
        today = datetime.now()
        # Создание файла xlsx
        wbook_date = today.strftime("%y-%m-%d-%H-%M")
        wbook_name = xls_name+"-"+wbook_date+xls_format
        wbook = Workbook(wbook_name)
        wsheet = wbook.add_worksheet()

        # Поиск выбранных строк в панелях
        itms = self.listView.selectedIndexes()
        # выделенная строка имеет значение 1 в массиве (строковое)
        for it in itms:
            # print('selected item index found at %s with data: %s' % (it.row(), it.data()))
            data_print[int(it.row())] = "1"
        # когда ничего не выбрано
        if len(itms) == 0:
            self.label_5.setText('nothing selected in data types list')
            return

        itms2 = self.listView_2.selectedIndexes()
        # выделенная строка имеет значение 1 в массиве (строковое)
        for it in itms2:
            # print('selected item index found at %s with data: %s' % (it.row(), it.data()))
            data_sessions_print[int(it.row())] = "1"
        # когда ничего не выбрано
        if len(itms2) == 0:
            self.label_5.setText('nothing selected in session list ')
            return

        # вывод в консоль, просто так, чтобы понимать где ты(я)
        print("hello, its me")

        # запись в таблицу Excel имен переменных
        row = 0
        for rw_ind in range(dt_ind):
            if data_print[rw_ind] == '1':
                wsheet.write(0, row, str(data_name[rw_ind]))
                wsheet.set_column(row, row, len(str(data_name[rw_ind]))+1)
                row += 1
        if data_print[0] == '1':
            # размер первой колонки
            wsheet.set_column(0, 0, 6)  # first 10601
        wsheet.freeze_panes(1, 0)  # freeze first row

        row = 1
        # количество сессий, если не максимальное
        xlsx_write = (sessions_n + 1) if (sessions_n + 1) < max_sessions else max_sessions

        choosed_records = 0
        for i in range(xlsx_write):
            if data_sessions_print[i] == '1':
                choosed_records += int(data_values_sessions[i][1])-int(data_values_sessions[i][0])
        print("Records choosed for convert: ", choosed_records)

        # запись данных в таблицу
        record_counter = 0
        for i in range(xlsx_write):
            for cl_ind in range(int(data_values_sessions[i][0]), int(data_values_sessions[i][1])):
                if data_sessions_print[i] == '1':
                    col = 0
                    record_counter += 1
                    for rw_ind in range(dt_ind):
                        if data_print[rw_ind] == '1':
                            wsheet.write(row, col, data_values[cl_ind][rw_ind])
                            col += 1
                            # визуализация процесса
                            self.progressBar.setValue(int((int(record_counter)/choosed_records)*100))
                    row += 1
        self.label_5.setVisible(True)
        wsheet.autofilter(0, 0, i, dt_ind)
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


def extract_string(buffer) -> int:
    """
    Конвертация размера заголовка с string у int
    Запись строки находится в формате "=[3500]

    :param buffer: входящий буфер в строковом формате
    :type buffer: str
    :return: считанное число в формате int
    """

    buffer_str = str(buffer, 'utf-8', errors='ignore')
    for i in range(0, len(buffer_str)):
        # поиск начала '=['
        if buffer_str[i] == '=' and buffer_str[i + 1] == '[':
            j = i + 2
            tmp_name = ""
            # пока не будет конец ']'
            while buffer_str[j] != ']':
                tmp_name += buffer_str[j]
                j = j + 1
    # Возврат результата
    return int(tmp_name)


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
