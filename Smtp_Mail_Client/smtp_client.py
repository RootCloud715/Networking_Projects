
import smtplib
from email.message import EmailMessage
import os
import mimetypes 


def main():
    
    try:
    
        sender_email = os.environ["GMAIL_ADDRESS"]
        app_password = os.environ["GMAIL_APP_PASSWORD"]
        recipient_email = os.environ["Recpt_GMAIL_ADDRESS"]
    except KeyError as e:
        print(f"Missing environment variable: {e}")
        return
    
    msg = EmailMessage()
    msg["Subject"] = input("Enter subject: ")
    msg.set_content(input("Enter body: "))
    msg["From"] = sender_email
    msg["To"] = recipient_email
    attachment_path = input("Enter path to attachment (or press Enter to skip): ")
    if attachment_path:
        try:
            with open(attachment_path, "rb") as f:
                file_data = f.read()
        except FileNotFoundError:
            print(f"File not found: {attachment_path}")
            return
        except OSError as e:
            print(f"Could not read attachment: {e}")
            return
        mime_type, _ = mimetypes.guess_type(attachment_path)
        if mime_type is None:
            mime_type = "application/octet-stream"
        maintype, subtype = mime_type.split("/")
        msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=os.path.basename(attachment_path))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:     
            
            server.login(sender_email, app_password)


            server.send_message(msg)
            print("Mail sent successfully")

    except smtplib.SMTPAuthenticationError: print("Login Failed - check email/App password.")
    except smtplib.SMTPRecipientsRefused: print("Recipient address was rejected.")
    except smtplib.SMTPException as e: print(f"SMTP error occured: {e}")


  
    
if __name__ == "__main__":
    main()