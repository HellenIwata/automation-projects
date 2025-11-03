import boto3
import csv
import json


def show_menu_transfer():
    print("""
====== Transfer Family Management Menu ======
| 1. Create Server                          |
| 2. Create User                            |
| 3. Delete User                            |   
| 4. Delete SSH Public Key                  |
| 5. Update User                            |
| 6. Update SSH Public Key                  |
| 7. Exports Users Server                   |
| 0. Back to Main Menu                      |
---------------------------------------------
""")
    choice = input("Enter your choice: ")
    return choice

transfer_client = boto3.client('transfer')

policy_document = """
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowReadAcess",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion",
            ],
            "Resource": [
                "arn:aws:s3:::meu-bucket/meu-objeto/*"
            ]
        },
        {
            "Sid": "AllowReadAcessAplication",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:GetObjectVersion",
                "s3:PutObject",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::meu-bucket/meu-objeto/*"
            ],
            "Condition": {
                "StringLikeIfExists": {
                    "aws:username": "*_motor"
                }
            }
        },
        {
            "Sid": "AllowListBucket",
            "Effect": "Allow",
            "Action": "s3:ListBucket",
            "Resource": [
                "arn:aws:s3:::meu-bucket"
            ],
        }
    ]
}
"""

# Functions Scopes
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


def scope_protocol():
    print("""
============ SERVER PROTOCOL SCOPE ============
| 1. SFTP (SSH File Transfer Protocol)        |
| 2. FTP  (File Transfer Protocol)            |
| 3. FTPS (File Transfer Protocol Secure)     |
| 4. AS2 (Applicability Statement 2)          |
| 0. Back to Main Menu                        |
-----------------------------------------------

""")
    choice = input("Enter your choice: ")
    mapping = {
        '1':['SFTP'],
        '2':['FTP'],
        '3':['FTPS'],
        '4':['AS2'],
        '0': 'back'
    }
    return mapping.get(choice, 'invalid choice')

# Functions Logics
def _create_user_logic(server_id, user_name, role_arn, directory_mapping,ssh_key,tag_customer):
    try:
        transfer_client.create_user(
            ServerId=server_id,
            UserName=user_name,
            RoleArn=role_arn,
            Policy=policy_document,
            HomeDirectoryMappings=[{
                'Entry':'/',
                'Target': directory_mapping
            }],
            Tags=[
                {
                    'Key': 'customer',
                    'Value': tag_customer
                }
            ]
        )

        transfer_client.import_ssh_public_key(
            ServerId=server_id,
            UserName=user_name,
            PublicKey=ssh_key
        )

        print("User {} created successfully on Server {}".format(user_name, server_id))
    except Exception as e:
        print("Error creating user: {}".format(e))


def _update_user_logic(server_id, user_name, role_arn, home_directory):
    try:
        transfer_client.update_user(
            ServerId=server_id,
            UserName=user_name,
            RoleArn=role_arn,
            Policy=policy_document,
            HomeDirectoryMappings=[{
                'Entry':'/',
                'Target': home_directory
            }]
        )
        print("User {} updated successfully on Server {}".format(user_name, server_id))
    except Exception as e:
        print("Error updating user: {}".format(e))


def _delete_user_logic(server_id, user_name):
    try:
        transfer_client.delete_user(
            ServerId=server_id,
            UserName=user_name
        )
        print("User {} deleted successfully from Server {}".format(user_name, server_id))
    except Exception as e:
        print("Error deleting user: {}".format(e))


def create_server():
    endpoint_type = scope_endpoint()
    if not endpoint_type:
        print("Invalid endpoint type selected")
        return
    
    protocol_type = scope_protocol()
    if not protocol_type:
        print("Invalid protocol type selected")
        return
    
    try:
        response = transfer_client.create_server(
            EndpointType=endpoint_type,
            Protocol=protocol_type
        )
        print("Server created successfully\nServer ID: {}".format(response['Server']['ServerId']))
    except Exception as e:
        print("Error creating server: {}".format(e))

""" def create_user():
    server_id = input("Enter server ID: ").strip()
    user_name = input("Enter user name: ").strip()
    role_arn = input("Enter role ARN: ").strip()
    policy_arn = input("Enter policy ARN: ").strip()
    directory_mapping = input("Enter home directory (e.g., /my-bucket/user): ").strip()
    ssh_key = input("Enter SSH key: ")

    if not server_id or not user_name or not role_arn or not policy_arn or not directory_mapping or not ssh_key:
        print("All fields are required.")
        return
    
    _create_user_logic(server_id, user_name, role_arn, policy_arn, directory_mapping, ssh_key) """


def create_multiple_users(server_id, user_name, role_arn, directory_mapping,ssh_key,tag_customer):
    print("Creating user '{}' on server '{}'...".format(user_name, server_id))
    _create_user_logic(server_id, user_name, role_arn, directory_mapping,ssh_key,tag_customer)


def update_multiple_users(server_id, user_name, role_arn, home_directory):
    print("Updating the user '{}' on server '{}'...".format(user_name, server_id))
    _update_user_logic(server_id, user_name, role_arn, home_directory)


def delete_multiple_users(server_id, user_name):
    print("Deleting the user '{}' from server '{}'...".format(user_name, server_id))
    _delete_user_logic(server_id, user_name)


def create_users():
    server_id = input("Enter server ID: ").strip()
    users_name = []
    directory_mappings=[]
    ssh_keys=[]
    tag_customers=[]

    while True:
        user_name = input("Enter a user name: ").lower()
        users_name.append(user_name)

        directory_mapping = input("Enter Home Directory (e.g., /my-bucket/user): ").strip()
        directory_mappings.append(directory_mapping)

        ssh_key = input("Enter SSH Key: ").strip()
        ssh_keys.append(ssh_key)

        tag_customer = input("Enter name Customer for TAG: ").strip()
        tag_customers.append(tag_customer)

        more = input("Do you want to add another user? (y/n): ")
        if more.lower() != 'y':
            break
    
    role_arn = input("Enter Role ARN: ").strip()

    for user, directory_mapping, ssh_key, tag_customer in zip(users_name, directory_mappings, ssh_keys, tag_customers):
        create_multiple_users(server_id, user, role_arn, directory_mapping, ssh_key, tag_customer)


def update_users():
    server_id = input("Enter Server ID: ").strip()
    users_name = []
    directory_mappings=[]
    while True:
        user_name = input("Enter a user name: ").lower()
        users_name.append(user_name)

        directory_mappings=input("Enter Home Directory (e.g., /my-bucket/user): ").strip()
        directory_mappings.append(directory_mappings)

        more = input("Do you want to add another user? (y/n): ")
        if more.lower() != 'y':
            break
    
    role_arn = input("Enter Role ARN: ").strip()

    for user, directory_mapping in zip(users_name, directory_mappings):
        update_multiple_users(server_id, user, role_arn, directory_mapping)


def delete_users():
    server_id = input("Enter Server ID: ").strip()
    users_name = []

    while True:
        users_name = input("Enter a user name: ").lower()
        users_name.append(users_name)

        more = input("Do you want to add another user? (y/n): ")
        if more.lower() != 'y':
            break
    
    for user in users_name:
        delete_multiple_users(server_id, user)


def delete_ssh_public_key():
    server_id = input("Enter Server ID: ").strip()
    user_name = input("Enter User Name: ").strip()
    ssh_key_name = input("Enter SSH Key Name: ")

    if not server_id or not user_name or not ssh_key_name:
        print("All fields are required.")
        return
    
    try:
        transfer_client.delete_ssh_public_key(
            ServerId=server_id,
            UserName=user_name,
            KeyName=ssh_key_name
        )
        print("SSH Key {} deleted successfully from User {} on Server {}".format(ssh_key_name, user_name, server_id))
    except Exception as e:
        print("Error deleting SSH Key: {}".format(e))


""" def update_user():
    server_id = input("Enter Server ID: ").strip()
    user_name = input("Enter User Name: ").strip()
    role_arn = input("Enter Role ARN: ").strip()
    policy_arn = input("Enter Policy ARN: ").strip()
    home_directory = input("Enter Home Directory (e.g., /my-bucket/user): ").strip()

    if not server_id or not user_name or not role_arn or not policy_arn or not home_directory:
        print("All fields are required.")
        return
    
    _update_user_logic(server_id, user_name, role_arn, policy_arn, home_directory)
"""


def update_ssh_public_key():
    server_id = input("Enter Server ID: ").strip()
    user_name = input("Enter User Name: ").strip()
    ssh_key = input("Enter New SSH Key: ").strip()

    if not server_id or not user_name or not ssh_key:
        print("All fields are required.")
        return
    
    try:
        transfer_client.import_ssh_public_key(
            ServerId=server_id,
            UserName=user_name,
            PublicKey=ssh_key
        )
        print("SSH Key updated successfully for User {} on Server {}".format(user_name, server_id))
    except Exception as e:
        print("Error updating SSH Key: {}".format(e))


def export_users():
    server_id = input("Enter Server ID: ").strip()

    if not server_id:
        print("Server ID is required.")
        return
    
    export_type = input("Choose export format (json/csv): ").strip().lower()

    if export_type not in ['json', 'csv']:
        print("Invalid export format. Please choose 'json' or 'csv'.")
        return
    
    try:
        users = transfer_client.list_users(ServerId=server_id)['Users']
        export_data  = []
        for user in users:
            username = user['UserName']
            
            user_desc = transfer_client.describe_user(
                ServerId=server_id,
                UserName=username
            )['User']
            ssh_keys = []
            ssh_list = transfer_client.list_ssh_public_keys(
                ServerId=server_id,
                UserName=username
            )['SshPublicKeys']
            for ssh_key in ssh_list:
                ssh_detail = transfer_client.describe_ssh_public_key(
                    ServerId=server_id,
                    UserName=username,
                    KeyName=ssh_key['KeyName']
                )['SshPublicKey']
                ssh_keys.append(ssh_detail['SshPublicKeyBody'])

            export_data.append({
                'username': username,
                'role_arn': user_desc['RoleArn'],
                'policy_arn': user_desc['PolicyArn'],
                'home_directory': user_desc['HomeDirectory'],
                'ssh_keys': ssh_keys
            })
        
        if export_type == 'json':
            with open('users.json', 'w', enconding='utf-8') as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)
            print("Users exported to users.json")
        elif export_type == 'csv':
            with open('users.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, 
                    fieldnames=[
                        'username',
                        'role_arn',
                        'policy_arn',
                        'home_directory',
                        'ssh_keys'
                    ]
                )
                writer.writeheader()
                for row in export_data:
                    writer.writerow({
                        'username': row['username'],
                        'role_arn': row['role_arn'],
                        'policy_arn': row['policy_arn'],
                        'home_directory': row['home_directory'],
                        'ssh_keys': ";".join(row['ssh_keys']) if row['ssh_keys'] else ""
                    })
            print("Users exported to users.csv")
    except Exception as e:
        print("Error exporting users: {}".format(e))


def handle_transfer_choice(choice):

    match choice:
        case '1':
            create_server()
        case '2':
            create_users()
        case '3':
            delete_users()
        case '4':
            delete_ssh_public_key()
        case '5':
            update_users()
        case '6':
            update_ssh_public_key()
        case '7':
            export_users()
        case '0':
            print("Exiting to main menu...")
            return 
        case _:
            print("Invalid choice. Please select a valid option (1-6).")

def main():
    while True:
        choice = show_menu_transfer()
        if choice == '0':
            break
        handle_transfer_choice(choice)

if __name__ == "__main__":
    main()