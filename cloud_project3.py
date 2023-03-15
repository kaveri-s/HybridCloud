import sys
import time

import yaml
import boto3
from datetime import datetime

WEB_TIER_AMI = "ami-000000000000"
SECURITY_GROUP_ID = "sg-000000000000"


with open('config/config.yaml') as fh:
    config_data = yaml.load(fh, Loader=yaml.FullLoader)


def create_queues():
    print(f"\nCreating queues for sending request and receiving response.")
    sqs_create = boto3.resource('sqs')

    request_queue_name = f"request-queue-{datetime.today().strftime('%m_%d_%y-%H-%M-%S-%f')}"
    request_queue = sqs_create.create_queue(QueueName=request_queue_name)
    print(f"created request-queue: {request_queue}\n")

    response_queue_name = f"response-queue-{datetime.today().strftime('%m_%d_%y-%H-%M-%S-%f')}"
    response_queue = sqs_create.create_queue(QueueName=response_queue_name)
    print(f"created output queue: {response_queue}\n")
    print(f"successfully created queues.\n")


def delete_queues():
    client = boto3.client('sqs')
    queues = client.list_queues()
    print("\n")
    if 'QueueUrls' not in queues:
        print(f"No queues found.")
        return
    print(queues)
    if len(queues) > 0:
        print(f"Queues found. Deleting the queues.")
        for url in queues['QueueUrls']:
            try:
                print("Deleting queue with following url: ", url)
                client.delete_queue(QueueUrl=url)
            except:
                continue
        print(f"Successfully deleted queue(s).")


def create_buckets():
    s3 = boto3.client('s3')
    print("\ncreating buckets")
    input_bucket_name = f"input-bucket-{datetime.today().strftime('%m-%d-%y-%H-%M-%S-%f')}"
    input_bucket = s3.create_bucket(Bucket=input_bucket_name)
    boto3.resource('s3').BucketVersioning(input_bucket_name).enable()
    print(f"successfully created bucket: {input_bucket_name}")
    output_bucket_name = f"output-bucket-{datetime.today().strftime('%m-%d-%y-%H-%M-%S-%f')}"
    output_bucket = s3.create_bucket(Bucket=output_bucket_name)
    boto3.resource('s3').BucketVersioning(output_bucket_name).enable()
    print(f"successfully created bucket: {output_bucket_name}")


def delete_buckets():
    s3 = boto3.client('s3')
    print("\nChecking for existing buckets")
    response = s3.list_buckets()
    any_buckets = False
    for bucket in response['Buckets']:
        if "elasticbeanstalk" in bucket["Name"]:
            continue
        try:
            s3_resource = boto3.resource('s3').Bucket(bucket["Name"])
            print(f"deleting bucket: {bucket['Name']}")
            s3_resource.object_versions.delete()
            s3_resource.objects.all().delete()
            s3_resource.delete()
            any_buckets = True
        except:
            continue

    if any_buckets:
        print(f"Deleted all buckets.")
    else:
        print("No buckets found")


if __name__ == "__main__":
    tearDown = False
    if len(sys.argv) == 2 and sys.argv[1] == "teardown":
        tearDown = True

    delete_queues()
    delete_buckets()

    if not tearDown:
        create_queues()
        create_buckets()
        time.sleep(30)
