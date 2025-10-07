<#
.SYNOPSIS
Script para fazer backup de uma colecao MongoDB para um arquivo e fazer upload para o S3.

.DESCRIPTION
Este script executa o 'mongodump' para fazer backup de uma colecao especifica do MongoDB,
verifica as ferramentas e configuracoes necessarias (MongoDB Tools, AWS CLI, S3),
e faz upload do backup para um bucket S3.

.PARAMETER ServerHost
O host ou cluster do MongoDB (ex: 'meucluster.exemplo.net').

.PARAMETER DatabaseName
O nome do banco de dados a ser feito o backup. (Nome corrigido para evitar conflito de alias)

.PARAMETER CollectionName
O nome da colecao especifica a ser feito o backup. (Nome corrigido para convencao PowerShell)

.PARAMETER Output_Dir
O diretorio local onde o arquivo de backup sera salvo temporariamente.

.NOTES
Autor: Hellen Cristina N. Iwata (Adaptado para PowerShell)
Versao: 2.0.0
Dependencias: MongoDB Database Tools, AWS CLI.
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ServerHost, 
    
    [Parameter(Mandatory=$true)]
    [string]$DatabaseName, 
    
    [Parameter(Mandatory=$true)]
    [string]$CollectionName, 
    
    [Parameter(Mandatory=$true)]
    [string]$Output_Dir
)


# Carrega a funcao para processar o arquivo .env
function Load-Env {
    param(
        [Parameter(Mandatory=$true)]
        [string]$EnvFilePath = ".env"
    )

    if (-not (Test-Path -Path $EnvFilePath)) {
        Write-Warning "Arquivo .env nao encontrado em: $EnvFilePath"
        return
    }

    Write-Host "Carregando variaveis do arquivo .env..." -ForegroundColor Cyan

    Get-Content -Path $EnvFilePath | ForEach-Object {
        # Ignora linhas vazias ou comentarios (#)
        if ($_ -match '^\s*#|^\s*$') {
            return
        }

        # Extrai chave e valor: KEY="VALUE" ou KEY=VALUE
        if ($_ -match '^(?<Key>[^=]+)=(?<Value>.*)$') {
            $Key = $Matches.Key.Trim()
            $Value = $Matches.Value.Trim().Trim('"').Trim("'")

            # Cria uma variavel de ambiente (disponivel para programas externos como mongodump/aws)
            Set-Item -Path Env:\$Key -Value $Value -Force
            
            Write-Host "  -> Variavel de ambiente '$Key' carregada." -ForegroundColor DarkGray
        }
    }
}

# Chamada da funcao para carregar .env
Load-Env -EnvFilePath (Join-Path -Path $PSScriptRoot -ChildPath ".env")

## Configuracao de Variaveis e Ambiente

# Variaveis carregadas do .env (devem ter sido definidas em .env)
$MONGO_USER = $env:MONGO_USER
$MONGO_PASS = $env:MONGO_PASS
$BUCKET_NAME = $env:BUCKET_NAME
$OBJECT_KEY = $env:OBJECT_KEY
$AWS_ACCOUNT_ID = $env:AWS_ACCOUNT_ID
$AWS_USER_NAME = $env:AWS_USER_NAME

# Variaveis do script
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"

# Usando $DatabaseName e $CollectionName
$OUTPUT_FILE = "${TIMESTAMP}-${ServerHost}-${DatabaseName}-${CollectionName}-backup"
$MONGO_URI = "mongodb+srv://${MONGO_USER}:${MONGO_PASS}@${ServerHost}/"
$BACKUP_PATH_GZIP = Join-Path -Path $Output_Dir -ChildPath "$($OUTPUT_FILE).gzip"
$MinimumDiskSpaceKB = 100000 # 100 MB

## Funcoes de Log e Utilidade

function Write-Log {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Level,
        [Parameter(Mandatory=$true)]
        [string]$Message
    )
    $TimestampLog = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    switch ($Level) {
        "INFO"    { Write-Host "[INFO] ${TimestampLog} - ${Message}" -ForegroundColor DarkGray }
        "SUCCESS" { Write-Host "[SUCCESS] ${TimestampLog} - ${Message}" -ForegroundColor Green }
        "WARN"    { Write-Host "[WARN] ${TimestampLog} - ${Message}" -ForegroundColor Yellow }
        "ERROR"   { Write-Host "[ERROR] ${TimestampLog} - ${Message}" -ForegroundColor Red; exit 1 }
        default   { Write-Host "[LOG] ${TimestampLog} - ${Message}" }
    }
}

function log_info { param([string]$msg) Write-Log -Level "INFO" -Message $msg }
function log_sucess { param([string]$msg) Write-Log -Level "SUCCESS" -Message $msg }
function log_warn { param([string]$msg) Write-Log -Level "WARN" -Message $msg }
function log_error { param([string]$msg) Write-Log -Level "ERROR" -Message $msg }

## Funcoes de Verificacao

function check_tools {
    log_info "Verificando ferramentas necessarias..."

    if (-not (Get-Command mongodump -ErrorAction SilentlyContinue)) {
        log_error "mongodump nao foi encontrado. Por favor, instale o MongoDB Database Tools."
    }
    if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
        log_error "aws cli nao foi encontrado. Por favor, instale e configure o AWS CLI."
    }
    if (-not (Get-Command mongorestore -ErrorAction SilentlyContinue)) {
        log_error "mongorestore nao foi encontrado. Por favor, instale o MongoDB Database Tools."
    }

    log_sucess "Ferramentas necessarias instaladas."
}

function check_configurations_aws {
    log_info "Verificando a configuracao do AWS CLI..."

    try {
        $CallerIdentity = aws sts get-caller-identity --query '{"Account":Account, "UserName":Arn}' --output json | ConvertFrom-Json
        $CurrentAccountId = $CallerIdentity.Account
        $CurrentUserName = $CallerIdentity.UserName.Split('/')[-1] # Extrai o nome de usuario do ARN

        if (-not $CurrentAccountId) {
            log_error "AWS CLI nao esta configurado. Configure-o usando 'aws configure'."
        }
        
        # Uso de aspas duplas para garantir comparacao de strings
        if ("$CurrentAccountId" -ne "$AWS_ACCOUNT_ID") {
            log_warn "AWS CLI configurado para o ID de conta '$CurrentAccountId', mas o esperado era '$AWS_ACCOUNT_ID'."
            log_error "Por favor, configure o AWS CLI com as credenciais corretas."
        }
        
        # Uso de aspas duplas para garantir comparacao de strings
        if ("$CurrentUserName" -ne "$AWS_USER_NAME") {
            log_warn "AWS CLI configurado para o usuario '$CurrentUserName', mas o esperado era '$AWS_USER_NAME'."
            log_error "Por favor, configure o AWS CLI com o usuario correto."
        }
        
        log_sucess "AWS CLI esta configurado."
        log_info "ID da Conta: $CurrentAccountId"
        log_info "Nome de Usuario: $CurrentUserName"
    }
    catch {
        log_error "Falha ao verificar a identidade do chamador do AWS CLI. $_"
    }

    # Verifica se o bucket S3 existe
    log_info "Verificando a existencia do bucket S3..."
    try {
        aws s3 ls "s3://$BUCKET_NAME" | Out-Null
        if ($LASTEXITCODE -ne 0) {
            log_error "O bucket S3 '$BUCKET_NAME' nao existe ou voce nao tem acesso."
        }
        log_sucess "O bucket S3 '$BUCKET_NAME' existe e esta acessivel."
    }
    catch {
        log_error "Falha ao verificar o bucket S3: $_"
    }

    # Verifica a existencia da chave (pasta) do objeto S3
    log_info "Verificando a existencia da chave (pasta) do objeto S3..."
    try {
        aws s3 ls "s3://$BUCKET_NAME/$OBJECT_KEY/" | Out-Null
        if ($LASTEXITCODE -ne 0) {
            log_warn "A chave (pasta) do objeto S3 '$OBJECT_KEY' nao existe no bucket '$BUCKET_NAME'. Ela sera criada no primeiro upload."
        } else {
            log_sucess "A chave (pasta) do objeto S3 '$OBJECT_KEY' existe no bucket '$BUCKET_NAME'."
        }
    }
    catch {
        log_warn "Nao foi possivel verificar a pasta S3: $_ (Continuando, pois sera criada se nao existir)."
    }

    # Verifica permissoes no bucket S3
    log_info "Verificando permissoes de acesso ao bucket S3..."
    try {
        aws s3api get-bucket-acl --bucket "$BUCKET_NAME" | Out-Null
        if ($LASTEXITCODE -ne 0) {
            log_error "Voce nao tem permissao para acessar o bucket S3 '$BUCKET_NAME'."
        }
        log_sucess "Voce tem permissao para acessar o bucket S3 '$BUCKET_NAME'."
    }
    catch {
        log_error "Falha ao verificar permissoes do bucket S3: $_"
    }
}

function check_acess_mongo {
    # Usando $DatabaseName
    log_info "Verificando a acessibilidade do banco de dados $DatabaseName..."
    #log_warn "print uri: '$MONGO_URI'"
    # Tenta um dump silencioso e em arquivo /dev/null
    mongodump --uri="$MONGO_URI" --quiet --archive=NUL
    $EXIT_CODE = $LASTEXITCODE
    
    # Usando $DatabaseName
    if ($EXIT_CODE -eq 0) {
        log_sucess "Banco de dados MongoDB '$DatabaseName' esta acessivel."
    } else {
        log_error "Falha ao acessar o banco de dados MongoDB '$DatabaseName'. Codigo de Saida: $EXIT_CODE"
    }
}

function check_permissions_mongo {
    log_info "Verificacao de permissoes de acesso ao MongoDB assumida como OK apos o teste de acessibilidade."
    log_sucess "Voce tem permissao para acessar o banco de dados MongoDB (baseado no teste de conexao)."
}

function check_output_dir {
    log_info "Verificando diretorio de saida..."
    log_info "Valor de Output_Dir: '$Output_Dir'"
    
    if (-not (Test-Path -Path $Output_Dir -PathType Container)) {
        log_warn "O diretorio de saida '$Output_Dir' nao existe. Criando..."
        try {
            New-Item -Path $Output_Dir -ItemType Directory -Force | Out-Null
            log_success "Diretorio de saida '$Output_Dir' criado com sucesso."
        }
        catch {
            log_error "Falha ao criar o diretorio de saida '$Output_Dir'. Verifique as permissoes. $_"
        }
    } else {
        log_info "O diretorio de saida '$Output_Dir' existe."
    }
}

function check_space_output_dir {
    log_info "Verificando espaco disponivel no diretorio de saida..."
    try {
        $DriveLetter = (Split-Path -Path $Output_Dir -Qualifier).Substring(0,1)
        $DriveInfo = Get-PSDrive -Name $DriveLetter

        $AvailableSpaceKB = [Math]::Floor($DriveInfo.Free / 1KB) # Espaco livre em KB
        
        if ($AvailableSpaceKB -lt $MinimumDiskSpaceKB) {
            log_error "Espaco insuficiente no diretorio de saida '$Output_Dir'. Disponivel: $AvailableSpaceKB KB. Requerido: $MinimumDiskSpaceKB KB."
        } else {
            log_sucess "Espaco suficiente disponivel no diretorio de saida '$Output_Dir'. Disponivel: $AvailableSpaceKB KB."
        }
    }
    catch {
        log_warn "Nao foi possivel verificar o espaco em disco. Continuando, mas pode falhar. $_"
    }
}

## Funcoes de Execucao

function run_mongo_backup {
    log_info "Iniciando backup da colecao MongoDB..."
    
    $BackupOutputDir = Join-Path -Path $Output_Dir -ChildPath $OUTPUT_FILE

    # Remove a pasta de backup anterior se existir
    if (Test-Path -Path $BackupOutputDir -PathType Container) {
        Remove-Item -Path $BackupOutputDir -Recurse -Force
    }

    # Executa o mongodump
    # Usando $DatabaseName e $CollectionName. Parametros do mongodump sao --db e --collection (sem _name)
    #mongodump --uri="$MONGO_URI" --db="$DatabaseName" --collection="$CollectionName" --gzip --out="$BackupOutputDir" 2>&1 | Out-String
    & mongodump --uri="$MONGO_URI" --db="$DatabaseName" --collection="$CollectionName" --gzip --out="$BackupOutputDir" 2>$null

    $EXIT_CODE = $LASTEXITCODE

    # Usando $DatabaseName e $CollectionName
    if ($EXIT_CODE -eq 0) {
        log_sucess "Colecao MongoDB '$CollectionName' do banco de dados '$DatabaseName' fez backup com sucesso para '$BackupOutputDir'."
    } else {
        log_error "Falha ao fazer backup da colecao MongoDB '$CollectionName' do banco de dados '$DatabaseName'. Codigo de Saida: $EXIT_CODE"
    }
}

function run_upload_s3 {
    log_info "Fazendo upload do backup para o bucket S3 '$BUCKET_NAME'..."
    
    $SOURCE_DIR = Join-Path -Path $Output_Dir -ChildPath $OUTPUT_FILE
    
    # O comando aws s3 cp com --recursive para upload de pasta.
    aws s3 cp "$SOURCE_DIR" "s3://$BUCKET_NAME/$OBJECT_KEY/$OUTPUT_FILE/" --recursive 2>&1 | Out-String
    $EXIT_CODE = $LASTEXITCODE

    if ($EXIT_CODE -eq 0) {
        log_sucess "Backup enviado com sucesso para 's3://$BUCKET_NAME/$OBJECT_KEY/$OUTPUT_FILE/'."
    } else {
        log_error "Falha ao enviar o backup para 's3://$BUCKET_NAME/$OBJECT_KEY/$OUTPUT_FILE/'. Codigo de Saida: $EXIT_CODE"
    }
}

function clear_temp_files {
    log_info "Removendo arquivos temporarios..."
    
    $BackupOutputDir = Join-Path -Path $Output_Dir -ChildPath $OUTPUT_FILE
    
    if (Test-Path -Path $BackupOutputDir -PathType Container) {
        Remove-Item -Path $BackupOutputDir -Recurse -Force
        if ($LASTEXITCODE -eq 0) {
            log_sucess "Diretorio de backup temporario '$BackupOutputDir' removido com sucesso."
        } else {
            log_warn "Falha ao remover o diretorio de backup temporario '$BackupOutputDir'. Por favor, remova manualmente."
        }
    }
}

function check_clear_files {
    log_info "Verificando se e necessario limpar arquivos temporarios..."
    # Uso de Read-Host simples para entrada visivel e facil de processar
    $RespostaLimpeza = Read-Host "Deseja remover os arquivos de backup temporarios gerados em '$Output_Dir'? (Y/N)"

    if ($RespostaLimpeza -eq 'Y' -or $RespostaLimpeza -eq 'y') {
        clear_temp_files
    } else {
        log_info "Arquivos temporarios nao serao removidos. Por favor, faca a remocao manual de '$Output_Dir' se necessario."
    }
}

function clear_sensitive_variables {
    log_info "Limpando variaveis sensiveis..."
    
    # Limpa variaveis locais do script
    Remove-Variable MONGO_USER, MONGO_PASS, MONGO_URI, AWS_ACCOUNT_ID, AWS_USER_NAME -ErrorAction SilentlyContinue
    
    # Limpa variaveis de AMBIENTE criadas pelo .env
    Remove-Item Env:\MONGO_USER, Env:\MONGO_PASS -ErrorAction SilentlyContinue
}

## Execucao Principal do Script

Write-Log -Level "INFO" -Message "Inicio do script de backup MongoDB e upload para S3 (PowerShell)."
# Usando $DatabaseName e $CollectionName
log_info "Host: $ServerHost, DB: $DatabaseName, Collection: $CollectionName, Dir: $Output_Dir"

check_tools
check_configurations_aws
check_acess_mongo
check_permissions_mongo
check_output_dir
check_space_output_dir

run_mongo_backup
run_upload_s3

Start-Sleep -Seconds 5

check_clear_files
clear_sensitive_variables

log_sucess "Backup da colecao MongoDB e upload para S3 concluidos com sucesso."

Write-Log -Level "INFO" -Message "Fim do script."
