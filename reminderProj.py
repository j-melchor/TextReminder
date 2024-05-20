import os
import smtplib
import email
import imaplib
from email.message import EmailMessage
import schedule # pip install schedule
import time
import datetime
import pytz # used for timezones

# TODO add news and other stuff
# TODO add gui
# TODO add more commmands
# TODO replace the array with a csv file
todoList = []

def txt_alert():

    msg = EmailMessage()
    
    # create and format the string to be texted
    textString = ""
    for i in todoList:
        textString += "- " + i + "\n"
    
    msg.set_content(textString)
    msg['subject'] = ""
    msg['to'] = "<YourPhoneNumber>@vtext.com"  
    """
    @vtext.com for verizon
    for other carriers, check this link
    https://www.digitaltrends.com/mobile/how-to-send-a-text-from-your-email-account/

    
    you will need your own email and app password
    the best way to do this is to make a new gmail and filter out any emails auto-sent by google
    """
    user = "<YourEmail>@gmail.com"
    msg['from'] = user
    password = "<YourEmailAppPassword>"

    server = smtplib.SMTP("smtp.gmail.com", 587) # 587 is the port number for gmail
    server.starttls()
    server.login(user, password)
    server.send_message(msg)
    server.quit()

def process_attachment(msg):
    """
    Process attachments in the email and look for text_0.txt
    """
    for part in msg.walk():
        content_disposition = str(part.get("Content-Disposition"))
        if "attachment" in content_disposition:
            filename = part.get_filename()
            if filename and filename.lower() == "text_0.txt":
                filepath = os.path.join('/tmp', filename)  # Save to temporary directory
                with open(filepath, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                return filepath
    return None

def update_agenda(action, item):
    """
    Update the agenda based on the given action and item.
    """
    if action == 'add':
        todoList.append(item)
    elif action == 'remove':
        if item in todoList:
            todoList.remove(item)

def read_command_from_file(filepath):
    """
    Extract and execute command from the given file.
    """
    with open(filepath, 'r') as file:
        content = file.read().lower()
        # check the first word of the text file to determine the action
        if content.startswith("add "):
            item_to_add = content[4:].strip()
            update_agenda('add', item_to_add)
        elif content.startswith("remove "):
            item_to_remove = content[7:].strip()
            update_agenda('remove', item_to_remove)

def check_email():
    """
    because the text messages sent back come in the form of an email 
    we can use the imaplib library to check for new messages
    """
    with imaplib.IMAP4_SSL('imap.gmail.com') as imap:
        imap.login('<YourEmail>@gmail.com', '<YourEmailAppPassword>')
        imap.select('inbox')
        
        status, messages = imap.search(None, '(UNSEEN)')
        for num in messages[0].split():
            status, data = imap.fetch(num, '(RFC822)')
            msg = email.message_from_bytes(data[0][1])
            
            # grab the txt attachment in the email
            filepath = process_attachment(msg)
            if filepath:
                read_command_from_file(filepath)
                os.remove(filepath)  # Clean up the temporary file

        imap.close()


pacific_time = pytz.timezone('US/Pacific')

schedule.ever().day.at("7:30").do(check_email)
schedule.every().day.at("8:30").do(txt_alert)

while True:
    # Get the current time in Pacific Time
    now_pacific = datetime.datetime.now(pacific_time)

    schedule.run_pending()
    time.sleep(60)  # Check every minute
