sudo mkdir -p /etc/wsl

sudo tee /etc/wsl.conf << 'EOF'
[network]
generateResolvConf = false

[boot]
command = ip addr add 172.24.64.34/20 dev eth0 label eth0:1
EOF

sudo tee /etc/init.d/wsl-static-ip << 'EOF'
#!/bin/bash
ip addr add 172.24.64.34/20 dev eth0 label eth0:1 || true
EOF

sudo chmod +x /etc/init.d/wsl-static-ip

sudo tee /etc/systemd/system/wsl-static-ip.service << 'EOF'
[Unit]
Description=Set static IP for WSL
After=network.target

[Service]
Type=oneshot
ExecStart=/etc/init.d/wsl-static-ip
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable wsl-static-ip
sudo systemctl start wsl-static-ip