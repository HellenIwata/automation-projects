import boto3
import json
from botocore.exceptions import ClientError

output_file = "audit_report.json"

s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')
sts_client = boto3.client('sts')


buckets = []

def get_account_info():
    try:
        response = sts_client.get_caller_identity()
        account_id = response['Account']
        account_username = response['Arn'].split('/')[1]

        return account_id, account_username
    except Exception as e:
        print(f"Error getting account information: {e}")
        return None, None

def list_buckets():
    global buckets
    try:
        response = s3_client.list_buckets()
        buckets = response['Buckets']

        print(f"Total de buckets encontrados: {len(buckets)}")

    except Exception as e:
        print(f"Error listing buckets: {e}")

def list_objects(bucket):
    objects = []
    global s3_resource
    try:
        bucket = s3_resource.Bucket(bucket)
        
        for obj in bucket.objects.all():
            objects.append(obj.key)

        return len(objects), objects

    except Exception as e:
        print(f"Error listing objects in bucket '{bucket}': {e}")
    return objects


def _check_public_acess_logic(bucket):
    try:
        response = s3_client.get_public_access_block(
            Bucket=bucket
        )
        config = response['PublicAccessBlockConfiguration']

        blocked = (config['BlockPublicAcls'] and 
            config['IgnorePublicAcls'] and 
            config['BlockPublicPolicy'] and 
            config['RestrictPublicBuckets'])
        
        return not blocked
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
            return True
        return False

def _check_static_website(bucket):
    try:
        s3_client.get_bucket_website(
            Bucket=bucket
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchWebsiteConfiguration':
            return False
        return False


def check_public_acess():
    public_buckets = []
    for b in buckets:
        bucket_name = b['Name']
        if _check_public_acess_logic(bucket_name):
            public_buckets.append(bucket_name)
    return public_buckets

def generate_report(public_buckets):
    details = []
    for bucket_name in public_buckets:
        print(f"  - Analyzing bucket: {bucket_name}")
        static_website_status = _check_static_website(bucket_name)
        object_count, object_keys = list_objects(bucket_name)

        details.append({
            'bucket_name': bucket_name,
            'public_access': True,
            'static_website': static_website_status,
            'object_count': object_count,
            'object_key': object_keys
        })
    return details

def audit_run():
    print("\n" + "="*50)
    print("         STARTING S3 SECURITY AUDIT REPORT")
    print("="*50)

    account_id, account_username = get_account_info()
    list_buckets()
    public_buckets = check_public_acess()
    
    final_details = []
    if public_buckets:
        print("\nGenerating detailed reports for risk buckets")
        final_details = generate_report(public_buckets)
    else:
        print("\nNo risk buckets found.")  
    
    print("\n" + "="*50)
    print("         FINAL S3 SECURITY AUDIT REPORT")
    print("="*50)
        
    final_reports = {
        "aws_account_id": account_id,
        "aws_account_username": account_username,
        "found_bucket_public_access": len(public_buckets),
        "name_buckets": public_buckets,
        "details_bucket": final_details
    }

    with open(output_file, 'w') as f:
        json.dump(final_reports, f, indent=4, ensure_ascii=False)
    
    print(f"\nReport saved to '{output_file}'")


if __name__ == "__main__":
    audit_run()