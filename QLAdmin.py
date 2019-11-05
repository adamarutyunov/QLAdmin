import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidgetItem, QMainWindow
from PyQt5.QtWidgets import QListWidgetItem, QFileDialog, QInputDialog
from PyQt5.QtGui import QColor
from PyQt5 import uic, QtGui, QtWidgets, Qt, QtCore
from PyQt5.Qt import QDialog


class QLWindow:
    def close(self):
        QLA.close(self)


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
        self.append(execution)

        return self.execute(execution)

    def update(self, table, key, value, row=[], options=""):
        if row:
            condition = "WHERE " + " AND ".join(row)
        else:
            condition = ""
    
        execution = f"UPDATE {table} SET {key}={value} {condition} {options}"
        self.append(execution)

        return self.execute(execution)

    def select(self, table, columns="*", row=[], options=""):
        if row:
            condition = "WHERE " + " AND ".join(row)
        else:
            condition = ""

        if type(columns) == list:
            columns = ", ".join(columns)

        execution = f"SELECT {columns} FROM {table} {condition} {options}"
        
        return self.execute(execution)

    def reindex_table(self, table):
        print(123)
        execution = f"REINDEX {table}"
        self.executions.append(execution)
        return self.execute(execution)

    def commit(self):
        self.connection.commit()

    def delete_table(self, table):
        execution = f"DROP TABLE {table}"
        self.executions.append(execution)
        return self.execute(execution)

    def truncate_table(self, table):
        execution = f"TRUNCATE TABLE {table}"
        self.executions.append(execution)
        return self.execute(execution)

    def execute(self, execution):
        self.cursor.execute(execution)
        return self.cursor.fetchall()

    def import_commits(self, commits):
        self.executions += commits

    def get_commit_list(self):
        return self.executions

    def clear_commits(self):
        self.executions = []

    def append(self, execution):
        if not self.executions or execution != self.executions[-1]:
            self.executions.append(execution)


class QLTableViewWindow(QMainWindow, QLWindow):
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
        except Exception as e:
            raise e
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


class QLDatabaseViewWindow(QMainWindow, QLWindow):
    def __init__(self, database):
        super().__init__()
        uic.loadUi("DatabaseViewWindow.ui", self)
        
        self.init_tables_list()
        self.commit_button.clicked.connect(self.ask_for_commits)
        self.edit_button.clicked.connect(lambda: self.edit_table(self.get_current_item_text()))
        self.delete_button.clicked.connect(lambda: self.delete_table(self.get_current_item_text()))
        self.truncate_button.clicked.connect(lambda: self.truncate_table(self.get_current_item_text()))
        self.reindex_button.clicked.connect(lambda: self.reindex_table(self.get_current_item_text()))
        self.sql_button.clicked.connect(self.sql_query)
        
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

    def get_current_item(self):
        return self.tables_list.item(self.tables_list.currentRow(), 0)

    def get_current_item_text(self):
        return self.get_current_item().text()

    def edit_table(self, table):
        QLA.open_window(QLTableViewWindow, table)

    def delete_table(self, table):
        PQLE.delete_table(table)

    def check_button_state(self):
        if len(self.tables_list.selectedItems()) == 0:
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.truncate_button.setEnabled(False)
            self.reindex_button.setEnabled(False)
        else:
            self.edit_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.truncate_button.setEnabled(True)
            self.reindex_button.setEnabled(True)

    def ask_for_commits(self):
        try:
            QLA.open_window(QLCommitDialog)
        except Exception as e:
            print(e)

    def truncate_table(self, table):
        QLA.open_window(QLDialog, f"truncate table {table}", lambda: PQLE.truncate_table(table))

    def reindex_table(self, table):
        QLA.open_window(QLDialog, f"reindex table {table}", lambda: PQLE.reindex_table(table))

    def sql_query(self):
        QLA.open_window(QLInputDialog, "Query:", PQLE.execute)

class QLAdmin:
    def __init__(self):
        self.windows = [QLLoginWindow()]

    def close_window(self, window):
        window.hide()
        self.windows.remove(window)

    def open_window(self, window, *options):
        self.windows.append(window(*options))


class QLCommitDialog(QDialog, QLWindow):
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


class QLLoginWindow(QMainWindow, QLWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("LoginWindow.ui", self)

        self.opendb_button.clicked.connect(self.open_db)
        self.createdb_button.clicked.connect(self.create_db)

        self.show()

    def init_db(self, dbname):
        global connection
        global PQLE

        connection = sqlite3.connect(dbname)
        PQLE = PyQL(connection)

        QLA.open_window(QLDatabaseViewWindow, dbname)
        self.close()

    def open_db(self):
        dbname = QFileDialog.getOpenFileName(self, 'Open existing database', '', "SQLite DB (*.db)")[0]
        if dbname:
            self.init_db(dbname)

    def create_db(self):
        QLA.open_window(QLInputDialog, "Database name:", self.init_db)


class QLInputDialog(QDialog, QLWindow):
    def __init__(self, obj, func):
        super().__init__()
        uic.loadUi("InputDialog.ui", self)

        self.function = func
        self.ok_button.clicked.connect(self.run_function)
        self.cancel_button.clicked.connect(self.close)
        self.label.setText(obj)

        self.show()

    def run_function(self):
        self.function(self.input.text())
        self.close()

class QLDialog(QDialog, QLWindow):
    def __init__(self, action, func):
        super().__init__()
        uic.loadUi("Dialog.ui", self)

        self.function = func
        self.label.setText(self.label.text().replace('"Action"', action))
        self.cancel_button.clicked.connect(self.close)
        self.ok_button.clicked.connect(self.run_function)

        self.show()

    def run_function(self):
        self.function()
        self.close()
    


def excepthook(type, value, tback):
    sys.__excepthook__(type, value, tback)
sys.excepthook = excepthook


app = QApplication(sys.argv)
QLA = QLAdmin()
sys.exit(app.exec()) 
