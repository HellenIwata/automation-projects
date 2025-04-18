import boto3
import json

# Inicializar o cliente IAM
iam_client = boto3.client('iam')

# Lista de clientes
clientes = ["Meta", "Boticario", "Arauco", "Ifood", "Bayer", "Porto"]

# Função para criar uma política
def criar_politica(cliente):
    nome_politica = f"aws-s3-read-{cliente.lower()}"
    acoes = ["s3:ListBucket", "s3:GetObject", "s3:GetObjectAcl", "s3:GetBucketAcl", "s3:GetBucketLocation", "s3:GetObjectVersion"]
    recursos = [
        f"arn:aws:s3:::sftp-prd",
        f"arn:aws:s3:::sftp-prd/clientes/{cliente}/*"
    ]
    documento_politica = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": acoes,
                "Resource":recursos
            }
        ]
    }
    try:
        resposta = iam_client.create_policy(
            PolicyName=nome_politica,
            PolicyDocument=json.dumps(documento_politica)
        )
        print(f"Política '{nome_politica}' criada com sucesso.")
    except iam_client.exceptions.EntityAlreadyExistsException:
        print(f"Política '{nome_politica}' já existe.")
    except Exception as e:
        print(f"Erro ao criar política '{nome_politica}': {e}")

# Criar políticas para todos os clientes
for cliente in clientes:
    criar_politica(cliente)
