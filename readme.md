# automation-project

Repositório criado para guardar scripts e automações em Python e Shell desenvolvidos por mim. O objetivo é centralizar soluções úteis para tarefas administrativas, especialmente voltadas a serviços AWS e administração de servidores Linux.

## 🛠️ Tecnologias utilizadas

- 🐍 Python
- 🖥️ Shell Script (Bash)
- ☁️ AWS CLI / Boto3
- ⚙️ Systemd (para serviços Linux)
---


## 📁 Estrutura do Projeto

| 📂 Caminho | 🧩 Tipo | 📄 Descrição |
|-----------|--------|--------------|
| [`python/aws/criacao-buckets-s3.py`](python/aws/criacao-buckets-s3.py) | 🐍 Python | Criação automatizada de buckets S3 com tags e regras de CORS |
| [`python/aws/criacao-politicas-iam.py`](python/aws/criacao-politicas-iam.py) | 🛡️ Python | Criação de políticas IAM personalizadas para buckets S3 |
| [`python/mongodb/download-upload-bkp-diario.py`](python/mongodb/download-upload-bkp-diario.py) | 🗓️ Python | Backup diário de snapshots do MongoDB Atlas |
| [`python/mongodb/download-upload-bkp-recente.py`](python/mongodb/download-upload-bkp-recente.py) | ⏱️ Python | Backup do snapshot mais recente do MongoDB Atlas |
| [`scripts-bash/services-linux/zabbix-update.sh`](scripts-bash/services-linux/zabbix-update.sh) | ⚙️ Bash | Validação e atualização do agente Zabbix em servidores Linux |
| [`scripts-bash/mongo/bkp-db-collection.sh`](scripts-bash/mongo/bkp-db-collection.sh) | 💾 Bash | Backup de coleção MongoDB com envio automático para S3 |


---

## 🚀 Como executar os scripts

### 🐍 Python:

<details> 
    <summary>☁️ Criação de Buckets S3 com Tags e CORS</summary>

    Arquivo: `python/aws/criacao-buckets-s3.py`
    Este script automatiza a criação de buckets S3 nomeados por cliente, adiciona tags de identificação e configura as regras de CORS (Cross-Origin Resource Sharing) para cada bucket. É útil para ambientes multi-clientes onde é necessário organizar buckets com metadata e controle de acesso.

    📌 Funcionalidades:
    Criação de buckets com sufixo -dev-test

    Inclusão de tags padrão (Environment, Name, Customer)

    Verificação e configuração de regras CORS caso não existam

    ✔️ Pré-requisitos:
    Python 3.x

    Biblioteca boto3 instalada

    Credenciais AWS configuradas localmente (via aws configure ou variáveis de ambiente)

    Permissão IAM com acesso para:

    Criar buckets

    Adicionar tags

    Configurar CORS

    ▶️ Execução:
</details>

<details>
  <summary>☁️ Criação de políticas IAM na AWS</summary>

    Arquivo: `python/aws/criacao-politicas-iam.py`

    Este script cria políticas IAM de leitura para buckets S3 personalizados para diferentes clientes.

    ✔️ Pré-requisitos:

    - Python 3.x
    - Biblioteca `boto3` instalada
    - Credenciais AWS configuradas localmente (via `aws configure` ou variáveis de ambiente)

    ▶️ Execução:
    cd python/aws
    python3 criacao-politicas-iam.py
</details>

<details>
    <summary> 🗂️ MongoDB - Backup Diário</summary>

    Arquivo: python/mongodb/download-upload-bkp-diario.py

    Este script realiza o backup diário de um cluster MongoDB no Atlas e o faz o upload para um bucket no S3. Ele conecta-se à API do MongoDB Atlas para obter informações sobre os snapshots diários e, ao encontrá-los, faz o download do arquivo e o envia para o bucket do S3.

    ✔️ Pré-requisitos:
    - Python 3.x
    - Bibliotecas requests e boto3 instaladas
    - Acesso ao MongoDB Atlas com credenciais configuradas
    - Acesso ao S3 com permissões adequadas
    - Como executar:
    - Configuração das variáveis de ambiente:

    Configure as variáveis de ambiente com suas credenciais do MongoDB Atlas e informações do S3:

    - atlas_public_key
    - atlas_private_key
    - group_id
    - cluster_name
    - bucket_name
    
    ▶️ Execução:
    cd python/mongodb
    python3 download-upload-bkp-diario.py
</details>

<details>
    <summary> 🗂️ MongoDB - Backup Recente</summary>

    Arquivo: python/mongodb/download-upload-bkp-recente.py

    Este script realiza o backup do snapshot mais recente de um cluster MongoDB no Atlas e o faz o upload para um bucket no S3. Ele se conecta à API do MongoDB Atlas para obter os backups disponíveis, seleciona o mais recente e faz o download do arquivo. Após o download, o arquivo é enviado para o bucket do S3 especificado.

    ✔️ Pré-requisitos:
    - Python 3.x
    - Bibliotecas requests e boto3 instaladas
    - Acesso ao MongoDB Atlas com credenciais configuradas
    - Acesso ao S3 com permissões adequadas
    - Como executar:
    - Configuração das variáveis de ambiente:

    Configure as variáveis de ambiente com suas credenciais do MongoDB Atlas e informações do S3:

    - atlas_public_key
    - atlas_private_key
    - group_id
    - cluster_name
    - s3_bucket_name
    - s3_folder_path

    ▶️ Execução:
    cd python/mongodb
    python3 download-upload-bkp-recente.py
</details>

### 🖥️ Shell Script:
<details>
    <summary> Atualização e Validação do Zabbix Agent</summary>

    Arquivo: scripts-bash/services-linux/zabbix-update.sh

    Este script valida a instalação do agente Zabbix, permite a edição do arquivo de configuração e reinicia o serviço. Também realiza backup da configuração antiga.

    Pré-requisitos:
    Permissões de root
    Sistema com systemd
    Zabbix Agent instalado
    Execução:
    Navegue até o diretório do script:

    Bash

    cd scripts-bash/services-linux
    Execute o script com permissões de superusuário:

    Bash

    sudo bash zabbix-update.sh
</details>

<details> <summary> Backup de coleção MongoDB com envio para S3</summary>

Arquivo: scripts-bash/mongo/bkp-db-collection.sh

Este script realiza o backup de uma coleção específica do MongoDB e envia os arquivos diretamente para um bucket S3 na AWS. Ele valida ferramentas, permissões e configurações antes de executar o backup e o upload, garantindo segurança e confiabilidade no processo.

✔️ Funcionalidades: - Validação de argumentos e ferramentas (mongodump, aws, mongorestore) - Verificação de acesso ao MongoDB e à AWS - Backup da coleção com compressão (--gzip) - Upload automático para o S3 - Logs coloridos e informativos - Limpeza de variáveis sensíveis

✔️ Pré-requisitos: - MongoDB Database Tools instalados - AWS CLI configurado - Arquivo .env com variáveis de acesso

▶️ Execução: bash cd scripts-bash/mongo bash bkp-db-collection.sh [host] [db_name] [collection_name] [output_dir] </details>

## 🙌 Contribuições
Atualmente, este repositório é de uso pessoal, mas contribuições e sugestões são bem-vindas!
Sinta-se à vontade para abrir issues ou pull requests.

## 👤 Autor
Desenvolvido por Hellen Iwata 🚀

