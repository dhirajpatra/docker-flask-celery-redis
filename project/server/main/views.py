# project/server/main/views.py


from unittest import result
from flask import render_template, Blueprint, jsonify, request, current_app
import redis
from rq import Queue, Connection, Worker
from werkzeug.utils import secure_filename
import os
from os.path import join, dirname, realpath
import time
from time import ctime
import datetime
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
import mimetypes
from server.main.tasks import upload, create_task


main_blueprint = Blueprint("main", __name__,)

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCCESS_KEY = os.environ['AWS_SECRET_ACCCESS_KEY']
AWS_REGION = os.environ['AWS_REGION']
UPLOAD_FOLDER = '/uploads'
ACCEPTED_FILE_TYPES = ['txt', 'zip', 'log', 'gzip', 'csv']



# upload the file to S3
@main_blueprint.route("/log", methods=["POST"])
def upload_file():
    """
    Function to upload a file to an S3 bucket
    """
    if 'log_file' not in request.files:
        response = 'no file'
    
    # start time to calculate the total processing time 
    start_time = round(time.time() * 1000)
    mac = request.form.get('mac').strip()
    restaurant_code = request.form.get('restaurant_code').strip()
    application_name = request.form.get('application_name').strip()
    application_type = request.form.get('application_type').strip()
    file = request.files['log_file']    
    file_name = str(start_time) + secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    file_save_time = ''

    # some file type do not provide file extension
    type = mimetypes.guess_type(file_path)
    mime_type = type[0]

    # for them need to create custom mime type info from their file extension
    if mime_type == None:
        _, file_extension = os.path.splitext(file_path)
        m_type = file_extension.split(".")[-1]
        mime_type = "application/" + m_type
    else:
        temp = mime_type.split("/")
        m_type = temp[1]
        

    # put constraint for file type allow [.txt, .zip, .log, .gzip, .csv]
    if m_type not in ACCEPTED_FILE_TYPES:
        write_error_log_s3(mime_type + " not accepted", mac)
        response = [mime_type + " type file not accepted"]
        response_object = {
            "status": "failure",
            "data": {
                "message": response
            }
        }
        return jsonify(response_object), 400

    
    # except
    try:  
        file.save(file_path)
        # time taken to save into EFS
        file_save_time = str(int(round(time.time() * 1000)) - int(start_time)) 
        
    except ClientError as e:
        write_error_log_s3(str(e), mac)
        response = [str(e)]
        response_object = {
            "status": "failure",
            "data": {
                "message": response
            }
        }
        return jsonify(response_object), 400 
   
    # queue has been saved actula upload will be done from queue
    response = ["Your file uploaded succesfully"]
    
    with Connection(redis.from_url(current_app.config["REDIS_URL"])):
        q = Queue('default')
        workers = Worker.count(redis.from_url(current_app.config["REDIS_URL"]))
        no_workers_in_queue = Worker.all(queue=q)
        
        task = q.enqueue(upload, args=(
            file_path, 
            file_name, 
            mac,
            restaurant_code,
            application_name,
            application_type,
            file_save_time,
            mime_type))
    
    response_object = {
        "status": "success",
        "data": {
            "message": response,
            "task_id": task.get_id()
        }
    }
    return jsonify(response_object), 202


@main_blueprint.route("/", methods=["GET"])
def home():
    return render_template("main/home.html")


# create a test task
@main_blueprint.route("/task", methods=["POST"])
def run_task():
    try:
        task_type = request.form["type"]
        with Connection(redis.from_url(current_app.config["REDIS_URL"])):
            q = Queue()
            task = q.enqueue(create_task, task_type)  
            
            response_object = {
                "status": "success",
                "data": {
                    "task_id": task.get_id()
                }
            }
        return jsonify(response_object), 202
    except:
        return ("Test task not created")


# get all tasks
@main_blueprint.route("/all_tasks", methods=["get"])
def get_all_tasks():
    try:
        # db = current_app.db
        # # col = db.collection_names()

        # # Collection name  
        # record_count = db.logs.find().count()
        tasks = []
        # if record_count > 0:
        #     # {
        #     #     "_id" : ObjectId("5fa3c8225abc2e000ad7564c"),
        #     #     "mac" : "AA-00-04-00-XX-YY",
        #     #     "task_id" : "642c3321-7d76-4915-91f7-676d9157d842",
        #     #     "file_name" : "Presentation.pdf",
        #     #     "start_time" : "1604569106142923800",
        #     #     "end_time" : "1604569122723834800"
        #     # }
            
        #     results = db.logs.find({}, {'_id': 1, 'mac': 1, 'task_id': 2, 'file_name': 3, 'start_time': 4, 'end_time': 5})
        #     for task in results:
        #         tasks.append(str(task))
        try:
            dynamodb = boto3.client('dynamodb', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCCESS_KEY)
            # dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000")
        except:
            return "dynamodb not able to connect"
    
        tasks = dynamodb.scan(
            TableName = os.environ['DYNAMODB_TABLE']
        )
        
        if tasks:
            tasks_result = []
            for task in tasks['Items']:
                tasks_result.append(task['task_id']['S'])
            
            response_object = {
                "status": "success",
                "data": {
                    "total": len(tasks_result),
                    "tasks": tasks_result
                }
            }
            return jsonify(response_object), 202
        else:
            return jsonify("no result found"), 400

    except ClientError as e:
        return str(e)

@main_blueprint.route("/tasks", methods=["GET"])
def get_task():
    return render_template("main/tasks.html")

# get task details from task_id
@main_blueprint.route("/tasks/<task_id>", methods=["GET"])
def get_status(task_id):
    try:
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCCESS_KEY)
        table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
        
        # response = table.get_item(            
        #     Key={
        #         'task_id' : task_id,
        #         'mac' : 'AA-00-04-00-XX-YX'
        #     }
        # )

        response = table.query(
            KeyConditionExpression=
                Key('task_id').eq(task_id)
        )
        
        if response and response['Count'] > 0:
            start_time = response['Items'][0]['info']['start_time']
            end_time = response['Items'][0]['info']['end_time']
            dt1 = datetime.datetime.fromtimestamp(int(start_time) / 1000.0)
            dt2 = datetime.datetime.fromtimestamp(int(end_time) / 1000.0)
            file_save_time = 'less than 1' if response['Items'][0]['info']['file_save_time'] else response['Items'][0]['info']['file_save_time']
            
            t1 = str(datetime.datetime.strptime(str(dt1)[0:19], "%Y-%m-%d  %H:%M:%S"))
            t2 = str(datetime.datetime.strptime(str(dt2)[0:19], "%Y-%m-%d  %H:%M:%S"))
            file_size = (int(response['Items'][0]['info']['file_size']) / 1024) / 1024
            
            response_object = {
                "status": "success",
                "data": {
                    "task_id": task_id,
                    "mac": response['Items'][0]['mac'],
                    "restaurant_code": response['Items'][0]['info']['restaurant_code'],
                    "file_name": response['Items'][0]['info']['file_name'],
                    "file_size": f'{file_size:.2f}'  + ' MB',
                    "start_time": t1,
                    "end_time": t2,
                    "time_taken": str(dt2 - dt1),
                    "s3_path" : response['Items'][0]['info']['s3_path'],
                    "file_save_time": file_save_time + ' ms',
                    "application_name": response['Items'][0]['info']['application_name'],
                    "application_type": response['Items'][0]['info']['application_type']                                 
                }
            }
        else:
            response_object = {"status": "error"}
        return jsonify(response_object)
        
    except ClientError as e:
        response_object = {"status": str(e)}
        return jsonify(response_object)


# get task status for test tasks
@main_blueprint.route("/task_status/<task_id>", methods=["GET"])
def get_task_status(task_id):
    with Connection(redis.from_url(current_app.config["REDIS_URL"])):
        q = Queue()
        task = q.fetch_job(task_id)
    if task:
        response_object = {
            "status": "success",
            "data": {
                "task_id": task.get_id(),
                "task_status": task.get_status(),
                "task_result": task.result,
            },
        }
    else:
        response_object = {"status": "error"}
    return jsonify(response_object)


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
        return True
    except ClientError as e:
        return False