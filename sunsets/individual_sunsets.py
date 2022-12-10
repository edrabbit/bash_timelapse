import datetime
import os
import subprocess

def create_one_day_timelapse(date=None, source_dir=None, output_file=None):
    # date is a datetime object
    if date:
        tl_date = date.strftime("%Y%m%d")
        print(tl_date)
        file_mask = f"{tl_date}*.jpg"
    else:
        file_mask = "*.jpg"
    input = os.path.join(source_dir,file_mask)
    framerate = 30
    crf = 23
    preset = "medium"
    #output_file = "timelapse_full_x265_30fps_crf23_hv1_medium.mp4"
    ff_cmd = ["ffmpeg",
              "-y", # THIS WILL FORCE OVERWRITE. PROBABLY WANT TO REMOVE FOR THE FUTURE TO PREVENT DUPLICATE WORK
              "-pattern_type", "glob",
              "-i", f'{input}',
              "-framerate",f"{framerate}",
              "-crf",f"{crf}",
              "-c:v","libx265",
              "-preset",f"{preset}",
              "-tag:v","hvc1",
              f"{output_file}"]
    print(ff_cmd)
    subprocess.run(ff_cmd)


if __name__ == '__main__':
    # 20211209164335395_TIMING
    # ffmpeg -pattern_type glob -i "*.jpg" -framerate 30 -crf 23 -c:v libx265 -preset medium -tag:v hvc1 timelapse_full_x265_30fps_crf23_hv1_medium.mp4
    #date = datetime.date(2022, 12, 6)
    output_path = "/Volumes/Timelapse/sunsets/"

    first_day = datetime.date(2022, 1, 1)
    last_day = datetime.date(2022, 12, 6)
    date = first_day
    while date <= last_day:
        outfile = os.path.join(output_path,f'{date.strftime("%Y%m%d")}.mp4')
        create_one_day_timelapse(date=date, source_dir="/Volumes/Timelapse/sunset_files/", output_file=outfile)
        date += datetime.timedelta(days=1)
