import paho.mqtt.client as client
import json
import aiosmtplib
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random


def on_message(client, userdata, message):
    try:
        msg = str(message.payload.decode("utf-8"))
        print(msg)
        msgJson = json.loads(msg)
        asyncio.run(sendEmail(msgJson["header"],msgJson["msg"],msgJson["to"]))
    except Exception as e:
        print(e)


async def sendEmail(header,msg,receiver):
    message = MIMEMultipart("alternative")
    message["From"] = "bimantorosatrio69@gmail.com"
    message["To"] = "{}".format(receiver)
    message["Subject"] = "{}".format(header)
    plain_text_message = MIMEText("OCR Product", "plain", "utf-8")
    html_message = MIMEText(
        msg, "html", "utf-8"
    )
    message.attach(plain_text_message)
    message.attach(html_message) 
    await aiosmtplib.send(
        message,
        hostname="smtp.gmail.com",
        port=587,
        username="bimantorosatrio69@gmail.com",
        password="zwyanzxtuuyxlzla",
        recipients="{}".format(receiver),
        #use_tls=True
    )

# if __name__ == "__main__":

Client = client.Client("node"+str(random.randint(1000,9999)))
Client.message_callback_add("/bimo/forwarder",on_message)
Client.connect('test.mosquitto.org',1883,60)
Client.subscribe("/#",0)
Client.loop_forever()

