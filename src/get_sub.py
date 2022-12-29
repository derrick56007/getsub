import os
import math
import copy
import codecs
import numpy as np
import srt
import subprocess
import datetime

from utils import mkdir, basename_without_ext
from voice_detector import VoiceDetector
from tqdm import tqdm

def shift_by_delay(bin_arr2, delay_by_frames):
    if delay_by_frames < 0:
        return bin_arr2[abs(delay_by_frames):]

    return np.concatenate([np.zeros(delay_by_frames).astype(np.uint8), bin_arr2])

def make_list_length_equal(lst1, lst2):
    len_lst1 = lst1.shape[0]
    len_lst2 = lst2.shape[0]
    max_len = max(len_lst1, len_lst2)
    return np.concatenate([lst1, np.zeros(max_len - len_lst1).astype(np.uint8)]), np.concatenate([lst2, np.zeros(max_len - len_lst2).astype(np.uint8)])

def error(bin_arr1, bin_arr2):
    # MAE
    return np.sum(bin_arr1.astype(np.uint8) ^ bin_arr2.astype(np.uint8)) / float(len(bin_arr1))


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

    def timedelta_to_frame(self, td):
        ms = float(td.seconds) * 1000.0 + float(td.microseconds) * 0.001
        return int(ms / self.vad.frame_duration_ms)

    def binary_array_from_srt(self, srt_path):
        common_encodings = ['latin1', 'utf-8', 'utf-16', 'cp1252']
        
        subs = []

        for encoding in common_encodings:
            try:
                srt_file = codecs.open(srt_path, 'r', encoding=encoding)
                srt_string = srt_file.read()
                srt_file.close()

                subs = np.array(list(srt.parse(srt_string)))

                break
            except BaseException as error:
            	pass
                # print('An exception occurred: {}'.format(error))

        start_end_pairs = [(self.timedelta_to_frame(sub.start), self.timedelta_to_frame(sub.end)) for sub in subs]

        # convert seconds and microseconds to milliseconds
        first_sub_frame = start_end_pairs[0][0]
        last_sub_frame = start_end_pairs[-1][1]

        bin_array = np.zeros(last_sub_frame).astype(np.uint8)
        
        print('Creating Binary Array from SRT..')

        for start_frame, end_frame in tqdm(start_end_pairs):
            bin_array[start_frame:end_frame] = 1

        # TODO
        five_second_delay = int(5 * 1000 / self.vad.frame_duration_ms)

        # set max delay to 5% of video
        max_delay = max(five_second_delay, int(len(bin_array) * 0.05))

        return bin_array, -first_sub_frame, max_delay, subs

        
    def chunks(self, lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]        

    def find_best_delay_milliseconds(self, bin_arr1, bin_arr2, delay_range_start, delay_range_end, error_csv_out):

        err = math.inf
        best_delay = 0

        delay_range_len = delay_range_end - delay_range_start
        rows = np.zeros((delay_range_len, 2))
        early_stop = False

        print('Finding Best Delay..')
        #with Parallel(n_jobs=cpus, prefer="threads") as parallel:

        for i, delay_by_frames in tqdm(enumerate(range(delay_range_start, delay_range_end)), total=delay_range_len):
            delay_by_frames, tmp_err = get_err(
                bin_arr1, 
                bin_arr2, 
                delay_by_frames, 
            )
            if tmp_err < err:
                err = tmp_err
                best_delay = delay_by_frames

            rows[i][0] = delay_by_frames * self.vad.frame_duration_ms * 0.001
            rows[i][1] = tmp_err

            percent_change = (tmp_err - err) / err

            if percent_change > 0.1:
                early_stop = True
                rows = rows[:(i + 1)]
                break
                   
        if early_stop:
            print('stopping early at', str(int(i / delay_range_len * 100.0)) + '%') 

        #df = pd.DataFrame(rows, columns=["delay_in_seconds", "MAE"])
        #df.set_index("delay_in_seconds", inplace=True)
        #df.to_csv(error_csv_out)

        return best_delay * self.vad.frame_duration_ms

    def align(self, vid_file_path, srt_path, out_dir, original_name):
        bin_arr1 = np.array(list(self.vad.detect(vid_file_path))).astype(np.uint8)
        bin_arr2, delay_range_start, delay_range_end, subs = self.binary_array_from_srt(srt_path)

        best_delay_ms = self.find_best_delay_milliseconds(
            bin_arr1, 
            bin_arr2, 
            delay_range_start, 
            delay_range_end, 
            os.path.join(out_dir, original_name + "_error.csv"),
        )
        best_delay_sec = best_delay_ms * 0.001
        print(f"best delay: {best_delay_sec}s")

        out_path = os.path.join(out_dir, original_name + "_synced.srt")
        
        td_to_shift = datetime.timedelta(seconds=best_delay_sec)

        print('Shifting Subtitles..')
        for subtitle in tqdm(subs):
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
