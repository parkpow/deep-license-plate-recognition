#!/bin/bash
set -e

# Function to check and install Docker
install_docker() {
    if command -v docker &> /dev/null; then
        echo "Docker is already installed."
        docker_version=$(docker --version | awk '{print $3}')
        echo "Docker version: $docker_version"
    else
        echo "Docker not found. Installing Docker..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh > /dev/null 2>&1
        echo "Docker installed successfully."
    fi
}

# Function to download Docker image
pull_docker_image() {
    local image_name=$1
    echo "Downloading image..."
    docker pull $image_name > /dev/null 2>&1
    echo "Image download complete."
}

# Identify the operating system
lsb_dist=$(uname -s)
architecture=$(uname -m)
path_stream=$(pwd)

echo "Operating System: $lsb_dist"
echo "Architecture: $architecture"

# Install Docker if needed
install_docker

# Function to get the value of the argument
get_value() {
    echo "$1" | cut -d'=' -f2
}

# Default variables
plate_recognizer_token=""
license_key=""

# Process command line arguments
for arg in "$@"; do
    case "$arg" in
        -t=*|--token=*)
            plate_recognizer_token="$(get_value "$arg")"
            ;;
        -l=*|--license_key=*)
            license_key="$(get_value "$arg")"
            ;;
    esac
done

# Prompt for values if not provided as arguments
if [ -z "$plate_recognizer_token" ]; then
    read -p "Enter your Plate Recognizer API token: " plate_recognizer_token
fi

if [ -z "$license_key" ]; then
    read -p "Enter your license key: " license_key
fi

echo "Token: $plate_recognizer_token"
echo "License Key: $license_key"

container_name="stream"
# Check if the container exists, and if so, stop and remove it
if docker ps -a --format "{{.Names}}" | grep -q "$container_name"; then
    echo "Stopping and removing existing container: $container_name"
    docker stop "$container_name" > /dev/null 2>&1
    docker rm "$container_name" > /dev/null 2>&1
fi

if [ "$architecture" == "x86_64" ]; then
    pull_docker_image "platerecognizer/alpr-stream"
    docker_command="docker run -t -d --restart="unless-stopped"  --name stream -v $path_stream/stream:/user-data --user $(id -u):$(id -g) -e LICENSE_KEY=$license_key -e TOKEN=$plate_recognizer_token platerecognizer/alpr-stream"
    
elif [ "$architecture" == "armv7l" ] || [ "$architecture" == "aarch64" ] || [ "$architecture" == "armv7hf" ]; then
    pull_docker_image "platerecognizer/alpr-stream:raspberry"
    docker_command="docker run -t -d --restart="unless-stopped" --name stream -v $path_stream/stream:/user-data --user $(id -u):$(id -g) -e LICENSE_KEY=$license_key -e TOKEN=$plate_recognizer_token platerecognizer/alpr-stream:raspberry"
    
else
    echo "Unsupported architecture: $architecture"
    exit 1
fi

echo "Running the Stream..."
$docker_command


echo "Stream is now up and running and will automatically start after boot."
