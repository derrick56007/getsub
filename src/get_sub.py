import os
import math
import copy
import codecs
import numpy as np
import srt
import subprocess
import pandas as pd
import datetime

from utils import mkdir, basename_without_ext
from voice_detector import VoiceDetector
from tqdm import tqdm
from joblib import Parallel, delayed
import multiprocessing

def shift_by_delay(bin_arr2, delay_by_frames):
    if delay_by_frames < 0:
        return bin_arr2[abs(delay_by_frames):]

    return np.concatenate([np.zeros(delay_by_frames), bin_arr2])

def make_list_length_equal(lst1, lst2):
    len_lst1 = lst1.shape[0]
    len_lst2 = lst2.shape[0]
    max_len = max(len_lst1, len_lst2)
    return np.concatenate([lst1, np.zeros(max_len - len_lst1)]), np.concatenate([lst2, np.zeros(max_len - len_lst2)])

def error(bin_arr1, bin_arr2):
    # MAE
    return sum(np.array(bin_arr1).astype(int) ^ np.array(bin_arr2).astype(int)) / float(len(bin_arr1))


def get_err(tmp_bin_arr1, tmp_bin_arr2, delay_by_frames):
    #tmp_bin_arr1 = arr1[:]
    #tmp_bin_arr2 = arr2[:]

    # shift by delay
    tmp_bin_arr2 = shift_by_delay(tmp_bin_arr2, delay_by_frames)

    # align arrays
    tmp_bin_arr1, tmp_bin_arr2 = make_list_length_equal(tmp_bin_arr1, tmp_bin_arr2)

    # calculate error
    tmp_err = error(tmp_bin_arr1, tmp_bin_arr2)

    return delay_by_frames, tmp_err

class GetSub:
    def __init__(self, aggressiveness, frame_duration_ms, padding_duration_ms):
        self.vad = VoiceDetector(
            aggressiveness, frame_duration_ms, padding_duration_ms)

    def make_list_length_equal(self, lst1, lst2):
        len_lst1 = lst1.shape[0]
        len_lst2 = lst2.shape[0]
        max_len = max(len_lst1, len_lst2)
        return np.concatenate([lst1, np.zeros(max_len - len_lst1)]), np.concatenate([lst2, np.zeros(max_len - len_lst2)])

    def timedelta_to_frame(self, td):
        ms = float(td.seconds) * 1000.0 + float(td.microseconds) * 0.001
        return int(ms / self.vad.frame_duration_ms)

    def binary_array_from_srt(self, srt_path):
        common_encodings = ['utf-8', 'latin1', 'utf-16', 'cp1252']

        for encoding in common_encodings:
            try:
                srt_file = codecs.open(srt_path, 'r', encoding=encoding)
                srt_string = srt_file.read()
                srt_file.close()

                subs = np.array(list(srt.parse(srt_string)))

                break
            except BaseException as error:
                print('An exception occurred: {}'.format(error))

        start_end_pairs = [(self.timedelta_to_frame(sub.start), self.timedelta_to_frame(sub.end)) for sub in subs]

        # convert seconds and microseconds to milliseconds
        first_sub_frame = start_end_pairs[0][0]
        last_sub_frame = start_end_pairs[-1][1]

        bin_array = np.zeros(last_sub_frame)
        
        print('Creating Binary Array from SRT..')

        for start_frame, end_frame in tqdm(start_end_pairs):
            bin_array[start_frame:end_frame] = 1

        # TODO
        five_second_delay = int(5 * 1000 / self.vad.frame_duration_ms)

        # set max delay to 5% of video
        max_delay = max(five_second_delay, int(len(bin_array) * 0.05))

        return bin_array, -first_sub_frame, max_delay, subs
        
    def error(self, bin_arr1, bin_arr2):
        # MAE
        return sum(np.array(bin_arr1).astype(int) ^ np.array(bin_arr2).astype(int)) / float(len(bin_arr1))

    def shift_by_delay(self, bin_arr2, delay_by_frames):
        if delay_by_frames < 0:
            return bin_arr2[abs(delay_by_frames):]

        return np.concatenate([np.zeros(delay_by_frames), bin_arr2])
        
    def chunks(self, lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]        

    def find_best_delay_milliseconds(self, bin_arr1, bin_arr2, delay_range_start, delay_range_end):

        err = math.inf
        best_delay = 0

        delay_range_len = delay_range_end - delay_range_start
        rows = np.zeros((delay_range_len, 2))
        cpus = multiprocessing.cpu_count()
        early_stop = False

        print('Finding Best Delay..')
        with Parallel(n_jobs=cpus, prefer="threads") as parallel:
            for i, chunk in tqdm(enumerate(self.chunks(range(delay_range_start, delay_range_end), cpus)), total=delay_range_len//cpus):
                results = parallel(
                    delayed(get_err)(
                        bin_arr1, 
                        bin_arr2, 
                        delay_by_frames, 
                    ) for delay_by_frames in chunk
                )
                
                for j, res in enumerate(results):
                    delay_by_frames, tmp_err = res
                    if tmp_err < err:
                        err = tmp_err
                        best_delay = delay_by_frames

                    rows[i * cpus + j][0] = delay_by_frames * self.vad.frame_duration_ms * 0.001
                    rows[i * cpus + j][1] = tmp_err

                    percent_change = (tmp_err - err) / err

                    if percent_change > 0.1:
                        early_stop = True
                        rows = rows[:(i * cpus + j + 1)]
                        break
                        
                if early_stop:
                    break    
                   
        if early_stop:
            print('stopping early at ', str(int((i * cpus + j) / delay_range_len * 100.0)) + '%') 

        df = pd.DataFrame(rows, columns=["delay_in_seconds", "MAE"])
        df.set_index("delay_in_seconds", inplace=True)

        return best_delay * self.vad.frame_duration_ms, df

    def align(self, vid_file_path, srt_path, out_dir, original_name):
        bin_arr1 = np.array(list(self.vad.detect(vid_file_path)))
        print('bin_arr1', bin_arr1, bin_arr1.shape)
        bin_arr2, delay_range_start, delay_range_end, subs = self.binary_array_from_srt(srt_path)

        best_delay_ms, df = self.find_best_delay_milliseconds(bin_arr1, bin_arr2, delay_range_start, delay_range_end)
        best_delay_sec = best_delay_ms * 0.001
        print("best delay:", best_delay_sec)

        df.to_csv(os.path.join(out_dir, original_name + "_error.csv"))
        out_path = os.path.join(out_dir, original_name + "_synced.srt")
        
        td_to_shift = datetime.timedelta(seconds=best_delay_sec)
        for subtitle in subs:
            subtitle.start += td_to_shift
            subtitle.end += td_to_shift

        with open(out_path, 'w') as file:
            file.write(srt.compose(subs))

        print('output aligned subs to:', out_path)

    def download(self, vid_file_path, language):

        out_dir = os.path.dirname(vid_file_path)
        temp_dir = "/temp/"

        mkdir(out_dir)
        mkdir(temp_dir)

        command1 = "python OpenSubtitlesDownload.py --cli --auto {} --output {} --lang {}"
        command1_list = command1.format(vid_file_path, temp_dir, language).split(" ")
        subprocess.call(command1_list)

        original_name = basename_without_ext(vid_file_path)
        srt_path = os.path.join(temp_dir, original_name + ".srt")

        # save original file as 'filename_unsynced.srt'
        out_path_unsynced = os.path.join(out_dir, original_name + "_unsynced.srt")

        command2 = "cp {} {}"
        command2_list = command2.format(srt_path, out_path_unsynced).split(" ")
        subprocess.call(command2_list)

        print('downloaded subs:', srt_path)

        self.align(vid_file_path, srt_path, out_dir, original_name)
