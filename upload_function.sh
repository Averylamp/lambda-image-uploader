#!/bin/bash

rm function.zip
cd env/lib/python3.6/site-packages/
zip -r ~/Pear/backend-image-uploader/function.zip .
cd ~/Pear/backend-image-uploader/
zip -g function.zip lambda_function.py


echo "Uploading function..."
aws lambda update-function-code --function-name imageCompressorUploader --zip-file fileb://function.zip
echo "Finished Uploading Function"
