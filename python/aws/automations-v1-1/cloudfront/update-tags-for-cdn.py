import logging
import boto3
from botocore.exceptions import ClientError
from colorama import init, Fore, Back, Style

# Inicializando a personalização de tags para Redis
init(autoreset=True, color=True, style=True)

# Definindo as configuracoes basicas de logging
logging.basicConfig(level=logging.INFO)

# Inicializando o cliente Redis
cdn_client = boto3.client('elasticache')

key = ''
value_key = ''
new_tags = {'Key': key, 'Value': value_key}

def list_updates_tags(resource_arn, tags):
    """Lista todas as tags de um recurso Redis."""
    print(Fore.CYAN + "Listando tags para o recurso: " + resource_arn)
    
    for tag in tags:
        print(Fore.GREEN + f"Tag Key: {tag['Key']}, Tag Value: {tag['Value']}")
    
def list_tags(resource_arn):

    """Lista todas as tags de um recurso Redis."""
    try:
        response = cdn_client.list_tags_for_resource(
            ResourceName=resource_arn
        )
        tags = response.get('Tags', [])
        if tags:
            logging.info(Fore.CYAN + "Tags existentes encontradas para {}: {}".format(resource_arn, tags))
        else:
            logging.info(Fore.YELLOW + "Nenhuma tag existente encontrada para {}".format(resource_arn))
    except ClientError as e:
        logging.error(Fore.RED + "Erro ao listar tags para {}: {}".format(resource_arn, e))
        return False

def update_tags(resource_arn, new_tags):
    """Atualiza as tags de um recurso Redis."""
    try:
        current_tags= list_tags(resource_arn)
        if current_tags is False:
            return False
        cdn_client.add_tags_to_resource(
            ResourceName=resource_arn,
            Tags=[new_tags]
        )
        logging.info(Fore.GREEN + "Tags atualizadas com sucesso para {}: {}".format(resource_arn, new_tags))

        logging.info(Fore.CYAN + "Verificando tags atualizadas para {}".format(resource_arn))
        response_updated = cdn_client.list_tags_for_resource(
            ResourceName=resource_arn
        )
        updated_tags = response_updated.get('Tags', {}).get('Items',[])
        list_updates_tags(resource_arn, updated_tags)
        return True

    except ClientError as e:
        logging.error(Fore.RED + "Erro ao atualizar tags para {}: {}".format(resource_arn, e))
        return False