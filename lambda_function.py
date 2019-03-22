import boto3
import os
import sys
import uuid
from PIL import Image
import json
import base64
import random
from multiprocessing.dummy import Pool as ThreadPool
from io import BytesIO
from time import perf_counter
import hashlib

def createResizedImage(image, resize_size):
    if image.size[0] > image.size[1]:
        min_size = image.size[1]
    else:
        min_size = image.size[0]
    new_size = (int(resize_size / min_size * image.size[0]), int(resize_size / min_size * image.size[1]))
    resized_image = image.resize(new_size, Image.ANTIALIAS)
    return resized_image, new_size

def upload_image(s3Client, size_str, rand_hash, size, dev=False, compressionQuality = 85):
    try:
        ogImage = Image.open("/tmp/{}-original.jpg".format(rand_hash))
        if size_str == "original":
            image = ogImage
            new_size = size
        else:
            image, new_size = createResizedImage(ogImage, size)
        buff = BytesIO()
        image.save(buff, format="JPEG", quality = compressionQuality)
        buff.seek(0)
        if not dev:
            imageKey = "images/{}/{}/{}.jpg".format(rand_hash, size_str, rand_hash)
        else:
            imageKey = "dev-images/{}/{}/{}.jpg".format(rand_hash, size_str, rand_hash)

        s3Client.put_object(Bucket="pear-images",Key=imageKey, Body=buff, ACL="public-read")
        url = "https://s3.amazonaws.com/pear-images/{}".format(imageKey)
        return (url, new_size)
    except Exception as e:
        print("Error saving image to public cloud")
        print(e)

def compressAndUploadImage(base64ImageString, dev=False, uid = "0"):
    start = perf_counter()

    image = Image.open(BytesIO(base64.b64decode(base64ImageString)))

    orientation = 274  # get 274 through upper loop
    try:
        exif = image._getexif()
        if exif:
            exif = dict(exif.items())
            if exif[orientation] == 3:
                image = image.rotate(180, expand=True)
            elif exif[orientation] == 6:
                image = image.rotate(270, expand=True)
            elif exif[orientation] == 8:
                image = image.rotate(90, expand=True)
    except Exception as e:
        # There is AttributeError: _getexif sometimes.
        print("Error getting exif data: {}".format(e))
        pass
    image = image.convert('RGB')
    image_ratio = image.size[1] / image.size[0]
    if image.size[0] > image.size[1]:
        min_size = image.size[1]
    else:
        min_size = image.size[0]

    max_original_size = 1500
    large_size = 1000
    medium_size = 600
    small_size = 300
    thumb_size = 150
    compressionQuality = 85

    if image.size[0] > max_original_size and image.size[1] > max_original_size:
        image, original_size = createResizedImage(image, max_original_size)
    else:
        original_size = (image.size)

    random_hash = str(uuid.uuid4())
    if dev:
        random_hash = str(hashlib.md5(base64ImageString.encode('utf-8')).hexdigest())
    image.save("/tmp/{}-original.jpg".format(random_hash), "JPEG", quality = compressionQuality, optimize=True)

    s3Client = boto3.client(u's3')
    tasks = [   (s3Client, "original", random_hash, original_size, dev, compressionQuality),
                (s3Client, "large", random_hash, large_size, dev, compressionQuality),
                (s3Client, "medium", random_hash, medium_size, dev, compressionQuality),
                (s3Client, "small", random_hash, small_size, dev, compressionQuality),
                (s3Client, "thumb", random_hash, thumb_size, dev, compressionQuality)]

    pool = ThreadPool(5)
    results = pool.starmap(upload_image, tasks)
    os.remove("/tmp/{}-original.jpg".format(random_hash))
    size_map = {
        "imageID" : random_hash,
        "original" : {
            "imageType": "original",
            "imageURL" : results[0][0],
            "width":  results[0][1][0],
            "height": results[0][1][1],
        },
        "large" : {
            "imageType": "large",
            "imageURL" : results[1][0],
            "width": results[1][1][0],
            "height": results[1][1][1],
        },
        "medium" : {
            "imageType": "medium",
            "imageURL" : results[2][0],
            "width": results[2][1][0],
            "height": results[2][1][1],
        },
        "small" : {
            "imageType": "small",
            "imageURL" : results[3][0],
            "width": results[3][1][0],
            "height": results[3][1][1],
        },
        "thumbnail" : {
            "imageType": "thumbnail",
            "imageURL" : results[4][0],
            "width": results[4][1][0],
            "height": results[4][1][1],
        },
    }
    return size_map


def lambda_handler(event, context):

    if event["httpMethod"] == "POST":
        decodedString = base64.b64decode(event["body"]).decode("utf-8").replace("'", '"')
        payload = json.loads(decodedString)
        base64ImageString = payload["image"]
        dev = False
        if "dev" in payload:
            dev = True
        size_map = compressAndUploadImage(base64ImageString, dev=dev)
        return {
            'statusCode': 200,
            'body': json.dumps(size_map)
        }
    return {
        'statusCode': 500,
        'body': "Invalid Request"
    }
