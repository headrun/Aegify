#!/bin/bash
ALERTMANAGER_VERSION="0.20.0"
wget https://github.com/prometheus/alertmanager/releases/download/v${ALERTMANAGER_VERSION}/alertmanager-${ALERTMANAGER_VERSION}.linux-amd64.tar.gz
tar xvzf alertmanager-${ALERTMANAGER_VERSION}.linux-amd64.tar.gz
cd alertmanager-${ALERTMANAGER_VERSION}.linux-amd64/

# create directories
mkdir /etc/alertmanager
mkdir /etc/alertmanager/template
mkdir -p /var/lib/alertmanager/data

# touch config file
touch /etc/alertmanager/alertmanager.yml

# set ownership
chown -R prometheus:prometheus /etc/alertmanager
chown -R prometheus:prometheus /var/lib/alertmanager

# copy binaries
cp alertmanager /usr/local/bin/
cp amtool /usr/local/bin/

# set ownership
chown prometheus:prometheus /usr/local/bin/alertmanager
chown prometheus:prometheus /usr/local/bin/amtool

# setup systemd
echo '[Unit]
Description=Prometheus Alertmanager Service
Wants=network-online.target
After=network.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/alertmanager \
    --config.file /etc/alertmanager/alertmanager.yml \
    --storage.path /var/lib/alertmanager/data \
    --cluster.listen-address="127.0.0.1:9094"
Restart=always

[Install]
WantedBy=multi-user.target' > /etc/systemd/system/alertmanager.service


systemctl daemon-reload
systemctl enable alertmanager
systemctl start alertmanager

# restart prometheus
systemctl start prometheus


#nginx setup
echo "
server {
    listen 0.0.0.0:8091;
    location / {
      proxy_pass http://localhost:9094/;

      auth_basic "alertmanager";
      auth_basic_user_file .htpasswd;
    }
  }
  " > /etc/nginx/sites-enabled/alertmanager.conf

#nginx restart
service nginx restart

echo "
Add the following lines and substitute with correct values to /etc/alertmanager/alertmanager.yml:

global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: '$noreply_email'
  smtp_auth_username: '$noreply_email'
  smtp_auth_password: '$noreply_password'
  smtp_require_tls: false

templates:
- '/etc/alertmanager/template/*.tmpl'

route:
  repeat_interval: 1h
  receiver: operations-team

receivers:
- name: 'operations-team'
  email_configs:
  - to: '$to_email'
"


echo "

Add targets
Alter the following config in /etc/prometheus/prometheus.yml:

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - localhost:9093"
