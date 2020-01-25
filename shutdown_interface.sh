#!/bin/sh

echo "waiting" > /var/run/shutdown_signal
while inotifywait -e close_write /var/run/shutdown_signal; do
  signal=$(cat /var/run/shutdown_signal)
  if [ "$signal" == "shutdown" ]; then
    echo "done" > /var/run/shutdown_signal
    shutdown -h now
  fi
  if [ "$signal" == "reboot" ]; then
    echo "done" > /var/run/shutdown_signal
    shutdown -r now
  fi
done