import json
import boto3


iam_client = boto3.client('iam')
def show_menu_roles():
    print('''\n
========== IAM Role Menu ============
|    1. Create Role                 |
|    2. Search Role                 |  
|    3. Attach Policy to Role       |
|    4. Exit                        |
-------------------------------------
    ''')

    choice = input("Enter your choice: ")
    return choice

def create_iam_role():
    print("Creating a new IAM role...")
    RoleName = input("Enter the role name: ")
    Description = input("Enter the role description: ")
    SPNName = input("Enter the service principal name (e.g., ec2.amazonaws.com): ")

    assume_role_policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": SPNName
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }

    try:
        response = iam_client.create_role(
            RoleName=RoleName,
            AssumeRolePolicyDocument=json.dumps(assume_role_policy_document),
            Description=Description
        )
        print(f"Role {RoleName} created successfully.")
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"Role with name '{RoleName}' already exists.")
    except Exception as e:
        print(f"Error creating role: {e}")

def filter_iam_roles(role_name_filter):
    searchRoles = []
    paginator = iam_client.get_paginator('list_roles')

    try:
        for page in paginator.paginate():
            for role in page['Roles']:
                role_name = role['RoleName']
                if role_name_filter.lower() in role_name.lower():
                    searchRoles.append({
                        'RoleName': role_name,
                        'RoleId': role['RoleId'],
                        'Arn': role['Arn'],
                        'CreateDate': role['CreateDate'],
                        'Path': role['Path'],
                        'AssumeRolePolicyDocument': role.get('AssumeRolePolicyDocument'),
                        'Description': role.get('Description', 'N/A'),
                        'Tags': role.get('Tags', [])
                    })
        return searchRoles
    except Exception as e:
        print(f"Error retrieving roles: {e}")
        return []

def list_iam_roles():
    print("Searching for IAM roles...")
    role_name_filter = input("Enter the role name filter (leave blank to list all roles): ")
    roles = filter_iam_roles(role_name_filter)

    if roles:
        print("Found {} role(s) matching the filter '{}':".format(
            len(roles),
            role_name_filter)
        )
        for role in roles:
            print("""
Role Name: {},
Role ID: {},
ARN: {},
Created On: {},
Path: {},
Description: {},
Tags: {}
""".format(
    role['RoleName'],
    role['RoleId'],
    role['Arn'],
    role['CreateDate'],
    role['Path'],
    role['Description'],
    role['Tags']
))

def attach_policy_to_role():
    print("Attaching policy to IAM role...")
    role_name = input("Enter the role name: ")
    policy_name = input("Enter the policy name to attach: ")
    policy_arn = "arn:aws:iam::aws:policy/{}".format(policy_name)

    try:
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn=policy_arn
        )
        print("Policy '{}' attached to role '{}' successfully.".format(
            policy_name,
            role_name)
        )
    except iam_client.exceptions.NoSuchEntityException:
        print("Role '{}' or Policy '{}' does not exist.".format(
            role_name,
            policy_name)
        )
    except iam_client.exceptions.LimitExceededException:
        print("Attachment limit exceeded for role '{}'.".format(role_name))
    except Exception as e:
        print("Error attaching policy: {}".format(e))


def handle_roles_choice(choice):
    match choice:
        case '1':
            create_iam_role()

        case '2':
            list_iam_roles()
        case '3':
            attach_policy_to_role()
        case '4':
            return
        case _:
            print("Invalid choice. Please select a valid option (1-4).")


def main():
    while True:
        choice = show_menu_roles()
        if choice == '4':
            break
        handle_roles_choice(choice)

if __name__ == "__main__":
    main()