# Script de Backup de Coleção MongoDB para AWS S3 (PowerShell)

Este script PowerShell automatiza o processo de backup de uma coleção específica de um banco de dados MongoDB, compacta o resultado e faz o upload para um bucket na AWS S3.

## Funcionalidades

- **Carregamento de Configuração**: Carrega variáveis sensíveis (como credenciais) e configurações de um arquivo `.env` para manter a segurança.
- **Verificações Prévias (Pre-flight checks)**:
  - Valida se as ferramentas necessárias (`mongodump`, `aws cli`) estão instaladas.
  - Verifica se o AWS CLI está configurado com as credenciais e conta corretas.
  - Confirma a acessibilidade ao bucket S3 de destino.
  - Testa a conexão com o banco de dados MongoDB.
  - Garante que o diretório de saída existe (e o cria se necessário).
  - Verifica se há espaço em disco suficiente para o backup.
- **Execução do Backup**: Utiliza o `mongodump` para criar um backup da coleção especificada, com compressão `gzip`.
- **Upload para S3**: Envia o diretório de backup gerado para uma pasta específica dentro de um bucket S3.
- **Limpeza**: Oferece a opção de remover os arquivos temporários de backup após o upload e limpa as variáveis de ambiente sensíveis da sessão atual.
- **Logs Detalhados**: Fornece feedback claro e colorido sobre cada etapa do processo (INFO, SUCCESS, WARN, ERROR).

## Pré-requisitos

Antes de executar o script, certifique-se de que os seguintes componentes estão instalados e configurados no seu ambiente Windows:

1.  **PowerShell**: Versão 5.1 ou superior.
2.  **MongoDB Database Tools**: É necessário ter o `mongodump` no PATH do sistema.
    - Link para download
3.  **AWS CLI**: A interface de linha de comando da AWS deve estar instalada e configurada.
    - Link para download
    - Configure-a executando `aws configure` no seu terminal e fornecendo seu `AWS Access Key ID`, `AWS Secret Access Key` e `Default region`.

## Configuração

O script requer um arquivo `.env` no mesmo diretório para carregar as configurações de ambiente. Crie um arquivo chamado `.env` com o seguinte conteúdo, substituindo os valores de exemplo pelos seus:

```env
# Credenciais do MongoDB
MONGO_USER="seu_usuario_mongo"
MONGO_PASS="sua_senha_mongo"

# Configuracoes do AWS S3
BUCKET_NAME="nome-do-seu-bucket-s3"
OBJECT_KEY="caminho/dentro/do/bucket" # Ex: backups/mongodb

# Verificacao de identidade AWS (para seguranca)
AWS_ACCOUNT_ID="123456789012"
AWS_USER_NAME="seu-usuario-iam"
```

**Importante**: Adicione o arquivo `.env` ao seu `.gitignore` para evitar que credenciais sejam enviadas para o controle de versão.

## Uso

Execute o script a partir de um terminal PowerShell, fornecendo os parâmetros obrigatórios.

### Sintaxe

```powershell
.\bkp-db-collection.ps1 -ServerHost <host_do_cluster> -DatabaseName <nome_do_banco> -CollectionName <nome_da_colecao> -Output_Dir <diretorio_de_saida>
```

### Exemplo

```powershell
# Navegue ate o diretorio do script
cd "d:\4.projetos\projetos\scripts-testes\download-bakcup-mongo-upload-s3\automacao-bkp-api\win"

# Execute o script
.\bkp-db-collection.ps1 -ServerHost "meucluster.exemplo.net" -DatabaseName "ecommerce" -CollectionName "produtos" -Output_Dir "C:\temp\mongo_backups"
```

### Parâmetros do Script

- `ServerHost` **(Obrigatório)**
  - O host ou cluster do MongoDB.
  - Exemplo: `'meucluster.exemplo.net'`

- `DatabaseName` **(Obrigatório)**
  - O nome do banco de dados do qual a coleção será copiada.
  - Exemplo: `'ecommerce'`

- `CollectionName` **(Obrigatório)**
  - O nome da coleção específica a ser salva no backup.
  - Exemplo: `'produtos'`

- `Output_Dir` **(Obrigatório)**
  - O caminho do diretório local onde o arquivo de backup será salvo temporariamente.
  - Exemplo: `'C:\temp\mongo_backups'`

## Fluxo de Execução

1.  Carrega as variáveis do arquivo `.env`.
2.  Executa todas as funções de verificação (`check_*`). Se alguma verificação crítica falhar, o script é interrompido.
3.  Executa o `mongodump` para criar o backup localmente.
4.  Executa o `aws s3 cp` para fazer o upload do backup para o S3.
5.  Pergunta ao usuário se deseja limpar os arquivos temporários.
6.  Limpa as variáveis de ambiente sensíveis da sessão.
7.  Exibe uma mensagem de sucesso e finaliza.