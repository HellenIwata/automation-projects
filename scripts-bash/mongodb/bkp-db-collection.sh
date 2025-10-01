#! /bin/bash

###############################################################################################################
# Script to backup a MongoDB collection to a file                                                             #
# Usage: ./bkp-db-collection.sh [host] [db_name] [collection_name] [output_dir]                          #
# Author: Hellen Cristina N. Iwata                                                                            #
# Version: 1.0                                                                                                #
###############################################################################################################
source .env

# Set ANSI Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Set variables from arguments and environment variables
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
HOST="$1"
DB_NAME="$2"
COLLECTION_NAME="$3"
OUTPUT_DIR="$4"
OUTPUT_FILE="${TIMESTAMP}-${HOST}-${DB_NAME}-${COLLECTION_NAME}-backup"
MONGO_USER="$MONGO_USER"
MONGO_PASS="$MONGO_PASS"
MONGO_URI="mongodb+srv://$MONGO_USER:$MONGO_PASS@$HOST/?retryWrites=true&w=majority"
BUCKET_NAME="$BUCKET_NAME"
OBJECT_KEY="$OBJECT_KEY"
AWS_ACCOUNT_ID="$AWS_ACCOUNT_ID"
AWS_USER_NAME="$AWS_USER_NAME"

# Set config log
log_info() {
    echo -e "${NC}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1"
}
log_sucess() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S')${NC} - $1}"
}
log_warn() {
    echo -e "${YELLOW}[WARN] $(date '+%Y-%m-%d %H:%M:%S')${NC} - $1"
}
log_error() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S')${NC} - $1"
}

# Check if the correct number of arguments is provided
check_args() {
    if [ "$#" -ne 4 ]; then
        log_error "Usage: $0 [host] [db_name] [collection_name] [output_dir]"
        exit 1
    fi
}

# Check if the required tools are installed
check_tools() {
    if ! command -v mongodump &> /dev/null; then
        log_error "mongodump could not be found. Please install MongoDB Database Tools."
        exit 1
    elif ! command -v aws &> /dev/null; then
        log_error "aws cli could not be found. Please install and configure AWS CLI."
        exit 1
    elif ! command -v mongorestore &> /dev/null; then
        log_error "mongorestore could not be found. Please install MongoDB Database Tools."
        exit 1
    else
        log_info "Required tools are installed."
    fi
}

check_configurations_aws() {
    # Check if AWS CLI is configured
    log_info "Checking AWS CLI configuration..."

    current_account_id=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
    current_user_name=$(aws iam get-user --query User.UserName --output text 2>/dev/null)

    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS CLI is not configured. Please configure it using 'aws configure'."
        exit 1
    elif [ "$current_account_id" != "$AWS_ACCOUNT_ID" ]; then
        log_warn "AWS CLI is configured for account ID '$current_account_id', but expected '$AWS_ACCOUNT_ID'."
        log_warn "Please configure AWS CLI with the correct credentials."
        exit 1
    elif [ "$current_user_name" != "$AWS_USER_NAME" ]; then
        log_warn "AWS CLI is configured for user '$current_user_name', but expected '$AWS_USER_NAME'."
        log_warn "Please configure AWS CLI with the correct user."
        exit 1
    else
        log_sucess "AWS CLI is configured."
        log_info "Account ID: $current_account_id"
        log_info "User Name: $current_user_name"
    fi

    # Check if the S3 bucket exists
    log_info "Checking S3 bucket existence..."
    if ! aws s3 ls "s3://$BUCKET_NAME" &> /dev/null; then
        log_error "S3 bucket '$BUCKET_NAME' does not exist or you do not have access."
        exit 1
    else
        log_info "S3 bucket '$BUCKET_NAME' exists and is accessible."
    fi

    #Check if the S3 object key (folder) exists
    log_info "Checking S3 object key (folder) existence..."
    if ! aws s3 ls "s3://$BUCKET_NAME/$OBJECT_KEY/" &> /dev/null; then
        log_warn "S3 object key (folder) '$OBJECT_KEY' does not exist in bucket '$BUCKET_NAME'. It will be created upon first upload."
    else
        log_info "S3 object key (folder) '$OBJECT_KEY' exists in bucket '$BUCKET_NAME'."
    fi 

    # Check if the user has permissions to access the S3 bucket
    log_info "Checking S3 bucket access permissions..."
    if ! aws s3api get-bucket-acl --bucket "$BUCKET_NAME" &> /dev/null; then
        log_error "You do not have permission to access the S3 bucket '$BUCKET_NAME'."
        exit 1
    else
        log_sucess "You have permission to access the S3 bucket '$BUCKET_NAME'."
    fi
}

check_acess_mongo() {
    # Check if the MongoDB database is accessible
    log_info "Checking MongoDB database accessibility..."
    
    mongodump --uri="$MONGO_URI" --quiet --archive=/dev/null &> /dev/null
    
    local EXIT_CODE=$?
    
    if [ "$EXIT_CODE" -eq 0 ]; then
        log_sucess "MongoDB database '$DB_NAME' is accessible."
    else
        log_error "Failed to access MongoDB database '$DB_NAME'."
        echo "$EXIT_CODE"
        exit 1
    fi
}

check_permissions_mongo() {
    # Check if the user has permissions to access the MongoDB database
    log_info "Checking MongoDB database access permissions..."
    if ! mongodump --help &> /dev/null; then
        log_error "You do not have permission to access the MongoDB database."
        exit 1
    else
        log_sucess "You have permission to access the MongoDB database."
    fi
}

check_output_dir(){
    # Check if the output directory exists, if not create it
    log_info "Checking output directory..."
    if [ ! -d "$OUTPUT_DIR" ]; then
        log_warn "Output directory '$OUTPUT_DIR' does not exist. Creating it..."
        mkdir -p "$OUTPUT_DIR"
        if [ $? -ne 0 ]; then
            log_error "Failed to create output directory '$OUTPUT_DIR'. Please check permissions."
            exit 1
        else
            log_sucess "Output directory '$OUTPUT_DIR' created successfully."
        fi
    else
        log_info "Output directory '$OUTPUT_DIR' exists."
    fi
}

check_space_output_dir(){
    # Check if there is enough space in the output directory
    log_info "Checking available space in output directory..."
    available_space=$(df -k "$OUTPUT_DIR" | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 100000 ]; then
        log_error "Not enough space in output directory '$OUTPUT_DIR'. Available space: $available_space KB."
        exit 1
    else
        log_info "Sufficient space available in output directory '$OUTPUT_DIR'. Available space: $available_space KB."
    fi
}

run_mongo_backup(){
    # Perform the backup using mongodump
    log_info "Starting MongoDB collection backup..."

    mongodump --uri="$MONGO_URI" --db="$DB_NAME" --collection="$COLLECTION_NAME" --gzip --out="$OUTPUT_DIR/$OUTPUT_FILE" 2>&1

    local EXIT_CODE=$?

    if [ "$EXIT_CODE" -eq 0 ]; then
        log_sucess "MongoDB collection '$COLLECTION_NAME' from database '$DB_NAME' backed up successfully to '$OUTPUT_DIR/$OUTPUT_FILE'."
    else
        log_error "Failed to back up MongoDB collection '$COLLECTION_NAME' from database '$DB_NAME'."
        echo "$EXIT_CODE"
        exit 1
    fi
}

run_upload_s3(){
    # Upload the backup file to the S3 bucket
    log_info "Uploading backup to S3 bucket '$BUCKET_NAME'..."
    
    local SOURCE_DIR="$OUTPUT_DIR/$OUTPUT_FILE"
    aws s3 cp "$SOURCE_DIR" "s3://$BUCKET_NAME/$OBJECT_KEY/" --recursive 2>&1

    local EXIT_CODE=$?

    if [ "$EXIT_CODE" -eq 0 ]; then
        log_sucess "Backup uploaded successfully to 's3://$BUCKET_NAME/$OBJECT_KEY/'."
    else
        log_error "Failed to upload backup to 's3://$BUCKET_NAME/$OBJECT_KEY/'."
        echo "$EXIT_CODE"
        return 1
    fi
}

clear_variables(){
    # Clear sensitive variables
    log_info "Clearing sensitive variables..."
    unset MONGO_USER
    unset MONGO_PASS
    unset MONGO_URI
    unset AWS_ACCOUNT_ID
    unset AWS_USER_NAME
}

# Main script execution
check_args "$@"
check_tools
check_configurations_aws
check_acess_mongo
check_permissions_mongo
check_output_dir
check_space_output_dir
run_mongo_backup
run_upload_s3
clear_variables

log_sucess "MongoDB collection backup and upload to S3 completed successfully."
# To do:  
    # 5. Realizar a limpeza dos arquivos temporários (se necessário)
        # 5.1 Remover o arquivo de backup gerado pelo mongodump (se necessário)
