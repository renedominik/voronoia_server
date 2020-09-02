import sqlite3

conn = sqlite3.connect('jobs.db')
print("Opened database successfully");

conn.execute('CREATE TABLE jobs (id INTEGER, tag TEXT, pdb TEXT, vol TEXT)')
print("Table created successfully");
conn.close()

