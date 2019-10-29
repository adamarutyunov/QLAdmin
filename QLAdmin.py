import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidgetItem, QMainWindow
from PyQt5.QtGui import QWindow
from PyQt5 import uic

class PyQL:
    def __init__(self, connection):
        self.cursor = connection.cursor()
        self.executions = []

    def insert(self, table, values, variables=[], options=""):
        if variables:
            option = "(" + ", ".join(variables) + ")"
        else:
            option = ""

        values = "(" + ", ".join(map(lambda x: f"'{str(x)}'", values)) + ")"

        execution = f"INSERT INTO {table}{option} VALUES {values} {options}"
        self.executions.append(execution)
        self.cursor.execute(execution)

        return self.cursor.fetchall()

    def update(self, table, key, value, row=[], options=""):
        if row:
            condition = "WHERE " + " AND ".join(row)
        else:
            condition = ""

        execution = f"UPDATE {table} SET {key}={value} {condition} {options}"
        self.executions.append(execution)
        self.cursor.execute(execution)

        return self.cursor.fetchall()

    def select(self, table, columns="*", row=[], options=""):
        if row:
            condition = "WHERE " + " AND ".join(row)
        else:
            condition = ""

        if type(columns) == list:
            columns = ", ".join(columns)

        execution = f"SELECT {columns} FROM {table} {condition} {options}"
        self.executions.append(execution)
        self.cursor.execute(execution)

        return self.cursor.fetchall()

    def commit(self):
        self.cursor.commit()

    def delete_table(self, table):
        execution = f"DROP TABLE {table}"
        self.executions.append(execution)
        self.cursor.execute(execution)

    def truncate_table(self, table):
        execution = f"TRUNCATE TABLE {table}"
        self.executions.append(execution)
        self.cursor.execute(execution)

    def execute(self, execution):
        self.cursor.execute(execution)
        return self.cursor.fetchall()


class QLTableViewWindow(QMainWindow):
    def __init__(self, table_name):
        super().__init__()
        uic.loadUi("TableViewWindow.ui", self)
        self.table_name = table_name
        self.table_init()
        self.show()

        self.ok_button.clicked.connect(self.close)

    def table_init(self):
        table = PQLE.select(self.table_name)
        column_names = PQLE.execute(f"PRAGMA table_info({self.table_name})")  # this shit must be refactored
        self.table.setColumnCount(len(column_names))
        self.table.setHorizontalHeaderLabels(map(lambda x: x[1], column_names))
        self.table.setRowCount(0)
        
        for i, row in enumerate(table):
            self.table.setRowCount(self.table.rowCount() + 1)
            for j, elem in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(elem)))
                
        self.table.resizeColumnsToContents()

    def close(self):
        self.__del__()


class QLAdmin:
    def __init__(self):
        self.tablewindow = QLTableViewWindow("Films")
        #del self.tablewindow


connection = sqlite3.connect("films.db")
PQLE = PyQL(connection)

app = QApplication(sys.argv)
QLA = QLAdmin()
sys.exit(app.exec()) 
