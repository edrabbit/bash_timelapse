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

    def get_sunset_images(self):
        # filenames from timelapse cam: 192.168.1.99_01_20220305235955789_TIMING.jpg
        # older ones have 192.168.1.208
        #print(f'Date: {dir.date}')
        #print(f'Sunset should be at {dir.sun["sunset"]}')
        # We're doing shots every 10 seconds it looks like? So this should return multiple files
        # If we ever move to >60 seconds, this won't work
        s = self.sun["sunset"].strftime("%Y%m%d%H%M")
        file_prefix = "*_01_"+s+"*.jpg"
        #print(file_prefix)
        files = natsort.natsorted(
            glob.glob(os.path.join(self.path, file_prefix)))
        if not files:
            raise Exception("No sunset images found")
        self.sunset_files = files
        # currently this is "full" paths, but actually just relative

class TLFiles:
    def __init__(self, tldirectory):
        # tldirectory is a TLDirectory object
        self.tldirectory = tldirectory
# is this really what I want?



def get_all_directories(path="/Volumes/cam/ftp"):
    # Return a list of TLDirectory objects for all the directories in 'path'
    list_subfolders= [f.path for f in os.scandir(path) if f.is_dir()] # full path
    subfolders = natsort.natsorted(list_subfolders)
    all_dirs = []
    for path in subfolders:
        tld = TLDirectory(path)
        all_dirs.append(tld)
    return all_dirs

if __name__ == '__main__':
    all_dirs = get_all_directories() # this should only have timelapse subdirs, other shit breaks it
    # move the sunset files into a folder
    dest = "sunset_files"

    for d in all_dirs:
        print(f"Processing: {d.path}")
        d.get_sunset_images()
        for f in d.sunset_files:
            dest_path = os.path.join(dest, f.split("/")[-1])
            if not os.path.exists(dest_path):
                print(f"  Copying {f} to {dest_path}")
                shutil.copy(f, dest_path)
            else:
                print(f"  Skipping {f}")



