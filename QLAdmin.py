import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidgetItem, QMainWindow
from PyQt5.QtGui import QWindow
from PyQt5 import uic, QtGui, QtWidgets, Qt, QtCore

class PyQL:
    def __init__(self, connection):
        self.connection = connection
        self.cursor = self.connection.cursor()
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
        print(execution)
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
        self.connection.commit()

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

    def import_commits(self, commits):
        self.executions += commits


class QLTableViewWindow(QMainWindow):
    def __init__(self, table_name):
        super().__init__()
        uic.loadUi("TableViewWindow.ui", self)
        self.table_name = table_name
        self.setWindowTitle(self.table_name)
        self.table_init()
        self.show()

        self.local_commits = []

        self.ok_button.clicked.connect(self.export_local_commits)
        self.table.cellChanged.connect(lambda i, j: self.change_cell(i, j))

    def table_init(self, query=""):
        if not query:
            table = PQLE.select(self.table_name)
        else:
            table = PQLE.select(query)
    
        self.python_table = table
        self.column_names = PQLE.execute(f"PRAGMA table_info({self.table_name})")
        self.column_names = list(map(lambda x: x[1], self.column_names))
        
        self.table.setColumnCount(len(self.column_names))
        self.table.setHorizontalHeaderLabels(self.column_names)
        self.table.setRowCount(0)

        self.header = self.table.horizontalHeader()

        for i in range(len(self.header)):
            self.header.setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
        
        for i, row in enumerate(table):
            self.table.setRowCount(self.table.rowCount() + 1)
            for j, elem in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(elem)))

    def close(self):
        QLA.close_window(self)

    def export_local_commits(self):
        PQLE.import_commits(self.local_commits)
        self.local_commits = []

    def change_cell(self, i, j):
        first_column = self.column_names[0]
        target_column = self.column_names[j]
        value = self.python_table[i][0]
        PQLE.update(self.table_name, target_column, self.table.item(i, j).text(), [f"{first_column}={value}"])


    def closeEvent(self, event):
        self.close()
        event.accept()


class QLDatabaseViewWindow(QMainWindow):
    def __init__(self, database):
        super().__init__()
        uic.loadUi("DatabaseViewWindow.ui", self)
        
        self.init_tables_table()
        self.commit_button.clicked.connect(self.commit_database)

        self.show()

    def init_tables_table(self):

        self.tables_list = PQLE.execute("""SELECT name FROM sqlite_master
                                        WHERE type = 'table' AND name NOT LIKE 'sqlite_%'""")
        
        self.tables_table.setColumnCount(2)
        self.tables_table.setRowCount(0)

        self.header = self.tables_table.horizontalHeader()

        self.header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        
        for i, row in enumerate(self.tables_list):
            self.tables_table.setRowCount(self.tables_table.rowCount() + 1)
            
            item_table = QTableWidgetItem(row[0])
            item_table.setFlags(item_table.flags() ^ QtCore.Qt.ItemIsEditable ^ QtCore.Qt.ItemIsSelectable)
            self.tables_table.setItem(i, 0, item_table)

            empty_item = QTableWidgetItem()
            empty_item.setFlags(empty_item.flags() ^ QtCore.Qt.ItemIsEditable ^ QtCore.Qt.ItemIsSelectable)
            self.tables_table.setItem(i, 1, empty_item)

    def commit_database(self):
        PQLE.commit()


class QLAdmin:
    def __init__(self):
        self.windows = [QLDatabaseViewWindow("films.db")]

    def close_window(self, window):
        window.hide()
        self.windows.remove(window)



connection = sqlite3.connect("films.db")
PQLE = PyQL(connection)

app = QApplication(sys.argv)
QLA = QLAdmin()
sys.exit(app.exec()) 
