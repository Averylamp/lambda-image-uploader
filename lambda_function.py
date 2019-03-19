import boto3
import os
import sys
import uuid
from PIL import Image
import json

def lambda_handler(event, context):
    print("HELLO")
    # TODO implement
    print(uuid.uuid1())
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
