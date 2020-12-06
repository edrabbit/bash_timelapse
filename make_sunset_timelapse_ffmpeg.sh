# San Francisco specific
# This grabs all the images for sunset regardles the time of the year. Gets more than it should. I should probably calculate the right range depending on the date.

ffmpeg -pattern_type glob -i "*2020????{16,17,18,19,20}*.jpg" -framerate 30 -crf 23 -c:v libx265 -preset medium -tag:v hvc1 timelapse_partial_x265_30fps_crf23_hv1_medium.mp4