import random
import smtplib
import time
from email.mime.text import MIMEText

from twilio.rest import Client

from core.config import Config
from domain.session import get_mongo_client, get_collection
from helper.cloud_helper import get_cloud_connection


def generate_otp(length=6):
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


async def send_otp(contact: str,method: str,driver_id=None):
    otp_expiry = Config.OTP_EXPIRY_SECONDS
    otp = generate_otp()
    expiry_time = int(time.time()) + int(otp_expiry)

    if method == "mobile"  and Config.ENABLE_TWILIO:
            await send_sms_twilio(contact)
            return

    # Upsert OTP document
    db_client = await get_mongo_client()
    otp_collection = await get_collection(db_client, "otps")
    await otp_collection.update_one(
        {'contact': contact,"driver_id":driver_id},
        {'$set': {'otp': otp, 'expires_at': expiry_time}},
        upsert=True
    )

    if method == "mobile":
            await send_sms(contact, f"[RideShare] Your OTP is {otp}. It expires in 5 mins.")
    else:
        await send_otp_email(contact,otp)



async def verify_otp_twilio(contact: str, otp: str) -> bool:
    account_sid = Config.TWILIO_ACCOUNT_SID
    auth_token =Config.TWILIO_AUTH_TOKEN
    service_sid =Config.TWILIO_SERVICE_SID
    client = Client(account_sid, auth_token)
    verification_check = client.verify \
        .v2 \
        .services(service_sid) \
        .verification_checks \
        .create(to=contact, code=otp)

    if verification_check.status == "approved":
        return True

    return False


async def send_sms(to_number: str, message: str):
    """
    Send SMS to a mobile number using AWS SNS

    Args:
        to_number (str): Phone number in E.164 format (e.g., +14155552671)
        message (str): SMS message body (max ~140 chars for standard SMS)

    Raises:
        Exception: if sending fails
    """
    sns_client = await get_cloud_connection("sns")
    try:
        # response = sns_client.publish(
        #     PhoneNumber=to_number,
        #     Message=message
        # )
        print(to_number,message)
        response = sns_client.publish(
            PhoneNumber=to_number,
            Message=message,
            MessageAttributes={
                'AWS.SNS.SMS.SMSType': {
                    'DataType': 'String',
                    'StringValue': 'Transactional'
                }
            }
        )
        message_id = response['MessageId']
        print("message id",message_id)
        print(f"[DEBUG] SMS sent via AWS SNS. Message ID: {message_id}")
        return message_id
    except Exception as e:
        print(f"[ERROR] Failed to send SMS: {e}")
        raise

async def send_sms_twilio(to_number: str):
    try:
        account_sid = Config.TWILIO_ACCOUNT_SID
        auth_token = Config.TWILIO_AUTH_TOKEN
        service_sid = Config.TWILIO_SERVICE_SID  # Twilio sender number (E.164 format)

        # Initialize Twilio client
        twilio_client = Client(account_sid, auth_token)

        verification = twilio_client.verify \
            .v2 \
            .services(service_sid
                      ) \
            .verifications \
            .create(to=to_number, channel='sms')

        print(verification.sid)
        # sms = twilio_client.messages.create(
        #     body=message,
        #     from_=TWILIO_FROM_NUMBER,
        #     to=to_number
        # )
        # print(f"[DEBUG] SMS sent via Twilio. Message SID: {sms.sid}")
        return verification.sid
    except Exception as e:
        print(f"[ERROR] Failed to send SMS via Twilio: {e}")
        raise

async def send_otp_email(to_email: str, otp: str):
    email_from = Config.EMAIL_FROM
    email_host = Config.EMAIL_HOST
    email_username = Config.EMAIL_USERNAME
    email_password = Config.EMAIL_PASSWORD
    email_port = Config.EMAIL_PORT
    subject = "Verify Your Email Address for RideShare"
    body =  f"""Hey ,

            Welcome to RideShare! 🎉  
            Here’s your verification code: {otp}
            
            It’s valid for {5} minutes.  
            If you didn’t request this, you can safely ignore it.
            
            Cheers,  
            – The RideShare Crew
            """

    # body = f"Your OTP For RideShare Login is: {otp}. It expires in 5 minutes."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = f"RideShare <{email_from}>"
    msg["To"] = to_email

    try:
        with smtplib.SMTP(email_host, email_port) as server:
            server.starttls()
            server.login(email_username, email_password)
            server.send_message(msg)
        print(f"[INFO] OTP email sent to {to_email}")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        raise


async def verify_otp(method:str,contact:str,otp:str):
    if method == "mobile" and Config.ENABLE_TWILIO:
        is_valid = await verify_otp_twilio(contact,otp)
        print("isvalid",is_valid)
        if not is_valid:
            return False
        else:
            return True

    print(Config.ENABLE_TWILIO)

    db_client = await get_mongo_client()
    otp_collection = await get_collection(db_client, "otps")
    record = await otp_collection.find_one({'contact': contact})

    if not record:
        return False

    if int(time.time()) > record['expires_at']:
        await otp_collection.delete_one({'contact': contact})
        return False

    if record['otp'] == otp:
        await otp_collection.delete_one({'contact': contact})
        return True
    return True

async def update_db(method,value):
    db_client = await get_mongo_client()
    drivers_collection = await get_collection(db_client, "drivers")
    if method == "mobile":
        await drivers_collection.update_one(
            {"mobile_number": value},
            {"$set": {"is_mobile_verified": True}}
        )
    elif method == "email":
        await drivers_collection.update_one(
            {"email": value},
            {"$set": {"is_email_verified": True}}
        )
    else:
        return False
    return True



