from scripts.iam.policy.create_policies_s3 import main as main_policy
from scripts.iam.role.create_role import main as main_role
from scripts.bucket_s3.management_bucket import main as main_bucket
from scripts.transfer_family.manager_server import main as main_transfer_family

def show_menu():
    menu = """
=======================================
        AWS Management Menu
=======================================
    1. Management of S3 Buckets
    2. Management of IAM Policies
    3. Management of IAM Role
    4. Management of AWS Transfer Family
    5. Management of AWS General Resources
    0. Exit
--------------------------------------------
    """
    print(menu)
    choice = input("Enter your choice: ")
    return choice

def handler_management_choice(choice):
    match choice:
        case '1':
            main_bucket()
        case '2':
            main_policy()
        case '3':
            main_role()
        case '4':
            main_transfer_family()
        case '5':
            pass
        case '0':
            return
        case _:
            print("Invalid choice. Please select a valid option (0-5).")


def main():    
    while True:
        choice = show_menu()
        if choice == '0':
            break
        handler_management_choice(choice)

if __name__ == "__main__":
    main()


#