import logging
import boto3
from botocore.exceptions import ClientError

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)

# Clientes boto3
secret_client = boto3.client('secretsmanager')
s3_client = boto3.client('s3')
ec2_client = boto3.client('ec2')

# Lista de recursos
resources = [
    {"arn": "arn/friendlyName", "type": "secret"},
    {"arn": "name-bucket", "type": "s3"},
    {"arn": "resource-id", "type": "ec2"},
    {"arn": "vpc-id", "type": "vpc"},
]

# Nova tag a ser adicionada
new_tag = {"Key": "chave", "Value": "valor"}


def exibir_tags(resource_arn, tags):
    print("----------------------------------------------")
    print(f"| Tags atuais para o {resource_arn}: {tags} |")
    print("----------------------------------------------")


def adicionar_tag_secret(resource_arn, tag):
    try:
        response = secret_client.describe_secret(SecretId=resource_arn)
        tags = response.get('Tags', [])
        logging.info(f"Tags atuais para o {resource_arn}: {tags}")
        exibir_tags(resource_arn, tags)

        tags.append(tag)
        secret_client.tag_resource(SecretId=resource_arn, Tags=tags)
        print(f"Nova tag {tag} adicionada ao recurso {resource_arn}")
        
        return True
    except ClientError as e:
        logging.error(f"Erro ao adicionar tag ao segredo {resource_arn}: {e}")
        return False


def adicionar_tag_s3(resource_arn, tag):
    try:
        response = s3_client.get_bucket_tagging(Bucket=resource_arn)
        tags = response.get('TagSet', [])
        logging.info(f"Tags atuais para o {resource_arn}: {tags}")
        exibir_tags(resource_arn, tags)

        tags.append(tag)
        s3_client.put_bucket_tagging(Bucket=resource_arn, Tagging={'TagSet': tags})
        print(f"Nova tag {tag} adicionada ao recurso {resource_arn}")
        
        return True
    except ClientError as e:
        logging.error(f"Erro ao adicionar tag ao bucket {resource_arn}: {e}")
        return False

def adicionar_tag_ec2(resource_arn, tag):
    try:
        response = ec2_client.describe_tags(
            Filters = [
                {"Name": "resource-id", "Values": [resource_arn]}
            ]
        )
        tags = response.get('TagSet', [])
        logging.info(f"Tags atuais para o {resource_arn}: {tags}")
        exibir_tags(resource_arn, tags)

        tags.append(tag)
        ec2_client.create_tags(
            Resources=[resource_arn],
            Tags=[tag]
        )
        print(f"Nova tag {tag} adicionada ao recurso {resource_arn}")
        
        return True
    except ClientError as e:
        logging.error(f"Erro ao adicionar tag ao ec2 {resource_arn}: {e}")
        return False
    
    
def adicionar_tag_vpc(resource_arn, tag):
    try:
        ec2_client.create_tags(
            Resources=[resource_arn],
            Tags=[tag]
        )
        print(f"Nova tag {tag} adicionada à VPC {resource_arn}")
        return True
    except ClientError as e:
        logging.error(f"Erro ao adicionar tag à VPC {resource_arn}: {e}")
        return False

def adiciona_tags(resource_arn, resource_type, tag):
    handlers = {
        "secret": adicionar_tag_secret,
        "s3": adicionar_tag_s3,
        "ec2": adicionar_tag_ec2,
        "vpc": adicionar_tag_vpc
    }

    handler = handlers.get(resource_type)
    if handler:
        return handler(resource_arn, tag)
    else:
        logging.error(f"Tipo de recurso não suportado: {resource_type}")
        return False


# Processa os recursos
for resource in resources:
    adiciona_tags(resource["arn"], resource["type"], new_tag)
