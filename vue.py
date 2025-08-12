#!/usr/bin/env python
# -*- coding: utf8 -*-

import tkinter as tk
from tkinter import filedialog

import argparse
from math import log2, log10, ceil
import random

# IO and file system
import os
import threading

# for less overhead, fewer attributes, clearer intent
from dataclasses import dataclass

ALPHABET = 256
MAX_HEIGHT = 100

@dataclass(slots=True)
class SmartBar:
	id: int
	height: float
	width: int = 1
	scale: float = 1.0

class Chart:
	def __init__(self, canvas, smart_bars, plot_height, fill="blue",
				 outline="pink", padding=5, scale=1, aspect_ratio=1):
		self.canvas = canvas
		self.smart_bars = smart_bars
		self.plot_height = plot_height
		self.padding = padding
		self.fill = fill
		self.outline = outline
		self.scale = scale
		self.aspect_ratio = aspect_ratio

	def draw(self):
		pad = self.padding
		for bar in self.smart_bars:
			x0 = pad + bar.id * self.scale * self.aspect_ratio
			y0 = (self.plot_height - bar.height) * self.scale
			x1 = pad + (bar.id + bar.width) * self.scale * self.aspect_ratio
			y1 = self.plot_height * self.scale
			self.canvas.create_rectangle(x0, y0, x1, y1, fill=self.fill, outline=self.outline)

	def flush(self):
		self.canvas.delete('all')

class FileResearchProcessor:
	strategies = {
		'normalized(in)': {"human_readable": "Normalized entropy of input", 'func': '_calculate_normalized_entropy'},
		'normalized[log2(in)]': {"human_readable": "Normalized entropy of Log2 of input", 'func': '_calculate_entropy_log2_normalized'},
		'normalized[log10(in)]': {"human_readable": "Normalized entropy of Log10 of input", 'func': '_calculate_entropy_log10_normalized'},
		'shannon(in)': {"human_readable": "Shannon entropy of input", 'func': '_calculate_shannon_entropy'},
		'shannon[log2(in)]': {"human_readable": "Shannon entropy of Log2 of input", 'func': '_calculate_entropy_log2_shannon'}
	}

	def __init__(self, filename):
		self.filename = filename
		self.listing = [0] * ALPHABET

		self.entropy_dict = {}

	def process_file(self, progress_callback=None):
		self.listing = [0] * ALPHABET
		try:
			total_size = os.path.getsize(self.filename)
			if total_size == 0:
				if progress_callback:
					progress_callback(100.0)
				return

			with open(self.filename, 'rb') as f:
				chunk_size= 1 << 22  # 4MB chunks
				processed = 0

				while True:
					chunk = f.read(chunk_size)
					if not chunk:
						break

					# Process chunk
					N = len(self.listing)  # == ALPHABET
					if N <= 0:
						raise ValueError("ALPHABET must be at least 1")

					for byte in chunk:
						idx = (byte * N) // 256  # map 0..255 -> 0..N-1
						self.listing[idx] += 1

					# Update progress
					processed += len(chunk)
					if progress_callback:
						percent = (processed / total_size) * 100
						progress_callback(min(percent, 100.0))

		except Exception as e:
			raise RuntimeError(f"File processing failed: {str(e)}")

	def _calculate_normalized_entropy(self):
		dataset = self.listing.copy()

		c = max(dataset) if dataset else 1
		c = 1 if c == 0 else c

		dataset = [round(v / c * 100) for v in dataset]
		entropy = round(sum(dataset) / (len(dataset) or 1), 2)
		return entropy, dataset

	def _calculate_shannon_entropy(self):
		alphabet_frequencies = self.listing.copy()

		# Calculate total number of bytes
		total_bytes = sum(alphabet_frequencies)

		# Calculate entropy for each byte
		dataset = []

		# Iterate over each frequency in alphabet_frequencies
		for freq in alphabet_frequencies:
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
		counts = [log2(c + 1) for c in self.listing]
		total = sum(counts)
		if total == 0:
			return 0.0, [0.0] * len(counts)

		dataset = []
		for c in counts:
			p = c / total
			dataset.append(-p * log2(p) * 100 if p > 0 else 0.0)

		entropy = sum(dataset) / 100
		return entropy, dataset

	def _calculate_entropy_log2_normalized(self):
		freqs = self.listing.copy()
		dataset = [round(log2(v + 1) * 100) for v in freqs]
		c = max(dataset) or 1
		dataset = [d / c * 100 for d in dataset]
		entropy = sum(dataset) / (len(dataset) or 1)
		return entropy, dataset

	def _calculate_entropy_log10_normalized(self):
		freqs = self.listing.copy()
		dataset = [round(log10(v + 1) * 100) for v in freqs]
		c = max(dataset) or 1
		dataset = [d / c * 100 for d in dataset]
		entropy = sum(dataset) / (len(dataset) or 1)
		return entropy, dataset

	def calculate_all_entropy(self):
		for name, strategy in FileResearchProcessor.strategies.items():
			try:
				entropy, dataset = getattr(self, strategy['func'])()
				self.entropy_dict[name] = {
					'human_readable': strategy['human_readable'],
					'entropy': entropy,
					'dataset': dataset
				}
			except Exception as e:
				print(f"Error in {name}: {e}")

	@classmethod
	def map_human_readable_to_machine_strategies(cls):
		return {strategy['human_readable']: name for name, strategy in cls.strategies.items()}

	def entropies_to_short_string(self):
		lines = []
		for key, d in self.entropy_dict.items():
			label = d['human_readable']
			unit = "bits/byte" if key.startswith("shannon") else "%"
			val = round(d['entropy'], 2)
			lines.append(f"{label}: {val} {unit}")
		return "\n".join(lines)

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

		self.button = None
		self.selected_option = None
		self.config_button = None
		self.toggle_button = None
		self.option_menu = None

		self.scale = 3
		self.aspect_ratio = 1

		self.dark_mode = True
		self.color_bg = "black"
		self.color_bars_fill = "red"
		self.color_bars_outline = "green"

	def on_resize(self, event):
		self.canvas.pack(fill="both", expand=True)

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

		self.redraw_from_option()

	def draw_chart(self, data, scale=1, aspect_ratio=1, flush=False):
		smart_bars = [SmartBar(i, h, scale=scale) for i, h in enumerate(data)]
		if flush and self.chart:
			self.chart.flush()
		self.chart = Chart(self.canvas, smart_bars, plot_height=MAX_HEIGHT,
						   scale=scale, aspect_ratio=aspect_ratio,
						   fill=self.color_bars_fill, outline=self.color_bars_outline)
		self.chart.draw()

	def update_label(self, event):
		if not self.chart:
			return
		pad = self.chart.padding
		bar_w = self.scale * self.aspect_ratio
		idx = int((event.x - pad) // bar_w)
		if idx < 0 or idx >= len(self.chart.smart_bars):
			self.label.config(text="")
			return
		bar = self.chart.smart_bars[idx]
		hex_width = 2 if len(self.chart.smart_bars) <= 256 else 4
		self.label.config(
			text=f"Symbol: 0x{bar.id:0{hex_width}X} ({bar.id}), Height: {bar.height:.2f}"
		)

	def process_file(self):
		if not self.file_path:
			return
		self.processor = FileResearchProcessor(self.file_path)
		self.processor.process_file()
		self.processor.calculate_all_entropy()
		self.entropy_string = self.processor.entropies_to_short_string()
		self.status_bar.config(text=f"Loaded file: {self.file_path}\n{self.entropy_string}")

	def open_file(self):
		try:
			def progress_callback(percent):
				# Update GUI thread-safe
				self.status_bar.after(0, lambda:
					self.status_bar.config(text=f"Loading {self.file_path}: {percent:.1f}%"))

			# Create processor with callback of progress
			self.processor = FileResearchProcessor(self.file_path)
			self.processor.process_file(progress_callback=progress_callback)

			# Finally
			self.processor.calculate_all_entropy()
			self.entropy_string = self.processor.entropies_to_short_string()

			# Update UI when complete
			self.status_bar.after(0, lambda:
				self.status_bar.config(text=f"Loaded: {self.file_path}\n{self.entropy_string}"))
			self.canvas.after(0, self.redraw_from_option)

		except Exception as e:
			self.status_bar.after(0, lambda:
				self.status_bar.config(text=f"Error: {str(e)}"))
		finally:
			# Always re-enable button when done
			self.button.after(0, lambda: self.button.config(state=tk.NORMAL))

	def open_file_interactive(self):
		self.file_path = filedialog.askopenfilename()

		if self.file_path:
			self.button.config(state=tk.DISABLED)
			self.status_bar.config(text="Initializing...")
			threading.Thread(target=self.open_file).start()

	def configure(self):
		window = tk.Toplevel()
		window.title("Cfg")

		tk.Label(window, text="MAX_HEIGHT").grid(row=0)
		tk.Label(window, text="ALPHABET").grid(row=1)
		tk.Label(window, text="Scale").grid(row=2)

		self.max_height_entry = tk.Entry(window)
		self.alphabet_entry = tk.Entry(window)
		self.scale_entry = tk.Entry(window)

		self.max_height_entry.insert(0, str(MAX_HEIGHT))
		self.alphabet_entry.insert(0, str(ALPHABET))
		self.scale_entry.insert(0, str(self.scale))

		self.max_height_entry.grid(row=0, column=1)
		self.alphabet_entry.grid(row=1, column=1)
		self.scale_entry.grid(row=2, column=1)

		tk.Button(window, text="Save", command=self.save_config).grid(row=3, columnspan=2)

	def redraw_hard(self):
		self.canvas.configure(
			width=10*2 + ALPHABET*self.scale*self.aspect_ratio,
			height=10*2 + MAX_HEIGHT*self.scale
		)
		if self.file_path:
			self.button.config(state=tk.DISABLED)
			threading.Thread(target=self.open_file, daemon=True).start()
		else:
			if self.chart: self.chart.flush()
			self.demo()

	def save_config(self):
		global MAX_HEIGHT, ALPHABET
		mh = int(self.max_height_entry.get())
		ab = int(self.alphabet_entry.get())
		sc = float(self.scale_entry.get())

		if mh <= 0: raise ValueError("MAX_HEIGHT must be > 0")
		if ab <= 0: raise ValueError("ALPHABET must be > 0")
		if sc <= 0: raise ValueError("Scale must be > 0")

		MAX_HEIGHT, ALPHABET, self.scale = mh, ab, sc
		self.redraw_hard()

	def _to_canvas(self, values):
		# values is any list of non-negative floats
		return AnalyzerContext._scale_to_height(values, MAX_HEIGHT)

	def redraw_from_option(self):
		if not (self.file_path and self.processor and self.processor.entropy_dict):
			return
		key = FileResearchProcessor.map_human_readable_to_machine_strategies() \
				  .get(self.selected_option.get(), "normalized(in)")
		datapick = self.processor.entropy_dict.get(key)
		if not datapick:
			return
		heights = self._to_canvas(datapick['dataset'])
		self.redraw_with_heights(heights)

	def redraw_with_heights(self, heights):
		self.draw_chart(heights, self.scale, self.aspect_ratio, flush=True)

	@staticmethod
	def _scale_to_height(values, height):
		m = max(values) or 1.0
		return [(v / m) * height for v in values]

	def redraw(self, datapick):
		if not self.file_path:
			return
		self.smart_bars = datapick['dataset']
		self.draw_chart(self.smart_bars, self.scale, self.aspect_ratio, flush=True)

	def demo(self):
		data = [0]*ALPHABET
		for i in range(ALPHABET):
			data[i] = (i*MAX_HEIGHT/ALPHABET)+random.randint(0, (ceil(ALPHABET/MAX_HEIGHT)))
		self.smart_bars = data
		self.draw_chart(data, self.scale, self.aspect_ratio)
		# Add centered text
		self.canvas.create_text((ALPHABET*self.scale*self.aspect_ratio)/2, (MAX_HEIGHT*self.scale)/2, font=("TkDefaultFont", int(self.scale*6)), fill="white", text="EntropyVUE Demo")


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Calculate entropies...')
	parser.add_argument('-f', '--file', dest='file_path', help='The path to the file to be analyzed')
	args = parser.parse_args()

	window = tk.Tk()
	window.title("EntropyVUE")
	context = AnalyzerContext()
	context.canvas = tk.Canvas(window, width=ALPHABET*context.scale*context.aspect_ratio, height=MAX_HEIGHT*context.scale,bg=context.color_bg)
	context.demo()
	context.label = tk.Label(window, text="")
	context.label.pack()
	context.canvas.bind("<Motion>", context.update_label)

	context.canvas.pack()
	context.status_bar = tk.Label(window, text="EntropyVUE by Tim Abdiukov. Please load a file", bd=1, relief=tk.SUNKEN, anchor=tk.W)
	context.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
	context.button = tk.Button(window, text="Select File", command=context.open_file_interactive)
	context.button.pack(side=tk.RIGHT)
	options = FileResearchProcessor.map_human_readable_to_machine_strategies()
	context.selected_option = tk.StringVar(window)
	context.selected_option.set("Normalized entropy of input")
	context.config_button = tk.Button(window, text="Configure", command=context.configure)
	context.config_button.pack(side=tk.RIGHT)
	context.toggle_button = tk.Button(window, text="◐", command=context.toggle_mode)
	context.toggle_button.pack(side=tk.RIGHT)
	context.option_menu = tk.OptionMenu(window, context.selected_option, *options, command=lambda _: context.redraw_from_option())
	context.option_menu.pack(side=tk.LEFT)

	if args.file_path:
		context.file_path = args.file_path
		context.button.config(state=tk.DISABLED)  # Access through context
		threading.Thread(target=context.open_file).start()

	window.mainloop()
