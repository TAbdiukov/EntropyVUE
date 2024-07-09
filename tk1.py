

import tkinter as tk
import random
from tkinter import filedialog

from math import log2, log10

# Fast IO
import mmap

import argparse

ALPHABET = 256
MAX_HEIGHT = 100

class SmartBar:
	def __init__(self, id, height, width=1, scale=1):
		self.id = id
		self.height = height
		self.width = width
		self.scale = scale


class Chart:
	def __init__(self, canvas, smart_bars, fill="blue", outline="pink", padding=10, scale=1, aspect_ratio=1):
		self.canvas = canvas
		self.smart_bars = smart_bars
		self.padding = padding
		self.fill = fill
		self.outline = outline
		self.scale = scale
		self.aspect_ratio = aspect_ratio

	def draw(self):
		for bar in self.smart_bars:
			self.canvas.create_rectangle(bar.id * self.scale * self.aspect_ratio,
										  (MAX_HEIGHT - bar.height) * self.scale,
										  (bar.id + bar.width) * self.scale * self.aspect_ratio,
										  MAX_HEIGHT * self.scale,
										  fill = self.fill,
										  outline = self.outline)

	def flush(self):
		self.canvas.delete('all')

class FileResearchProcessor:
	def __init__(self, filename):
		self.filename = filename
		self.listing = [0]*ALPHABET

		self.entropy_dict = {}

	strategies = {
		'normal': {"human_readable": "Normalized", 'func': '_calculate_normalized_entropy'},
		'shannon': {"human_readable": "Shannon", 'func': '_calculate_shannon_entropy'},
		'log2→shannon': {"human_readable": "Shannon of Log2", 'func': '_calculate_entropy_log2_shannon'},
		'log2→normal': {"human_readable": "Normalized of Log2", 'func': '_calculate_entropy_log2_normalized'},
		'log10→normal': {"human_readable": "Normalized of Log10", 'func': '_calculate_entropy_log10_normalized'}
	}

	def process_file(self):
		with open(self.filename, 'rb') as f:
			mmapped_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
			for byte in mmapped_file:
				self.listing[byte[0] % ALPHABET] += 1
			mmapped_file.close()

	def _calculate_normalized_entropy(self):
		MODE = 1
		dataset = self.listing.copy()

		# Normalize
		c = 0
		entropy = 0
		for b in range(ALPHABET):
			c = max(c, dataset[b])
		c = 1 if c == 0 else c

		for b in range(ALPHABET):
			dataset[b] = round(dataset[b] / c * 100)

		for b in range(ALPHABET):
			entropy += dataset[b]

		entropy = round(entropy / ALPHABET, 2)

		return entropy, dataset

	def _calculate_shannon_entropy(self):
		byte_frequencies = self.listing.copy()

		# Calculate total number of bytes
		total_bytes = sum(byte_frequencies)

		# Calculate entropy for each byte
		dataset = []

		# Iterate over each frequency in byte_frequencies
		for freq in byte_frequencies:
			# Check if the frequency is greater than 0
			if freq > 0:
				# Calculate the probability
				prob = freq / total_bytes
				# Calculate the value and append it to the dataset
				value = -prob * log2(prob) * 100
				dataset.append(value)
			else:
				# If the frequency is not greater than 0, append 0 to the dataset
				dataset.append(0)

		# Calculate overall entropy
		entropy = sum(dataset)/100

		return entropy, dataset


	def _calculate_entropy_log2_shannon(self):
		byte_frequencies = self.listing.copy()
		total_bytes = sum(byte_frequencies)

		for b in range(ALPHABET):
			byte_frequencies[b] = round(log2(byte_frequencies[b] + 1) * 100)

		# Calculate entropy for each byte
		dataset = []

		# Iterate over each frequency in byte_frequencies
		for freq in byte_frequencies:
			# Check if the frequency is greater than 0
			if freq > 0:
				# Calculate the probability
				prob = freq / total_bytes
				# Calculate the value and append it to the dataset
				value = -prob * log2(prob) * 100
				dataset.append(value)
			else:
				# If the frequency is not greater than 0, append 0 to the dataset
				dataset.append(0)

		# Calculate overall entropy
		entropy = sum(dataset)/100

		return entropy, dataset

	def _calculate_entropy_log2_normalized(self):
		a = self.listing.copy()
		dataset = [0]*ALPHABET

		for b in range(ALPHABET):
			dataset[b] = round(log2(a[b] + 1) * 100)

		# Normalize
		c = 0
		entropy = 0
		for b in range(ALPHABET):
			c = max(c, dataset[b])
		c = 1 if c == 0 else c

		for b in range(ALPHABET):
			dataset[b] = dataset[b] / c * 100

		for b in range(ALPHABET):
			entropy += dataset[b]

		entropy = entropy / ALPHABET

		return entropy, dataset

	def _calculate_entropy_log10_normalized(self):
		a = self.listing.copy()
		dataset = [0]*ALPHABET

		for b in range(ALPHABET):
			dataset[b] = round(log10(a[b] + 1) * 100)

		# Normalize
		c = 0
		entropy = 0
		for b in range(ALPHABET):
			c = max(c, dataset[b])
		c = 1 if c == 0 else c

		for b in range(ALPHABET):
			dataset[b] = dataset[b] / c * 100

		for b in range(ALPHABET):
			entropy += dataset[b]

		entropy = entropy / ALPHABET

		return entropy, dataset

	def calculate_all_entropy(self):
		for name, strategy in self.strategies.items():
			entropy, dataset = getattr(self, strategy['func'])()
			self.entropy_dict[name] = {
				'human_readable': strategy['human_readable'],
				'entropy': entropy,
				'dataset': dataset
			}

	@classmethod
	def map_human_readable_to_machine_strategies(cls):
		return {strategy['human_readable']: name for name, strategy in cls.strategies.items()}

	def entropies_to_short_string(self):
		entropy_str = ""
		for entropy_type, entropy_data in self.entropy_dict.items():
			entropy_value = round(entropy_data['entropy'], 2)
			entropy_str += f"Entropy type: {entropy_type}, Entropy: {entropy_value}%\n"
		return entropy_str

class AnalyzerContext:
	def __init__(self):
		self.chart = None
		self.file_path = None
		self.processor = None
		self.entropy_string = None
		self.smart_bars = None
		self.canvas = None
		self.label = None
		self.status_bar = None
		self.selected_option = None

		self.scale = 3
		self.aspect_ratio = 1

		self.dark_mode = True
		self.color_bg = "black"
		self.color_bars_fill = "red"
		self.color_bars_outline = "green"

	def toggle_mode(self):
		self.dark_mode = not self.dark_mode
		if self.dark_mode:
			self.color_bg = 'black'  # Black is highly visible in dark mode
			self.color_bars_fill = 'red'  # White is highly visible in dark mode
			self.color_bars_outline = 'green'  # Yellow is highly visible in dark mode
		else:
			self.color_bg = 'lightgray'  # White is highly visible in light mode
			self.color_bars_fill = 'red'  # Blue is highly visible in light mode
			self.color_bars_outline = 'black'  # Black is highly visible in light mode

		self.canvas.configure(bg=self.color_bg)

		self.draw_from_option()

	def draw_chart(self, data, scale=1, aspect_ratio=1, flush=False):
		smart_bars = []
		for i in range(ALPHABET):
			bar = SmartBar(i, data[i], scale=scale)
			smart_bars.append(bar)
		if flush and self.chart:
			self.chart.flush()
		self.chart = Chart(self.canvas, smart_bars, scale=scale, aspect_ratio=aspect_ratio,
			fill=self.color_bars_fill, outline=self.color_bars_outline)
		self.chart.draw()

	def update_label(self, event):
		try:
			bar = self.chart.smart_bars[int(event.x // (self.scale * self.aspect_ratio))]
			display_height = round(bar.height, 2)
			self.label.config(text=f"Bar ID: {bar.id}, Height: {display_height}")
		except IndexError as e:
			pass

	def open_file(self):
		if not self.file_path:
			return
		self.processor = FileResearchProcessor(self.file_path)
		self.processor.process_file()
		self.processor.calculate_all_entropy()
		self.entropy_string = self.processor.entropies_to_short_string()
		self.status_bar.config(text=f"Loaded file: {self.file_path}\n{self.entropy_string}")
		self.draw_from_option()

	def open_file_interactive(self):
		self.file_path = filedialog.askopenfilename()
		self.open_file()

	def draw_from_option(self):
		if not self.file_path:
			return
		datapick = self.processor.entropy_dict[options.get(self.selected_option.get(),"normal")]
		self.smart_bars = datapick['dataset']
		self.draw_chart(self.smart_bars, self.scale, self.aspect_ratio, flush=True)

	def demo(self):
		data = [0]*ALPHABET
		for i in range(ALPHABET):
			data[i] = random.randint(i//3,MAX_HEIGHT)
		self.draw_chart(data, self.scale, self.aspect_ratio)

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Calculate entropies...')
	parser.add_argument('-f', '--file', dest='file_path', help='The path to the file to be analyzed')
	args = parser.parse_args()

	window = tk.Tk()
	context = AnalyzerContext()
	context.canvas = tk.Canvas(window, width=ALPHABET*context.scale*context.aspect_ratio, height=MAX_HEIGHT*context.scale,bg=context.color_bg)
	context.demo()
	context.label = tk.Label(window, text="")
	context.label.pack()
	context.canvas.bind("<Motion>", context.update_label)
	context.canvas.pack()
	context.status_bar = tk.Label(window, text="Please load a file", bd=1, relief=tk.SUNKEN, anchor=tk.W)
	context.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
	button = tk.Button(window, text="Select File", command=context.open_file_interactive)
	button.pack(side=tk.RIGHT)
	options = FileResearchProcessor.map_human_readable_to_machine_strategies()
	context.selected_option = tk.StringVar(window)
	context.selected_option.set("Normalized")
	toggle_button = tk.Button(window, text="◐", command=context.toggle_mode)
	toggle_button.pack(side=tk.RIGHT)
	option_menu = tk.OptionMenu(window, context.selected_option, *options, command=lambda _: context.draw_from_option())
	option_menu.pack(side=tk.LEFT)

	if args.file_path:
		context.file_path = args.file_path
		context.open_file()

	window.mainloop()
