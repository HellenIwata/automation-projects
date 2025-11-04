import json
import boto3

transfer_client = boto3.client('transfer')
iam_client = boto3.client('iam')
s3_client = boto3.client('s3')


def show_welcome():
    print(
"""
===========================================================
|CREATE AN SFTP SERVER IN THE AWS TRANSFER FAMILY SERVICE |
-----------------------------------------------------------

"""
    )


# .TODO:
## - CREATE BUCKET
## - CREATE POLICY
## - CREATE ROLE
## - CREATE SERVER SFTP
## - CREATE USERS

# CREATE FUNCTION LOGIC 
def _create_bucket_logic(bucket_name, tag_customer):
    try:
        region = s3_client.meta.region_name
        if region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': region}
            )
        bucket_arn='arn:aws:s3:::{}'.format(bucket_name)

        s3_client.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging={
                'TagSet': [
                    {
                        'Key': 'customer',
                        'Value': tag_customer
                    }
                ]
            }
        )

        print("Bucket {} created successfully.\nBucket ARN: {}".format(bucket_name, bucket_arn))
    except Exception as e:
        print("Error creating bucket: {}".format(e))

def _create_object_bucket_logic(bucket_name, bucket_object, tag_customer):
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=(bucket_object + "/"), Tagging=f"customer={tag_customer}"
        )
    except Exception as e:
        print("Error creating object: {}".format(e))

def _create_policy_logic(policy_name, policy_document, tag_customer):
    try:
        response = iam_client.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document),
            Tags=[
                {
                    'Key': 'customer',
                    'Value': tag_customer
                }
            ]
        )
        policy_arn = response['Policy']['Arn']
        print("Policy {} created successfully.\nPolicy ARN: {}".format(policy_name, policy_arn))
        return policy_arn
    except Exception as e:
        print("Error creating policy: {}".format(e))

def _create_role_logic(role_name, policy_arn, tag_customer, trust_policy):
    try:
        iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Tags=[
                {
                    'Key': 'customer',
                    'Value': tag_customer
                }
            ]
        )
        role_arn = iam_client.get_role(RoleName=role_name)['Role']['Arn']

        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )

        print("Role {} created successfully.\nRole ARN: {}\n\nAttached Policy ARN: {}".format(role_name, role_arn, policy_arn))
        return role_arn
    except Exception as e:
        print("Error creating role: {}".format(e))

def _create_server_logic(endpoint_type, tag_customer,role_arn_logging):
    try:
        response = transfer_client.create_server(
            IdentityProviderType='SERVICE_MANAGED',
            EndpointType=endpoint_type,
            Protocols=['SFTP'],
            LoggingRole=role_arn_logging,
            Tags=[
                {
                    'Key': 'customer',
                    'Value': tag_customer
                }
            ]
            
        )
        print("Server created successfully\nServer ID: {}".format(response['ServerId']))
    except Exception as e:
        print("Error creating server: {}".format(e))

def _create_user_logic(server_id, user_name, role_arn, home_directory, ssh_key, tag_customer):
    try:
        transfer_client.create_user(
            ServerId=server_id,
            UserName=user_name,
            Role=role_arn,
            HomeDirectory="/",
            HomeDirectoryType='LOGICAL',
            HomeDirectoryMappings=[
                {
                    'Entry': '/',
                    'Target': home_directory
                }

            ],
            SshPublicKeyBody=ssh_key,
            Tags=[
                {
                    'Key': 'customer',
                    'Value': tag_customer
                }
            ]
        )

        print("User {} created successfully on Server {}".format(user_name, server_id))
    except Exception as e:
        print("Error creating user: {}".format(e))

# CREATE BUCKET
def create_bucket(bucket_name, tag_customer, bucket_object):

    _create_bucket_logic(bucket_name, tag_customer)
    _create_object_bucket_logic(bucket_name, bucket_object, tag_customer)


# CREATE POLICY
def create_policy(policy_name, tag_customer, bucket_name, bucket_object):
    bucket_arn = "arn:aws:s3:::{}".format(bucket_name)
    bucket_unique_arn = "arn:aws:s3:::{}/{}/*".format(bucket_name, bucket_object)

    action_read = [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:GetObjectAcl"       
    ]
    action_write = [
        "s3:GetObject",
        "s3:GetObjectVersion",
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

    _create_policy_logic(policy_name, policy_document, tag_customer)
    return f"arn:aws:iam::{boto3.client('sts').get_caller_identity().get('Account')}:policy/{policy_name}"

# CREATE ROLE
def create_role(role_name, policy_arn, tag_customer):
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "transfer.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

    return _create_role_logic(role_name, policy_arn, tag_customer, trust_policy)


def scope_endpoint():
    print("""
============ SERVER ENDPOINT SCOPE ============
| 1. Public                                   |
| 2. VPC                                      |
| 3. VPC Endpoint                             |
| 0. Back to Main Menu                        |
-----------------------------------------------

""")
    choice = input("Enter your choice: ")
    mapping = {
        '1': 'PUBLIC',
        '2': 'VPC',
        '3': 'VPC_ENDPOINT',
        '0': 'back'
    }
    return mapping.get(choice, 'invalid choice')


# CREATE SERVER
def create_server(tag_customer):
    endpoint_type = scope_endpoint()
    role_logging = input("Enter name Role for Logging: ").strip()
    account_id = boto3.client('sts').get_caller_identity().get('Account')
    role_arn_logging = f"arn:aws:iam::{account_id}:role/{role_logging}"

    _create_server_logic(endpoint_type, tag_customer, role_arn_logging)


# CREATE USERS
def create_users(role_arn, policy_arn):
    server_id = input("Enter server ID: ").strip()
    users_name = []
    directory_mappings=[]
    ssh_keys=[]
    tag_customers=[]

    while True:
        user_name = input("Enter a user name: ").lower()
        users_name.append(user_name)
    
        directory_mapping = input("Enter Home Directory (e.g., /my-bucket/user): ").strip()
        if not directory_mapping.startswith('/'):
            directory_mapping = '/' + directory_mapping
            print(f"Home directory did not start with '/'. Corrected to: {directory_mapping}")
        directory_mappings.append(directory_mapping)

        ssh_key = input("Enter SSH Key: ").strip()
        
        # Validate and clean the SSH key
        if not (ssh_key.startswith('ssh-rsa ') or ssh_key.startswith('ecdsa-')):
            print(f"Invalid SSH key format for user '{user_name}'. It must start with 'ssh-rsa' or 'ecdsa-'. Skipping this user.")
            users_name.pop()
            directory_mappings.pop()
            continue

        # AWS Transfer Family expects the SSH key without the comment part.
        # The key is typically in the format: <algorithm> <key-data> <comment>
        # We split the key and take the first two parts.
        key_parts = ssh_key.split()
        cleaned_ssh_key = ' '.join(key_parts[:2])
        ssh_keys.append(cleaned_ssh_key)

        tag_user_customer= input("Enter name Customer User for TAG: ").strip()
        tag_customers.append(tag_user_customer)

        more = input("Do you want to add another user? (y/n): ")
        if more.lower() != 'y':
            break

    for i in range(len(users_name)):
        _create_user_logic(
            server_id, 
            users_name[i], 
            role_arn, 
            directory_mappings[i], 
            ssh_keys[i], 
            tag_customers[i])
        
# VALIDATIONS FUNCTIONS
def bucket_exists(bucket_name):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except Exception as e:
        return False

def policy_exists(policy_name):
    try:
        iam_client.get_policy(PolicyName=policy_name)
        return True
    except Exception as e:
        return False

def role_exists(role_name):
    try:
        iam_client.get_role(RoleName=role_name)
        return True
    except Exception as e:
        return False

def server_exists(tag_customer):
    try:
        response = transfer_client.list_servers(
            Filters=[
                {
                    'Key': 'tag:customer',
                    'Values': [tag_customer]
                }
            ]
        )
        return len(response['Servers']) > 0
    except Exception as e:
        return False

def get_policy_arn(policy_name):
    response = iam_client.get_policy(PolicyName=policy_name)
    return response['Policy']['Arn']

def get_role_arn(role_name):
    response = iam_client.get_role(RoleName=role_name)
    return response['Role']['Arn']


def main():
    show_welcome()
    #bucket_name = input("Enter bucket name: ")
    #tag_customer = input("Enter name Customer for TAG: ").strip()
#
    #if not bucket_exists(bucket_name):
    #    bucket_object = input("Enter bucket object (e.g. /my-bucket/customer/user): ")
    #    create_bucket(bucket_name, tag_customer, bucket_object)
    #else:
    #    print("Bucket already exists: {}".format(bucket_name))
    #
    #bucket_object = input("Enter bucket object (e.g. /my-bucket/customer/user): ")
    #policy_name = input("Enter policy name: ")
    #if not policy_exists(policy_name):
    #    policy_arn = create_policy(policy_name, tag_customer, bucket_name, bucket_object)
    #else:
    #    policy_arn = get_policy_arn(policy_name)
    #    print(f"Política '{policy_name}' já existe. Usando ARN existente.")
#
    #role_name = input("Enter role name: ")
    #if not role_exists(role_name):
    #    role_arn = create_role(role_name, policy_arn, tag_customer)
    #else:
    #    role_arn = get_role_arn(role_name)
    #    print(f"Role '{role_name}' já existe. Usando ARN existente.")
#
    #if not server_exists(tag_customer):
    #    create_server(tag_customer)
    #else:
    #    print(f"Servidor com tag '{tag_customer}' já existe. Pulando criação.")
    role_arn= 'arn:aws:iam::739275464426:role/aws-transfer-acess-role'
    policy_arn='arn:aws:iam::739275464426:policy/aws-s3-user-acess-policy'
    create_users(role_arn, policy_arn)


if __name__ == "__main__":
    main()
    
    
