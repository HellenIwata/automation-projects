import json
import boto3

s3_client = boto3.client('s3')

def show_menu_bucket():
    print("""
========== Bucket Management Menu ============
| 1. Create S3 Bucket                        |
| 2. Create Object (Folder) in Bucket        |
| 3. Configure Bucket Policy                 |
| 5. Configure CORS                          |
| 6. Configure Lifecycle Rules               |
| 7. Back to Main Menu                       |
| 8. Exit                                    |
----------------------------------------------
""")
    choice = input("Enter your choice: ")
    return choice

def create_s3_bucket():
    print("Creating a new S3 bucket...")
    bucket_name = input("Enter the bucket name: ")
    try:
        s3_client.create_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' created successfully!")
    except Exception as e:
        print(f"Error creating bucket: {e}")
    return bucket_name

def create_s3_object():
    print("Creating a new object (folder) in S3 bucket...")
    bucket_name = input("Enter the bucket name: ")
    folder_name = input("Enter the folder name: ")
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=(folder_name + "/")
        )
        print(f"Folder '{folder_name}' created successfully in bucket '{bucket_name}'!")
    except Exception as e:
        print(f"Error creating folder: {e}")

def get_scope_policy():
    print("""
=========== Defining policy scope ===========
| 1. Cross-Account Access (read-only)       |
| 2. Require use of HTTPS/SSL               |
| 3. Read access to specific IP             |
| 4. Enforce encryption on uploads          |
| 5. Back to Bucket Menu                    |
| 6. Exit                                   |
---------------------------------------------
""")
    choice = input("Enter your choice: ")

    cross_account_policy ={
        "ID":"CrossAccountAccessReadOnly",
        "Sid":"AllowCrossAccountReadOnly",
        "Effect":"Allow",
        "Principal":{},
        "Action":"s3:GetObject"
    }
    require_https_policy ={
        "Id":"DenyUnsecureConnections",
        "Sid":"DenyUnsecureConnections",
        "Effect":"Deny",
        "Action":"s3:*",
        "Condition":{
            "Bool":{"aws:SecureTransport":"false"}
        }
    }
    read_access_ip_policy ={
        "Id":"AllowSpecificIPAcess",
        "Sid":"AcessoFromSpecificIP",
        "Effect":"Allow",
        "Action":["s3:GetObject","s3:ListBucket"],
        "Condition":{
            "IpAddress":{"aws:SourceIp":{}}
        }
    }
    enforce_encryption_policy ={
        "Id":"DenyUnencryptedPutObjects",
        "Sid":"DenyUnencryptedPutObjects",
        "Effect":"Deny",
        "Principal":"*",
        "Action":"s3:PutObject",
        "Condition":{
            "Null":{"s3:x-amz-server-side-encryption":"AES256"}
        }
    }

    match choice:
        case '1':
            print("This policy allows aexternal account to read objects in the bucket.")
            account_aws_id = input("Enter the AWS Account ID to allow read-only access: ")
            cross_account_policy['Principal'] = {"AWS":"arn:aws:iam::{}:root".format(account_aws_id)}
            return cross_account_policy

        case '2':
            print("This policy denies any request that is not using trabsoirt encryption HTTPS/SSL.")
            return require_https_policy

        case '3':
            print("""
This is policy allow public acess to the bucket only for a spefic block of IP addresses.
Usually for on-premises apps or trusted networks"""
            )
            source_ip = input("Enter the Blocked of IP addresses: ")
            read_access_ip_policy['Condition']['IpAddress']['aws:SourceIp'] = source_ip
            return read_access_ip_policy
        
        case '4':
            print("""
This policy ensures that, for the s3:PutObject action to be successful, the ´x-amz-server-side-encryption header´ must be set to ´AES256´. 
If the upload does not meet this condition, it will be denied.
""")
            return enforce_encryption_policy
        
        case '5':
            show_menu_bucket()
        
        case '6':
            exit()
        
        case _:
            print("Invalid choice. Please select a valid option (1-6).")

def _create_policy_logic(policy_document, bucket_name):
    """Helper function to create an Bucket policy."""
    policy_document = {
        "Version": "2012-10-17",
        "Id":policy_document['Id'],
        "Statement": [
            {
                "Sid":policy_document['Sid'],
                "Effect":policy_document['Effect'],
                "Principal":policy_document['Principal'],
                "Action":policy_document['Action'],
                #"Resource":policy_document['Resource'],
                "Condition":policy_document['Condition']
            }
        ]
    }
    try:
        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(policy_document)
        )
        print("Policy applied successfully!")
    except Exception as e:
        print(f"Error applying policy: {e}")

def configure_bucket_policy():
    print("Configuring bucket policy...")
    bucket_name = input("Enter the bucket name: ")

    resource_arn = "arn:aws:s3:::{}/*".format(bucket_name)

    policy= get_scope_policy()

    policy_document = {
        "Id":policy['Id'],
        "Sid":policy['Sid'],
        "Effect":policy['Effect'],
        "Principal":policy['Principal'],
        "Action":policy['Action'],
        "Resource":resource_arn,
        "Condition":policy['Condition']
    }
    _create_policy_logic(policy_document, bucket_name)

def configure_cors():
    print("Configuring CORS...")
    bucket_name = input("Enter the bucket name: ")
    cors_configuration = {
        "CorsConfiguration": {
            "CorsRules": [
                {
                    "AllowedHeaders": ["*"],
                    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
                    "AllowedOrigins": ["*"],
                    "MaxAgeSeconds": 3000
                }
            ]
        }
    }
    try:
        s3_client.put_bucket_cors(
            Bucket=bucket_name,
            CORSConfiguration=cors_configuration["CorsConfiguration"]
        )
        print("CORS configuration applied successfully!")
    except Exception as e:
        print(f"Error applying CORS configuration: {e}")    

def get_lifecycle_rules():
    print("""
=========== Defining lifecycle rules ===========
| 1. Transition Actions                        |
| 2. Expiration Actions                        |
| 3. Expiration and Transition Actions         |
| 4. Back to Bucket Menu                       |
| 5. Exit                                      |
------------------------------------------------
""")
    choice = input("Enter your choice: ")

    transition_actions={
        "Id":"MoveData",
        "Filter":{
            "Prefix":{} # Aplica apenas para objetos dentro do objeto
        },
        "Status":"Enabled",
        "Transitions":[
            { # Regra de transicao para versao atual, move o objeto para classes mais frias
                "Days":{},
                "StorageClass":{}
            },
            {
                "Days":{},
                "StorageClass":{}
            }
        ]
    }
    
    expiration_actions={
        "Id":"DeleteData",
        "Filter":{
            "Prefix":{}
        },
        "Status":"Enabled",
        "Expiration":{ # Regra de expiração para a versao atual. Após 1095 idas (3 anos), adiciona um Delete Marker
            "Days":{}
        },
        "NoncurrentVersionTransitions":[ # Regra transação para Versao não atual
            {
                "NoncurrentDays":{},
                "StorageClass":{}
            }
        ],
        "NoncurrentVersionExpiration":{ # Regra de expiração para a Versao não atual
            "NoncurrentDays":{}
        },
        "AbortIncompleteMultipartUpload":{ # Limpa uplaod fracionados que não foram concluídos dentro de 7 dias, economizando espaços e custos.
            "DaysAfterInitiation":{}
        }        
    }   

    expiration_transition_actions={
        "ID": "MoveAndExpireData",
        "Filter": {
            "Prefix": {}
        },
        "Status": "Enabled",
        
        "Transitions": [
            {
                "Days": {},
                "StorageClass": {}
            },
            {
                "Days": {},
                "StorageClass": {}
            }
        ],
        
        "Expiration": {
            "Days": {} 
        },
        
        "NoncurrentVersionTransitions": [
            {
                "NoncurrentDays": {},
                "StorageClass": {}
            }
        ],
        
        "NoncurrentVersionExpiration": {
            "NoncurrentDays": {}
        },
        
        "AbortIncompleteMultipartUpload": {
            "DaysAfterInitiation": {}
        }
    }
    match choice:
        case 1:
            object = input ("Enter the object name (e.g., /* for all objects): ")
            first_days = input(" Enter the firts date for transition (e.g., 30, 60 or 180 days): ")
            first_storage_class = input("Enter the first storage class for transition (e.g., STANDARD_IA, GLACIER): ").upper()
            second_days = input(" Enter the second date for transition (e.g., 30, 60 or 180 days): ")
            second_storage_class = input("Enter the second storage ckass for transition (e.g., STANDARD_IA, GLACIER): ").upper()
            
            transition_actions['Filter']['Prefix'] = object
            transition_actions['Transitions'][0]['Days'] = first_days
            transition_actions['Transitions'][0]['StorageClass'] = first_storage_class
            transition_actions['Transitions'][1]['Days'] = second_days
            transition_actions['Transitions'][1]['StorageClass'] = second_storage_class

            return transition_actions
        case 2:
            object = input ("Enter the object name (e.g., /* for all objects): ")
            expiration_days_current =  input("Enter the date for expiration (e.g., 30, 60 or 180 days):")
            expirantion_days_noncurrent = input("Enter the date for noncurrent expiration (e.g., 30, 60 or 180 days): ")
            abort_incomplete_upload = input("Enter the date for abort incomplete upload (e.g., 30, 60 or 180 days): ")

            expiration_actions['Filter']['Prefix'] = object
            expiration_actions['Expiration']['Days'] = expiration_days_current
            expiration_actions['NoncurrentVersionExpiration']['NoncurrentDays'] = expirantion_days_noncurrent  
            expiration_actions['AbortIncompleteMultipartUpload']['DaysAfterInitiation'] = abort_incomplete_upload
            return expiration_actions
        case 3:
            object = input ("Enter the object name (e.g., /* for all objects): ")
            first_days = input(" Enter the firts date for transition (e.g., 30, 60 or 180 days): ")
            first_storage_class = input("Enter the first storage class for transition (e.g., STANDARD_IA, GLACIER): ").upper()
            second_days = input(" Enter the second date for transition (e.g., 30, 60 or 180 days): ")
            second_storage_class = input("Enter the second storage ckass for transition (e.g., STANDARD_IA, GLACIER): ").upper()
            expiration_days_current =  input("Enter the date for expiration (e.g., 30, 60 or 180 days):")
            expirantion_days_noncurrent = input("Enter the date for noncurrent expiration (e.g., 30, 60 or 180 days): ")
            abort_incomplete_upload = input("Enter the date for abort incomplete upload (e.g., 30, 60 or 180 days): ")

            expiration_transition_actions['Filter']['Prefix'] = object
            expiration_transition_actions['Transitions'][0]['Days'] = first_days
            expiration_transition_actions['Transitions'][0]['StorageClass'] = first_storage_class
            expiration_transition_actions['Transitions'][1]['Days'] = second_days
            expiration_transition_actions['Transitions'][1]['StorageClass'] = second_storage_class
            expiration_transition_actions['Expiration']['Days'] = expiration_days_current
            expiration_transition_actions['NoncurrentVersionExpiration']['NoncurrentDays'] = expirantion_days_noncurrent  
            expiration_transition_actions['AbortIncompleteMultipartUpload']['DaysAfterInitiation'] = abort_incomplete_upload

            return expiration_transition_actions
        case 4:
            show_menu_bucket()
        case 5:
            exit()

def _configure_lifecycle_rules(bucket_name):
    lifecycle_rules = get_lifecycle_rules()
    try:
        s3_client.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration={
                'Rules': [lifecycle_rules]
            }
        )
        print("Lifecycle rules applied successfully!")
    except Exception as e:
        print(f"Error applying lifecycle rules: {e}")

def configure_lifecycle_rules():
    print("Configuring lifecycle rules...")
    bucket_name = input("Enter the bucket name: ")
    _configure_lifecycle_rules(bucket_name)

def handle_bucket_choice(choice):
    match choice:
        case '1':
            create_s3_bucket()
        case '2':
            create_s3_object()
        case '3':
            configure_bucket_policy()
        case '5':
            configure_cors()
        case '6':
            configure_lifecycle_rules()
        case '7':
            return
        case '8':
            exit()
        case _:
            print("Invalid choice. Please select a valid option (1-8).")

def main():
    while True:
        choice = show_menu_bucket()
        if choice == '8':
            break
        handle_bucket_choice(choice)

if __name__ == "__main__": 
    main()

