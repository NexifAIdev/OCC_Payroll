#!/bin/bash

set -euo pipefail
sudo apt install -y net-tools ipcalc

log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

backup_file() {
    local file="$1"
    local backup="${file}.$(date +%Y%m%d_%H%M%S).bak"
    sudo cp "$file" "$backup"
    log_message "Created backup: $backup"
}

if ! command -v psql &> /dev/null; then
    log_message "Error: PostgreSQL is not installed"
    exit 1
fi

INTERFACE=${INTERFACE:-eth0}
if ! sudo ip link show "$INTERFACE" &> /dev/null; then
    log_message "Error: Interface $INTERFACE not found"
    exit 1
fi

ip=$(sudo ip -f inet addr show "$INTERFACE" | awk '/inet / {print $2}' | cut -d'/' -f1)
mask=$(sudo ip -f inet addr show "$INTERFACE" | awk '/inet / {print $2}' | cut -d'/' -f2)

if [[ -n "$mask" ]]; then
    mask=$(printf "%d.%d.%d.%d" \
        $(( 0xffffffff << (32 - mask) >> 24 & 0xff )) \
        $(( 0xffffffff << (32 - mask) >> 16 & 0xff )) \
        $(( 0xffffffff << (32 - mask) >> 8 & 0xff )) \
        $(( 0xffffffff << (32 - mask) & 0xff )))
fi

IFS=. read -r i1 i2 i3 i4 <<< "$ip"
IFS=. read -r m1 m2 m3 m4 <<< "$mask"
net_ip=$(printf "%d.%d.%d.%d" $((i1 & m1)) $((i2 & m2)) $((i3 & m3)) $((i4 & m4)))

PG_VERSION=$(psql -V | awk '{print $3}' | cut -d'.' -f1)
PG_HBA="/etc/postgresql/${PG_VERSION}/main/pg_hba.conf"
POSTGRES_CONF="/etc/postgresql/${PG_VERSION}/main/postgresql.conf"

for file in "$PG_HBA" "$POSTGRES_CONF"; do
    if [[ ! -f "$file" ]]; then
        log_message "Error: Configuration file not found: $file"
        exit 1
    fi
done

if ! sudo grep -q "host all all $net_ip/24 md5" "$PG_HBA" || \
   ! sudo grep -q "host all all 0.0.0.0/0 md5" "$PG_HBA"; then
    backup_file "$PG_HBA"
    {
        echo "# Added by configuration script $(date)"
        echo "host all all $net_ip/24 md5"
        echo "host all all 0.0.0.0/0 md5"
    } | sudo tee -a "$PG_HBA" > /dev/null
    log_message "Added required host lines to pg_hba.conf"
else
    log_message "Required lines already exist in pg_hba.conf"
fi

if sudo grep -q "^#listen_addresses" "$POSTGRES_CONF"; then
    backup_file "$POSTGRES_CONF"
    sudo sed -i "/^#listen_addresses/ s/^#//" "$POSTGRES_CONF"
fi

if ! sudo grep -q "listen_addresses = 'localhost,$ip'" "$POSTGRES_CONF"; then
    backup_file "$POSTGRES_CONF"
    sudo sed -i "s/^listen_addresses.*/listen_addresses = 'localhost,$ip'/" "$POSTGRES_CONF"
    log_message "Updated listen_addresses in postgresql.conf to: localhost,$ip"
else
    log_message "listen_addresses already correctly set to: localhost,$ip"
fi

if sudo systemctl is-active --quiet postgresql; then
    log_message "Restarting PostgreSQL service..."
    sudo systemctl restart postgresql
    log_message "PostgreSQL service restarted successfully"
else
    log_message "Warning: PostgreSQL service is not running"
fi

log_message "Configuration complete"