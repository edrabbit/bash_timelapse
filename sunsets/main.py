import astral
from astral.sun import sun, golden_hour, SunDirection
import datetime
import os
import os.path
import natsort


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

    def get_sun_info(self):
        city = astral.LocationInfo("San Francisco", "US", "America/Los_Angeles", 37.754444, -122.4425)
        print((f"Location: {city.name}/{city.region}\n"))
        return sun(city.observer, date=self.date, tzinfo=city.timezone)
        # returns a dict with dawn, sunrise, noon, sunset, dusk

    def get_golden_hour(self):
        city = astral.LocationInfo("San Francisco", "US", "America/Los_Angeles", 37.754444, -122.4425)
        print((f"Location: {city.name}/{city.region}\n"))
        gh = golden_hour(city.observer, self.date, direction=SunDirection.SETTING, tzinfo=city.timezone)
        goldenhour = {'start': gh[0], 'end': gh[1]}
        return goldenhour

    def dt_from_dir(self):
        # Return a datetime.date object by parsing the weird directory name: "2022_03_05-2022_03_05"
        d = [int(x) for x in self.name.split("-")[0].split("_")]
        dt = datetime.date(year=d[0], month=d[1], day=d[2])
        return dt

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
    all_dirs = get_all_directories()
    print("pause")
    for d in all_dirs:
        print(d)
        print("pause")



