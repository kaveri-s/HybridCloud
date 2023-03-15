import base64
from multiprocessing import Process
import time
import boto3
from flask import *
from flask_cors import CORS, cross_origin
import json

App = Flask(__name__)
sqs = boto3.client("sqs")
processed_images = {}
CORS(App)

APP_TIER_ID = "ami-000000000000000"
SECURITY_GROUP_ID = "sg-000000000000000"
MSG_PER_INS = 3


def get_url(url_type):
    queue = sqs.list_queues()
    for url in queue['QueueUrls']:
        if url_type in url:
            return url


@App.route('/web-tier', methods=['POST', 'GET'])
@cross_origin()
def start_point():
    image_file = request.files['myfile']
    file_name = request.files['myfile'].filename
    x = image_file.read()
    encoded_image = base64.b64encode(x).decode("utf-8")

    print(f"\nSending request to sqs queue.")
    sqs.send_message(
        QueueUrl=get_url('request-queue'),
        DelaySeconds=10,
        MessageAttributes={
            'Name': {
                'DataType': 'String',
                'StringValue': file_name
            }
        },
        MessageBody=encoded_image
    )
    print(f"Request message sent.\n")

    while True:
        try:
            cache_result = json.load(open('cache.json'))
            if file_name in cache_result:
                return {
                    "status": 200,
                    "name": file_name,
                    "result": cache_result[file_name]
                }
            time.sleep(0.5)
        except:
            continue


def process_response_queue():
    response_url = get_url('response-queue')
    while True:
        response = sqs.receive_message(
            QueueUrl=response_url,
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

        if 'Messages' in response:
            message = response["Messages"][0]
            image_name = message["MessageAttributes"]["Name"]["StringValue"]
            msg_receipt_handel = message["ReceiptHandle"]
            cache_result = json.load(open('cache.json'))
            cache_result[image_name] = message["MessageAttributes"]["Result"]["StringValue"]
            json_object = json.dumps(cache_result)
            with open("cache.json", "w") as outfile:
                outfile.write(json_object)
            sqs.delete_message(
                QueueUrl=response_url,
                ReceiptHandle=msg_receipt_handel
            )


def clean_cache():
    a = {}
    with open("cache.json", "w") as outfile:
        outfile.write(json.dumps(a))


def process_app_tier():
    while True:
        url = get_url("request-queue")
        messages_count = get_messages_count(url)
        instances_count = get_number_of_instances()
        required_instances = messages_count // MSG_PER_INS

        if required_instances > 20:
            required_instances = 20
        if required_instances < 0:
            required_instances = 0

        print(f"Messages count: {messages_count}, Instances count: {instances_count}, Required Instances: {required_instances}")

        app_tier_name = "app_tire_instance"
        # if instances_count == 0:
        #     app_tier_name += "_main"
        if required_instances > instances_count:
            for i in range(0, required_instances - instances_count):
                print(f"Creating {required_instances - instances_count} app-tier instance.")
                app_tier_instance = boto3.resource("ec2").create_instances(
                    ImageId=APP_TIER_ID,
                    MinCount=1,
                    MaxCount=1,
                    InstanceInitiatedShutdownBehavior='terminate',
                    InstanceType='t2.micro',
                    KeyName='cc',
                    SecurityGroupIds=[
                        SECURITY_GROUP_ID,
                    ],
                    TagSpecifications=[
                        {
                            'ResourceType': 'instance',
                            'Tags': [
                                {
                                    'Key': 'Name',
                                    'Value': app_tier_name
                                },
                            ]
                        },
                    ]
                )
                instance = app_tier_instance[0]
                print(f"Instance id: {instance.id}")
        time.sleep(0.2)


def get_messages_count(url):
    # print(f"Getting message count.")
    sqs = boto3.client('sqs')
    res = sqs.get_queue_attributes(QueueUrl=url,
                                   AttributeNames=['ApproximateNumberOfMessages'])
    messages_count = int(res['Attributes']['ApproximateNumberOfMessages'])
    # print(f"Messages count: {messages_count}")
    return messages_count


def get_number_of_instances():
    # print("\n Getting instances count.")
    ec2 = boto3.resource('ec2')
    instances_count = 0
    instances = ec2.instances.all()
    for instance in instances:
        if (instance.state['Name'] == 'running' or \
                instance.state['Name'] == 'pending') and \
                instance.image.id == APP_TIER_ID:
            instances_count += 1
    # print(f"Instances count: {instances_count}\n")
    return instances_count


if __name__ == "__main__":
    clean_cache()
    p1 = Process(target=process_response_queue)
    p2 = Process(target=process_app_tier)
    p1.start()
    p2.start()
    App.run(threaded=True, host='0.0.0.0', port=5000)
