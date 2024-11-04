#!/bin/bash

TOMCAT_ADMIN_USER="${TOMCAT_ADMIN_USER:-tomcat_odoo_admin}"
TOMCAT_ADMIN_PASSWORD="${TOMCAT_ADMIN_PASSWORD:-T0mc@t0d00@dm!n}"
TOMCAT_VERSION="${TOMCAT_VERSION:-9.0.96}"
TOMCAT_MAJOR_VERSION="9"
TOMCAT_HOME="/opt/tomcat9"

sudo apt-get update

sudo apt-get install -y openjdk-11-jdk

JAVA_HOME=$(sudo update-java-alternatives -l | awk '{print $3}')

if [ -z "$JAVA_HOME" ]; then
    echo "Error: Could not determine Java home path. Please ensure Java is installed."
    exit 1
fi

sudo groupadd --system tomcat
sudo useradd -m -p $(openssl passwd -1 tomcat) -s /bin/bash -g tomcat -d ${TOMCAT_HOME} tomcat

wget https://downloads.apache.org/tomcat/tomcat-${TOMCAT_MAJOR_VERSION}/v${TOMCAT_VERSION}/bin/apache-tomcat-${TOMCAT_VERSION}.tar.gz -O /tmp/tomcat.tar.gz

sudo mkdir -p ${TOMCAT_HOME}
sudo tar xzvf /tmp/tomcat.tar.gz -C ${TOMCAT_HOME} --strip-components=1

sudo chown -R tomcat:tomcat ${TOMCAT_HOME}
sudo chmod -R 755 ${TOMCAT_HOME}

sudo tee ${TOMCAT_HOME}/conf/tomcat-users.xml > /dev/null << EOL
<?xml version="1.0" encoding="UTF-8"?>
<tomcat-users xmlns="http://tomcat.apache.org/xml"
              xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
              xsi:schemaLocation="http://tomcat.apache.org/xml tomcat-users.xsd"
              version="1.0">
    <role rolename="manager-gui"/>
    <role rolename="admin-gui"/>
    <user username="${TOMCAT_ADMIN_USER}" password="${TOMCAT_ADMIN_PASSWORD}" 
          roles="manager-gui,admin-gui"/>
</tomcat-users>
EOL

sudo tee ${TOMCAT_HOME}/webapps/manager/META-INF/context.xml > /dev/null << EOL
<?xml version="1.0" encoding="UTF-8"?>
<Context antiResourceLocking="true" privileged="true" >
  <Valve className="org.apache.catalina.valves.RemoteAddrValve"
         allow=".*" />
</Context>
EOL

sudo tee ${TOMCAT_HOME}/webapps/host-manager/META-INF/context.xml > /dev/null << EOL
<?xml version="1.0" encoding="UTF-8"?>
<Context antiResourceLocking="true" privileged="true" >
  <Valve className="org.apache.catalina.valves.RemoteAddrValve"
         allow=".*" />
</Context>
EOL

sudo tee /etc/systemd/system/tomcat.service > /dev/null << EOL
[Unit]
Description=Apache Tomcat Web Application Container
After=network.target

[Service]
Type=forking
Environment=JAVA_HOME=${JAVA_HOME}
Environment=CATALINA_PID=${TOMCAT_HOME}/temp/tomcat.pid
Environment=CATALINA_HOME=${TOMCAT_HOME}
Environment=CATALINA_BASE=${TOMCAT_HOME}
Environment='CATALINA_OPTS=-Xms512M -Xmx1024M -server -XX:+UseParallelGC'
Environment='JAVA_OPTS=-Djava.awt.headless=true -Djava.security.egd=file:/dev/./urandom'

ExecStart=${TOMCAT_HOME}/bin/startup.sh
ExecStop=${TOMCAT_HOME}/bin/shutdown.sh
User=tomcat
Group=tomcat
UMask=0007
RestartSec=10
Restart=always

[Install]
WantedBy=multi-user.target
EOL

sudo systemctl daemon-reload

sudo systemctl enable tomcat
sudo systemctl start tomcat

rm /tmp/tomcat.tar.gz

if sudo systemctl is-active --quiet tomcat; then
    echo "Tomcat ${TOMCAT_VERSION} installed successfully!"
    echo "Java Home: ${JAVA_HOME}"
    echo "Tomcat Installation Directory: ${TOMCAT_HOME}"
    echo "Tomcat User: tomcat (password: tomcat)"
    echo "Tomcat Manager GUI Credentials:"
    echo "Username: ${TOMCAT_ADMIN_USER}"
    echo "Password: ${TOMCAT_ADMIN_PASSWORD}"
    echo "Access Tomcat Manager at: http://your_server_ip:8080/manager/html"
    echo "Access Host Manager at: http://your_server_ip:8080/host-manager/html"
else
    echo "Tomcat installation failed"
    exit 1
fi