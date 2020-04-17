#!/usr/bin/env sh

SHUTDOWN_SIGNAL=/var/run/shutdown_signal

echo "waiting" > "$SHUTDOWN_SIGNAL"
while inotifywait -e close_write "$SHUTDOWN_SIGNAL"; do
  signal=$(cat "$SHUTDOWN_SIGNAL")
  if [ "$signal" = "shutdown" ]; then
    echo "done" > ${SHUTDOWN_SIGNAL}
    shutdown -h now
  fi
  if [ "$signal" = "reboot" ]; then
    echo "done" > "$SHUTDOWN_SIGNAL"
    shutdown -r now
  fi
done