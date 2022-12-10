import astral
from astral.sun import sun, golden_hour, SunDirection
import datetime
import glob
import os
import os.path
import natsort
import shutil



class TLDirectory:
    # My timelapse camera makes weird directory names and filenames. This class helps parse it
    # directory name: 2022_03_05-2022_03_05
    # filenames from timelapse cam: 192.168.1.99_01_20220305235955789_TIMING.jpg

    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.date = self.dt_from_dir() # datetime.date
        self.sun = self.get_sun_info() # dict with dawn, sunrise, noon, sunset, dusk
        self.goldenhour = self.get_golden_hour() #dict with 'start' and 'end' for golden hour
        self.sunset_files = None

    def get_sun_info(self):
        city = astral.LocationInfo("San Francisco", "US", "America/Los_Angeles", 37.754444, -122.4425)
        return sun(city.observer, date=self.date, tzinfo=city.timezone)
        # returns a dict with dawn, sunrise, noon, sunset, dusk

    def get_golden_hour(self):
        city = astral.LocationInfo("San Francisco", "US", "America/Los_Angeles", 37.754444, -122.4425)
        gh = golden_hour(city.observer, self.date, direction=SunDirection.SETTING, tzinfo=city.timezone)
        goldenhour = {'start': gh[0], 'end': gh[1]}
        return goldenhour

    def dt_from_dir(self):
        # Return a datetime.date object by parsing the weird directory name: "2022_03_05-2022_03_05"
        d = [int(x) for x in self.name.split("-")[0].split("_")]
        dt = datetime.date(year=d[0], month=d[1], day=d[2])
        return dt

    def get_sunset_images(self, number_of_minutes=1):
        # number_of_minutes is the total number of minutes worth of frames to return,
        # with the sunset in the middle
        # Filenames from timelapse cam: 192.168.1.99_01_20220305235955789_TIMING.jpg
        # older ones have 192.168.1.208
        # At first I was using glob in here to get actual filenames acorss the network
        # but that's hella slow, so lets just put together the list of wildcards and
        # leave the network calls in other functions

        # We're doing shots every 10 seconds it looks like? So this should return multiple files
        # If we ever move to >60 seconds, this won't work
        s = self.sun["sunset"].strftime("%Y%m%d%H%M")
        file_prefix = "*_01_"+s+"*.jpg"
        # for 5 minutes before and 5 minutes after, grab each shot for each minute. Do we want to go down and grab each shot for seconds?
        s_before = self.sun["sunset"] + datetime.timedelta(minutes=(0-int(number_of_minutes/2)))
        s_after = self.sun["sunset"] + datetime.timedelta(minutes=int(number_of_minutes/2))
        files = []
        i = s_before
        while i <= s_after:
            file_prefix = "*_01_"+i.strftime("%Y%m%d%H%M%S")[:-1]+"*.jpg" #strip off the ones place for seconds
            files.append(os.path.join(self.path, file_prefix))
            i = i + datetime.timedelta(seconds=10)

        if not files:
            raise Exception("No sunset images found")
        self.sunset_files = files


def get_all_directories(path="/Volumes/cam/ftp", last_x_days=0):
    # Return a list of TLDirectory objects for all the directories in 'path'
    list_subfolders= [f.path for f in os.scandir(path) if f.is_dir()] # full path
    _subfolders = natsort.natsorted(list_subfolders)
    all_dirs = []
    if last_x_days:
        subfolders = _subfolders[(0-last_x_days):]
    else:
        subfolders = _subfolders
    for path in subfolders:
        tld = TLDirectory(path)
        all_dirs.append(tld)
    return all_dirs

if __name__ == '__main__':
    number_of_minutes = 15
    all_dirs = get_all_directories(path="/Volumes/Timelapse/ftp", last_x_days=0) # this should only have timelapse subdirs, other shit breaks it
    # move the sunset files into a folder
    dest = "/Volumes/Timelapse/sunset_files"
    # get a list of local files already downloaded
    dest_file_list = os.listdir(dest)
    if not os.path.exists(dest):
        os.mkdir(dest)
    i = 0
    dir_count = len(all_dirs)
    for d in all_dirs:
        i+=1
        print(f"Processing: [{i}/{dir_count}] {d.path}")
        d.get_sunset_images(number_of_minutes=number_of_minutes)
        sunset_for_the_day = d.sun["sunset"].strftime("%Y%m%d%H%M")
        print(f'..Sunset was at {sunset_for_the_day}')
        # Check to see how many sunset images were downloaded for this day to see if we need to check it
        res = list(filter(lambda x: sunset_for_the_day[:8] in x, dest_file_list))
        expected_num_files = len(d.sunset_files)
        if len(res) >= expected_num_files:
            print(f'..Found {len(res)}/{expected_num_files} frames, skipping..')
        else:
            print(f'..Expected {expected_num_files} images found {len(res)}, downloading..')
            i=1
            for f in d.sunset_files:
# IndexError: list index out of range
                try:
                    fpath = glob.glob(f)[0]
                except IndexError:
                    print(f"  Did not find {f}")
                    continue
                clean_dest_fname = fpath.split("/")[-1].replace("192.168.1.99_01_","")
                dest_path = os.path.join(dest, clean_dest_fname)
                if not os.path.exists(dest_path):
                    print(f"  [{i}/{expected_num_files}] Copying {fpath} to {dest_path}")
                    shutil.copy(fpath, dest_path)
                else:
                    print(f"  [{i}/{expected_num_files}] Skipping {fpath}")
                i+=1
                #break # just do one image
