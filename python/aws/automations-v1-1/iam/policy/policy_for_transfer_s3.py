import json
import boto3

iam_client = boto3.client('iam')

def create_policy():
    print("Creating a new IAM policy...")
    bucket_name = input("Enter the S3 bucket name: ")
    object_path = input("Enter the S3 object path (e.g., transfer-users/*): ")
    policy_name = input("Enter the policy name: ")
    description = "IAM policy for S3 access in transfer family"

    bucket_arn = 'arn:aws:s3:::{}'.format(bucket_name)
    bucket_unique_arn = 'arn:aws:s3:::{}/{}/*'.format(bucket_name, object_path)

    action_read = [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:GetObjectAcl"       
    ]

    action_write = [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:GetObjectAcl",
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:DeleteObject"
    ]

    action_list_bucket = [
        "s3:ListBucket"
    ]


    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowReadAcess",
                "Effect": "Allow",
                "Action": action_read,
                "Resource": [
                    bucket_unique_arn
                ]
            },
            {
                "Sid": "AllowReadAcessAplication",
                "Effect": "Allow",
                "Action": action_write,
                "Resource": [
                    bucket_unique_arn
                ],
                "Condition": {
                    "StringLikeIfExists": {
                        "aws:username": "*-dbw"
                    }
                }
            },
            {
                "Sid": "AllowListBucket",
                "Effect": "Allow",
                "Action": action_list_bucket,
                "Resource": [
                    bucket_arn
                ],
            }
        ]
    }
    
    try:
        response = iam_client.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document),
            Description=description
        )
        print(f"Policy '{policy_name}' created successfully.")
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"Policy with name '{policy_name}' already exists.")
    except Exception as e:
        print(f"Error creating policy '{policy_name}': {e}")