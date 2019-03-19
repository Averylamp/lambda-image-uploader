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


def upload_image(bucket, size_str, rand_hash, image, compressionQuality = 85):
    try:
        buff = BytesIO()
        image.save(buff, format="JPEG", quality = compressionQuality, optimize=True)
        buff.seek(0)
        blob = bucket.blob("images/{}/{}/{}.jpg".format(rand_hash, size_str, rand_hash))
        url = bucket.put_object(Bucket="pear-images", Body=buff)
        print(url)
        return url
    except Exception as e:
        print("Error")
        print(e)
        return None

def compressAndUploadImage(base64ImageString, uid = "0"):

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
    except:
        # There is AttributeError: _getexif sometimes.
        pass
    image = image.convert('RGB')
    image_ratio = image.size[1] / image.size[0]
    if image.size[0] > image.size[1]:
        min_size = image.size[1]
    else:
        min_size = image.size[0]

    max_original_size = 1600
    large_size = 1000
    medium_size = 600
    small_size = 300
    thumb_size = 150
    compressionQuality = 85

    def createResizedImage(image, resize_size):
        if image.size[0] > image.size[1]:
            min_size = image.size[1]
        else:
            min_size = image.size[0]
        new_size = (int(resize_size / min_size * image.size[0]), int(resize_size / min_size * image.size[1]))
        resized_image = image.resize(new_size, Image.ANTIALIAS)
        return resized_image, new_size


    large_image, large_size = createResizedImage(image, large_size)
    medium_image, medium_size = createResizedImage(image, medium_size)
    small_image, small_size = createResizedImage(image, small_size)
    thumb_image, thumb_size = createResizedImage(image, thumb_size)


    if image.size[0] > max_original_size and image.size[1] > max_original_size:
        image, original_size = createResizedImage(image, max_original_size)
    else:
        original_size = (image.size)

    random_hash = "%032x" % (random.getrandbits(128))
    s3Client = boto3.client(u's3')
    print(s3Client)
    buff = BytesIO()
    image.save(buff, format="JPEG", quality = compressionQuality, optimize=True)
    buff.seek(0)
    print("Putting object in bucket")
    imageKey = "images/{}/{}/{}.jpg".format(random_hash, "original", random_hash)
    # imageKey = "test3.jpg"
    res = s3Client.put_object(Bucket="pear-images",Key=imageKey, Body=buff, ACL="public-read")
    print(res)
    print("Put")
    print("URL: https://s3.amazonaws.com/pear-images/{}".format(imageKey))
    # tasks = [   (bucket, "original", random_hash, image, compressionQuality),
    #             (bucket, "large", random_hash, large_image, compressionQuality),
    #             (bucket, "medium", random_hash, medium_image, compressionQuality),
    #             (bucket, "small", random_hash, small_image, compressionQuality),
    #             (bucket, "thumb", random_hash, thumb_image, compressionQuality)]
    #
    # pool = ThreadPool(5)
    #
    # results = pool.starmap(upload_image, tasks)
    # pool.close()
    # pool.join()

    # size_map = {
    #     "imageID" : random_hash,
    #     "original" : {
    #         "imageType": "original",
    #         "imageURL" : results[0],
    #         "width":  original_size[0],
    #         "height": original_size[1],
    #     },
    #     "large" : {
    #         "imageType": "large",
    #         "imageURL" : results[1],
    #         "width": large_size[0],
    #         "height": large_size[1],
    #     },
    #     "medium" : {
    #         "imageType": "medium",
    #         "imageURL" : results[2],
    #         "width": medium_size[0],
    #         "height": medium_size[1],
    #     },
    #     "small" : {
    #         "imageType": "small",
    #         "imageURL" : results[3],
    #         "width": small_size[0],
    #         "height": small_size[1],
    #     },
    #     "thumbnail" : {
    #         "imageType": "thumbnail",
    #         "imageURL" : results[4],
    #         "width": thumb_size[0],
    #         "height": thumb_size[1],
    #     },
    # }
    return size_map


def lambda_handler(event, context):
    print("HELLO")
    # TODO implement
    print(uuid.uuid1())
    # print("Received event: " + json.dumps(event, indent=2))
    print("Log stream name:", context.log_stream_name)
    print("Log group name:",  context.log_group_name)
    print("Request ID:", context.aws_request_id)
    print("Mem. limits(MB):", context.memory_limit_in_mb)
    # Code will execute quickly, so we add a 1 second intentional delay so you can see that in time remaining value.
    print("Time remaining (MS):", context.get_remaining_time_in_millis())

    if event["httpMethod"] == "POST":
        print("POST Request received")
        decodedString = base64.b64decode(event["body"]).decode("utf-8").replace("'", '"')
        payload = json.loads(decodedString)
        base64ImageString = payload["image"]
        print("Image base64 len: {}".format(len(base64ImageString)))


        size_map = compressAndUploadImage(base64ImageString)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
