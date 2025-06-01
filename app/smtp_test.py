import smtplib
from email.message import EmailMessage

def send_test_email():
    email_address = 'kalebmenbere@gmail.com'
    email_password = 'xoyyyngdxxyjbvlw'  # App password

    msg = EmailMessage()
    msg['Subject'] = '✅ Gmail SMTP Test from Python'
    msg['From'] = email_address
    msg['To'] = 'atsewkaleb@gmail.com'  # Replace with your test email
    msg.set_content('Hello!\nThis is a test email sent from Python using Gmail SMTP.')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
        print("✅ Email sent successfully.")
    except Exception as e:
        print("❌ Failed to send email.")
        print("Error:", e)

send_test_email()
