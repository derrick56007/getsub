import os
import math
import copy
import codecs
import numpy as np
import srt
import subprocess

from utils import mkdir
from ntpath import basename
from voice_detector import VoiceDetector
from subscene import search_with_filename
from progress.bar import Bar

class GetSub:
	def __init__(self, aggressiveness, frame_duration_ms, padding_duration_ms):
		self.vad = VoiceDetector(aggressiveness, frame_duration_ms, padding_duration_ms)

	def make_list_length_equal(self, lst1, lst2):
		len_lst1 = len(lst1)
		len_lst2 = len(lst2)
		max_len = max(len_lst1, len_lst2)
		return list(lst1) + list(np.zeros(max_len - len_lst1).astype(int)), list(lst2) + list(np.zeros(max_len - len_lst2).astype(int))

	def timedelta_to_frame(self, td):
		ms = float(td.seconds) * 1000.0 + float(td.microseconds) * 0.001
		return int(ms / self.vad.frame_duration_ms)

	def binary_array_from_srt(self, srt_path):
		srt_file = codecs.open(srt_path, 'r', encoding='utf-8')
		srt_string = srt_file.read()
		srt_file.close()

		subs = list(srt.parse(srt_string))
		
		start_end_pairs = [(self.timedelta_to_frame(sub.start), self.timedelta_to_frame(sub.end)) for sub in subs]

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
		
		with Bar('Finding Best Delay', max=(delay_range_end - delay_range_start)) as bar:
			for delay_by_frames in range(delay_range_start, delay_range_end):
				tmp_bin_arr1 = copy.copy(bin_arr1)
				tmp_bin_arr2 = copy.copy(bin_arr2)
				
				# shift by delay
				tmp_bin_arr2 = self.shift_by_delay(tmp_bin_arr2, delay_by_frames)
				
				# align arrays
				tmp_bin_arr1, tmp_bin_arr2 = self.make_list_length_equal(tmp_bin_arr1, tmp_bin_arr2)
			
				# calculate error
				tmp_err = self.error(tmp_bin_arr1, tmp_bin_arr2)
				
				if tmp_err < err:
					err = tmp_err
					best_delay = delay_by_frames

				bar.next()
		
		return best_delay * self.vad.frame_duration_ms
		
	def align_subs(self, vid_file_path, srt_path):
		bin_arr1 = list(self.vad.detect(vid_file_path))
		bin_arr2, delay_range_start, delay_range_end = self.binary_array_from_srt(srt_path)
		
		best_delay_ms = self.find_best_delay_milliseconds(bin_arr1, bin_arr2, delay_range_start, delay_range_end)
		best_delay_sec = best_delay_ms * 0.001
		print("best delay:", best_delay_sec)

		out_dir = os.path.dirname(vid_file_path)
		mkdir(out_dir)

		out_path = os.path.join(out_dir, ".".join(basename(srt_path).split(".")[:-1]) + "_synced.srt")

		subprocess.call(["srt", "fixed-timeshift", "--input", srt_path, "--output", out_path, "--seconds", str(best_delay_sec)])
		return out_path

	def download(self, vid_file_path, language):
		srt_path = search_with_filename(vid_file_path, language)

		print('downloaded subs:', srt_path)

		out_path = self.align_subs(vid_file_path, srt_path)

		print('output aligned subs to:', out_path)




