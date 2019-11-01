import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidgetItem, QMainWindow, QListWidgetItem
from PyQt5.QtGui import QWindow, QColor
from PyQt5 import uic, QtGui, QtWidgets, Qt, QtCore
from PyQt5.Qt import QDialog

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

    def get_commit_list(self):
        return self.executions

    def clear_commits(self):
        self.executions = []


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
        self.close()

    def change_cell(self, i, j):
        first_column = self.column_names[0]
        target_column = self.column_names[j]
        value = self.python_table[i][0]
        try:
            PQLE.update(self.table_name, target_column, self.table.item(i, j).text(), [f"{first_column}={value}"])
        except:
            self.table.item(i, j).setBackground(QColor(255, 0, 0))
            self.table.clearSelection()
            return
        if self.table.item(i, j).text():
            self.table.item(i, j).setBackground(QColor(255, 220, 0))
        else:
            self.table.item(i, j).setBackground(QColor(200, 200, 200))
        self.table.clearSelection()

    def closeEvent(self, event):
        self.close()
        event.accept()


class QLDatabaseViewWindow(QMainWindow):
    def __init__(self, database):
        super().__init__()
        uic.loadUi("DatabaseViewWindow.ui", self)
        
        self.init_tables_list()
        self.commit_button.clicked.connect(self.ask_for_commits)
        self.edit_button.clicked.connect(lambda: self.edit_table(self.tables_list.item(self.tables_list.currentRow(), 0).text()))
        self.delete_button.clicked.connect(lambda: self.delete_table(self.tables_list.item(self.tables_list.currentRow(), 0).text()))
        self.tables_list.itemSelectionChanged.connect(self.check_button_state)

        self.check_button_state()

        self.show()

    def init_tables_list(self):
        self.tables = PQLE.select("sqlite_master", "name", ["type = 'table'", "name NOT LIKE 'sqlite_%'"])
        
        self.tables_list.setColumnCount(1)
        self.tables_list.setRowCount(0)

        self.header = self.tables_list.horizontalHeader()
        self.header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        
        for i, row in enumerate(self.tables):
            self.tables_list.setRowCount(self.tables_list.rowCount() + 1)
            
            item_table = QTableWidgetItem(row[0])
            item_table.setFlags(item_table.flags() ^ QtCore.Qt.ItemIsEditable)
            self.tables_list.setItem(i, 0, item_table)

    def edit_table(self, table):
        QLA.open_window(QLTableViewWindow, table)

    def delete_table(self, table):
        PQLE.delete_table(table)

    def check_button_state(self):
        if len(self.tables_list.selectedItems()) == 0:
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)
        else:
            self.edit_button.setEnabled(True)
            self.delete_button.setEnabled(True)

    def ask_for_commits(self):
        try:
            QLA.open_window(QLCommitDialog)
        except Exception as e:
            print(e)


class QLAdmin:
    def __init__(self):
        self.windows = [QLDatabaseViewWindow("films.db")]

    def close_window(self, window):
        window.hide()
        self.windows.remove(window)

    def open_window(self, window, *options):
        self.windows.append(window(*options))


class QLCommitDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi("CommitDialog.ui", self)
        self.fill_commits()

        self.commit_button.clicked.connect(self.commit)
        self.cancel_button.clicked.connect(self.cancel)
        self.discard_button.clicked.connect(self.discard)

        self.show()

    def fill_commits(self):
        for commit in PQLE.get_commit_list():
            self.commit_list.addItem(QListWidgetItem(commit))

    def commit(self):
        PQLE.commit()
        QLA.close_window(self)

    def cancel(self):
        QLA.close_window(self)

    def discard(self):
        PQLE.clear_commits()
        QLA.close_window(self)


connection = sqlite3.connect("films.db")
PQLE = PyQL(connection)

app = QApplication(sys.argv)
QLA = QLAdmin()
sys.exit(app.exec()) 
