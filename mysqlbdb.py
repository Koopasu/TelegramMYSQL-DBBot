
import configparser
from telnetlib import STATUS 
from telethon import TelegramClient, events 
from datetime import datetime
import MySQLdb 

# config
print("Initializing configuration...")
config = configparser.ConfigParser()
config.read('config.ini')

# Read values for Telethon and set session name
API_ID = config.get('default','api_id') 
API_HASH = config.get('default','api_hash')
BOT_TOKEN = config.get('default','bot_token')
session_name = "sessions/Bot"

# MYSQLdb
HOSTNAME = config.get('default','hostname')
USERNAME = config.get('default','username')
PASSWORD = config.get('default','password')
DATABASE = config.get('default','database')
 
# Start the Client (utilizing telethon)
client = TelegramClient(session_name, API_ID, API_HASH).start(bot_token=BOT_TOKEN)


# START COMMAND
@client.on(events.NewMessage(pattern="(?i)/start"))
async def start(event):
    # Get sender
    sender = await event.get_sender()
    SENDER = sender.id
    
    # set text and send message
    text = "Hello i am a bot that creates and edits Customer and Balance inside a MySQL database"
    await client.send_message(SENDER, text)


# Insert command
@client.on(events.NewMessage(pattern="(?i)/insert"))
async def insert(event):
    try:
        # Get the sender 
        sender = await event.get_sender()
        SENDER = sender.id

        # /insert 17321 kelly.nguyen1230@gmail.com 100

        # Receive text of the user after /insert command and convert it to a list (splitting up information by the SPACE)
        list_of_words = event.message.text.split(" ")
        
        cusid = list_of_words[1] # the first item is customer ID
        cusemail = list_of_words[2] # the second item is the email
        cusbalance = list_of_words[3] # the third item is the balance
        dt_string = datetime.now().strftime("%d/%m/%Y") # Use the datetime library to the get the date (and format it as DAY/MONTH/YEAR)

        # Check if the cusid already exists in the database
        #crsr.execute("SELECT * FROM orders WHERE cusid = %s", (cusid,))
        #if crsr.fetchone():
        crsr.execute("SELECT COUNT(*) FROM orders WHERE ID = %s", (cusid,))
        if crsr.fetchone()[0] > 0:
            # If an entry exists, send an error message
            text = f"An order with customer ID {cusid} already exists. Please use a different ID."
            await client.send_message(SENDER, text, parse_mode='html')
            return

        
        
        
        # Create the params with all the parameters inserted by the user
        params = (cusid, cusemail,cusbalance, dt_string)
        sql_command = "INSERT INTO orders (ID, Email , Balance , LAST_EDIT)  VALUES ( %s, %s, %s, %s);" # using this to pass the params to SQL
        crsr.execute(sql_command, params) # Execute the query
        conn.commit() # commit the changes

        # If rows do not match send below
        if crsr.rowcount < 1:
            text = "Something went wrong, please try again"
            await client.send_message(SENDER, text, parse_mode='html')
        else:
            text = "Order correctly inserted"
            await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e: 
        print(e)
        await client.send_message(SENDER, "Something Wrong happend", parse_mode='html')
        return



# Function that creates a message containing a list of all the oders
def create_message_select_query(ans):
    text = ""
    for i in ans:
        cusid = i[0]
        cusemail = i[1]
        cusbalance = i[2]
        creation_date = i[3]
        text += "<b>"+ str(cusid) +"</b> | " + "<b>"+ str(cusemail) +"</b> | " + "<b>"+ str(cusbalance)+"</b> | " + "<b>"+ str(creation_date)+"</b>\n"
    message = "<b>Received  </b> Information about orders:\n\n"+text
    return message

# VIEWALL COMMAND
@client.on(events.NewMessage(pattern="(?i)/viewall"))
async def viewall(event):
    try:
        # Get the sender of the message
        sender = await event.get_sender()
        SENDER = sender.id
        # Execute the query and get all (*) the oders
        crsr.execute("SELECT * FROM orders")
        res = crsr.fetchall() # fetch all the results
        if(res):
            text = create_message_select_query(res) 
            await client.send_message(SENDER, text, parse_mode='html')
        # Otherwhise, print a default text
        else:
            text = "No orders found inside the database."
            await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e: 
        print(e)
        await client.send_message(SENDER, "Something Wrong happened... Check your input!", parse_mode='html')
        return

# VIEW COMMAND
@client.on(events.NewMessage(pattern="(?i)/view"))
async def view(event):
    try:
        # Get the sender
        sender = await event.get_sender()
        SENDER = sender.id

        # get ID and info /view 17321
        list_of_words = event.message.text.split(" ")
        if len(list_of_words) != 2:
            await client.send_message(SENDER, "Please provide the customer ID in the format: /view <ID>", parse_mode='html')
            return
        
        cusid = list_of_words[1]  # Customer ID from the input

        # Execute the query to get the specific order
        crsr.execute("SELECT * FROM orders WHERE ID = %s", (cusid,))
        result = crsr.fetchone()
        
        if result:
            id, email, balance, last_edit = result
            text = f"<b>ID:</b> {id} | <b>Email:</b> {email} | <b>Balance:</b> {balance} | <b>Status:<b> {STATUS} <b>Last Edited:</b> {last_edit}"
            await client.send_message(SENDER, text, parse_mode='html')
        else:
            text = "No order found with the specified ID."
            await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e:
        print(e)
        await client.send_message(SENDER, "Something went wrong... Please check your inputs and try again!", parse_mode='html')

# UPDATE COMMAND
@client.on(events.NewMessage(pattern="(?i)/update"))
async def update(event):
    try:
        # Get the sender
        sender = await event.get_sender()
        SENDER = sender.id
        
        # /update 10000 koopasu1@gmail.com 150

        list_of_words = event.message.text.split(" ")
        new_cusid = list_of_words[1]  # first item is id
        new_cusemail = list_of_words[2]  # Second item is the email
        new_cusbalance = int(list_of_words[3])  # third item is the quantity
        dt_string = datetime.now().strftime("%d/%m/%Y")  # New date of when data was touched

        new_status = 'inactive' if new_cusbalance <= 0 else 'active'

        # Create the tuple with all the params inserted by the user
        params = (new_cusemail, new_cusbalance, new_status, dt_string, new_cusid)

        # Create the UPDATE query, we are updating the specific id so we must put the WHERE clause
        sql_command = "UPDATE orders SET Email = %s, Balance = %s, Status = %s, LAST_EDIT = %s WHERE ID = %s"
        crsr.execute(sql_command, params)  # Execute the query
        conn.commit()  # Commit the changes
    
        if crsr.rowcount < 1:
            text = "Order with id {} is not present".format(new_cusid)
            await client.send_message(SENDER, text, parse_mode='html')
        else:
            text = "Order with id {} correctly updated".format(new_cusid)
            await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e: 
        print(e)
        await client.send_message(SENDER, "Something Wrong happened...", parse_mode='html')
        return
    

# ADD COMMAND
@client.on(events.NewMessage(pattern="(?i)/add"))
async def add_balance(event):
    try:
        # Get the sender
        sender = await event.get_sender()
        SENDER = sender.id



        # /add 17321 50
        list_of_words = event.message.text.split(" ")
        cusid = list_of_words[1]  # Customer ID from the input
        balance_change = int(list_of_words[2])  # Balance change (can be positive or negative)

        # First, retrieve the current balance of the customer
        crsr.execute("SELECT Balance, Status FROM orders WHERE ID = %s", (cusid,))
        result = crsr.fetchone()
        if result:
            current_balance, status = result
            if status != 'active':
                text = "Cannot add balance: account is inactive. Please activate the account."
                await client.send_message(SENDER, text, parse_mode='html')
                return
        
            new_balance = current_balance + balance_change  # Calculate new balance
            new_status = 'inactive' if new_balance <= 0 else 'active'  # Determine new status

            # Update the customer balance and status in the database
            dt_string = datetime.now().strftime("%d/%m/%Y")  # Current date
            update_sql = "UPDATE orders SET Balance = %s, Status = %s, LAST_EDIT = %s WHERE ID = %s"
            crsr.execute(update_sql, (new_balance, new_status, dt_string, cusid))
            conn.commit()

            if crsr.rowcount > 0:
                text = f"Balance updated successfully for customer ID {cusid}. New balance is {new_balance}."
                if new_status == 'inactive':
                    text += " The account is now inactive due to zero or negative balance."
            else:
                text = "No customer found with the specified ID."
        else:
            text = "No customer found with the specified ID."

        await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e:
        print(e)
        await client.send_message(SENDER, "Something went wrong..... Please check your inputs and try again", parse_mode='html')



@client.on(events.NewMessage(pattern="(?i)/activate"))
async def activate_account(event):
    sender = await event.get_sender()
    SENDER = sender.id

    # Extract the ID and add balance ( no concern for status )
    # /activate 17321 50
    list_of_words = event.message.text.split(" ")
    if len(list_of_words) != 3:
        await client.send_message(SENDER, "Please provide the customer ID and additional balance in the format /activate <ID> <balance>", parse_mode='html')
        return

    cusid = list_of_words[1]
    additional_balance = int(list_of_words[2])

    # Retrieve the current balance and status of the customer
    crsr.execute("SELECT Balance, Status FROM orders WHERE ID = %s", (cusid,))
    result = crsr.fetchone()
    if result:
        current_balance, status = result

        if status == 'active':
            text = "The account is already active."
            await client.send_message(SENDER, text, parse_mode='html')
            return

        new_balance = current_balance + additional_balance
        if new_balance > 0:
            dt_string = datetime.now().strftime("%d/%m/%Y")
            crsr.execute("UPDATE orders SET Balance = %s, Status = 'active', LAST_EDIT = %s WHERE ID = %s", (new_balance, dt_string, cusid))
            conn.commit()

            text = f"Account {cusid} has been activated with an additional balance. New balance is {new_balance}."
        else:
            text = f"Cannot activate account {cusid}. The total balance after addition must be positive."
    else:
        text = "No customer found with the specified ID."

    await client.send_message(SENDER, text, parse_mode='html')



# better user feedback
@client.on(events.NewMessage(pattern="(?i)/help"))
async def help_command(event):
    sender = await event.get_sender()
    SENDER = sender.id

    help_text = """
    <b>Bot Commands:</b>
    /start - Start the bot
    /insert <ID> <email> <balance> - Insert a new customer order
    /view <ID> - View a specific customer order
    /viewall - View all customer orders
    /update <ID> <email> <balance> - Update a specific customer order
    /add <ID> <balance> - Add balance to a specific customer order
    /delete <ID> - Delete a specific customer order
    /activate <ID> <balance> - Activate a customer order with additional balance
    """
    await client.send_message(SENDER, help_text, parse_mode='html')
    

# DELETE COMMAND
@client.on(events.NewMessage(pattern="(?i)/delete"))
async def delete(event):
    try:
        # Get the sender
        sender = await event.get_sender()
        SENDER = sender.id

        #/ delete 17321

        # get list of words inserted by the user
        list_of_words = event.message.text.split(" ")
        id = list_of_words[1] # The second (1) element is the id

        # Crete the DELETE query passing the id as a parameter
        sql_command = "DELETE FROM orders WHERE ID = (%s);"

        # ans here will be the number of rows affected by the delete
        ans = crsr.execute(sql_command, (id,))
        conn.commit()
        
        # If at least 1 row is affected by the query we send a specific message
        if ans < 1:
            text = "Order with id {} is not present".format(id)
            await client.send_message(SENDER, text, parse_mode='html')
        else:
            text = "Order with id {} was correctly deleted".format(id)
            await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e: 
        print(e)
        await client.send_message(SENDER, "Something Wrong happened... Check your input and try again!", parse_mode='html')
        return



# Create database function
def create_database(query):
    try:
        crsr_mysql.execute(query)
        print("Database created successfully")
    except Exception as e:
        print(f"WARNING: '{e}'")




       

# MAIN
if __name__ == '__main__':
    try:
        print("Initializing Database...")
        conn_mysql = MySQLdb.connect( host=HOSTNAME, user=USERNAME, passwd=PASSWORD )
        crsr_mysql = conn_mysql.cursor()

        query = "CREATE DATABASE "+str(DATABASE)
        create_database(query)
        conn = MySQLdb.connect( host=HOSTNAME, user=USERNAME, passwd=PASSWORD, db=DATABASE )
        crsr = conn.cursor()

        # Command that creates the "oders" table 
        sql_command = """CREATE TABLE IF NOT EXISTS orders ( 
            
            ID INT(12),
            Email VARCHAR(200),
            Balance int(14),
            Status VARCHAR(100) DEFAULT 'active',
            LAST_EDIT VARCHAR(100));"""

        crsr.execute(sql_command)
        print("All tables are ready")
        
        print("Bot Started...")
        client.run_until_disconnected()

    except Exception as error:
        print('Cause: {}'.format(error))