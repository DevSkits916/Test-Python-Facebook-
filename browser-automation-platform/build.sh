#!/usr/bin/env bash
set -euxo pipefail

# Ensure system packages are up to date
apt-get update
apt-get install -y wget gnupg unzip curl

# Install Google Chrome
if ! command -v google-chrome >/dev/null 2>&1; then
  wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  apt-get install -y /tmp/google-chrome.deb
fi

CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
CHROME_MAJOR=${CHROME_VERSION%%.*}

# Install matching ChromeDriver
LATEST_CHROMEDRIVER=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR}")
curl -s -o /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${LATEST_CHROMEDRIVER}/chromedriver-linux64.zip"
unzip -o /tmp/chromedriver.zip -d /tmp
mv /tmp/chromedriver-linux64/chromedriver /usr/bin/chromedriver
chmod +x /usr/bin/chromedriver

# Clean up
rm -rf /tmp/chromedriver.zip /tmp/google-chrome.deb /tmp/chromedriver-linux64
