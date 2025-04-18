import requests
import boto3
import time
from requests.auth import HTTPDigestAuth
import logging
import os

# Configurações do MongoDB Atlas
os.environ['atlas_public_key'] = 'CHAVE_PUBLICA_MONGO'
os.environ['atlas_private_key'] = 'CHAVE_PRIVADA_MONGO'
os.environ['group_id'] = 'ID_DO_PROJETO'
os.environ['cluster_name'] = 'NOME_CLUSTER'

atlas_public_key = os.environ.get('atlas_public_key')
atlas_private_key = os.environ.get('atlas_private_key')
group_id = os.environ.get('group_id')
cluster_name = os.environ.get('cluster_name')

# Configurações do S3
os.environ['s3_bucket_name']='NOME_BUCKET_S3'
os.environ['s3_folder_path']='NOME_DIRETORIO_S3'

s3_bucket_name = os.environ.get('s3_bucket_name')
s3_folder_path = os.environ.get('s3_folder_path')

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_envs():
    print(f"Atlas_API: {os.getenv('atlas_private_key')}")
    print(f"group_id: {os.getenv('group_id')}")
    print(f"cluster: {os.getenv('cluster_name')}")

def get_backup_link():
    try:
        url = f'https://cloud.mongodb.com/api/atlas/v1.0/groups/{group_id}/clusters/{cluster_name}/backup/snapshots'
        response = requests.get(url, auth=HTTPDigestAuth(atlas_public_key, atlas_private_key))
        response.raise_for_status()
        snapshots = response.json()['results']
        if snapshots:
            snapshot = snapshots[0]
            snapshot_id = snapshot['id']
            download_link = snapshot['links'][0]['href']
            return download_link
        else:
            logging.info("Nenhum snapshot encontrado.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao acessar a API do MongoDB Atlas: {e}")
        return None

def download_snapshot(download_link):
    try:
        response = requests.get(download_link, auth=HTTPDigestAuth(atlas_public_key, atlas_private_key), stream=True)
        response.raise_for_status()
        with open('nome_bkp.tar.gz', 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        logging.info("Backup baixado com sucesso!")
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao baixar o snapshot: {e}")

def upload_to_s3(file_name):
    try:
        s3_client = boto3.client('s3')
        s3_path = f'{s3_folder_path}/{file_name}'
        s3_client.upload_file(file_name, s3_bucket_name, s3_path)
        logging.info(f'Backup enviado para o S3: s3://{s3_bucket_name}/{s3_path}')
    except Exception as e:
        logging.error(f"Erro ao enviar o arquivo para o S3: {e}")

if __name__ == "__main__":
    get_envs()
    download_link = get_backup_link()
    if download_link:
        download_snapshot(download_link)
        time.sleep(30)
        #upload_to_s3('nome_bkp.tar.gz')
