import configparser
import os
import sys
import boto3
import json
from botocore.exceptions import ClientError

# ---- Initialization and Global Variables ----

s3_client = None
s3_resource = None
sts_client = None


buckets = []

reports ={
    "AWS_ACCOUNT_ID": "",
    "AWS_PROFILE_NAME": '',
    "FOUND_BUCKET_PUBLIC_ACCESS": 0,
    "VUNERABLE_BUCKET_NAMES": '',
    "BUCKET_DETAILS": {}
}

# ---- 1. Utility Functions (GET Profile/Account Info) ----
def get_all_target_profiles(credentials_path='~/.aws/credentials'):
    """
    Reads the AWS credentials file and returns a list of profile names.
    """
    credentials_file = os.path.expanduser(credentials_path)

    if not os.path.exists(credentials_file):
        print("ERROR: AWS credentials file not found at {}".format(credentials_file), file=sys.stderr)
        sys.exit(1)
        return []
    
    config = configparser.ConfigParser()
    config.read(credentials_file)

    profiles = [section for section in config.sections()]

    return profiles

def get_account_info():
    """
    GETs the AWS Account ID for the current session
    """
    try:
        response = sts_client.get_caller_identity()

        reports["AWS_ACCOUNT_ID"] = response['Account']

        print("Audit running on AWS Account ID: {}".format(reports["AWS_ACCOUNT_ID"]))
        
    except Exception as e:
        print("Error getting account information: {}".format(e),file=sys.stderr)

# ---- 2. Core Audit Functions ----

def list_buckets():
    """LISTs all buckets for the current profile"""

    global buckets

    try:
        response = s3_client.list_buckets()
        buckets = response['Buckets']

        print(f"Total de buckets encontrados: {len(buckets)}")

    except Exception as e:
        print("Error listing buckets: {}".format(e),file=sys.stderr)

def _check_public_acess_logic(bucket):
    """
    Return ´TRUE´ if Public Access Block (PAB) is *NOT* fully enabled (indicating risk).
    """

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

def check_vunerable_access():
    """
    Identifies and registers all buckets with potential public access risk.
    """
    
    for b in buckets:
        bucket_name = b['Name']
        if _check_public_acess_logic(bucket_name):
            reports["VUNERABLE_BUCKET_NAMES"].append(bucket_name)
            reports["FOUND_BUCKET_PUBLIC_ACCESS"] += 1

# ---- 3. Details Functions for vunerable buckets ----

def _check_static_website_logic(bucket):
    """
    Checks if Static Website Hosting is enabled for the given bucket.
    """
    try:
        s3_client.get_bucket_website(
            Bucket=bucket
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchWebsiteConfiguration':
            return False
        return False

def list_objects(bucket):
    """
    Lists all objects (recursively) in the specified bucket and returns the count and keys.
    """
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

def generate_detailed_report():
    """
    Generates a detailed report structure for EACH vunerable bucket.
    """
    for bucket_name in reports["VUNERABLE_BUCKET_NAMES"]:
        print("\t - Analyzing bucket: {}".format(bucket_name))

        public_access_status = True
        static_website_status = _check_static_website_logic(bucket_name)
        object_count, object_keys = list_objects(bucket_name)

        reports["BUCKET_DETAILS"][bucket_name] = {
            'bucket_name': bucket_name,
            'public_access': public_access_status,
            'static_website': static_website_status,
            'object_count': object_count,
            'object_key': object_keys
        }

# ---- 4. Main Execution Functions ----
def audit_run(profile_name):
    """
    Executes the full audit process for a single account using the specified profile.
    """
    print("\n" + "="*100)
    print("\t\tSTARTING S3 SECURITY AUDIT REPORT FOR: {}".format(profile_name))
    print("="*100)

    # 4.1. Initialize Session and Clients for the Profile
    try:
        session = boto3.Session(profile_name=profile_name)
        global s3_client, s3_resource, sts_client

        s3_client = session.client('s3')
        s3_resource = session.resource('s3')
        sts_client = session.client('sts')
    
    except Exception as e:
        print("ERROR: Failed to initialize session for profile '{}': {}".format(profile_name,e),file=sys.stderr)
        return
    
    # 4.2. Reset Global Report and Set Profile Name
    global reports
    reports = {
        "AWS_ACCOUNT_ID": "",
        "AWS_PROFILE_NAME": profile_name,
        "FOUND_BUCKET_PUBLIC_ACCESS": 0,
        "VUNERABLE_BUCKET_NAMES": [],
        "BUCKET_DETAILS": {}
    }

    # 4.3. Execute Audit Steps

    get_account_info()
    list_buckets()
    check_vunerable_access()
    
    if reports["FOUND_BUCKET_PUBLIC_ACCESS"] > 0:
        print("\nGenerating detailed reports for risk buckets")
        generate_detailed_report()
    else:
        print("\nNo vulnerable buckets found in this account.")  

    # 4.4. Save Final Report to File
    report_filename = "s3_audit_report_{}_{}.json".format(profile_name, reports["AWS_ACCOUNT_ID"])
    
    final_report = {
        "AWS_PROFILE_NAME": reports["AWS_PROFILE_NAME"],
        "AWS_ACCOUNT_ID": reports["AWS_ACCOUNT_ID"],
        "FOUND_BUCKET_PUBLIC_ACCESS": reports["FOUND_BUCKET_PUBLIC_ACCESS"],
        "VUNERABLE_BUCKET_NAMES": reports["VUNERABLE_BUCKET_NAMES"],
        "BUCKET_DETAILS": [
            details for bucket, details in reports["BUCKET_DETAILS"].items()
        
        ]
    }

    print("\n" + "="*100)
    print("\t\tFINAL S3 SECURITY AUDIT REPORT")
    print("="*100)

    try:
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=4, ensure_ascii=False)
        print("\nReport saved to '{}'".format(report_filename))
    except Exception as e:
        print("ERROR: Failed to save report to file {}: {}".format(report_filename,e),file=sys.stderr)


if __name__ == "__main__":
    all_profiles = get_all_target_profiles()

    if not all_profiles:
        print("No AWS profiles found or configured in ´~/.aws/credentials´.")
    else:
        for profile in all_profiles:
            if profile == "default":
                print("Skipping 'default' profile.")
                continue
            audit_run(profile)

