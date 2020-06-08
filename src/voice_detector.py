import os
import sys
import wave
import webrtcvad
import subprocess
import contextlib
import collections
from progress.bar import Bar
from utils import mkdir, basename_without_ext

class Frame:
	""" Represents a 'frame' of audio data"""

	def __init__(self, bytes, timestamp, duration):
		self.bytes = bytes
		self.timestamp = timestamp
		self.duration = duration

class VoiceDetector:

	def __init__(self, aggressiveness, frame_duration_ms, padding_duration_ms):
		self.vad = webrtcvad.Vad(aggressiveness)
		self.frame_duration_ms = frame_duration_ms
		self.padding_duration_ms = padding_duration_ms

	def set_mode(self, aggressiveness):
		self.vad.set_mode(aggressiveness)

	def read_wav(self, path):
		""" Reads a .wav file.

		Takes a path and returns (PCM audio data, sample rate).
		"""

		print("reading .wav")

		with contextlib.closing(wave.open(path, 'rb')) as wf:
			num_channels = wf.getnchannels()
			assert num_channels == 1
			sample_width = wf.getsampwidth()
			assert sample_width == 2
			sample_rate = wf.getframerate()
			assert sample_rate in (8000, 16000, 32000, 48000)
			pcm_data = wf.readframes(wf.getnframes())
			return pcm_data, sample_rate

	def generate_frames(self, audio, sample_rate):
		""" Generates audio frames from PCM (.wav) audio data.

		Takes the desired frame duration in milliseconds, the PCM data, and
		the sample rate.

		Yields Frames of the requested duration.
		"""

		n = int(sample_rate * (self.frame_duration_ms / 1000.0) * 2)
		offset = 0
		timestamp = 0.0
		duration = (float(n) / sample_rate) / 2.0

		with Bar('Creating Frames', max=int(len(audio)/n)) as bar:
			while offset + n < len(audio):
				yield Frame(audio[offset:offset + n], timestamp, duration)
				timestamp += duration
				offset += n
				bar.next()

	def extract_audio(self, in_path):
		out_dir = "temp/"
		mkdir(out_dir)

		file_name = basename_without_ext(in_path) + ".wav"
		out_path = out_dir + file_name

		command = "ffmpeg -nostdin -y -i {} -vn -acodec pcm_s16le -ac 1 -ar 16000 {}"
		command_list = command.format(in_path, out_path).split(" ")
		subprocess.call(command_list)

		print("done extracting")
		return out_path

	def detect(self, vid_file_path):
		""" Detect voice activity given a video file path.

		Yields 1 if speech is detected in a given frame duration, else 0
		"""

		wav_file_path = self.extract_audio(vid_file_path)
		audio, sample_rate = self.read_wav(wav_file_path)
		
		num_padding_frames = int(self.padding_duration_ms / self.frame_duration_ms)
		ring_buffer = collections.deque(maxlen=num_padding_frames)
		triggered = False

		frames = list(self.generate_frames(audio, sample_rate))

		with Bar('Detecting Voice Activity', max=len(frames)) as bar:
			for frame in frames:
				is_speech = self.vad.is_speech(frame.bytes, sample_rate)
				ring_buffer.append((frame, is_speech))

				if not triggered:
					num_voiced = len([f for f, speech in ring_buffer if speech])

					yield 0

					if num_voiced > 0.9 * ring_buffer.maxlen:
						triggered = True
						ring_buffer.clear()

				else:
					num_unvoiced = len([f for f, speech in ring_buffer if not speech])

					yield 1
					
					if num_unvoiced > 0.9 * ring_buffer.maxlen:
						triggered = False
						ring_buffer.clear()

				bar.next()
