#!/bin/bash

TOMCAT_WEBAPPS="/opt/tomcat9/webapps"

# Directory to search for WAR files (current directory by default)
DEPLOY_DIR="${1:-.}"

if [ ! -d "$TOMCAT_WEBAPPS" ]; then
    echo "Error: Tomcat webapps directory not found at $TOMCAT_WEBAPPS"
    exit 1
fi

if [ ! -d "$DEPLOY_DIR" ]; then
    echo "Error: Deployment directory $DEPLOY_DIR does not exist"
    exit 1
fi

WAR_FILES=$(find "$DEPLOY_DIR" -maxdepth 1 -type f -name "*.war")

if [ -z "$WAR_FILES" ]; then
    echo "No WAR files found in $DEPLOY_DIR"
    exit 1
fi

echo "Deploying WAR files from $DEPLOY_DIR to $TOMCAT_WEBAPPS:"

for war_file in $WAR_FILES; do
    filename=$(basename "$war_file")
    
    if [ -f "$TOMCAT_WEBAPPS/$filename" ]; then
        echo "- Replacing existing deployment: $filename"
        sudo rm -rf "${TOMCAT_WEBAPPS}/${filename%.war}"
    else
        echo "- Deploying new application: $filename"
    fi
    
    sudo cp "$war_file" "$TOMCAT_WEBAPPS/"
    
    sudo chown tomcat:tomcat "$TOMCAT_WEBAPPS/$filename"
done

echo "Restarting Tomcat to apply deployments..."
sudo systemctl restart tomcat

if sudo systemctl is-active --quiet tomcat; then
    echo "Tomcat restarted successfully. WAR files deployed."
else
    echo "Error: Tomcat failed to restart after deployment"
    exit 1
fi

exit 0