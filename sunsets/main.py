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
        self.date = self.dt_from_dir()  # datetime.date
        self.sun = self.get_sun_info()  # dict with dawn, sunrise, noon, sunset, dusk
        self.goldenhour = self.get_golden_hour()  # dict with 'start' and 'end' for golden hour
        self.middle_of_golden_hour = self.get_middle_of_golden_hour()
        self.event_files = {"sunrise": None,
                            "sunset": None,
                            "goldenhour": None
                            }

    def get_sun_info(self):
        city = astral.LocationInfo("San Francisco", "US", "America/Los_Angeles", 37.754444, -122.4425)
        return sun(city.observer, date=self.date, tzinfo=city.timezone)
        # returns a dict with dawn, sunrise, noon, sunset, dusk

    def get_golden_hour(self):
        city = astral.LocationInfo("San Francisco", "US", "America/Los_Angeles", 37.754444, -122.4425)
        gh = golden_hour(city.observer, self.date, direction=SunDirection.SETTING, tzinfo=city.timezone)
        goldenhour = {'start': gh[0], 'end': gh[1]}
        return goldenhour

    def get_middle_of_golden_hour(self):
        gh_span = self.goldenhour # golden hour has a start and end time
        length_of_gh = gh_span["end"]-gh_span["start"]
        gh_middle = gh_span["start"] + length_of_gh/2
        return gh_middle


    def dt_from_dir(self):
        # Return a datetime.date object by parsing the weird directory name: "2022_03_05-2022_03_05"
        d = [int(x) for x in self.name.split("-")[0].split("_")]
        dt = datetime.date(year=d[0], month=d[1], day=d[2])
        return dt

    def get_sunset_images(self, number_of_minutes=1):
        # SHOULD BE DEPRECATED WITH get_event_images
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
        file_prefix = "*_01_" + s + "*.jpg"
        # for 5 minutes before and 5 minutes after, grab each shot for each minute. Do we want to go down and grab each shot for seconds?
        s_before = self.sun["sunset"] + datetime.timedelta(minutes=(0 - int(number_of_minutes / 2)))
        s_after = self.sun["sunset"] + datetime.timedelta(minutes=int(number_of_minutes / 2))
        files = []
        i = s_before
        while i <= s_after:
            file_prefix = "*_01_" + i.strftime("%Y%m%d%H%M%S")[:-1] + "*.jpg"  # strip off the ones place for seconds
            files.append(os.path.join(self.path, file_prefix))
            i = i + datetime.timedelta(seconds=10)

        if not files:
            raise Exception("No sunset images found")
        self.sunset_files = files

    def get_event_images(self, event="sunset", number_of_minutes=1):
        # number_of_minutes is the total number of minutes worth of frames to return,
        # with the event in the middle
        # Filenames from timelapse cam: 192.168.1.99_01_20220305235955789_TIMING.jpg
        # older ones have 192.168.1.208
        # At first I was using glob in here to get actual filenames across the network
        # but that's hella slow, so lets just put together the list of wildcards and
        # leave the network calls in other functions

        # We're doing shots every 10 seconds it looks like? So this should return multiple files
        # If we ever move to >60 seconds, this won't work
        if event == "goldenhour":
            gh_span = self.get_golden_hour() # golden hour has a start and end time
                #.strftime("%Y%m%d%H%M")
            length_of_gh = gh_span["end"]-gh_span["start"]
            gh_middle = gh_span["start"] + length_of_gh/2
            s = gh_middle.strftime("%Y%m%d%H%M")
            file_prefix = "*_01_" + s + "*.jpg"
            if number_of_minutes == 1:
                number_of_minutes = 60  # Assume that we want the full golden hour unless otherwise specified
            s_before = gh_middle + datetime.timedelta(minutes=(0 - int(number_of_minutes / 2)))
            s_after = gh_middle + datetime.timedelta(minutes=int(number_of_minutes / 2))
        else:
            s = self.sun[event].strftime("%Y%m%d%H%M")
            file_prefix = "*_01_" + s + "*.jpg"
            s_before = self.sun[event] + datetime.timedelta(minutes=(0 - int(number_of_minutes / 2)))
            s_after = self.sun[event] + datetime.timedelta(minutes=int(number_of_minutes / 2))
        files = []
        i = s_before
        while i <= s_after:
            file_prefix = "*_01_" + i.strftime("%Y%m%d%H%M%S")[:-1] + "*.jpg"  # strip off the ones place for seconds
            files.append(os.path.join(self.path, file_prefix))
            i = i + datetime.timedelta(seconds=10)

        if not files:
            raise Exception(f"No {event} images found")
        self.event_files[event] = files


def get_all_directories(path="/Volumes/cam/ftp", last_x_days=0):
    # Return a list of TLDirectory objects for all the directories in 'path'
    list_subfolders = [f.path for f in os.scandir(path) if f.is_dir()]  # full path
    _subfolders = natsort.natsorted(list_subfolders)
    all_dirs = []
    if last_x_days:
        subfolders = _subfolders[(0 - last_x_days):]
    else:
        subfolders = _subfolders
    for path in subfolders:
        tld = TLDirectory(path)
        all_dirs.append(tld)
    return all_dirs


def copy_all_files(source_dir="/Volumes/Timelapse/ftp",
                   dest_dir="/Volumes/Timelapse/sunset_files",
                   event="sunset",
                   number_of_minutes=15, last_x_days=0):
    """Copy subset of files from directories in source_dir to dest_dir
    :param event: sunrise, goldenhour, or sunset. Default: sunset
    """
    all_dirs = get_all_directories(path=source_dir,
                                   last_x_days=last_x_days)  # this should only have timelapse subdirs, other shit breaks it
    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)
    dest_file_list = os.listdir(dest_dir)  # get a list of local files already downloaded
    missing_files = []
    i = 0
    dir_count = len(all_dirs)
    for d in all_dirs:
        i += 1
        print(f"Processing: [{i}/{dir_count}] {d.path}")
        # Skip 2020 because I took pictures at a different frequency
        if "2020" in os.path.basename(d.path):
            print("Skipping 2020")
            continue
        # Skip 2021 because it's already done
        if "2021" in os.path.basename(d.path):
            print("Skipping 2021")
            continue
        d.get_event_images(event=event, number_of_minutes=number_of_minutes)
        if event == "goldenhour":
            event_for_the_day = d.middle_of_golden_hour.strftime("%Y%m%d%H%M")
        else:
            event_for_the_day = d.sun[event].strftime("%Y%m%d%H%M")

        print(f'..{event} was at {event_for_the_day}')
        # Check to see how many images were downloaded for this day's event to see if we need to check it
        res = list(filter(lambda x: event_for_the_day[:8] in x, dest_file_list))
        expected_num_files = len(d.event_files[event])
        if len(res) >= expected_num_files:
            print(f'..Found {len(res)}/{expected_num_files} frames, skipping..')
        else:
            print(f'..Expected {expected_num_files} images found {len(res)}, downloading..')
            ii = 1
            for f in d.event_files[event]:
                try:
                    fpath = glob.glob(f)[0]
                except IndexError:
                    print(f"  Did not find {f}")
                    missing_files.append(f)
                    continue
                clean_dest_fname = fpath.split("/")[-1].replace("192.168.1.99_01_", "")
                dest_path = os.path.join(dest_dir, clean_dest_fname)
                if not os.path.exists(dest_path):
                    print(f"  [{ii}/{expected_num_files}] Copying {fpath} to {dest_path}")
                    shutil.copy(fpath, dest_path)
                else:
                    print(f"  [{ii}/{expected_num_files}] Skipping {fpath}")
                ii += 1
                # break # just do one image
            if missing_files:
                print("Not all expected files were found. Missing the following:")
                for x in missing_files:
                    print(x)


if __name__ == '__main__':
    # Copy the subset of files for the event into the dest_dir
    # defaults to 15 minutes worth of images for the event
    copy_all_files(dest_dir="/Volumes/Timelapse/event_test_files", event="goldenhour")
