#!/bin/sh
SRCPATH=/Volumes/cam/ftp
SAVEPATH=/Volumes/cam/vids
#SAVEPATH=/Users/edrabbit/Pictures/camtest
YESTERDAY=$(date -j -v -1d +"%Y-%m-%d");
YESTERDAYFOLDER=$(date -j -v -1d +"%Y_%m_%d-%Y_%m_%d")
/usr/local/bin/ffmpeg -y -pattern_type glob -i "$SRCPATH/$YESTERDAYFOLDER/*.jpg" -framerate 30 -crf 23 -c:v libx265 -preset medium -tag:v hvc1 $SAVEPATH/$YESTERDAY-timelapse_full_x265_30fps_crf23_hv1_medium.mp4

