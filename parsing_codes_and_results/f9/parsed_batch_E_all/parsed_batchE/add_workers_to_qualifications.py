import boto3
import csv

# Replace with your QualificationTypeId
QUALIFICATION_TYPE_ID = '36YIZPMVI2VHIMVPLA0VDJZR98J7UK'

# Initialize MTurk client (sandbox or live)
mturk = boto3.client('mturk',
    region_name='us-east-1',
    aws_access_key_id='AKIATUCSXUFKS7TBUAXB',
    aws_secret_access_key='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',
    endpoint_url='https://mturk-requester.us-east-1.amazonaws.com'  # for production
    # endpoint_url='https://mturk-requester-sandbox.us-east-1.amazonaws.com'  # for sandbox
)

with open('./parsing_codes_and_results/f9/parsed_batchF/participants_upload.csv', newline='') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        worker_id = row['WorkerId']
        value = int(row['Value'])
        response = mturk.associate_qualification_with_worker(
            QualificationTypeId=QUALIFICATION_TYPE_ID,
            WorkerId=worker_id,
            IntegerValue=value,
            SendNotification=False
        )
        print(f"Assigned qualification to {worker_id}")
