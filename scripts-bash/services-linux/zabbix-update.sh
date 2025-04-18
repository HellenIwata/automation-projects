#! /bin/bash

set -e # Interrompe o script em caso de erro inesperado

log_info() {
        echo -e "\e[32m[INFO] $1\e[0m"
}

log_error() {
        echo -e "\e[31m[ERROR] $1\e[0m" >&2
}

run_or_fail() {
        "$@"
        local status=$?
        if [ $status -ne 0 ]; then
                log_error "Falha ao executar: $*"
                exit $status
        fi
}

#Variáveis
SERVER_NAME="$(hostname | tr '[:lower:]' '[:upper:]')"
ZABBIX_CONF="/etc/zabbix/zabbix_agentd.conf"
ZABBIX_SERVICE="zabbix-agent.service"
BACKUP_DIR="/etc/backup/zabbix"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

edit_conf_zabbix(){
        echo "Exibindo configuracoes atuais do arquivo $ZABBIX_CONF:"
        echo "------------------------------------------------------"
        grep -vE '^#|^$' "$ZABBIX_CONF"
        echo "------------------------------------------------------"
        read -p "Deseja editar o arquivo de configuracao? (y/n): " EDITAR
        if [[ "$EDITAR" == "y" ]]; then
                log_info "Parando o serviço para editar o arquivo"
                systemctl stop "$ZABBIX_SERVICE"
                zabbix_conf_backup

                cat > "$ZABBIX_CONF" <<EOL
################### GENERAL PARAMETERS ###################
PidFile=/run/zabbix/zabbix_agentd.pid
LogFile=/var/log/zabbix/zabbix_agentd.log
LogFileSize=0
Server=ip-server
ServerActive=ip-server
Hostname=hiwata-$SERVER_NAME.LNX.LOC
Include=/etc/zabbix/zabbix_agentd.d/*.conf
EOL

                log_info "Iniciando o serviço"
                systemctl start "$ZABBIX_SERVICE"
                log_info "Zabbix atualizado com sucesso!"
        else
                echo "Nenhuma alteração realizada."
                exit 1
        fi
}

verify_zabbix_install(){
    if ! command -v zabbix_agentd &> /dev/null; then
         log_error "O $ZABBIX_SERVICE nao esta instalado. Verifique a distribuicao e realize a instalacao"
         exit 1
    else
         log_error "O $ZABBIX_SERVICE esta instalado, mas o serviço esta parado."
         edit_conf_zabbix
    fi
}

zabbix_status(){
        if systemctl is-active --quiet "$ZABBIX_SERVICE"; then
            log_info "O $ZABBIX_SERVICE esta em execucao."
        else
                verify_zabbix_install
        fi
}

zabbix_conf_backup(){
        log_info "Criando backup do arquivo .conf em: $BACKUP_DIR"
        mkdir -p "$BACKUP_DIR"
        cp "$ZABBIX_CONF" "$BACKUP_DIR/zabbix_agentd.conf.bkp.$TIMESTAMP"
}
log_info "Iniciando o script para validacao/atualizacao do Zabbix"

log_info "Status do $ZABBIX_SERVICE"
zabbix_status
edit_conf_zabbix
