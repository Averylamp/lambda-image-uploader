#!/bin/bash

sh upload_function.sh

echo "Invoking function"

keys='"{"image":"'
image="$(cat Avery0.jpg | base64)"
end='"}"'
payload="$keys$image$end"
echo $payload > payload.txt
aws lambda invoke --function-name imageCompressorUploader --log-type Tail \
--payload file://payload.txt  \
output.txt | grep "LogResult"| awk -F'"' '{print $4}' | base64 --decode

echo "---"
echo "Response:"
cat output.txt

