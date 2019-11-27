import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QWidget, QTableWidget, QTableWidgetItem, QMainWindow
from PyQt5.QtWidgets import QListWidgetItem, QFileDialog, QInputDialog
from PyQt5.QtGui import QColor, QFontDatabase, QFont, QPixmap
from PyQt5 import uic, QtGui, QtWidgets, Qt, QtCore
from PyQt5.Qt import QDialog


class QLWindow:
    # This class is parent for other classes.
    def close(self):
        # Method for nice window close
        QLA.close(self)

    def closeEvent(self, event):
        # Close handler
        self.close()
        event.accept()


class PyQL:
    # SQL shell for Python by me
    def __init__(self, connection, dbname):
        self.dbname = dbname.split("/")[-1].split(".")[0]
        self.connection = connection
        self.cursor = self.connection.cursor()
        self.executions = []

    def insert(self, table, values, variables=[], options=""):
        # Insert row
        if variables:
            option = "(" + ", ".join(variables) + ")"
        else:
            option = ""

        values = "(" + ", ".join(map(str, values)) + ")"

        execution = f"INSERT INTO {table}{option} VALUES {values} {options}"
        self.append(execution)

        return self.execute(execution)

    def update(self, table, key, value, row=[], options=""):
        # Update table
        if row:
            condition = "WHERE " + " AND ".join(row)
        else:
            condition = ""
    
        execution = f"UPDATE {table} SET {key}={value} {condition} {options}"
        self.append(execution)

        return self.execute(execution)

    def select(self, table, columns="*", row=[], options=""):
        # Select by query
        if row:
            condition = "WHERE " + " AND ".join(row)
        else:
            condition = ""

        if type(columns) == list:
            columns = ", ".join(columns)

        execution = f"SELECT {columns} FROM {table} {condition} {options}"
        
        return self.execute(execution)

    def reindex_table(self, table):
        # Reindex table
        execution = f"REINDEX {table}"
        return self.execute(execution)

    def commit(self):
        # Commit
        self.connection.commit()

    def delete_table(self, table):
        # Delete table
        execution = f"DROP TABLE {table}"
        return self.execute(execution)

    def truncate_table(self, table):
        # Truncate table
        execution = f"DELETE FROM {table}"
        return self.execute(execution)

    def execute(self, execution):
        # Execute special query and return it result
        self.cursor.execute(execution)
        return self.cursor.fetchall()

    def import_commits(self, commits):
        # Import local commits from class (QLTableViewWindow as ex.)
        for c in commits:
            self.append(c)

    def get_commit_list(self):
        # Get self commit list
        return self.executions

    def clear_commits(self):
        # Clear commit list
        self.executions = []

    def append(self, execution):
        # Add execuion to self list
        if not self.executions or execution != self.executions[-1]:
            self.executions.append(execution)

    def add_column(self, table, column_name, data_type, default_value=""):
        # Add column (field) to a table
        execution = f"""ALTER TABLE {table}
                        ADD COLUMN {column_name}
                        {data_type} {'DEFAULT ' + default_value if default_value else ''}"""
        self.execute(execution)

    def rename_table(self, table, new_name):
        # Rename a table
        execution = f"ALTER TABLE {table} RENAME TO {new_name}"
        self.execute(execution)

    def rename_column(self, table, column, new_name):
        # Rename a column (not working in Python)
        execution = f"ALTER TABLE {table} RENAME COLUMN {column} TO {new_name}"
        print(execution)
        self.execute(execution)

    def create_table(self, table_name, columns):
        # Create table from created columns
        def prepare_field(field):
            # Preparing field description from tuple
            out = ""
            out += str(field[0]) + " "
            out += str(field[1]) + " "
            if field[2]:
                out += "DEFAULT " + field[2] + " "
            if field[3]:
                out += "PRIMARY KEY "
            if field[4]:
                out += "UNIQUE "
            return out

        execution = f"CREATE TABLE {table_name} ({', '.join(map(prepare_field, columns))})"
        self.execute(execution)

    def vacuum(self):
        # Vacuum database (isn't working in Python)
        execution = f"VACUUM {self.dbname}"
        self.execute(execution)

    def delete(self, table, row=[], options=""):
        # Delete row
        if row:
            condition = "WHERE " + " AND ".join(row)
        else:
            condition = ""

        execution = f"DELETE FROM {table} {condition} {options}"
        self.append(execution)
        self.execute(execution)

    def get_dbname(self):
        # Get name of database
        return self.dbname


class QLLoginWindow(QMainWindow, QLWindow):
    # Main login window. You see it at the start
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/LoginWindow.ui", self)

        self.setStyleSheet("background-image: url('img/background.jpg')")
        self.setWindowTitle("QLAdmin")

        self.opendb_button.clicked.connect(self.open_db)
        self.createdb_button.clicked.connect(self.create_db)

        self.show()
        self.repaint()

    def init_db(self, dbname):
        # Creating connection and redirecting to new window
        global connection
        global PQLE

        connection = sqlite3.connect(dbname)
        PQLE = PyQL(connection, dbname)

        QLA.open_window(QLDatabaseViewWindow, dbname)
        self.close()

    def open_db(self):
        # Open file selection window
        dbname = QFileDialog.getOpenFileName(self, 'Open existing database', '', "SQLite DB (*.db)")[0]
        if dbname:
            self.init_db(dbname)

    def create_db(self):
        # Open input dialog for creating a database
        QLA.open_window(QLInputDialog, "Database name:", self.init_db)


class QLDatabaseViewWindow(QMainWindow, QLWindow):
    # Class for viewing list of tables (whole database)
    def __init__(self, database):
        super().__init__()
        uic.loadUi("ui/DatabaseViewWindow.ui", self)

        self.setWindowTitle(PQLE.get_dbname())
        
        self.init_tables_list()
        self.commit_button.clicked.connect(self.ask_for_commits)
        self.edit_button.clicked.connect(lambda: self.edit_table(self.get_current_item_text()))
        self.delete_button.clicked.connect(lambda: self.delete_table(self.get_current_item_text()))
        self.truncate_button.clicked.connect(lambda: self.truncate_table(self.get_current_item_text()))
        self.reindex_button.clicked.connect(lambda: self.reindex_table(self.get_current_item_text()))
        self.rename_button.clicked.connect(lambda: self.rename_table(self.get_current_item_text()))

        self.fields_button.clicked.connect(self.view_table_fields)
        self.newtable_button.clicked.connect(self.create_table)
        self.sql_button.clicked.connect(self.sql_query)
        
        self.tables_list.itemSelectionChanged.connect(self.check_button_state)
        self.tables_list.itemDoubleClicked.connect(lambda: self.edit_table(self.get_current_item_text()))
        self.tables_list.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

        self.check_button_state()

        self.show()

    def init_tables_list(self):
        # Load tables list in main table
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
        # Get selected QTableWidgetItem
        return self.tables_list.item(self.tables_list.currentRow(), 0)

    def get_current_item_text(self):
        # Get text of current selected QTableWidgetItem
        return self.get_current_item().text()

    def edit_table(self, table):
        # Open table editing window
        QLA.open_window(QLTableViewWindow, table)

    def delete_table(self, table):
        # Delete table
        QLA.open_window(QLDialog, f"delete table {table}", lambda: (PQLE.delete_table(table), self.init_tables_list()))

    def check_button_state(self):
        # Disable buttons if no table selected
        # Enable is at least one table selected
        if len(self.tables_list.selectedItems()) == 0:
            self.edit_button.setEnabled(False)
            self.delete_button.setEnabled(False)
            self.truncate_button.setEnabled(False)
            self.reindex_button.setEnabled(False)
            self.fields_button.setEnabled(False)
            self.rename_button.setEnabled(False)
        else:
            self.edit_button.setEnabled(True)
            self.delete_button.setEnabled(True)
            self.truncate_button.setEnabled(True)
            self.reindex_button.setEnabled(True)
            self.fields_button.setEnabled(True)
            self.rename_button.setEnabled(True)

    def closeEvent(self, event):
        # Overload close event to open QLLoginWindow again
        self.close()
        QLA.open_window(QLLoginWindow)
        event.accept()

    def ask_for_commits(self):
        # Open commit dialog window
        QLA.open_window(QLCommitDialog)

    def truncate_table(self, table):
        # Truncate table
        QLA.open_window(QLDialog, f"truncate table {table}", lambda: PQLE.truncate_table(table))

    def reindex_table(self, table):
        # Reindex table
        QLA.open_window(QLDialog, f"reindex table {table}", lambda: PQLE.reindex_table(table))

    def sql_query(self):
        # Open input dialog for query
        QLA.open_window(QLInputDialog, "Query:", self.execute_sql)

    def view_table_fields(self):
        # Open field view window
        table = self.get_current_item_text()
        QLA.open_window(QLFieldViewWindow, table)

    def rename_table(self, table):
        # Open rename table window
        QLA.open_window(QLInputDialog, "New name:", lambda new: (self.rename(table, new), self.init_tables_list()))

    def rename(self, table, new_name):
        # Rename table
        PQLE.rename_table(table, new_name)
        self.init_tables_list()

    def create_table(self):
        # Open table creation window
        QLA.open_window(QLTableCreateWindow, self.init_tables_list)

    def execute_sql(self, query):
        # Execute custom SQL and parsing to get columns
        # if query like SELECT
        while ", " in query:
            query = query.replace(", ", ",")
        q = query.split()
        if q[0] == "SELECT":
            columns = q[1].split(",")
        else:
            columns = []
        if columns == ["*"]:
            columns = []
        results = PQLE.execute(query)
        if results:
            QLA.open_window(QLResultsViewWindow, results, columns)


class QLTableViewWindow(QMainWindow, QLWindow):
    # Class for editing tables
    def __init__(self, table_name):
        super().__init__()
        uic.loadUi("ui/TableViewWindow.ui", self)
        self.table_name = table_name
        self.setWindowTitle(self.table_name)
        self.table_init()
        self.table.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.show()

        self.local_commits = []

        self.ok_button.clicked.connect(self.export_local_commits)
        self.insert_button.clicked.connect(self.insert_row)
        self.delete_button.clicked.connect(self.delete_row)

    def lam(self, i, j):
        # pseudo-lambda function
        self.change_cell(i, j)

    def table_init(self):
        # Load tables list
        try:
            self.table.cellChanged.disconnect(self.lam)
        except:
            pass
        table = PQLE.select(self.table_name)
    
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
                if type(self.python_table[i][j]) is str:
                    self.table.setItem(i, j, QTableWidgetItem("'" + elem + "'"))
                elif self.python_table[i][j] is None:
                    self.table.setItem(i, j, QTableWidgetItem("NULL"))
                else:
                    self.table.setItem(i, j, QTableWidgetItem(str(elem)))

        self.table.cellChanged.connect(self.lam)

    def export_local_commits(self):
        # Export local commits to PQLE
        PQLE.import_commits(self.local_commits)
        self.local_commits = []
        self.close()

    def change_cell(self, i, j):
        # Cell changed event
        first_column = self.column_names[0]
        target_column = self.column_names[j]
        value = self.table.item(i, 0).text()
        try:
            PQLE.update(self.table_name, target_column, self.table.item(i, j).text(), [f"{first_column}={value}"])
        except:
            self.table.item(i, j).setBackground(QColor(255, 0, 0))
            self.table.clearSelection()
            return
        if self.table.item(i, j).text() not in ["NULL", "''", '""']:
            self.table.item(i, j).setBackground(QColor(255, 220, 0))
        else:
            self.table.item(i, j).setBackground(QColor(200, 200, 200))
        self.table.clearSelection()

    def insert_row(self):
        # Open row insertion window
        QLA.open_window(QLRowInsertWindow, self.table_name)

    def delete(self, row):
        # Delete row
        first_column = self.column_names[0]
        value = self.table.item(row, 0).text()
        PQLE.delete(self.table_name, [f"{first_column}={value}"])
        self.table_init()

    def delete_row(self):
        # Open row deletion window
        QLA.open_window(QLDialog, "delete this row", lambda: self.delete(self.table.currentRow()))


class QLRowInsertWindow(QMainWindow, QLWindow):
    # Row insertion window
    def __init__(self, table_name):
        super().__init__()
        uic.loadUi("ui/RowInsertWindow.ui", self)

        self.setWindowTitle("Row insert")
        self.table_name = table_name
        self.label.setText(self.label.text().replace("TableName", self.table_name))

        self.cancel_button.clicked.connect(self.close)
        self.ok_button.clicked.connect(self.insert)

        self.init_table()
        self.show()

    def init_table(self):
        # Load tables list
        self.table.setColumnCount(3)
        self.table.setRowCount(0)
        self.table.setHorizontalHeaderLabels(["Field name", "Field type", "Value"])

        self.column_names = PQLE.execute(f"PRAGMA table_info({self.table_name})")
        self.table.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

        self.header = self.table.horizontalHeader()

        for i in range(len(self.header)):
            self.header.setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
        
        for i, row in enumerate(self.column_names):
            self.table.setRowCount(self.table.rowCount() + 1)
            
            item_table = QTableWidgetItem(self.column_names[i][1])
            item_table.setFlags(item_table.flags() ^ QtCore.Qt.ItemIsEditable)
            self.table.setItem(i, 0, item_table)

            item_table = QTableWidgetItem(self.column_names[i][2])
            item_table.setFlags(item_table.flags() ^ QtCore.Qt.ItemIsEditable)
            self.table.setItem(i, 1, item_table)

    def insert(self):
        # Insert row to a table
        values = []
        for i in range(self.table.rowCount()):
            values.append(self.table.item(i, 2).text())

        PQLE.insert(self.table_name, values)
        self.close()


class QLFieldViewWindow(QMainWindow, QLWindow):
    # Window for viewing table fields
    def __init__(self, table):
        super().__init__()
        uic.loadUi("ui/FieldViewWindow.ui", self)
        self.table_name = table

        self.setWindowTitle(f"Fields of {self.table_name}")
        self.name_label.setText(self.name_label.text().replace('"TableName"', self.table_name))

        self.column_names = PQLE.execute(f"PRAGMA table_info({self.table_name})")

        self.add_column_button.clicked.connect(self.add_column)
        self.rename_column_button.clicked.connect(self.rename_column)

        self.table.itemSelectionChanged.connect(self.check_button_state)
        self.table.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.check_button_state()

        self.init_table()
        self.show()

    def init_table(self):
        # Load fields and theirs data types
        self.table.setColumnCount(2)
        self.table.setRowCount(0)
        self.table.setHorizontalHeaderLabels(["Field name", "Field type"])

        self.header = self.table.horizontalHeader()

        for i in range(len(self.header)):
            self.header.setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
        
        for i, row in enumerate(self.column_names):
            self.table.setRowCount(self.table.rowCount() + 1)
            
            item_table = QTableWidgetItem(self.column_names[i][1])
            item_table.setFlags(item_table.flags() ^ QtCore.Qt.ItemIsEditable)
            self.table.setItem(i, 0, item_table)

            item_table = QTableWidgetItem(self.column_names[i][2])
            item_table.setFlags(item_table.flags() ^ QtCore.Qt.ItemIsEditable)
            self.table.setItem(i, 1, item_table)

    def check_button_state(self):
        # Disable rename column button if needs (now always disabled)
        if len(self.table.selectedItems()) == 0:
            self.rename_column_button.setEnabled(False)
        else:
            self.rename_column_button.setEnabled(False)

    def rename_column(self):
        # Open column rename window
        current_column = self.table.item(self.table.currentRow(), 0).text()
        QLA.open_window(QLFieldRenameWindow, self.table_name, current_column)
        
    def add_column(self):
        # Open column add window
        QLA.open_window(QLAddFieldWindow, self.table_name)


class QLAddFieldWindow(QMainWindow, QLWindow):
    # Class for adding a field to a table
    def __init__(self, table):
        super().__init__()
        uic.loadUi("ui/AddFieldWindow.ui", self)
        self.table = table
        self.current_type = ""
        self.setWindowTitle(f"Add field to {self.table}")

        self.init_types()
        self.fieldtype.activated[str].connect(self.change_type)

        self.cancel_button.clicked.connect(self.close)
        self.ok_button.clicked.connect(self.add_column)

        self.show()

    def init_types(self):
        # Load all data types to a ComboBox
        for dtype in data_types:
            self.fieldtype.addItem(dtype)

    def change_type(self, dtype):
        # Handling type changing event
        self.current_type = dtype

    def add_column(self):
        # Add column to table
        column_name = self.fieldname.text()
        data_type = self.current_type
        default_value = self.defaultvalue.text()
        PQLE.add_column(self.table, column_name, data_type, default_value)
        self.close()


class QLFieldRenameWindow(QDialog, QLWindow):
    # Class for renaming field in the table (not working in Python)
    def __init__(self, table, column_name):
        super().__init__()
        uic.loadUi("ui/FieldRenameWindow.ui", self)

        self.column_name = column_name
        self.table_name = table

        self.setWindowTitle(f"Rename field '{column_name}'")
        self.cancel_button.clicked.connect(self.close)
        self.ok_button.clicked.connect(self.rename)

        self.label.setText(self.label.text().replace('"FieldName"', self.column_name))

        self.show()

    def rename(self):
        # Renaming column
        new_name = self.new_input.text()
        PQLE.rename_column(self.table_name, self.column_name, new_name)
        self.close()


class QLTableCreateWindow(QMainWindow, QLWindow):
    # Class for table creation
    def __init__(self, func):
        super().__init__()
        uic.loadUi("ui/TableCreateWindow.ui", self)

        self.cancel_button.clicked.connect(self.close)
        self.ok_button.clicked.connect(self.create)
        self.createf_button.clicked.connect(self.create_field)
        self.deletef_button.clicked.connect(self.delete_field)
        self.table.itemSelectionChanged.connect(self.check_button_state)
        self.table.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.setWindowTitle("Create table")
        self.function = func

        self.check_button_state()

        self.fields = []
        self.update_table()

        self.show()

    def create_field(self):
        # Open field creation window
        QLA.open_window(QLCreateFieldWindow, self.add_field)

    def add_field(self, field):
        # Add field to table
        self.fields.append(field)
        self.update_table()

    def update_table(self):
        # Update the main table
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Field name", "Field type", "Default value", "Primary key", "Unique"])
        self.table.setRowCount(0)

        self.header = self.table.horizontalHeader()

        for i in range(len(self.header)):
            self.header.setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
        
        for i, row in enumerate(self.fields):
            self.table.setRowCount(self.table.rowCount() + 1)
            for j, elem in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(elem)))

    def check_button_state(self):
        # Disable field delete button if no fields selected
        if len(self.table.selectedItems()) == 0:
            self.deletef_button.setEnabled(False)
        else:
            self.deletef_button.setEnabled(True)

    def delete_field(self):
        # Delete field
        self.fields.pop(self.table.currentRow())
        self.update_table()

    def create(self):
        # Create table in PQLE
        PQLE.create_table(self.table_name.text(), self.fields)
        self.function()
        self.close()


class QLCreateFieldWindow(QMainWindow, QLWindow):
    # Class for creating new field to a new table
    def __init__(self, func):
        super().__init__()
        uic.loadUi("ui/CreateFieldWindow.ui", self)

        self.setWindowTitle("Field creation")
        self.cancel_button.clicked.connect(self.close)
        self.ok_button.clicked.connect(self.prepare_field)
        self.fieldtype.activated[str].connect(self.change_type)
        self.ftype = "INT"

        self.primary_key.stateChanged.connect(self.change_primary_key_status)
        self.unique.stateChanged.connect(self.change_unique_status)

        self.function = func

        self.primary_key_status = False
        self.unique_status = False

        self.init_types()

        self.show()

    def prepare_field(self):
        # Putting info to a tuple
        out = (self.fieldname.text(), self.ftype, self.defaultvalue.text(),
               self.primary_key_status, self.unique_status)

        self.function(out)
        self.close()

    def init_types(self):
        # Load all data types into ComboBox
        for dtype in data_types:
            self.fieldtype.addItem(dtype)

    def change_type(self, ftype):
        # Handler for ComboBox selection changed
        self.ftype = ftype

    def change_primary_key_status(self, status):
        # Enable/disable primary key option
        if status == 2:
            self.primary_key_status = True
        else:
            self.primary_key_status = False

    def change_unique_status(self, status):
        # Enable/disable unique option
        if status == 2:
            self.unique_status = True
        else:
            self.unique_status = False


class QLResultsViewWindow(QMainWindow, QLWindow):
    # Window for seeing results of special SQL query
    def __init__(self, res, cnames=[]):
        super().__init__()
        uic.loadUi("ui/SQLResultsViewWindow.ui", self)

        self.setWindowTitle("Query results")

        self.results = res
        if cnames:
            self.column_names = cnames
        else:
            self.column_names = range(1, len(self.results[0]) + 1)

        self.init_table()
        self.table.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.show()

    def init_table(self):
        # Load table
        self.table.setColumnCount(len(self.column_names))
        self.table.setHorizontalHeaderLabels(list(map(str, self.column_names)))
        self.table.setRowCount(0)

        self.header = self.table.horizontalHeader()

        for i in range(len(self.header)):
            self.header.setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
        
        for i, row in enumerate(self.results):
            self.table.setRowCount(self.table.rowCount() + 1)
            for j, elem in enumerate(row):
                if type(self.results[i][j]) is str:
                    self.table.setItem(i, j, QTableWidgetItem("'" + elem + "'"))
                elif self.results[i][j] is None:
                    self.table.setItem(i, j, QTableWidgetItem("NULL"))
                else:
                    self.table.setItem(i, j, QTableWidgetItem(str(elem)))
                self.table.item(i, j).setFlags(self.table.item(i, j).flags() ^ QtCore.Qt.ItemIsEditable)


class QLCommitDialog(QDialog, QLWindow):
    # Dialog for commiting or discarding changes in tables
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/CommitDialog.ui", self)
        self.fill_commits()

        self.commit_button.clicked.connect(self.commit)
        self.cancel_button.clicked.connect(self.close)
        self.discard_button.clicked.connect(self.discard)

        self.show()

    def fill_commits(self):
        # Add commits to table
        for commit in PQLE.get_commit_list():
            self.commit_list.addItem(QListWidgetItem(commit))

    def commit(self):
        # If commit
        PQLE.commit()
        self.close()

    def discard(self):
        # If discarded commits
        PQLE.clear_commits()
        self.close()


class QLDialog(QDialog, QLWindow):
    # Dialog to approve or discard changes
    def __init__(self, action, func):
        super().__init__()
        uic.loadUi("ui/Dialog.ui", self)

        self.function = func
        self.label.setText(self.label.text().replace('"Action"', action))
        self.cancel_button.clicked.connect(self.close)
        self.ok_button.clicked.connect(self.run_function)

        self.show()

    def run_function(self):
        # User function calling
        self.function()
        self.close()


class QLInputDialog(QDialog, QLWindow):
    # Dialog for getting input from user
    def __init__(self, obj, func):
        super().__init__()
        uic.loadUi("ui/InputDialog.ui", self)

        self.function = func
        self.ok_button.clicked.connect(self.run_function)
        self.setWindowTitle(obj[:-1])
        self.cancel_button.clicked.connect(self.close)
        self.label.setText(obj)

        self.show()

    def run_function(self):
        # User function calling
        self.function(self.input.text())
        self.close()

                
class QLMessageBox(QDialog, QLWindow):
    # My message box of errors
    def __init__(self, text):
        super().__init__()
        uic.loadUi("ui/MessageBox.ui", self)
        self.label.setText(str(text).capitalize())
        self.ok_button.clicked.connect(self.close)

        self.pix.setPixmap(QPixmap("img/error.jpg"))

        self.show()


class QLAdmin:
    # Class for controlling all windows in QLAdmin
    def __init__(self):
        self.windows = [QLLoginWindow()]

    def close_window(self, window):
        # Close window and delete from list
        window.hide()
        self.windows.remove(window)

    def open_window(self, window, *options):
        # Open window with parameters
        self.windows.append(window(*options))


# All SQLite3 data types
data_types = ['INT', 'INTEGER', 'TINYINT', 'SMALLINT', 'MEDIUMINT',
              'BIGINT', 'UNSIGNED BIG INT', 'INT2', 'INT8', 'CHARACTER(20)',
              'VARCHAR(255)', 'VARYING CHARACTER(255)', 'NCHAR(55)',
              'NATIVE CHARACTER(70)', 'NVARCHAR(100)', 'TEXT', 'CLOB',
              'BLOB', 'REAL', 'DOUBLE', 'DOUBLE PRECISION', 'FLOAT',
              'NUMERIC', 'DECIMAL(10,5)', 'BOOLEAN', 'DATE', 'DATETIME']


# My excepthook for pushing Qt to raise errors
def excepthook(type, value, tback):
    QLA.open_window(QLMessageBox, value)
    sys.__excepthook__(type, value, tback)
sys.excepthook = excepthook

# Creating application and use stylesheets
app = QApplication(sys.argv)
app.setStyleSheet(open("style.qss").read())

# Add custom font
fid = QFontDatabase.addApplicationFont("fonts/Lato-Regular.ttf")  # Replace with your path
fontstr = QFontDatabase.applicationFontFamilies(fid)[0]
font = QFont(fontstr)
app.setFont(font)

# Run
QLA = QLAdmin()
sys.exit(app.exec()) 
