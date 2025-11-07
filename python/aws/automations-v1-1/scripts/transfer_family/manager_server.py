import csv
import json
import boto3

# FUNCTIONS VIEWS MENUS
def show_menu_transfer():
    print("""
===== Transfer Family Management Menu =====
| 1. Manager Users                          |
| 2. Manager SSH Keys                       |
| 3. Exports Users Server                   |
| 0. Back to Main Menu                      |
---------------------------------------------
""")
    choice = input("Enter your choice: ")
    return choice

def show_submenu_users():
    print("""
======= Users Management Menu =======
| 1. Create User                    |
| 2. Update User                    |
| 3. Delete User                    |
| 0. Back main Menu                 |
-------------------------------------

""")
    choice = input("Enter your choice: ")
    return choice

def show_submenu_keys():
    print("""
======= Users Management Menu =======
| 1. Update SSH public Key          |
| 2. Delete SSH public Key          |
| 0. Back main Menu                 |
-------------------------------------

""")
    choice = input("Enter your choice: ")
    return choice

def show_scope_update_user():
    print("""
=========== UPDATE SCOPE ===========
| 1. Home Directory Mappings        |
| 2. Role                           |
| 3. SSH Public Key                 |
| 0. Back to Main Menu              |
-------------------------------------
""")
    choice = input("Enter your choice: ")
    return choice

transfer_client = boto3.client('transfer')

# FUNCTIONS LOGICS
## users logics
def _create_user_logic(
    server_id, 
    user,
    role_arn,
    directory_mapping,
    ssh_key,
    tag_user_customer):
    try:
        response = transfer_client.create_user(
            ServerId=server_id,
            UserName=user,
            Role=role_arn,
            HomeDirectory="/",
            HomeDirectoryType='LOGICAL',
            HomeDirectoryMappings=[
                {
                    'Entry': '/',
                    'Target': directory_mapping
                }

            ],
            SshPublicKeyBody=ssh_key,
            Tags=[
                {
                    'Key': 'customer',
                    'Value': tag_user_customer
                }
            ]
        )
        print("\nUser ´{}´ created successfully on Server {}".format(
            response['UserName'], 
            server_id
        ))
    except Exception as e:
        print("Error creating user: \n\t{}".format(e))

def _update_user_logic(
    server_id, 
    user,
    role_arn,
    directory_mapping):
    try:
        response = transfer_client.update_user(
            ServerId=server_id,
            UserName=user,
            Role=role_arn,
            HomeDirectory="/",
            HomeDirectoryType='LOGICAL',
            HomeDirectoryMappings=[{
                'Entry':'/',
                'Target': directory_mapping
            }]
        )
        print("User ´{}´ updated successfully on Server {}".format(
            response['UserName'], 
            server_id
        ))
    except Exception as e:
        print("Error updating user:\n\t{}".format(e))

def _delete_user_logic(
    server_id, 
    user):
    try:
        response = transfer_client.delete_user(
            ServerId=server_id,
            UserName=user
        )
        print("User ´{}´ deleted successfully from Server {}".format(
            response['UserName'], 
            server_id
        ))
    except Exception as e:
        print("Error deleting user:\n\t{}".format(e))

def _update_user_logic_directory_mapping(
    server_id, 
    user,
    directory_mapping):
    try:
        response = transfer_client.update_user(
            ServerId=server_id,
            UserName=user,
            HomeDirectoryMappings=[{
                'Entry':'/',
                'Target': directory_mapping
            }]
        )
        print("Home directory Mappings ´{}´ updated successfully on User ´{}´".format(
            response['HomeDirectoryMappings'], 
            response['UserName']
        ))
    except Exception as e:
        print("Error updating Home directory Mappings:\n\t{}".format(e))

def _update_user_logic_role(
    server_id, 
    user,
    role_arn):
    try:
        response = transfer_client.update_user(
            ServerId=server_id,
            UserName=user,
            Role=role_arn
        )
        print("Role ´{}´ updated successfully on User ´{}´".format(
            response['Role'], 
            response['UserName']
        ))
    except Exception as e:
        print("Error updating Role:\n\t{}".format(e))

def _update_user_logic_ssh_key(
    server_id, 
    user,
    ssh_key):
    try:
        response = transfer_client.update_user(
            ServerId=server_id,
            UserName=user,
            SshPublicKeyBody=ssh_key
        )
        print("SSH Key ´{}´ updated successfully on User ´{}´".format(
            response['SshPublicKeyBody'], 
            response['UserName']
        ))
    except Exception as e:
        print("Error updating SSH Key:\n\t{}".format(e))

## keys logics
def _update_ssh_public_key_logic(
    server_id, 
    user,
    ssh_key):
    try:
        response = transfer_client.import_ssh_public_key(
            ServerId=server_id,
            UserName=user,
            PublicKey=ssh_key
        )
        print("SSH Key ´{}´ imported successfully for User ´{}´ on Server {}".format(
            response['KeyName'],
            response['UserName'],
            server_id
        ))
    except Exception as e:
        print("Error importing SSH Key:\n\t{}".format(e))

def _delete_ssh_public_key_logic(
    server_id, 
    user,
    ssh_key):
    try:
        response = transfer_client.delete_ssh_public_key(
            ServerId=server_id,
            UserName=user,
            KeyName=ssh_key
        )
        print("SSH Key ´{}´ deleted from user ´{}´ on server Successfully".format(
            response['KeyName'],
            response['UserName'],
            server_id
        ))
    except Exception as e:
        print("Error deleting SSH Key:\n\t{}".format(e))


# FUNCTIONS GETS
# validates whether the user has “motor” in their name to apply the correct role
def get_transfer_role(user_name):
    try:
        if user_name.endswith('motor'):
            return 'arn:aws:iam::739275464426:role/Transfer-ReadWriteDelete-Role'
        else:
            return 'arn:aws:iam::739275464426:role/Transfer-ReadOnly-Role'
    except Exception as e:
        print("Error getting role: {}".format(e))

def get_transfer_user(user_name):
    try:
        transfer_client.describe_user(
            UserName=user_name
        )
        user_found = True
        return user_found
    except Exception as e:
        user_found = False
        return user_found


# FUNCTIONS MUTIPLES EXECUTING
def create_multiple_users(
    server_id, 
    user,
    role_arn,
    directory_mapping,
    ssh_key,
    tag_user_customer):
    print("Creating user '{}' on server '{}'...".format(user, server_id))
    _create_user_logic(
        server_id, 
        user,
        role_arn,
        directory_mapping,
        ssh_key,
        tag_user_customer)

def update_multiple_users(
    server_id, 
    user,
    role_arn,
    directory_mapping):
    print("Updating the user '{}' on server '{}'...".format(user, server_id))
    _update_user_logic(
        server_id, 
        user,
        role_arn,
        directory_mapping)

def update_multiple_users_directory_mapping(
    server_id, 
    user,
    directory_mapping):
    print("Updating the directory mapping '{}' on user '{}'...".format(directory_mapping, user))

    _update_user_logic_directory_mapping(
        server_id, 
        user,
        directory_mapping)

def update_multiple_users_role(
    server_id, 
    user,
    role_arn):
    print("Updating the role '{}' on user '{}'...".format(role_arn, user))

    _update_user_logic_role(
        server_id, 
        user,
        role_arn)

def update_multiple_users_ssh_key(
    server_id, 
    user,
    ssh_key):
    print("Updating the ssh key '{}' on user '{}'...".format(ssh_key, user))

    _update_user_logic_ssh_key(
        server_id, 
        user,
        ssh_key)

def delete_multiple_users(
    server_id, 
    user):
    print("Deleting the user '{}' from server '{}'...".format(user, server_id))
    _delete_user_logic(
        server_id, 
        user)

def update_ssh_keys(
    server_id, 
    user,
    ssh_key):
    print("Updating user '{}' on server '{}'...".format(user, server_id))
    _update_ssh_public_key_logic(
        server_id, 
        user,
        ssh_key)

def delete_ssh_keys(
    server_id, 
    user,
    ssh_key):
    print("Deleting user '{}' on server '{}'...".format(user, server_id))
    _delete_ssh_public_key_logic(
        server_id, 
        user,
        ssh_key)


# FUNCTIONS EXECUTING

def create_users():
    server_id = input("Enter Server ID: ").strip()
    users = []

    while True:
        user_name = input("Enter a user name: ").lower().strip()
        
        home_dir = input("Enter Home Directory (e.g., /my-bucket/user): ").strip()
        if not home_dir.startswith('/'):
            home_dir = '/' + home_dir
            print("Home directory corrected to: '{}'".format(home_dir))
        
        ssh_key = input("Enter SSH Key: ").strip()
        if not ssh_key.startswith('ssh-rsa ') and not ssh_key.startswith('ecdsa-'):
            print("Invalid SSH key format. Skipping this user.")
            continue
        
        key_parts = ssh_key.split()
        cleaned_ssh_key = ' '.join(key_parts[:2])

        tag_customer = input("Enter name Customer User for TAG: ").strip()
        role_arn = get_transfer_role(user_name)

        users.append({
            'user_name': user_name,
            'home_dir': home_dir,
            'ssh_key': cleaned_ssh_key,
            'tag_customer': tag_customer,
            'role_arn': role_arn
        })

        more = input("Do you want to add another user? (y/n): ")
        if more.lower() != 'y':
            break
    
    for user in users:
        create_multiple_users(
            server_id,
            user['user_name'],
            user['role_arn'],
            user['home_dir'],
            user['ssh_key'],
            user['tag_customer']
        )

def update_user_home_directory():
    
    server_id = input("Enter Server ID: ").strip()
    users = []

    while True:
        user = input("Enter a user name: ").lower().strip()
        
        directory_mapping = input("Enter Home Directory (e.g., /my-bucket/user): ").strip()
        if not directory_mapping.startswith('/'):
            directory_mapping = '/' + directory_mapping
            print("Home directory corrected to: '{}'".format(directory_mapping))
        
        users.append({
            'user': user,
            'directory_mapping': directory_mapping
        })

        more = input("Do you want to add another user? (y/n): ")
        if more.lower() != 'y':
            break
    
    for user in users:
        update_multiple_users_directory_mapping(
            server_id,
            user['user'],
            user['directory_mapping']
        )

def update_user_role():
        server_id = input("Enter Server ID: ").strip()
        users = []

        while True:
            user = input("Enter a user name: ").lower().strip()
            role_arn = get_transfer_role(user)

            users.append({
                'user': user,
                'role_arn': role_arn
            })

            more = input("Do you want to add another user? (y/n): ")
            if more.lower() != 'y':
                break

        for user in users:
            update_multiple_users_role(
                server_id,
                user['user'],
                user['role_arn']
            )

def update_user_ssh_key():
    server_id = input("Enter Server ID: ").strip()
    users=[]

    while True:
        user = input("Enter a user name: ").lower().strip()
        ssh_key = input("Enter SSH Key: ").strip()
        
        users.append({
            'user': user,
            'ssh_key': ssh_key
        })
        more = input("Do you want to add another user? (y/n): ")
        if more.lower() != 'y':
            break
    
    for user in users:
        update_multiple_users_ssh_key(
            server_id,
            user['user'],
            user['ssh_key']
        )

def update_users():
    choice = show_scope_update_user()
    match choice:
        case '1':
            update_user_home_directory()
        case '2':
            update_user_role()
        case '3':
            update_user_ssh_key()
        case '0':
            print("Exiting to main menu...")
        case _:
            print("Invalid choice. Please select a valid option (1-3).")

def delete_users():
    server_id = input("Enter Server ID: ").strip()
    users = []

    while True:
        user_name = input("Enter a user name to delete: ").lower().strip()
        users.append(user_name)

        more = input("Do you want to add another user to delete? (y/n): ")
        if more.lower() != 'y':
            break
    
    for user in users:
        delete_multiple_users(server_id, user)

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

            home_directory_mappings = user_desc.get('HomeDirectoryMappings', [])
            home_directory = ""
            if home_directory_mappings:
                home_directory = home_directory_mappings[0].get('Target', '')

            ssh_keys = []
            if user_desc.get('SshPublicKeys'):
                for key in user_desc['SshPublicKeys']:
                    ssh_keys.append(key.get('SshPublicKeyBody', ''))

            export_data.append({
                'username': username,
                'role_arn': user_desc.get('Role', ''),
                'home_directory': home_directory,
                'ssh_keys': ssh_keys
            })
        
        if export_type == 'json':
            with open('users.json', 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=4, ensure_ascii=False)
            print("Users exported to users.json")
        elif export_type == 'csv':
            with open('users.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, 
                    fieldnames=[
                        'username',
                        'role_arn',
                        'home_directory',
                        'ssh_keys'
                    ]
                )
                writer.writeheader()
                for row in export_data:
                    writer.writerow({
                        'username': row['username'],
                        'role_arn': row['role_arn'],
                        'home_directory': row['home_directory'],
                        'ssh_keys': ";".join(row['ssh_keys']) if row['ssh_keys'] else ""
                    })
            print("Users exported to users.csv")
    except Exception as e:
        print("Error exporting users: {}".format(e))


# FUNCTIONS HANDLE CHOICES
def handle_transfer_choice(choice):

    match choice:
        case '1':
            user_choice = show_submenu_users()
            handle_users_choice(user_choice)
        case '2':
            key_choice = show_submenu_keys()
            handle_keys_choice(key_choice)
        case '3':
            export_users()
        case '0':
            print("Exiting to main menu...")
            return 
        case _:
            print("Invalid choice. Please select a valid option (1-3).")

def handle_users_choice(choice):

    match choice:
        case '1':
            create_users()
        case '2':
            update_users()
        case '3':
            delete_users()
        case '0':
            print("Exiting to main menu...")
            return
        case _:
            print("Invalid choice. Please select a valid option (1-3).")

def handle_keys_choice(choice):
    
    match choice:
        case '1':
            update_ssh_keys()
        case '2':
            delete_ssh_keys()
        case '0':
            print("Exiting to main menu...")
            return
        case _:
            print("Invalid choice. Please select a valid option (1-2).")


def main():
    while True:
        choice = show_menu_transfer()
        if choice == '0':
            break
        handle_transfer_choice(choice)

if __name__ == "__main__":
    main()