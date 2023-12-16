#!/bin/bash

# Run script as root user
if [[ $EUID -ne 0 ]]; then
    echo -e "[\e[1;31mError\e[0m] This script must be run as root, exiting..."
    exit 1
fi

hours=1

# Install cron
if ! dpkg -s cron >/dev/null 2>&1; then
    echo "Cron is not installed. Installing..."
    sudo apt install cron
fi

# Check current timezone
echo "Your current timezone is: $(date +%Z)"

# Get user prompt
while true; do
    read -p "Indicate the time duration (in hours) to remove images older than: " num

    # Check if input is a number
    if [[ $num =~ ^[0-9]+$ ]]; then
        # Check if number is within the specified range
        if ((num >= 1 && num <= 23)); then
            hours=$num
            break
        else
            echo "Please enter a number between 1 and 23."
        fi
    else
        echo "Invalid input. Please enter a valid number."
    fi
done

# Get current working directory for Stream
stream_directory=$(pwd)

# Get file age threshold
threshold=$((hours * 60))

# Add scheduler to change passwod every 12AM UTC
echo -e "0 */$hours\t* * *\troot\tremove-images" >>/etc/crontab
systemctl restart cron

# Create remove-images service
cat <<'EOFSH' >/usr/local/sbin/remove-images
#!/bin/bash

# Navigate to the stream folder
cd STREAM-DIRECTORY

# Delete image files in the current directory
find . -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" \) -mmin +THRESHOLD -delete

# Delete empty directories after deleting the images (optional)
find . -type d -empty -delete
EOFSH

sed -i "s|STREAM-DIRECTORY|$stream_directory|g" /usr/local/sbin/remove-images
sed -i "s|THRESHOLD|$threshold|g" /usr/local/sbin/remove-images

# Make service executable
chmod +x /usr/local/sbin/remove-images
cd ~

# Create start up service
if [[ ! -e /etc/platerecognizer ]]; then
    mkdir -p /etc/platerecognizer
fi

cat <<'EOFSH' >/etc/platerecognizer/startup.sh
#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
/usr/local/sbin/remove-images
EOFSH

chmod +x /etc/platerecognizer/startup.sh

echo "[Unit]
Description=Stream Images Removal Startup Script
Before=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/bin/bash /etc/platerecognizer/startup.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target" >/etc/systemd/system/stream-remove-images.service
chmod +x /etc/systemd/system/stream-remove-images.service
systemctl daemon-reload
systemctl start stream-remove-images
systemctl enable stream-remove-images &>/dev/null

# Run image removal service
remove-images

echo "Service successfully installed."

rm -f remove-images.sh
