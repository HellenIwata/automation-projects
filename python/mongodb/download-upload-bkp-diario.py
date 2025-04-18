import os
import requests
import boto3
from requests.auth import HTTPDigestAuth
from datetime import datetime, timezone

# Configurações do MongoDB Atlas
os.environ['atlas_public_key'] = 'CHAVE_PUBLICA_MONGO'
os.environ['atlas_private_key'] = 'CAHVE_PRIVADA_MONGO'
os.environ['group_id'] = 'ID_DO_PROJETO'
os.environ['cluster_name'] = 'NOME_CLUSTER'

atlas_public_key = os.environ.get('atlas_public_key')
atlas_private_key = os.environ.get('atlas_private_key')
group_id = os.environ.get('group_id')
cluster_name = os.environ.get('cluster_name')

# Configurações do S3
s3_client = boto3.client('s3')
bucket_name = 'NOME_BUCKET_S3'


# Função para obter o snapshot
def get_daily_snapshot():
    try:
        # Endpoint da API para listar os backups
        url = f'https://cloud.mongodb.com/api/atlas/v1.0/groups/{group_id}/clusters/{cluster_name}/backup/snapshots'

        # Requisição GET para listar backups
        response = requests.get(url, auth=HTTPDigestAuth(atlas_public_key, atlas_private_key))
        print(f'url: {url}')
        print(f'Status code: {response.status_code}')
        #print(f'Response: {response.text}')

        response.raise_for_status()

        backups = response.json().get('results', [])
        if backups:
            return filter_snapshot(backups)
        else:
            print('Nenhum Backup encontrado')
        
    except requests.exceptions.RequestException as e:
        print(f'Erro: {e}')
    return None
    """ if response.status_code == 200:
        backups = response.json().get('results', [])
        # Filtra os backups para encontrar o snapshot diário
        for backup in backups:
            if 'monthly' in backup.get('frequencyType', ''):  # Supondo que o snapshot diário tenha 'daily' na descrição
                snapshot_id = backup['_id']
                download_link = backup['links'][0].get('href') # O link de download do snapshot
                print(f"Backup diário encontrado: {download_link}")
                return download_link
        print("Nenhum backup diário encontrado.")
    else:
        print("Erro ao listar backups:", response.status_code)
    return None """

# Função para filtrar o tipo de snapshot 
def filter_snapshot(backups):
    for backup in backups:
        #Verifica se existe o backup com o tipo de frequencia
        """ if 'frequencyType' in backup and 'monthly' in backup['frequencyType']:
            download_link = backup['links'][0]['href']
            print(f'Backup encontrado: {download_link}')
            return download_link """
        
        created_date_str = backup.get('createdAt')
        if created_date_str:
            created_date = datetime.fromisoformat(created_date_str.replace('Z',"+00:00"))
            print(f'Snapshot encontrado\nData de criação: {created_date}')

        current_date = datetime.now(timezone.utc).date()
        if created_date.date() == current_date:
            print('Este é o snapshot diário mais recente')
            download_link = backup['links'][0]['href']
            return download_link
        else:
            print('Snapshot encontrado, mas sem data de criação')

    print("Nenhum Backup encontrado")
    return None
        
# Função para baixar o snapshot específico e fazer o upload para o S3
def download_and_upload_snapshot(download_link, destino_diretorio):
    if not os.path.exists(destino_diretorio):
        os.makedirs(destino_diretorio)
        print(f'Diretório {destino_diretorio} criado.')

    arquivo_destino = os.path.join(destino_diretorio, 'snp-cls-familhao-dev-v1-2-3.tar.gz')

    # Baixa o snapshot
    print("iniciando o download")
    response = requests.get(download_link, auth=HTTPDigestAuth(atlas_public_key, atlas_private_key), stream=True)

    if response.status_code == 200:
        
        with open(arquivo_destino, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Backup baixado com sucesso para {arquivo_destino}!")

        # Agora faz o upload para o S3
        upload_to_s3(arquivo_destino)
    else:
        print("Erro ao baixar o snapshot:", response.status_code)

# Função para fazer o upload do arquivo para o S3
def upload_to_s3(arquivo_local):
    try:
        s3_client.upload_file(arquivo_local, bucket_name, os.path.basename(arquivo_local))
        print(f"Arquivo {arquivo_local} enviado para o S3 com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar o arquivo para o S3: {e}")

# Função principal para buscar o snapshot e fazer o upload para o S3
def main():
    # Define o diretório de destino para salvar o backup antes de enviar para o S3
    destino_diretorio = "C:\\Users\\admin-user\\Documents\\api-bkp-teste\\projetos-main\\bkp" 
    
    
    # Obtem o link do backup diário
    download_link = get_daily_snapshot()
    
    if download_link:
        # Baixa o snapshot e envia para o S3
        download_and_upload_snapshot(download_link, destino_diretorio)

if __name__ == "__main__":
    main()
