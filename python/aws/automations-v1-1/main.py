from iam.policy.create_policies import main as main_policy
from iam.role.create_role import main as main_role

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
    6. Exit
--------------------------------------------
    """
    print(menu)
    choice = input("Enter your choice: ")
    return choice

def handler_management_choice(choice):
    match choice:
        case '1':
            pass
        case '2':
            main_policy()
        case '3':
            main_role()
        case '4':
            pass
        case '5':
            pass
        case '6':
            return
        case _:
            print("Invalid choice. Please select a valid option (1-6).")


def main():    
    while True:
        choice = show_menu()
        if choice == '6':
            break
        handler_management_choice(choice)

if __name__ == "__main__":
    main()


#