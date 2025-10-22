<#
.SYNOPSIS
Script para fazer backup de uma colecao/database MongoDB para um arquivo e fazer upload para o S3 (opcional).

.DESCRIPTION
Este script executa o 'mongodump' para fazer backup de uma colecao especifica do MongoDB,
verifica as ferramentas e configuracoes necessarias (MongoDB Tools, AWS CLI, S3),
e faz upload do backup para um bucket S3.

.PARAMETER ServerHost
O host ou cluster do MongoDB (ex: 'meucluster.exemplo.net').

.PARAMETER DatabaseName
O nome do banco de dados a ser feito o backup. 

.PARAMETER CollectionName
O nome da colecao especifica a ser feito o backup.

.PARAMETER Output_Dir
O diretorio local onde o arquivo de backup sera salvo temporariamente.

.NOTES
Autor: Hellen Cristina N. Iwata (Adaptado para PowerShell)
Versao: 2.1.0
Dependencias: MongoDB Database Tools, AWS CLI.
Data de atualização: 21/10/2025

.UPDATES
- Versao 2.1.0: [
    - Adicionado suporte para autentificacao com usuario e senha.
    - Remoção das functions logs e error handling para simplificar o script.
    - Opção de upload opcional para S3.
    - Criação de menu interativo para facilitar o uso.
]
- Versao 2.0.0: Migracao para PowerShell, adicionado suporte para S3.
- Versao 1.0.0: Script inicial em Bash para backup de colecao MongoDB.
#>

# Variaveis de configuracao
$S3BucketName = "nome-bucket-s3"          # Substitua pelo nome do seu bucket S3
$S3BucketObject = "nome-objeto-s3"  # Substitua pelo nome do objeto/pasta no bucket S3
$AWSAccountId = "user-iam" # Substitua pelo nome do usuario AWS
$MinimumDiskSpaceKB = 500000          # 500 MB
$Output_Dir = "C:\caminho\para\backup"   # Diretorio local para salvar os backups (deve ser um caminho absoluto)
$HeaderWidth = 52 # Largura padrao para os cabecalhos do console

# Variaveis Globais (usadas para compartilhar estado entre o fluxo principal e as funcoes)
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Global:BackupFileName = "$DatabaseName`_$CollectionName`_$Timestamp"
$Global:BackupFilePath = Join-Path -Path $Output_Dir -ChildPath "$Global:BackupFileName"
$Global:MongoUriSecure = $null # Inicializa a variavel global de URI segura

#---------------------------------------------------
#|       FUNCOES DE SEGURANCA E UTILIDADES         |
#--------------------------------------------------- 
function Get-UserInput {
    param (
        [string]$Prompt
    )
    Write-Host -NoNewline $Prompt
    return Read-Host
}

function Write-CenteredHost {
    param (
        [string]$Text,
        [int]$Width = $HeaderWidth,
        [string]$BorderChar = " ",
        [string]$ForegroundColor = "Cyan"
    )
    $paddingTotal = $Width - $Text.Length - ($BorderChar.Length * 2)
    if ($paddingTotal -lt 0) { $paddingTotal = 0 }
    $paddingLeft = [Math]::Floor($paddingTotal / 2)
    $paddingRight = $paddingTotal - $paddingLeft
    
    $leftSpace = ' ' * $paddingLeft
    $rightSpace = ' ' * $paddingRight
    
    $centeredText = "$BorderChar$leftSpace$Text$rightSpace$BorderChar"
    
    Write-Host $centeredText -ForegroundColor $ForegroundColor
}

function Show-Menu {
    $line = "=" * $HeaderWidth
    Write-Host $line -ForegroundColor Cyan
    Write-CenteredHost -Text "Sistema de Backup MongoDB"
    Write-Host $line -ForegroundColor Cyan
    
    Write-Host "1. Fazer backup e enviar para S3"
    Write-Host "2. Fazer backup sem enviar para S3"
    Write-Host "3. Restaurar backup (nao implementado)"
    Write-Host "4. Sair"
}

function Get-SecureMongoUri {
    <#
        .SYNOPSIS
        Obtem a URI de conexao MongoDB com autentificacao segura (entrada oculta).
    #>
    $line = "=" * $HeaderWidth
    Write-Host $line -ForegroundColor Cyan
    Write-CenteredHost -Text "Obtendo MongoDB URI Seguro"
    Write-Host ("-" * $HeaderWidth) -ForegroundColor Cyan
    Write-Host "ATENCAO: INFORME A URI DO MONGODB COM USUARIO E SENHA. ('mongodb+srv://usuario:pass@host/')"
    Write-Host "A senha sera ocultada durante a entrada e nao ficara exposta no shell." -ForegroundColor Yellow
    
    return Read-Host -Prompt "Informe a MongoDB URI: " -AsSecureString
}

function Convert-SecureStringToString {
    <#
    .SYNOPSIS
    Converte uma SecureString para String no momento de uso e a limpa da memoria.
    #>
    param(
        [Parameter(Mandatory = $true)]
        [System.Security.SecureString]$SecureString
    )
    # Requer o namespace para fazer a conversao
    Add-Type -AssemblyName System.Runtime.InteropServices
    
    $Ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureString)
    try {
        # Converte o BSTR para uma string (Plain Text)
        return [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($Ptr)
    }
    finally {
        # Limpa o BSTR da memoria imediatamente apos o uso
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Ptr)
    }
}

#---------------------------------------------------
#|               FUNCOES DE VERIFICACAO              |
#--------------------------------------------------- 

function Check_Dependencies {
    Write-Host "Verificando a dependencias (mongodump, mongosh, aws)..." -ForegroundColor Yellow
    
    if (-not (Get-Command mongodump -ErrorAction SilentlyContinue)) {
        Write-Host "Erro: 'mongodump' nao encontrado. Instale o MongoDB Database Tools." -ForegroundColor Red
        exit 1
    }
    if (-not (Get-Command mongosh -ErrorAction SilentlyContinue)) {
        Write-Host "Erro: 'mongosh' nao encontrado. Instale o MongoDB Database Tools." -ForegroundColor Red
        exit 1
    }
    if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
        Write-Host "Erro: 'aws' CLI nao encontrado. Instale a AWS CLI." -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Todas as dependencias estao instaladas." -ForegroundColor Green
}

function Check_AWS_Configuration {
    param (
        [Parameter(Mandatory = $true)]
        [string]$S3BucketName,
        [Parameter(Mandatory = $true)]
        [string]$BucketObject,
        [Parameter(Mandatory = $true)]
        [string]$AWSAccountId,
        [Parameter(Mandatory = $true)]
        [string]$AWSUserName
    )

    $line = "=" * $HeaderWidth
    Write-Host $line -ForegroundColor Cyan
    Write-CenteredHost -Text "CONFIGURACAO DA AWS"
    Write-Host ("-" * $HeaderWidth) -ForegroundColor Cyan
    
    Write-Host "Verificando a configuracao da AWS..." -ForegroundColor Yellow
    
    try {
        $awsIdentity = aws sts get-caller-identity --output json | ConvertFrom-Json
        $awsCurrentAccountId = $awsIdentity.Account
        $awsCurrentUserName = $awsIdentity.Arn.Split('/')[-1]

        if (-not $awsCurrentAccountId) {
            Write-Host "Erro: Nao foi possivel obter a identidade AWS atual." -ForegroundColor Red
            exit 1
        }
        
        if ($awsCurrentAccountId -ne $AWSAccountId -or $awsCurrentUserName -ne $AWSUserName) {
            Write-Host "Aviso: Configuracao AWS difere do usuario/conta esperado ($AWSUserName@$AWSAccountId)." -ForegroundColor Yellow
            Write-Host "Atual: $awsCurrentUserName@$awsCurrentAccountId. Continuar? (s/n)" -ForegroundColor Yellow
            $continue = Get-UserInput 
            if ($continue -ne "s" -and $continue -ne "S") { exit 1 }
        }
        else {
            Write-Host "Configuracao AWS verificada com sucesso ($awsCurrentUserName@$awsCurrentAccountId)." -ForegroundColor Green
        }
    }
    catch {
        Write-Host "Erro ao verificar a configuracao AWS (aws configure pode ser necessário): $_" -ForegroundColor Red
        exit 1
    }
    
    # Verifica Bucket S3
    Write-Host "Verificando a existencia do bucket S3 '$S3BucketName'..." -ForegroundColor Yellow

    try {
        aws s3 ls "s3://$S3BucketName" 2>&1 | Out-String | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Erro: Nao foi possivel acessar o bucket S3 '$S3BucketName'. Verifique o nome e as permissoes." -ForegroundColor Red
            exit 1
        }
        Write-Host "Acesso ao bucket S3 verificado com sucesso." -ForegroundColor Green
    }
    catch {
        Write-Host "Erro ao verificar o acesso ao bucket S3: $_" -ForegroundColor Red
        exit 1
    }
    
    # Verifica permissoes do usuario AWS (Tentativa simples de Get-Bucket-Acl, indica acesso)
    Write-Host "Verificando as permissoes basicas do usuario AWS para o bucket S3..." -ForegroundColor Yellow
    
    try {
        aws s3api get-bucket-acl --bucket "$S3BucketName" 2>&1 | Out-String | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Aviso: Usuario AWS pode nao ter permissoes completas (get-bucket-acl falhou)." -ForegroundColor Yellow
            Write-Host "Continuando, mas a permissao de `s3:PutObject` é essencial para o upload." -ForegroundColor Yellow
        }
        else {
            Write-Host "Permissoes do usuario AWS verificadas com sucesso." -ForegroundColor Green
        }
    }
    catch {
        Write-Host "Aviso ao verificar permissoes: $_" -ForegroundColor Yellow
    }
    
    # Verifica objeto S3
    Write-Host "Verificando o acesso ao objeto S3 (pasta de destino)..." -ForegroundColor Yellow

    try {
        aws s3 ls "s3://$S3BucketName/$BucketObject/" 2>&1 | Out-String | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Aviso: Nao foi possivel listar o objeto S3 '$BucketObject'. A pasta sera criada no primeiro upload." -ForegroundColor Yellow
        }
        else {
            Write-Host "Acesso ao objeto S3 verificado com sucesso." -ForegroundColor Green
        }
    }
    catch {
        Write-Host "Erro ao verificar o acesso ao objeto S3: $_" -ForegroundColor Red
        exit 1
    }
}

function Check_MongoDB_Connection {
    param (
        [Parameter(Mandatory = $true)]
        [System.Security.SecureString]$MongoUriSecure
    )
    
    $line = "=" * $HeaderWidth
    Write-Host $line -ForegroundColor Cyan
    Write-CenteredHost -Text "CONEXAO MONGO DB"
    Write-Host ("-" * $HeaderWidth) -ForegroundColor Cyan
    Write-Host "Verificando a conexao com o MongoDB..." -ForegroundColor Yellow
    
    $MongoUri = Convert-SecureStringToString -SecureString $MongoUriSecure
    
    try {
        # Usa mongosh para pingar o banco de dados de admin
        # Se houver a necessidade adicione "?connectTimeoutMS=5000" ao final da URI
        mongosh --quiet "$MongoUri" --eval "db.adminCommand({ ping: 1 })" 2>&1 | Out-String | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Erro: Nao foi possivel conectar ao MongoDB com a URI fornecida. Verifique as credenciais, o host e a porta." -ForegroundColor Red
            exit 1
        }
        Write-Host "Conexao com o MongoDB verificada com sucesso." -ForegroundColor Green
    }
    catch {
        Write-Host "Erro ao verificar a conexao com o MongoDB: $_" -ForegroundColor Red
        exit 1
    }
}

function Check_Output_Dir {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Output_Dir,
        [Parameter(Mandatory = $true)]
        [int]$Minimum_Disk_Space_KB
    )
    $line = "=" * $HeaderWidth
    Write-Host $line -ForegroundColor Cyan
    Write-CenteredHost -Text "DIRETORIO LOCAL"
    Write-Host ("-" * $HeaderWidth) -ForegroundColor Cyan
    Write-Host "Verificando o diretorio de saida '$Output_Dir'..." -ForegroundColor Yellow

    # 1. Cria o diretorio se nao existir
    if (-not (Test-Path -Path $Output_Dir -PathType Container)) {
        Write-Host "Aviso: O diretorio de saida '$Output_Dir' nao existe. Criando..." -ForegroundColor Yellow
        try {
            New-Item -Path $Output_Dir -ItemType Directory -Force | Out-Null
            Write-Host "Diretorio de saida '$Output_Dir' criado com sucesso." -ForegroundColor Green
        }
        catch {
            Write-Host "Erro ao criar o diretorio de saida '$Output_Dir': $_" -ForegroundColor Red
            exit 1
        }
    }
    else {
        Write-Host "Diretorio de saida verificado com sucesso." -ForegroundColor Green
    }
    
    # 2. Verifica espaco em disco 
    Write-Host "Verificando o espaco em disco (minimo: $(($Minimum_Disk_Space_KB / 1MB).ToString("F2")) MB)..." -ForegroundColor Yellow
    try {
        # Extrai a raiz do caminho (ex: "C:\")
        $driveRoot = [System.IO.Path]::GetPathRoot($Output_Dir)
        
        if ([string]::IsNullOrEmpty($driveRoot)) {
            Write-Host "Erro: Nao foi possivel determinar a unidade de disco para o diretorio '$Output_Dir'. Certifique-se de que e um caminho absoluto (ex: C:\caminho)." -ForegroundColor Red
            exit 1
        }

        # Cria um objeto DriveInfo para a unidade
        $driveInfo = New-Object System.IO.DriveInfo($driveRoot)
        
        # Verifica se a unidade esta pronta (montada e acessivel)
        if (-not $driveInfo.IsReady) {
            Write-Host "Erro: A unidade '$driveRoot' nao esta pronta ou acessivel. Verifique se a unidade esta conectada e acessivel." -ForegroundColor Red
            exit 1
        }

        $Free_Space_KB = [Math]::Ceiling($driveInfo.AvailableFreeSpace / 1KB)

        if ($Free_Space_KB -lt $Minimum_Disk_Space_KB) { 
            Write-Host "Erro: Nao ha espaco em disco suficiente para o backup." -ForegroundColor Red
            Write-Host "Espaco necessario (minimo): $Minimum_Disk_Space_KB KB, Espaco livre: $Free_Space_KB KB" -ForegroundColor Red
            exit 1
        }
        else {
            Write-Host "Espaco em disco suficiente verificado (Livre: $(($Free_Space_KB / 1MB).ToString("F2")) MB)." -ForegroundColor Green
        }
    }
    catch [System.Exception] {
        Write-Host "Erro ao verificar o espaco em disco para '$Output_Dir': $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

#---------------------------------------------------
#|           FUNCOES DE EXECUCAO E FLUXO             |
#--------------------------------------------------- 
function Perform_Backup {
    param (
        [Parameter(Mandatory = $true)]
        [System.Security.SecureString]$MongoUriSecure,
        [Parameter(Mandatory = $true)]
        [string]$DatabaseName,
        [Parameter(Mandatory = $false)] # Colecao é opcional
        [string]$CollectionName,
        [Parameter(Mandatory = $true)]
        [string]$BackupFilePath,
        [Parameter(Mandatory = $true)]
        [string]$BackupScope
    )
    $MongoUri = Convert-SecureStringToString -SecureString $MongoUriSecure
    
    $line = "=" * $HeaderWidth
    Write-Host $line -ForegroundColor Cyan
    Write-CenteredHost -Text "BACKUP MONGODB ($BackupScope)"
    Write-Host ("-" * $HeaderWidth) -ForegroundColor Cyan
    Write-Host "Iniciando o backup em '$BackupFilePath'..." -ForegroundColor Yellow
    
    try {
        # 1. Limpeza do diretorio de backup se ja existir para evitar conflitos
        if (Test-Path -Path $BackupFilePath -PathType Container) {
            Remove-Item -Path $BackupFilePath -Recurse -Force
        }

        # 2. Executa o mongodump 
        if ($BackupScope -eq "COLLECTION") {
            $dumpCommand = "mongodump --uri `"$MongoUri`" --db `"$DatabaseName`" --collection `"$CollectionName`" --out `"$BackupFilePath`" --gzip"
            Write-Host "Comando: mongodump ... --collection $CollectionName" -ForegroundColor DarkGray
        }
        else {
            $dumpCommand = "mongodump --uri `"$MongoUri`" --db `"$DatabaseName`" --out `"$BackupFilePath`" --gzip"
            Write-Host "Comando: mongodump ... --db $DatabaseName" -ForegroundColor DarkGray
        }
    
        Invoke-Expression $dumpCommand 2>&1 | Out-String | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Erro: Falha ao executar o mongodump. (Codigo $LASTEXITCODE)" -ForegroundColor Red
            exit 1
        }
        Write-Host "Backup concluido com sucesso em '$BackupFilePath'." -ForegroundColor Green
        
    }
    catch {
        Write-Host "Erro ao fazer o backup: $_" -ForegroundColor Red
        exit 1
    }
}

function Perform_Upload_S3 {
    param (
        [Parameter(Mandatory = $true)]
        [string]$BackupFilePath,
        [Parameter(Mandatory = $true)]
        [string]$S3BucketName,
        [Parameter(Mandatory = $true)]
        [string]$S3BucketObject
    )
    
    $line = "=" * $HeaderWidth
    Write-Host $line -ForegroundColor Cyan
    Write-CenteredHost -Text "UPLOAD S3"
    Write-Host ("-" * $HeaderWidth) -ForegroundColor Cyan
    Write-Host "Iniciando o upload recursivo de '$BackupFilePath' para S3..." -ForegroundColor Yellow
    
    try {
        $S3Target = "s3://$S3BucketName/$S3BucketObject/$($BackupFilePath | Split-Path -Leaf)/"
        
        # Upload recursivo da pasta de backup
        aws s3 cp "$BackupFilePath" "$S3Target" --recursive 2>&1 | Out-String | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Erro: Falha ao fazer o upload para o S3. (Codigo $LASTEXITCODE). Verifique as permissoes S3 (s3:PutObject)." -ForegroundColor Red
            exit 1
        }
        Write-Host "Upload concluido com sucesso para '$S3Target'." -ForegroundColor Green
    }
    catch {
        Write-Host "Erro ao fazer o upload para o S3: $_" -ForegroundColor Red
        exit 1
    }
}

function Perform_Clear_Temp_Files {
    param (
        [Parameter(Mandatory = $true)]
        [string]$BackupFilePath
    )
    Write-Host "Limpando arquivos temporarios em '$BackupFilePath'..." -ForegroundColor Yellow
    
    try {
        Remove-Item -Path $BackupFilePath -Recurse -Force
        Write-Host "Arquivos temporarios limpos com sucesso." -ForegroundColor Green
    }
    catch {
        Write-Host "Erro ao limpar os arquivos temporarios: $_" -ForegroundColor Red
    }
}

function Check_Clear_Files {
    param (
        [Parameter(Mandatory = $true)]
        [string]$BackupFilePath
    )
    
    $line = "=" * $HeaderWidth
    Write-Host $line -ForegroundColor Cyan
    Write-CenteredHost -Text "LIMPEZA LOCAL"
    Write-Host ("-" * $HeaderWidth) -ForegroundColor Cyan
    
    if (-not (Test-Path -Path $BackupFilePath -PathType Container)) {
        Write-Host "Nao ha diretorio de backup para limpar: $BackupFilePath" -ForegroundColor DarkGray
        return
    }
    
    $UserClearResponse = Get-UserInput -Prompt "Deseja remover os arquivos temporarios de backup em '$BackupFilePath'? (s/n): "
    
    if ($UserClearResponse -eq "s" -or $UserClearResponse -eq "S") {
        Perform_Clear_Temp_Files -BackupFilePath $BackupFilePath
    }
    else {
        Write-Host "Arquivos temporarios mantidos. Remova manualmente se necessario." -ForegroundColor Yellow
    }
}

function Perform_Clear_Variables {
    Write-Host "Limpando variaveis da sessao..." -ForegroundColor Yellow
    # Garante que as variaveis globais criticas sejam removidas
    Remove-Variable MongoUriSecure, DatabaseName, CollectionName, BackupFileName, BackupFilePath -Scope Global -ErrorAction SilentlyContinue
    Write-Host "Variaveis globais limpas com sucesso." -ForegroundColor Green
}

function Perform_Sub_Menu_Backup {
    param (
        [Parameter(Mandatory = $true)]
        [System.Security.SecureString]$MongoUriSecure, # Nome do parametro alterado para refletir a variavel
        [string]$UploadMode = "false"
    )
    
    $line = "=" * $HeaderWidth
    Write-Host $line -ForegroundColor Cyan
    Write-CenteredHost -Text "Escopo do Backup"
    Write-Host ("-" * $HeaderWidth) -ForegroundColor Cyan
    Write-Host "1. Backup de Colecao especifica"
    Write-Host "2. Backup do Banco de Dados completo"
    Write-Host "3. Voltar ao menu principal"

    while ($true) {
        $SubMenuChoice = Get-UserInput -Prompt "Escolha uma opcao: "

        if ($SubMenuChoice -eq "1" -or $SubMenuChoice -eq "2") {
            # Atribui as variaveis ao escopo global para que a funcao Check_Clear_Files possa acessa-las
            $Global:DatabaseName = Get-UserInput -Prompt "Informe o nome do Banco de Dados: "

            if ($SubMenuChoice -eq "1") { 
                $Global:CollectionName = Get-UserInput -Prompt "Informe o nome da Colecao: "
                $BackupScope = "COLLECTION"
            }
            else {
                $Global:CollectionName = "" # Limpa a colecao se for full database
                $BackupScope = "DATABASE"
            }
            
            # Recria o nome do arquivo de backup com os valores do usuario
            $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $Global:BackupFileName = "$Global:DatabaseName`_$Global:CollectionName`_$Timestamp"
            $Global:BackupFilePath = Join-Path -Path $Output_Dir -ChildPath "$Global:BackupFileName"
            
            # ----------- Execucao das verificacoes e backup -----------
            
            Check_Output_Dir -Output_Dir $Output_Dir -Minimum_Disk_Space_KB $MinimumDiskSpaceKB
            Perform_Backup -MongoUriSecure $MongoUriSecure -DatabaseName $Global:DatabaseName -CollectionName $Global:CollectionName `
            -BackupFilePath $Global:BackupFilePath -BackupScope $BackupScope

            # ----------------- UPLOAD (SE MODO 1 FOR ESCOLHIDO) ----------------- 
            if ($UploadMode -eq "true") {
                Perform_Upload_S3 -BackupFilePath $Global:BackupFilePath -S3BucketName $S3BucketName -S3BucketObject $S3BucketObject
            }
            
            return $null
        }
        elseif ($SubMenuChoice -eq "3") {
            return $null
        }
        else {
            Write-Host "Opcao invalida. Tente novamente." -ForegroundColor Red
        }
    }
}

# -------------------------
# |     FLUXO PRINCIPAL     |
# ------------------------- 

$line = "=" * $HeaderWidth
Write-Host $line -ForegroundColor Cyan
Write-CenteredHost -Text "INICIO: SCRIPT DE BACKUP MONGODB E S3" -BorderChar "|"
Write-Host $line -ForegroundColor Cyan

# 1. Verifica as dependencias
Check_Dependencies

# 2. Obtem a MongoDB URI segura
$Global:MongoUriSecure = Get-SecureMongoUri

# 3. Verifica a conexao inicial
Check_MongoDB_Connection -MongoUriSecure $Global:MongoUriSecure

# Menu interativo
while ($true) {
    Show-Menu
    $UserChoice = Get-UserInput -Prompt "Escolha uma opcao: "

    if ($UserChoice -eq "1") { 
        # Modo 1: Backup e Upload S3
        Write-Host "Iniciando o modo: Backup e Upload para S3." -ForegroundColor Yellow
        
        Check_AWS_Configuration -S3BucketName $S3BucketName -BucketObject $S3BucketObject -AWSAccountId $AWSAccountId -AWSUserName $AWSUserName
        
        Perform_Sub_Menu_Backup -MongoUriSecure $Global:MongoUriSecure -UploadMode "true"
        
        # Uso da variavel global apos a execucao da funcao
        Check_Clear_Files -BackupFilePath $Global:BackupFilePath
        Perform_Clear_Variables
        break
    }
    elseif ($UserChoice -eq "2") { 
        # Modo 2: Apenas Backup Local
        Write-Host "Iniciando o modo: Apenas Backup Local." -ForegroundColor Yellow
        
        
        Perform_Sub_Menu_Backup -MongoUriSecure $Global:MongoUriSecure -UploadMode "false"
        
        # Uso da variavel global apos a execucao da funcao
        Check_Clear_Files -BackupFilePath $Global:BackupFilePath
        Perform_Clear_Variables
        break
    }
    elseif ($UserChoice -eq "3") { 
        Write-Host "Não implementado" -ForegroundColor Yellow
        Perform_Clear_Variables
        break
    }
    elseif ($UserChoice -eq "4") { 
        Write-Host "Saindo do script." -ForegroundColor Yellow
        Perform_Clear_Variables
        break
    }
    else {
        Write-Host "Opcao invalida. Tente novamente." -ForegroundColor Red
    }
}

Write-Host $line -ForegroundColor Cyan
Write-CenteredHost -Text "FIM: SCRIPT DE BACKUP MONGODB E S3" -BorderChar "|"
Write-Host $line -ForegroundColor Cyan