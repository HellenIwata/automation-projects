# MongoDB Collection Backup Script

Script em Bash para realizar o backup de uma coleção específica do MongoDB e enviar automaticamente para um bucket S3 da AWS.

## 🚀 Funcionalidades

- Validação de argumentos e ferramentas (`mongodump`, `aws`, `mongorestore`)
- Verificação de acesso ao MongoDB e à AWS
- Backup da coleção com compressão (`--gzip`)
- Upload automático para o S3
- Logs coloridos e informativos
- Limpeza de variáveis sensíveis após execução

## 📦 Requisitos

- MongoDB Database Tools (`mongodump`, `mongorestore`)
- AWS CLI configurado
- Arquivo `.env` com as seguintes variáveis:
  ```env
  MONGO_USER=seu_usuario
  MONGO_PASS=sua_senha
  BUCKET_NAME=nome_do_bucket
  OBJECT_KEY=pasta_no_bucket
  AWS_ACCOUNT_ID=seu_id_aws
  AWS_USER_NAME=seu_usuario_aws
    ```

## 🛠️ Uso

```bash
./bkp-db-collection.sh [host] [db_name] [collection_name] [output_dir]
```
Exemplo:

```bash
./bkp-db-collection.sh cluster0.mongodb.net minhaDatabase minhaColecao ./backups
```


## 📁 Saída
O backup será salvo em:

```bash
[output_dir]/[timestamp]-[host]-[db_name]-[collection_name]-backup/
```

E enviado para:

```bash
s3://[BUCKET_NAME]/[OBJECT_KEY]/
```


## 👩‍💻 Autora
Hellen Cristina N. Iwata 
Versão: 1.0

Contribuições, sugestões e melhorias são muito bem-vindas!

