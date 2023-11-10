"""
Before running this code you will need:
A copy of your fonts folder (C:/Windows/Fonts for me) in your project folder inside a directory called fonts
(Alternatively you could point the script at that folder)
An image in your project folder inside a directory called images with filename placeholder.png
"""

import tkinter as t
from tkinter import filedialog as fd
from PIL import Image, ImageTk, ImageDraw, ImageFont
from pathlib import Path

# Define theme colors for the GUI
THEME_COLOUR = '#5BC2E7'
SECONDARY_COLOUR = '#5B7CE7'
TERTIARY_COLOUR = '#5BE7C6'

# Define font settings for buttons
BUTTON_FONT = ('Arial', 16, 'bold')

# Constants for default values
DEFAULT_OPACITY = 0.2
DEFAULT_FONT_COLOR = (0, 0, 0)
DEFAULT_WATERMARK_SIZE = 100
DEFAULT_SPACING = 100

# Lessons to consider: 1: Model, View, Controller.  2: Refactor: def init_sliders(self) etc


def make_transparent(im, opacity):
    """
    Make the input image transparent by adjusting the alpha channel.

    Parameters:
    - im: PIL Image object
    - opacity: Opacity value between 0 (fully transparent) and 1 (fully opaque)

    Returns:
    - PIL Image object with adjusted transparency
    """
    rgba = im.convert('RGBA')
    datas = rgba.getdata()
    new_data = [(item[0], item[1], item[2], opacity) for item in datas]
    rgba.putdata(new_data)
    return rgba


def rescale(im, max_width):
    """
    Rescale the input image while maintaining its aspect ratio.

    Parameters:
    - im: PIL Image object
    - max_width: Maximum width of the rescaled image

    Returns:
    - Rescaled PIL Image object
    """
    ratio = max_width / im.size[0]
    new_size = int(im.size[0] * ratio), max(int(im.size[1] * ratio), 1)
    rescaled_image = im.resize(new_size)
    return rescaled_image


def tile(mark, size, spacing):
    """
    Tile the input watermark image across a target size.

    Parameters:
    - mark: PIL Image object (watermark)
    - size: Target size (width, height)
    - spacing: Spacing between watermark tiles

    Returns:
    - Tiled PIL Image object
    """
    mark_width = mark.size[0] + spacing
    mark_height = mark.size[1] + spacing
    x_scale = size[0] // mark_width + 1
    y_scale = size[1] // mark_height + 1
    width = mark_width * x_scale
    height = mark_height * y_scale
    new_image = Image.new('RGBA', (width, height))
    for i in range(x_scale):
        for j in range(y_scale):
            new_image.paste(mark, (i * mark_width, j * mark_height))
    new_image = new_image.crop((0, 0, size[0], size[1]))
    return new_image


def get_text_dimensions(text_string, font):
    """
    Calculate the dimensions (width and height) of a text string rendered with a given font.

    Parameters:
    - text_string: Text string
    - font: PIL ImageFont object

    Returns:
    - Tuple containing text width and height
    """
    # Thank you iimos https://stackoverflow.com/a/46220683/9263761
    ascent, descent = font.getmetrics()
    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent
    return text_width, text_height


def create_text_image(text_string, font, font_colour):
    """
    Create an image containing the specified text, using the provided font and font color.

    Parameters:
    - text_string: Text string
    - font: PIL ImageFont object
    - font_colour: Font color as a tuple (r, g, b, a)

    Returns:
    - PIL Image object with the rendered text
    """
    w, h = get_text_dimensions(text_string, font)
    txt = Image.new(mode='RGBA', size=(w, h))
    draw = ImageDraw.Draw(txt)
    draw.text((0, 0), text_string, font=font, fill=font_colour)
    return txt


class WaterMarker(t.Tk):
    """
    Initialize the WaterMarker application.

    - Set up the GUI with buttons, sliders, and labels.
    - Initialize default values for image, watermark, and other settings.
    """
    def __init__(self):
        super().__init__()

        # Configure the GUI background color
        self.config(bg=THEME_COLOUR)

        # Placeholder image for initial setup
        placeholder = rescale(Image.open('images/placeholder.png'), 100)

        # Set window title and initialize image and watermark variables
        self.title('Watermarker')
        self.raw_image = placeholder
        self.raw_watermark = placeholder
        self.image = rescale(self.raw_image, 500).convert('RGBA')
        self.watermark = rescale(self.raw_watermark, 100)

        # Initialize flags and variables for text watermark
        self.is_watermark_text = False
        self.text = None

        # Buttons for importing image and watermark
        self.import_image_button = t.Button(text='Import Image', command=lambda: self.open_file('image'),
                                            background=SECONDARY_COLOUR, foreground=TERTIARY_COLOUR,
                                            activebackground=TERTIARY_COLOUR, activeforeground=SECONDARY_COLOUR,
                                            font=BUTTON_FONT)
        self.import_watermark_button = t.Button(text='Import Watermark', command=lambda: self.open_file('watermark'),
                                                background=SECONDARY_COLOUR, foreground=TERTIARY_COLOUR,
                                                activebackground=TERTIARY_COLOUR, activeforeground=SECONDARY_COLOUR,
                                                font=BUTTON_FONT)

        # Labels for displaying image and watermark thumbnails
        self.image_thumbnail = t.Label(borderwidth=5, relief='ridge')
        self.watermark_thumbnail = t.Label(borderwidth=5, relief='ridge')

        # Entry for inputting text for text watermark
        self.water_text_entry = t.Entry()

        # Buttons for font selection and using text as a watermark
        self.select_font_button = t.Button(text='Select Font', command=self.select_font,
                                           background=SECONDARY_COLOUR, foreground=TERTIARY_COLOUR,
                                           activebackground=TERTIARY_COLOUR, activeforeground=SECONDARY_COLOUR,
                                           font=BUTTON_FONT)
        self.select_text_watermark = t.Button(text='Use Text for Watermark', command=self.use_text_as_watermark,
                                              background=SECONDARY_COLOUR, foreground=TERTIARY_COLOUR,
                                              activebackground=TERTIARY_COLOUR, activeforeground=SECONDARY_COLOUR,
                                              font=BUTTON_FONT)

        # Initialize colour sliders and set default font
        self.font = ImageFont.truetype('fonts/arial.ttf')
        self.font_red = t.Scale(from_=0, to=255, fg='red', troughcolor='red',
                                command=self.select_text_colour, background=THEME_COLOUR,
                                relief=t.RAISED, font=BUTTON_FONT, highlightthickness=2,
                                activebackground=TERTIARY_COLOUR, highlightbackground=TERTIARY_COLOUR
                                )
        self.font_green = t.Scale(from_=0, to=255, troughcolor='green', fg='green',
                                  command=self.select_text_colour, background=THEME_COLOUR,
                                  relief=t.RAISED, font=BUTTON_FONT, highlightthickness=2,
                                  activebackground=TERTIARY_COLOUR, highlightbackground=TERTIARY_COLOUR
                                  )
        self.font_blue = t.Scale(from_=0, to=255, troughcolor='blue', fg='blue',
                                 command=self.select_text_colour, background=THEME_COLOUR,
                                 relief=t.RAISED, font=BUTTON_FONT, highlightthickness=2,
                                 activebackground=TERTIARY_COLOUR, highlightbackground=TERTIARY_COLOUR)

        # Initialize output variables and labels
        self.output = None
        self.output_label = t.Label(borderwidth=5, relief='raised', padx=200, pady=20, background=SECONDARY_COLOUR)

        # Button for saving the watermarked image
        self.save_button = t.Button(text='Save As', command=self.save_image,
                                    background=SECONDARY_COLOUR, foreground=TERTIARY_COLOUR,
                                    activebackground=TERTIARY_COLOUR, activeforeground=SECONDARY_COLOUR,
                                    font=BUTTON_FONT)

        # Initialize opacity, font color, and size variables
        self.opacity = DEFAULT_OPACITY
        self.font_colour = (0, 0, 0)
        self.opacity_label = t.Label(text='Opacity', font=BUTTON_FONT, fg=SECONDARY_COLOUR, bg=THEME_COLOUR)

        # Sliders for controlling opacity, size, and spacing
        self.opacity_slider = t.Scale(from_=0, to=100, command=self.change_opacity, background=THEME_COLOUR,
                                      relief=t.RAISED, font=BUTTON_FONT, highlightthickness=2,
                                      activebackground=TERTIARY_COLOUR, highlightbackground=TERTIARY_COLOUR,
                                      troughcolor=SECONDARY_COLOUR, foreground=SECONDARY_COLOUR
                                      )
        self.opacity_slider.set(int(DEFAULT_OPACITY * 100))
        self.watermark_size = DEFAULT_WATERMARK_SIZE
        self.size_label = t.Label(text='Size', font=BUTTON_FONT, fg=SECONDARY_COLOUR, bg=THEME_COLOUR)
        self.size_slider = t.Scale(from_=1, to=100, command=self.change_size, background=THEME_COLOUR,
                                   relief=t.RAISED, font=BUTTON_FONT, highlightthickness=2,
                                   activebackground=TERTIARY_COLOUR, highlightbackground=TERTIARY_COLOUR,
                                   troughcolor=SECONDARY_COLOUR, foreground=SECONDARY_COLOUR)
        self.size_slider.set(int(DEFAULT_WATERMARK_SIZE * 0.2))
        self.spacing = DEFAULT_SPACING
        self.spacing_label = t.Label(text='Spacing', font=BUTTON_FONT, fg=SECONDARY_COLOUR, bg=THEME_COLOUR)
        self.spacing_slider = t.Scale(from_=0, to=100, command=self.change_spacing, background=THEME_COLOUR,
                                      relief=t.RAISED, font=BUTTON_FONT, highlightthickness=2,
                                      activebackground=TERTIARY_COLOUR, highlightbackground=TERTIARY_COLOUR,
                                      troughcolor=SECONDARY_COLOUR, foreground=SECONDARY_COLOUR)
        self.spacing_slider.set(int(DEFAULT_SPACING * 0.2))

        # Grid layout for arranging widgets
        self.import_image_button.grid(column=0, row=0, pady=10)
        self.import_watermark_button.grid(column=1, row=0, pady=10)
        self.select_text_watermark.grid(column=2, row=0, columnspan=3, pady=10)
        self.select_font_button.grid(column=5, row=0, columnspan=3, pady=10, padx=10)

        self.image_thumbnail.grid(column=0, row=1)
        self.watermark_thumbnail.grid(column=1, row=1)
        self.water_text_entry.grid(column=2, row=1, columnspan=6, sticky='ew', padx=10)

        self.font_red.grid(column=5, row=2, sticky='n')
        self.font_green.grid(column=6, row=2, sticky='n')
        self.font_blue.grid(column=7, row=2, sticky='n')

        self.output_label.grid(column=0, row=2, columnspan=2, rowspan=2, padx=20, pady=20)
        self.opacity_label.grid(column=2, row=2, sticky='s')
        self.size_label.grid(column=3, row=2, sticky='s')
        self.spacing_label.grid(column=4, row=2, sticky='s')

        self.opacity_slider.grid(column=2, row=3, sticky='n')
        self.size_slider.grid(column=3, row=3, sticky='n')
        self.spacing_slider.grid(column=4, row=3, sticky='n')

        self.save_button.grid(column=0, row=4, pady=20)
        self.update_images()

    def create_composite(self):
        """
        Create a composite image by overlaying the watermark on the main image.

        Uses the selected watermark (either text or image) and adjusts opacity, size, and spacing.

        """
        if self.is_watermark_text:
            # Create a text watermark with specified color and opacity
            mark = create_text_image(self.text, self.font, (self.font_colour[0],
                                                            self.font_colour[1],
                                                            self.font_colour[2],
                                                            int(self.opacity * 255)))
        else:
            # Make the image watermark transparent with specified opacity
            mark = make_transparent(self.raw_watermark, int(self.opacity * 255))

        # Tile the watermark and create a composite image
        tiled = tile(rescale(mark, self.watermark_size), self.image.size, self.spacing)
        alpha_composite = Image.alpha_composite(self.image, tiled)

        # Display the composite image in the GUI
        marked = ImageTk.PhotoImage(alpha_composite)
        self.output_label.config(image=marked)
        self.output_label.image = marked

    def update_images(self):
        """
        Update thumbnail images in the GUI.

        Rescale and display the current main image and watermark images.

        """
        image_thumbnail = rescale(self.raw_image, 100)
        watermark_thumbnail = rescale(self.raw_watermark, 100)
        im = ImageTk.PhotoImage(image_thumbnail)
        self.image_thumbnail.config(image=im)
        self.image_thumbnail.image = im
        im = ImageTk.PhotoImage(watermark_thumbnail)
        self.watermark_thumbnail.config(image=im)
        self.watermark_thumbnail.image = im
        self.create_composite()

    def change_opacity(self, value):
        """
        Change the opacity of the watermark.

        Updates the displayed composite image.

        """
        self.opacity = float(value) / 100
        self.update_images()

    def change_size(self, value):
        """
        Change the size of the watermark.

        Updates the displayed composite image.

        """
        self.watermark_size = int(value) * 5
        self.watermark = rescale(self.raw_watermark, self.watermark_size)
        self.update_images()

    def change_spacing(self, value):
        """
        Change the spacing of the watermark.

        Updates the displayed composite image.

        """
        self.spacing = int(value) * 5
        self.update_images()

    def open_file(self, choice):
        """
        Open a file dialog to select an image file.

        Depending on the choice ('image' or 'watermark'), the selected image is loaded.

        """
        filename = fd.askopenfilename(filetypes=(('image files', ('.png', 'jpg')),), initialdir=str(Path.home()))
        if filename:
            new_image = Image.open(filename)
            if choice == 'image':
                self.raw_image = new_image.convert('RGBA')
                self.image = rescale(self.raw_image, 500)
            elif choice == 'watermark':
                self.raw_watermark = new_image
                self.watermark = rescale(self.raw_watermark, self.watermark_size)
                self.is_watermark_text = False
            self.update_images()

    def select_font(self):
        """
        Open a file dialog to select a TrueType font file.

        Updates the font used for the text watermark.

        """
        filename = fd.askopenfilename(filetypes=[('TrueType fonts', '.ttf')],
                                      initialdir='fonts',
                                      initialfile='arial.ttf')
        if filename:
            self.font = ImageFont.truetype(filename, 500)
        self.use_text_as_watermark()

    def use_text_as_watermark(self):
        """
        Use the entered text as a watermark.

        Updates the displayed composite image.

        """
        text = self.water_text_entry.get()
        if text:
            self.text = text
            self.raw_watermark = create_text_image(text, self.font, self.font_colour)
            self.watermark = rescale(self.raw_watermark, self.watermark_size)
            self.is_watermark_text = True
            self.update_images()

    def select_text_colour(self, _):
        """
        Select the color of the text watermark.

        Updates the displayed composite image.

        """
        r = int(self.font_red.get())
        g = int(self.font_green.get())
        b = int(self.font_blue.get())
        self.font_colour = (r, g, b)
        self.use_text_as_watermark()

    def save_image(self):
        """
        Save the watermarked image.

        Opens a file dialog to select the file type and location.

        """
        if self.is_watermark_text:
            mark = create_text_image(self.text, self.font, (self.font_colour[0],
                                                            self.font_colour[1],
                                                            self.font_colour[2],
                                                            int(self.opacity * 255)))
        else:
            mark = make_transparent(self.raw_watermark, int(self.opacity * 255))
        width = self.raw_image.size[0]
        spacing = int(self.spacing * width / 500)
        mark_width = int(self.watermark_size * width / 500)
        scaled_watermark = rescale(mark, mark_width)
        tiled_mark = tile(scaled_watermark, self.raw_image.size, spacing)
        watermarked_image = Image.alpha_composite(self.raw_image, tiled_mark).convert('RGB')
        data = [('Image Files', '.jpg .png'), ('JPEG', '*.jpg'), ('PNG', '.png')]
        filename = fd.asksaveasfilename(filetypes=data,
                                        initialfile='watermarked_image.jpg',
                                        initialdir=str(Path.home()),
                                        defaultextension='.jpg')
        if filename:
            watermarked_image.save(filename)
