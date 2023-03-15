# Cloud_project_3 - Openstack
This project is a part of course work CSE 546: Cloud Computing.
Professor - Yuli Deng.


## Team Members
* Bharath Kumar Bandaru - 1219442718
* Kaveri Subramaniam - 1222089687
* Shruti Pattikara Sekaran - 1222257972

## Project Requirements


### Software Requirements
    Python3
    Boto3 - AWS SDK for python
    Flask - REST service
    Flask_cors - Enable CORS for all routes.
    Ec2_metadata - Metadata information regarding the instance.
    
### AWS CLI
    Install aws-cli from 
    https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

### AWS Configuration.
    Use command: aws configure
    ACCESS_KEY_ID = ABCDEFABCDEF12345
    SECRET_ACCESS_KEY_ID = AbcdEf1234/aBc123+ZxcvbQwErtFghJk12Z/v2
    REGION = us-east-1
    OUTPUT = JSON

    PEM key file for SSH Access: cc.pem

### Installing requirements

Download Python from ``https://www.python.org/downloads/``

### Installing openstack
    git clone https://git.openstack.org/openstack-dev/devstack
    ./stack.sh (and wait for it to finish.)
    Use the localhost ip address to access the openstack dashboard.

#### Installing packages:
    boto3         : pip3 install boto3
    flask         : pip3 install flask
    flask_cors    : pip3 install flask_cors
    ec2_metadata  : pip3 install ec2_metadata

### AWS services details
    URL for web-tier: http://<web_tier_appliation_dns>:5000/web-tier
    The web-tier dns address will be displayed once the web-tier instance starts.
    The m,d,y,H,M,S,f - are month, date, year, hours, minutes, seconds and milli second values.
    at the time of creation. This makes sure that the queue names and bucket names are unique.
    SQS Names:
        1. Request queue: request-queue-%m_%d_%y-%H-%M-%S-%f.
        2. Response queue: response-queue-%m_%d_%y-%H-%M-%S-%f.
    S3 Bucket Names:
        1. Input bucket: input-bucket-%m-%d-%y-%H-%M-%S-%f.
        2. Output bucket: output-bucket-%m-%d-%y-%H-%M-%S-%f.

### AWS EC2 image export
    aws ec2 export-image --image-id <web-tier-image-instance> --disk-image-format VMDK --s3-export-location S3Bucket=<input-bucket-name>,S3Prefix=<path-to-the-bucket>

### Running the application
    Make sure to install all the requirements before running the application.
    To start the application run the following command:
        python3 cloud_project3.py
        python3 opensource.py
    To perform only teardown of aws resources run the following command:
        python3 cloud_project3.py teardown