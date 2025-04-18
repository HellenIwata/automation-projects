# automation-project

Repositório criado para guardar scripts e automações em Python e Shell desenvolvidos por mim. O objetivo é centralizar soluções úteis para tarefas administrativas, especialmente voltadas a serviços AWS e administração de servidores Linux.

## 🛠️ Tecnologias utilizadas

- 🐍 Python
- 🖥️ Shell Script (Bash)
- ☁️ AWS CLI / Boto3
- ⚙️ Systemd (para serviços Linux)
---

## 📁 Estrutura do projeto

automation-project/ # 📂 Repositório principal
├── python/ # 🐍 Scripts Python
│   └── aws/ # ☁️ Automação para serviços AWS
│       └── criacao-politicas-iam.py # 🛡️ Criação de políticas IAM em S3
├── mongodb/ # 💾 Scripts para manipulação de MongoDB
│   └── download-upload-bkp/ # 💾 Backup
│       ├── download-upload-bkp-diario.py # 🗓️ Backup diário de MongoDB
│       └── download-upload-bkp-recente.py # ⏱️ Backup recente de MongoDB
└── scripts-bash/ # ⚙️ Scripts Bash
└── services-linux/ # 🛠️ Utilitários para administração de sistemas Linux
└── zabbix-update.sh # 🚀 Validação e atualização do Zabbix Agent


---

## 🚀 Como executar os scripts

### 🐍 Python:

<details>
  <summary>Criação de políticas IAM na AWS</summary>

    **Arquivo:** `python/aws/criacao-politicas-iam.py`

    Este script cria políticas IAM de leitura para buckets S3 personalizados para diferentes clientes.

    #### Pré-requisitos:

    - Python 3.x
    - Biblioteca `boto3` instalada
    - Credenciais AWS configuradas localmente (via `aws configure` ou variáveis de ambiente)

    #### Execução:

    ```bash
    cd python/aws
    python3 criacao-politicas-iam.py
</details>

<details>
    <summary> 🗂️ MongoDB - Backup Diário</summary>

    Arquivo: python/mongodb/download-upload-bkp-diario.py

    Este script realiza o backup diário de um cluster MongoDB no Atlas e o faz o upload para um bucket no S3. Ele conecta-se à API do MongoDB Atlas para obter informações sobre os snapshots diários e, ao encontrá-los, faz o download do arquivo e o envia para o bucket do S3.

    Pré-requisitos:
    Python 3.x
    Bibliotecas requests e boto3 instaladas
    Acesso ao MongoDB Atlas com credenciais configuradas
    Acesso ao S3 com permissões adequadas
    Como executar:
    Configuração das variáveis de ambiente:

    Configure as variáveis de ambiente com suas credenciais do MongoDB Atlas e informações do S3:

    atlas_public_key
    atlas_private_key
    group_id
    cluster_name
    bucket_name
    Executando o script:

    <!-- end list -->

    Bash

    cd python/mongodb
    python3 download-upload-bkp-diario.py
</details>

<details>
    <summary> 🗂️ MongoDB - Backup Recente</summary>

    Arquivo: python/mongodb/download-upload-bkp-recente.py

    Este script realiza o backup do snapshot mais recente de um cluster MongoDB no Atlas e o faz o upload para um bucket no S3. Ele se conecta à API do MongoDB Atlas para obter os backups disponíveis, seleciona o mais recente e faz o download do arquivo. Após o download, o arquivo é enviado para o bucket do S3 especificado.

    Pré-requisitos:
    Python 3.x
    Bibliotecas requests e boto3 instaladas
    Acesso ao MongoDB Atlas com credenciais configuradas
    Acesso ao S3 com permissões adequadas
    Como executar:
    Configuração das variáveis de ambiente:

    Configure as variáveis de ambiente com suas credenciais do MongoDB Atlas e informações do S3:

    atlas_public_key
    atlas_private_key
    group_id
    cluster_name
    s3_bucket_name
    s3_folder_path
    Executando o script:

    <!-- end list -->

    Bash

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

## 🙌 Contribuições
Atualmente, este repositório é de uso pessoal, mas contribuições e sugestões são bem-vindas!
Sinta-se à vontade para abrir issues ou pull requests.

## 👤 Autor
Desenvolvido por Hellen Iwata 🚀

