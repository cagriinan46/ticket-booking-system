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

def send_ticket_email(receiver_email, event_name, event_id):
    sender_email = os.getenv("SENDER_MAIL")
    app_password = os.getenv("SENDER_APP_PASSWORD")

    message = MIMEMultipart()
    message["From"] = f"PortaBilet <{sender_email}>"
    message["To"] = receiver_email
    message["Subject"] = "Biletiniz Başarıyla Oluşturuldu!"

    html_body = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Biletiniz Hazır</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #fdf8f5;">

        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-top: 40px; margin-bottom: 40px;">
            
            <!-- Üst Turuncu Header -->
            <div style="background: linear-gradient(135deg, #f97316 0%, #f59e0b 100%); padding: 30px 20px; text-align: center;">
                <h1 style="color: #ffffff; margin: 0; font-size: 28px; letter-spacing: 1px;">PortaBilet</h1>
            </div>

            <!-- Gövde -->
            <div style="padding: 40px 30px;">
                <h2 style="color: #1f2937; margin-top: 0;">Merhaba,</h2>
                <p style="color: #4b5563; font-size: 16px; line-height: 1.6;">
                    Harika bir haberimiz var! <strong>{event_name}</strong> etkinliği için biletiniz başarıyla oluşturuldu ve hesabınıza tanımlandı.
                </p>

                <!-- Bilet Kartı Tasarımı -->
                <div style="background-color: #fff7ed; border: 1px solid #ffedd5; border-left: 5px solid #f97316; border-radius: 8px; padding: 20px; margin: 30px 0;">
                    <p style="margin: 0 0 10px 0; color: #9a3412; font-size: 12px; text-transform: uppercase; font-weight: bold;">ETKİNLİK DETAYI</p>
                    <h3 style="margin: 0; color: #1f2937; font-size: 20px;">{event_name}</h3>
                    <p style="margin: 10px 0 0 0; color: #c2410c; font-weight: bold;">
                        Referans No: #TKT-{event_id}982
                    </p>
                </div>

                <p style="color: #4b5563; font-size: 16px; line-height: 1.6;">
                    Biletinizin detaylarını görmek ve QR kodunuza erişmek için profilinize gidebilirsiniz.
                </p>

                <!-- Buton -->
                <div style="text-align: center; margin: 40px 0;">
                    <a href="http://localhost:5173/profile" style="background-color: #f97316; color: #ffffff; text-decoration: none; padding: 14px 30px; border-radius: 8px; font-weight: bold; font-size: 16px; display: inline-block;">
                        Biletlerimi Görüntüle
                    </a>
                </div>

                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">

                <p style="color: #6b7280; font-size: 14px; text-align: center; margin: 0;">
                    Keyifli seyirler dileriz!<br>
                    <strong>PortaBilet Ekibi</strong>
                </p>
            </div>
            
            <!-- Alt Kısım -->
            <div style="background-color: #f3f4f6; padding: 20px; text-align: center;">
                <p style="color: #9ca3af; font-size: 12px; margin: 0;">
                    © 2026 PortaBilet. Tüm hakları saklıdır.<br>
                    Bu mail otomatik olarak gönderilmiştir, lütfen cevaplamayınız.
                </p>
            </div>

        </div>

    </body>
    </html>
    """
    
    message.attach(MIMEText(html_body, "html"))

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

                send_ticket_email(user_email, event_title, event_id)

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