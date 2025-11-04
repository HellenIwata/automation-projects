import json
import boto3

def show_menu_policy_creation():
    print("=== IAM Policy Creation Menu ===")
    print("1. Create a new IAM policy for S3 access")
    print("2. Create multiple IAM policies for S3 access")
    print("3. Exit to main menu")
    choice = input("Please select an option (1-3): ")
    return choice

iam_client = boto3.client('iam')

def get_policy_scope():
    menu_scope_policy = """Define the scope of the policy:
1. Read-only
2. Read-Write
3. Full Access
Enter your choice (1-3): 
    """
    choice = input(menu_scope_policy)
    read_only= [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:GetObjectAcl"
    ]

    read_write= [
        "s3:ListBucket",
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:GetObjectAcl",
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:DeleteObject"
    ]

    full_access= [
        "s3:*"
    ]

    match choice:
        case '1':
            return read_only
        case '2':
            return read_write
        case '3':
            return full_access
        case _:
            print("Invalid choice. Defaulting to 'Read-only'.")
            return read_only
    
def _create_policy_logic(policy_name, description, policy_document):
    """Helper function to create an IAM policy."""
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": policy_document['Action'],
                "Resource": policy_document['Resource']
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

def create_iam_policy():
    print("Creating a new IAM policy...")
    customer_name = input("Enter the customer name (used in policy name): ")
    bucket_name = input("Enter the S3 bucket name (e.g., example-bucket): ") 
    object_path = input("Enter the S3 object path (e.g., customer-folder/*): ")
    
    actions = get_policy_scope()
    policy_name = f'aws-s3-access-{customer_name.lower()}'
    description = f'IAM policy for S3 access for customer {customer_name} in transfer family'
    
    resource_arn = f'arn:aws:s3:::{bucket_name}'
    resource_unique_arn = f"{resource_arn}/{object_path}"

    policy_document = {
        "Action": actions,
        "Resource": [resource_arn, resource_unique_arn]
    }
    _create_policy_logic(policy_name, description, policy_document)

def create_multiple_iam_policies(customer, bucket_name, base_object_path, actions):
    print(f"Creating IAM policy for {customer}...")
    policy_name = f'aws-s3-access-{customer.lower()}'
    description = f'IAM policy for S3 access for customer {customer} in transfer family'

    resource_arn = f'arn:aws:s3:::{bucket_name}'
    # Each customer gets their own subfolder
    resource_unique_arn = f"{resource_arn}/{base_object_path}/{customer}/*"

    policy_document = {
        "Action": actions,
        "Resource": [resource_arn, resource_unique_arn]
    }
    _create_policy_logic(policy_name, description, policy_document)

def create_iam_policies():
    print("Creating a list of IAM policies...")
    customers = []
    while True:
        customer_name = input("Enter a customer name: ")
        customers.append(customer_name)
        more = input("Do you want to add another customer? (y/n): ")
        if more.lower() != 'y':
            break
    
    bucket_name = input("\nEnter the S3 bucket name for all policies (e.g., example-bucket): ")
    base_object_path = input("Enter the base S3 object path (e.g., transfer-users): ")
    print("\nNow, define the scope for ALL policies to be created.")
    actions = get_policy_scope()

    for customer in customers:
        create_multiple_iam_policies(customer, bucket_name, base_object_path, actions)

def handle_policy_creation_choice(choice):
    match choice:
        case '1':
            create_iam_policy()
        case '2':
            create_iam_policies()
        case '3':
            print("Exiting to main menu...")
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