import os
import math
import copy
import codecs
import numpy as np
import srt
import subprocess
import pandas as pd

from utils import mkdir, basename_without_ext
from voice_detector import VoiceDetector
from progress.bar import Bar


class GetSub:
    def __init__(self, aggressiveness, frame_duration_ms, padding_duration_ms):
        self.vad = VoiceDetector(
            aggressiveness, frame_duration_ms, padding_duration_ms)

    def make_list_length_equal(self, lst1, lst2):
        len_lst1 = len(lst1)
        len_lst2 = len(lst2)
        max_len = max(len_lst1, len_lst2)
        return list(lst1) + list(np.zeros(max_len - len_lst1).astype(int)), list(lst2) + list(np.zeros(max_len - len_lst2).astype(int))

    def timedelta_to_frame(self, td):
        ms = float(td.seconds) * 1000.0 + float(td.microseconds) * 0.001
        return int(ms / self.vad.frame_duration_ms)

    def binary_array_from_srt(self, srt_path):
        common_encodings = ['utf-8', 'utf-16', 'cp1252']

        for encoding in common_encodings:
            try:
                srt_file = codecs.open(srt_path, 'r', encoding=encoding)
                srt_string = srt_file.read()
                srt_file.close()

                subs = list(srt.parse(srt_string))

                break
            except BaseException as error:
                print('An exception occurred: {}'.format(error))

        start_end_pairs = [(self.timedelta_to_frame(
            sub.start), self.timedelta_to_frame(sub.end)) for sub in subs]

        # convert seconds and microseconds to milliseconds
        first_sub_frame = start_end_pairs[0][0]
        last_sub_frame = start_end_pairs[-1][1]

        bin_array = np.zeros(last_sub_frame)

        with Bar('Creating Binary Array from SRT', max=len(start_end_pairs)) as bar:
            for start_frame, end_frame in start_end_pairs:
                for i in range(start_frame, end_frame):
                    bin_array[i] = 1
                bar.next()

        # TODO
        five_second_delay = int(5 * 1000 / self.vad.frame_duration_ms)

        # set max delay to 5% of video
        max_delay = max(five_second_delay, int(len(bin_array) * 0.05))

        return bin_array, -first_sub_frame, max_delay

    def error(self, bin_arr1, bin_arr2):
        # MAE
        return sum(np.array(bin_arr1).astype(int) ^ np.array(bin_arr2).astype(int)) / float(len(bin_arr1))

    def shift_by_delay(self, bin_arr2, delay_by_frames):
        if delay_by_frames < 0:
            return bin_arr2[abs(delay_by_frames):]

        return list(np.zeros(delay_by_frames).astype(int)) + list(bin_arr2)

    def find_best_delay_milliseconds(self, bin_arr1, bin_arr2, delay_range_start, delay_range_end):

        err = math.inf
        best_delay = 0

        delay_range_len = delay_range_end - delay_range_start
        rows = np.zeros((delay_range_len, 2))

        with Bar('Finding Best Delay', max=delay_range_len) as bar:
            for i, delay_by_frames in enumerate(range(delay_range_start, delay_range_end)):
                tmp_bin_arr1 = copy.copy(bin_arr1)
                tmp_bin_arr2 = copy.copy(bin_arr2)

                # shift by delay
                tmp_bin_arr2 = self.shift_by_delay(
                    tmp_bin_arr2, delay_by_frames)

                # align arrays
                tmp_bin_arr1, tmp_bin_arr2 = self.make_list_length_equal(
                    tmp_bin_arr1, tmp_bin_arr2)

                # calculate error
                tmp_err = self.error(tmp_bin_arr1, tmp_bin_arr2)

                if tmp_err < err:
                    err = tmp_err
                    best_delay = delay_by_frames

                rows[i][0] = delay_by_frames * \
                    self.vad.frame_duration_ms * 0.001
                rows[i][1] = tmp_err

                bar.next()

                percent_change = (tmp_err - err) / err

                if percent_change > 0.1:
                    print('')
                    print('stopping early at ', str(
                        int(i / delay_range_len * 100.0)) + '%')

                    rows = rows[:(i + 1)]
                    break

        df = pd.DataFrame(rows, columns=["delay_in_seconds", "MAE"])
        df.set_index("delay_in_seconds", inplace=True)

        return best_delay * self.vad.frame_duration_ms, df

    def align(self, vid_file_path, srt_path, out_dir, original_name):
        bin_arr1 = list(self.vad.detect(vid_file_path))
        bin_arr2, delay_range_start, delay_range_end = self.binary_array_from_srt(
            srt_path)

        best_delay_ms, df = self.find_best_delay_milliseconds(
            bin_arr1, bin_arr2, delay_range_start, delay_range_end)
        best_delay_sec = best_delay_ms * 0.001
        print("best delay:", best_delay_sec)

        df.to_csv(os.path.join(out_dir, original_name + "_error.csv"))
        out_path = os.path.join(out_dir, original_name + "_synced.srt")

        command = "srt fixed-timeshift --input {} --output {} --seconds {}"
        command_list = command.format(
            srt_path, out_path, best_delay_sec).split(" ")

        subprocess.call(command_list)

        print('output aligned subs to:', out_path)

    def download(self, vid_file_path, language):

        out_dir = os.path.dirname(vid_file_path)
        temp_dir = "temp/"

        mkdir(out_dir)
        mkdir(temp_dir)

        command1 = "python OpenSubtitlesDownload.py --cli --auto {} --output {} --lang {}"
        command1_list = command1.format(
            vid_file_path, temp_dir, language).split(" ")
        subprocess.call(command1_list)

        original_name = basename_without_ext(vid_file_path)
        srt_path = os.path.join(temp_dir, original_name + ".srt")

        # save original file as 'filename_unsynced.srt'
        out_path_unsynced = os.path.join(
            out_dir, original_name + "_unsynced.srt")

        command2 = "srt fixed-timeshift --input {} --output {} --seconds 0"
        command2_list = command2.format(
            srt_path, out_path_unsynced).split(" ")
        subprocess.call(command2_list)

        print('downloaded subs:', srt_path)

        self.align(vid_file_path, srt_path, out_dir, original_name)
