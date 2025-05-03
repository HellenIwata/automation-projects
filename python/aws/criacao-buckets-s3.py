import logging
import boto3 
from botocore.exceptions import ClientError

#Inicializar o recurso S3
s3 = boto3.resource('s3')
s3_client = boto3.client('s3')
#Lista de buckets
buckets=["bucket-cliente-1","bucket-cliente-2","bucket-cliente-3","bucket-cliente-4","bucket-cliente-5"]
customers=["cliente1", "cliente2", "cliente3", "cliente4", "cliente5"]

#Função para criar o bucket
def criar_bucket_s3(bucket):
    nome_bucket = f"{bucket.lower()}-dev-test"
        
    #Criar bucket
    try:
        resposta = s3.create_bucket(
            Bucket = nome_bucket
        )
        
        print (f"Bucket '{nome_bucket}' criado com sucesso")
    except ClientError as e:
        logging.error(e)
        return False
    return True
    
def incluir_tags(bucket, customer):
    nome_bucket = f"{bucket.lower()}-dev-test"
    tags = {
        'TagSet':[
            {'Key':'Environment','Value':'prd'},
            {'Key':'Name','Value':f'{nome_bucket.lower()}'},{'Key':'Customer','Value': f'{customer.lower()}'}
        ]
    }
    
    try:
        s3_client.put_bucket_tagging(
            Bucket=nome_bucket,
            Tagging=tags
        )
        print (f"Incluido as tags no bucket '{nome_bucket}' com sucesso")
    except ClientError as e:
        logging.error(e)
        return False
    return True
    
def incluir_cors(bucket):
    nome_bucket = f"{bucket.lower()}-dev-test"
    cors_configuration = {
        'CORSRules': [{
            'AllowedHeaders': ['Authorization'],
            'AllowedMethods': ['GET', 'PUT'],
            'AllowedOrigins': ['*'],
            'ExposeHeaders': ['ETag', 'x-amz-request-id'],
            'MaxAgeSeconds': 3000
        }]
    }
    try:
        # Tenta obter a configuração CORS existente
        response = s3_client.get_bucket_cors(Bucket=nome_bucket)
        print(f"CORS já configurado no bucket '{nome_bucket}': {response['CORSRules']}")
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchCORSConfiguration':
            # Se não houver configuração CORS, define uma nova
            try:
                s3_client.put_bucket_cors(
                    Bucket=nome_bucket,
                    CORSConfiguration=cors_configuration
                )
                print(f"CORS configurado com sucesso no bucket '{nome_bucket}'")
            except ClientError as put_error:
                logging.error(f"Erro ao configurar CORS no bucket '{nome_bucket}': {put_error}")
                return False
        else:
            logging.error(f"Erro ao obter configuração CORS do bucket '{nome_bucket}': {e}")
            return False
    return True

    
for bucket, customer in zip(buckets, customers):
    if criar_bucket_s3(bucket):
        incluir_tags(bucket,customer)
        incluir_cors(bucket)