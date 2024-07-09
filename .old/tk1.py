

import tkinter as tk
import random
from tkinter import filedialog

from math import log2, log10

# Fast IO
import mmap

ALPHABET = 256
MAX_HEIGHT = 100

class SmartBar:
	def __init__(self, id, height, width=1, scale=1):
		self.id = id
		self.height = height
		self.width = width
		self.scale = scale


class Chart:
	def __init__(self, canvas, smart_bars, fill="red", outline="green", padding=10, scale=1, aspect_ratio=1):
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
		'standard': {"human_readable": "Standard", 'func': '_calculate_entropy_standard'},
		'log2': {"human_readable": "Logarithm to Base 2", 'func': '_calculate_entropy_log2'},
		'log10': {"human_readable": "Logarithm to Base 10", 'func': '_calculate_entropy_log10'}
	}

	def process_file(self):
		with open(self.filename, 'rb') as f:
			mmapped_file = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
			for byte in mmapped_file:
				self.listing[byte[0] % ALPHABET] += 1
			mmapped_file.close()

	def _calculate_entropy_standard(self):
		MODE = 1
		a = self.listing

		dataset = a.copy()

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


	def _calculate_entropy_log2(self):
		a = self.listing
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
			dataset[b] = round(dataset[b] / c * 100, 2)

		for b in range(ALPHABET):
			entropy += dataset[b]

		entropy = round(entropy / ALPHABET, 2)

		return entropy, dataset

	def _calculate_entropy_log10(self):
		a = self.listing
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
			dataset[b] = round(dataset[b] / c * 100, 2)

		for b in range(ALPHABET):
			entropy += dataset[b]

		entropy = round(entropy / ALPHABET, 2)

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
			entropy_str += f"Entropy type: {entropy_type}, Entropy: {entropy_data['entropy']}%\n"
		return entropy_str

def draw_chart(canvas, data, scale=1, aspect_ratio=1, flush=False):
	global chart
	# Create a list to store the SmartBar objects
	smart_bars = []

	# Draw ALPHABET bars with increasing height
	for i in range(ALPHABET):
		bar = SmartBar(i, data[i], scale=scale)
		smart_bars.append(bar)

	# Create a Chart object and draw it
	if(flush): chart.flush()
	chart = Chart(canvas, smart_bars, scale=scale, aspect_ratio=aspect_ratio)
	chart.draw()

# Function to update the label
def update_label(event):
	try:
		bar = chart.smart_bars[int(event.x // (scale * aspect_ratio))]
		label.config(text=f"Bar ID: {bar.id}, Height: {bar.height}")
	except IndexError as e:
		pass

def open_file():
	global file_path
	file_path = filedialog.askopenfilename()

	# Check if a file is selected
	if not file_path:
		return

	global processor
	processor = FileResearchProcessor(file_path)
	processor.process_file()
	processor.calculate_all_entropy()

	global entropy_string
	entropy_string = processor.entropies_to_short_string()

	# Update the status bar
	status_bar.config(text=f"Loaded file: {file_path}\n{entropy_string}")
	draw_from_option()

def draw_from_option():
	# Check if a file is selected
	if not file_path:
		return

	datapick = processor.entropy_dict[options[selected_option.get()]]

	global smart_bars
	smart_bars = datapick['dataset']

	draw_chart(canvas, smart_bars, scale, aspect_ratio, flush=True)

def demo():
	data = [0]*ALPHABET
	for i in range(ALPHABET):
		data[i] = random.randint(i//3,MAX_HEIGHT)

	draw_chart(canvas, data, scale, aspect_ratio)

if __name__ == '__main__':
	# Create a new Tkinter window
	window = tk.Tk()

	# Set the scale and aspect ratio
	scale = 2.5
	aspect_ratio = 1

	# Create a canvas to draw the histogram
	global canvas
	canvas = tk.Canvas(window, width=ALPHABET*scale*aspect_ratio, height=MAX_HEIGHT*scale,bg="black")  # Set the background color to white

	demo()

	# Create a label to display the bar ID and value
	label = tk.Label(window, text="")
	label.pack()

	# Bind the function to the canvas
	canvas.bind("<Motion>", update_label)

	# Pack the canvas into the window
	canvas.pack()

	# Create a status bar
	status_bar = tk.Label(window, text="Please load a file", bd=1, relief=tk.SUNKEN, anchor=tk.W)
	status_bar.pack(side=tk.BOTTOM, fill=tk.X)


	# Create a button to open file dialog
	button = tk.Button(window, text="Select File", command=open_file)
	button.pack(side=tk.RIGHT)

	# Create a dictionary for the options
	options = FileResearchProcessor.map_human_readable_to_machine_strategies()

	# Create a variable to store the selected option
	selected_option = tk.StringVar(window)
	selected_option.set("Standard")  # set the default option

	# Create the option menu
	option_menu = tk.OptionMenu(window, selected_option, *options, command=lambda _: draw_from_option())
	option_menu.pack(side=tk.LEFT)

	# Start the Tkinter event loop
	window.mainloop()
