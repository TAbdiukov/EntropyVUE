# EntropyVUE

EntropyVUE is a Python application that visualizes the entropy of a file. Gain insight into spectre and range of entropy in a file.

EntropyVUE uses Tkinter library for the GUI and requires no outside dependencies,

![GUI](.img/gui.png) |
---- | 

## Features

- **Interactive Visualization** (*Vue*): The application provides an interactive visualization of the entropy of the selected file against several entropy algorithms.
- **Cross-Platform**: EntropyVUE uses cross-platform Python and embedded Tkinter library for the GUI.
- **Customizability**: Users can configure the `MAX_HEIGHT`, `ALPHABET`, and `Scale` parameters. The user may use `ALPHABET` values over the span of 1 byte.

## Usage

You can start the program by double-clicking on `vue.py`, or by passing `vue.py` to Python,
```bash
python vue.py
```

The program will start in "demo" mode, and you can specify a file to open using the "Select File" button.

Alternatively, you can run the program from the command line with the `-f` or `--file` option

```bash
python vue.py -f /path/to/file
```

## Discover EntropyVUE interactivity

* What does the entropy of a text file (like this README) look like when compared to a ZIP archive?
* How does the entropy of a deflate ZIP archive file compare to that of a compressed RAR or 7-zip archive file?
* What's the difference in entropy between an MP3 file and a WAV file?
* How does the entropy of a JPG file compare to that of a PNG file?

What additional insights can be extracted from these entropy readings?

-----------------------------------

**Tim Abdiukov**
