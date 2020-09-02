import sqlite3

conn = sqlite3.connect('jobs.db')
print("Opened database successfully");

conn.execute('DROP TABLE jobs ')
print("Table deleted successfully");
conn.close()

