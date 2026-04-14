import time
import json
import boto3
import smtplib
import models
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import SessionLocal
from dotenv import load_dotenv

load_dotenv()

sqs = boto3.client('sqs', region_name='eu-central-1')
SQS_QUEUE_URL = os.getenv("SQS_URL")

def send_ticket_email(receiver_email, event_name):
    sender_email = os.getenv("SENDER_MAIL")
    app_password = os.getenv("SENDER_APP_PASSWORD")

    message = MIMEMultipart()
    message["From"] = f"BiletSistemi <{sender_email}>"
    message["To"] = receiver_email
    message["Subject"] = "Biletiniz Başarıyla Oluşturuldu!"

    body = f"""
    Merhaba,
    
    {event_name} etkinliği için biletiniz başarıyla oluşturulmuştur.
    
    Biletlerinizi profil sayfanızdan görüntüleyebilirsiniz.
    Keyifli seyirler dileriz!
    """
    
    message.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        print(f"Mail başarıyla gönderildi: {receiver_email}")
    except Exception as e:
        print(f"Mail gönderilirken hata oluştu: {e}")

def start_worker():
    print("SQS kuyrugu dinleniyor...")

    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=20
            )

            if "Messages" in response:
                message = response["Messages"][0]
                receipt_handle = message["ReceiptHandle"]

                body = json.loads(message["Body"])

                user_id = body['user_id']
                user_email = body['user_email']
                event_id = body['event_id']
                event_title = body['event_title']

                print(f"\nYeni Siparis Yakalandi: {user_email} -> {event_title}")

                db = SessionLocal()
                new_ticket = models.Ticket(user_id=user_id, event_id=event_id)
                db.add(new_ticket)
                db.commit()
                db.close()
                print("Bilet Veritabanina Kaydedildi.")

                send_ticket_email(user_email, event_title)

                sqs.delete_message(
                    QueueUrl=SQS_QUEUE_URL,
                    ReceiptHandle=receipt_handle
                )
                print("Siparis islendi ve kuyruktan silindi.\n")

            else:
                pass

        except Exception as e:
            print(f"Hata: {e}")
            time.sleep(5)

if __name__ == "__main__":
    start_worker()
