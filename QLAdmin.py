import sqlite3


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


# connection = sqlite3.connect()
PQLE = PyQl()
