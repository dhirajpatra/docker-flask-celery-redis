import time
from flask import current_app
import boto3
from boto3.s3.transfer import TransferConfig, S3Transfer
from botocore.exceptions import ClientError, ParamValidationError 
from rq import Queue, Connection, get_current_job
from rq.registry import FailedJobRegistry
import os
import redis


BUCKET = "presto-infra-staging-test-logs"
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCCESS_KEY = os.environ['AWS_SECRET_ACCCESS_KEY']
AWS_REGION = os.environ['AWS_REGION']
# REGION = "us-west-1"
MB = 1024
GB = MB ** 3

def create_task(task_type):
    time.sleep(int(task_type) * 2)
    return True

# actul uploading to s3
def upload(file_path, file_name, mac, restaurant_code, application_name, application_type, file_save_time, mime_type):
    try:
        s3_client = False
        s3_client = boto3.client('s3', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCCESS_KEY)
        config = TransferConfig(multipart_threshold=25 * MB, 
            max_concurrency=5,
            multipart_chunksize=25 * MB, 
            use_threads=True,
            num_download_attempts=10)
        # remove time stamp from file name to extract the actual file name        
        actual_file_name = file_name[13:]
        start_time = file_name[0:13]
        object = mac + '/' + actual_file_name
        file_size = os.stat(file_path).st_size


        s3_client.upload_file(
            file_path, 
            BUCKET, 
            object, 
            ExtraArgs={
                'ContentType': mime_type
                },
                Config=config
                ) 

        try:
            # save into database
            # {
            #     "_id" : ObjectId("5fa2a9443b2cb0000bb334ad"),
            #     "mac" : "ff4v-fdf4-j7j8-3f44",
            #     "task_id": "7614f5f6-3b50-43d7-bcbb-3e34a56807ee",
            #     "file_name" : "actual.log",
            #     "start_time" : "324224443434347",
            #     "end_time" : "535346345344"
            # }
            # get current job details
            job = get_current_job()
            # db = current_app.db
            dynamodb = boto3.client('dynamodb',  region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCCESS_KEY)
            s3_path = 'https://' + BUCKET + '.s3-' + os.environ['AWS_REGION'] + '.amazonaws.com/' + object
            end_time = round(time.time() * 1000)
            
            post = {
                "task_id" : {
                    "S" : job.id
                },
                "mac": {
                    "S" : mac
                },
                "info" : {
                    "M" : {
                        "application_name" : {
                            "S" : application_name
                        },
                        "application_type" : {
                            "S" : application_type
                        },
                        "restaurant_code" : {
                            "S" : restaurant_code
                        },
                        "file_name" : { 
                            "S" : actual_file_name
                        },    
                        "file_size" : {
                            "S" : str(file_size)
                        },
                        "start_time" : { 
                            "S" : start_time 
                        },    
                        "end_time": {
                            "S" : str(end_time)
                        },
                        "s3_path": {
                            "S" : s3_path
                        },
                        "file_save_time": {
                            "S": file_save_time
                        }
                    }                          
                }
            }
            
            dynamodb.put_item(
                TableName=os.environ['DYNAMODB_TABLE'],
                Item=post
            )
            # db.logs.insert_one(post)

            # create msg for queue to remove file task
            with Connection(redis.from_url(current_app.config["REDIS_URL"])):
                q = Queue('default')
                q.enqueue(remove_file, args=(mac, file_path))

        except ClientError as e:
            # remove failed job
            # q = Queue()
            # registry = FailedJobRegistry(queue=q)
            # for job_id in registry.get_job_ids():
            #     registry.remove(job_id, delete_job=True)
            try:
                os.remove(file_path)         
            except ClientError as e:
                write_error_log_s3(str(e), mac)
            return False 
        
    except ClientError as e:
        write_error_log_s3(str(e), mac)
        return False 
    except ParamValidationError as e:
        write_error_log_s3(str(e), mac)
        return False    

    return True


# this will remove file from EFS or intermidiatary place as a task
def remove_file(mac, file_path):
    try:
        os.remove(file_path)         
    except ClientError as e:
        write_error_log_s3(str(e), mac)
        return False 


# this will upload a error log file
def write_error_log_s3(error, mac):
    s3_client = boto3.client('s3', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCCESS_KEY)
    file_name = str(round(time.time() * 1000)) + '.txt' 
    object = mac + '/error_logs/' + file_name
    
    f = open(file_name, "w")
    f.write(error)
    f.close()

    try:
        s3_client.upload_file(file_name, BUCKET, object)
        os.remove(file_name)
        return True
    except ClientError as e:
        return False
