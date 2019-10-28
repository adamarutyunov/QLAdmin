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

        execution = f"UPDATE {table} SET {key}={value} {condition} {options}"
        self.cursor.execute(execution)

        return self.cursor.fetchall()

    def select(self, table, )
