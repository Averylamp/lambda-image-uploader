#!/bin/bash

sh upload_function.sh

echo "Invoking function"

aws lambda invoke --function-name imageCompressorUploader --log-type Tail \
--payload '{"image":"asdf"}' \
output.txt

cat output.txt

