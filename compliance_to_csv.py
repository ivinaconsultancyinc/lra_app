import sqlite3
import csv

# Connect to your local database
conn = sqlite3.connect('instance/lra_app.db')
cursor = conn.cursor()

# Fetch all data
cursor.execute("SELECT * FROM compliance")
rows = cursor.fetchall()

# Get column headers
headers = [description[0] for description in cursor.description]

# Write to CSV
with open('compliance_export.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)

conn.close()
print("Exported to compliance_export.csv")