import boto3
from botocore.exceptions import ClientError,BotoCoreError
from core.config import Config

async def get_cloud_connection(resource,endpoint_url=None):
    if endpoint_url:
        boto_client = boto3.client(
            resource,
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION,
            endpoint_url=Config.AWS_S3_ENDPOINT_URL
        )
    else:
        boto_client = boto3.client(
            resource,
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            region_name=Config.AWS_REGION
        )
    return boto_client