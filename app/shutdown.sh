#!/usr/bin/env sh

if [ "$1" = "-r" ]; then
  shutdown -r
fi
if [ "$1" = "-h" ]; then
  shutdown -h now
fi