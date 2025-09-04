import smtplib
import os
from dotenv import load_dotenv

if os.path.exists('../.env'):
    load_dotenv()

YOUR_GOOGLE_EMAIL = os.getenv("EMAIL_SENDER")  # The email you setup to send the email using app password
YOUR_GOOGLE_EMAIL_APP_PASSWORD = os.getenv("EMAIL_PASSWORD")   # The app password you generated

smtpserver = smtplib.SMTP_SSL('smtp.gmail.com', 465)
smtpserver.ehlo()
smtpserver.login(YOUR_GOOGLE_EMAIL, YOUR_GOOGLE_EMAIL_APP_PASSWORD)

# Test send mail
sent_from = YOUR_GOOGLE_EMAIL
sent_to = sent_from  #  Send it to self (as test)
email_text = 'This is a test'
smtpserver.sendmail(sent_from, sent_to, email_text)

# Close the connection
smtpserver.close()