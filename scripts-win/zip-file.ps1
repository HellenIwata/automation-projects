$source_dir="caminho/origem" # Define o diretório de origem
$destination_dir="caminho/compactacao/arquivo" # Define o diretório de saída
$base_name="teste-zip" # Define o nome do arquivo
$logfile="caminho/log/zip-file-log.log" # Define o caminho do log
$cut_date= (Get-Date).AddDays(-90).Date

function Register-Log{
    param(
        [string]$mensage
    )   
    try {
        $timestamp_log = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $format_mensage = "$timestamp_log - $mensage"
        Add-Content -Path $logfile -Value $format_mensage
    } catch {
        Write-Error "Erro ao escrever no log: $_"
    }
}


function Validate-Directory{
    if (-not (Test-Path -Path $destination_dir)){
        New-Item -Path $destination_dir -ItemType Directory -Force
        Register-Log "Diretório de saída criado: $destination_dir"
    } else {
        Register-Log "Diretório de saída já criado: $destination_dir"
    }
}
function Get-Files{
    try{
        $files_to_zip = Get-ChildItem -Path $source_dir -Recurse -File | Where-Object { $_.LastWriteTime.Date -lt $cut_date }
    }
    catch{
        Register-Log "Erro ao obter arquivos para compactação: $_"
        return $null
    }
    
    if ($files_to_zip)
    {
        $file_count = $files_to_zip.Count
        Register-Log "$file_count arquivo(s) encontrado(s) para compactação."
        return $files_to_zip
    }
    else {
        Register-Log "Nenhum arquivo encontrado com data superior a 5 dias para compactação."
        return $null
    }
}

function Remove-Files {
    param(
        [string[]]$Files
    )
    if ($Files) {
        Register-Log "--- Iniciando a exclusão de arquivos compactados com sucesso. ---"        
            foreach ($file_path in $Files) {
            try {
                Remove-Item -Path $file_path -Force
                Register-Log "Arquivo '$file_path' excluído."
            } catch {
                Register-Log "Erro ao excluir o arquivo '$file_path': $_"
            }
        }        
    Register-Log "--- Exclusão de arquivos compactados concluída. ---"
    }
}

function Zip-Files{
    $files_to_zip = Get-Files
    if ($files_to_zip) {
        Register-Log "--- Iniciando a compactacao de $($files_to_zip.Count) arquivo(s) ---"
        $timestamp_file = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
        $name_file_to_zip = "$base_name-$timestamp_file.zip"
        $destination_file_zip = Join-Path $destination_dir -ChildPath $name_file_to_zip

        try {
            $files_full_names = $files_to_zip | Select-Object -ExpandProperty FullName
            Compress-Archive -Path $files_full_names -DestinationPath $destination_file_zip -Force
            Register-Log "$($files_to_zip.Count) arquivo(s) compactado(s) com sucesso para '$destination_file_zip'."
            $success_files = $files_full_names
        } catch {
            Register-Log "Erro ao compactar arquivos: $_"
        }
        Register-Log " -- Arquivos acima de 5 dias foram processados ---"
        if ($success_files) {
            Remove-Files -Files $success_files            
        }
    } else {
        Register-Log "Nenhum arquivo acima de 90 dias para compactação encontrado."
    }
}

Validate-Directory
Zip-Files