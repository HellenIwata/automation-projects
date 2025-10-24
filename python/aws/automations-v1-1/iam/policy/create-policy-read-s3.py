import json
import boto3

def show_menu_policy_creation():
    print("=== IAM Policy Creation Menu ===")
    print("1. Create a new IAM policy")
    print("2. Create a list IAM policies")
    print("3. Exit to main menu")
    choice = input("Please select an option (1-3): ")
    return choice

iam_client = boto3.client('iam')

def create_iam_policy():
    print("Creating a new IAM policy...")
    # Placeholder for actual IAM policy creation logic
    customer_name = input("Enter the name of the new IAM policy: ")
    resource_arn = input("Enter the S3 bucket ARN (e.g., arn:aws:s3:::example-bucket): ") 
    object_arn = input("Enter the S3 object ARN (e.g., object/*): ")


    policy_name = 'aws-s3-read-{}'.format(customer_name.lower())
    resource_unique_arn = f"{resource_arn}/{object_arn}"

    actions = [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:GetObjectAcl"
    ]

    resources = [
        resource_arn,
        resource_unique_arn
    ]

    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": actions,
                "Resource": resources
            }
        ]
    }

    try:
        response = iam_client.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document),
            Description='IAM policy for S3 read access for customer {}  in transfer family'.format(customer_name)
        )
        print("Policy created successfully:'{}'".format(policy_name))
    except iam_client.exceptions.EntityAlreadyExistsException:
        print("Policy with name '{}' already exists.".format(policy_name))

def create_iam_policy_list(customer):
    print("Creating a new IAM policy...")
    # Placeholder for actual IAM policy creation logic
    customer_name = customer
    resource_arn = input("Enter the S3 bucket ARN (e.g., arn:aws:s3:::example-bucket): ") 
    object_arn = input("Enter the S3 object ARN (e.g., object/*): ")


    policy_name = 'aws-s3-read-{}'.format(customer_name.lower())
    resource_unique_arn = f"{resource_arn}/{object_arn}/{customer_name}"

    actions = [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:GetObjectAcl"
    ]

    resources = [
        resource_arn,
        resource_unique_arn
    ]

    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": actions,
                "Resource": resources
            }
        ]
    }

    try:
        response = iam_client.create_policy(
            PolicyName=policy_name,
            PolicyDocument=json.dumps(policy_document),
            Description='IAM policy for S3 read access for customer {}  in transfer family'.format(customer_name)
        )
        print("Policy created successfully:'{}'".format(policy_name))
    except iam_client.exceptions.EntityAlreadyExistsException:
        print("Policy with name '{}' already exists.".format(policy_name))
    except Exception as e:
        print("Error creating policy: {}".format(e))

def create_list_iam_policies():
    print("Creating a list of IAM policies...")
    customer = []
    while True:
        customer_name = input("Enter the base name for the IAM policies: ")
        customer.append(customer_name)
        more = input("Do you want to add another customer? (y/n): ")
        if more.lower() != 'y':
            break
        else:
            continue
    for customer in customer:
        create_iam_policy_list(customer)

def handle_policy_creation_choice(choice):
    match choice:
        case '1':
            create_iam_policy()
            
        
        case '2':
            create_list_iam_policies()
        case '3':
            return
        case _:
            print("Invalid choice. Please select a valid option (1-3).")

def main():
    while True:
        choice = show_menu_policy_creation()
        if choice == '3':
            break
        handle_policy_creation_choice(choice)

if __name__ == "__main__":
    main()