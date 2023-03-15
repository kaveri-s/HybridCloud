import time

import boto3
import os
from image_classification_new import classify
import base64
from datetime import datetime
from ec2_metadata import ec2_metadata

sqs = boto3.client('sqs')
s3 = boto3.client('s3')

input_bucket = ""
output_bucket = ""
request_url = ""
response_url = ""
image_folder = "input_image_folder"
WAITING_TIME = 11


def get_url(url_type):
    queue = sqs.list_queues()
    for url in queue['QueueUrls']:
        if url_type in url:
            return url


def read_message_from_queue():
    return sqs.receive_message(
        QueueUrl=request_url,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=0,
        WaitTimeSeconds=10
    )


def perform_classification(image_name):
    value = classify(image_name)
    return value


def get_number_of_instances():
    ec2 = boto3.resource('ec2')
    instances_count = 0
    instances = ec2.instances.all()
    for instance in instances:
        if instance.state['Name'] == 'running' or \
                instance.state['Name'] == 'pending' and \
                instance.image.id == ec2_metadata.ami_id:
            instances_count += 1
    return instances_count


def check_to_terminate(start_time):
    end_time = time.time()
    if end_time - start_time > WAITING_TIME:
        instance_id = ec2_metadata.instance_id
        instance = boto3.resource("ec2").Instance(instance_id)
        if not "main" in instance.tags[0]['Value']:
            instance.terminate()


def read_request_message():
    start_time = time.time()
    while True:
        response = read_message_from_queue()
        if 'Messages' in response:
            message = response["Messages"][0]
            image_name = message["MessageAttributes"]["Name"]["StringValue"]
            msg_receipt_handel = message["ReceiptHandle"]

            sqs.delete_message(
                QueueUrl=request_url,
                ReceiptHandle=msg_receipt_handel
            )
            time.sleep(1)
            decoded_image_name = decode_image(response, image_name)
            result = perform_classification(decoded_image_name)
            print(result)
            s3_result = f"({image_name.replace('.JEPG', '')}, {result[1]})"
            s3.put_object(Bucket=output_bucket, Key=image_name.replace('.JPEG', ''), Body=s3_result,
                          Metadata={'Name':image_name.replace('.JPEG', ''), 'Result':result[1]})
            send_response_to_queue(image_name, result[1])
            start_time = time.time()
        check_to_terminate(start_time)
        time.sleep(0.5)


def send_response_to_queue(image_name, result):
    response = sqs.send_message(
        QueueUrl=get_url("response-queue"),
        DelaySeconds=10,
        MessageAttributes={
            'Name': {
                'DataType': 'String',
                'StringValue': image_name
            },
            'Result': {
                'DataType': 'String',
                'StringValue': result
            }
        },
        MessageBody=(
            "Success processed image"
        )
    )


def upload_to_input_bucket(filename, image_name):
    with open(filename, "rb") as f:
        s3.upload_fileobj(f, input_bucket, image_name)


def decode_image(response, image_name):
    message = response['Messages'][0]
    image_64_decode = base64.b64decode(message['Body'])
    random = ''.join(datetime.today().strftime('%m-%d-%y-%H-%M-%S-%f'))
    if not os.path.exists(f"./{image_folder}"):
        os.mkdir(f"./{image_folder}")
    filename = f"./{image_folder}/image_{random}_{image_name}.JPEG"
    with open(filename, 'wb') as f:
        f.write(image_64_decode)
    upload_to_input_bucket(filename, image_name)
    return filename


if __name__ == "__main__":
    request_url = get_url('request-queue')
    response_url = get_url('response-queue')
    buckets = boto3.resource('s3').buckets.all()
    for bucket in buckets:
        if "input-bucket" in bucket.name:
            input_bucket = bucket.name
        if "output-bucket" in bucket.name:
            output_bucket = bucket.name
        pass
    read_request_message()
