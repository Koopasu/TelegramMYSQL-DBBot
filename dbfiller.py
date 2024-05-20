import MySQLdb
import configparser
from datetime import datetime

def insert_sample_data(cursor):
    # Number of sample records to insert
    num_samples = 9000

    # SQL command to insert a record into the orders table
    insert_command = "INSERT INTO orders (ID, Email, Balance, LAST_EDIT) VALUES (%s, %s, %s, %s);"

    # Execute the command for each sample record
    for i in range(num_samples):
        id = 1000 + i  # Start IDs from 1001 onwards
        email = f"user{id}@example.com"
        balance = 100 * (i % 10 + 1)  # Create varying balances
        last_edit = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(insert_command, (id, email, balance, last_edit))
    
    # Commit the changes to the database
    cursor.connection.commit()
    print(f"{num_samples} sample data entries inserted successfully.")

# Configuration and database connection setup
config = configparser.ConfigParser()
config.read('config.ini')
hostname = config.get('default','hostname')
username = config.get('default','username')
password = config.get('default','password')
database = config.get('default','database')

# Connect to the MySQL database
conn = MySQLdb.connect(host=hostname, user=username, passwd=password, db=database)
crsr = conn.cursor()

# Insert sample data
insert_sample_data(crsr)

# Close the database connection
crsr.close()
conn.close()
