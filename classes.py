import tkinter as t
from tkinter import filedialog as fd
from PIL import Image, ImageTk, ImageDraw, ImageFont
from pathlib import Path

THEME_COLOUR = '#5BC2E7'
SECONDARY_COLOUR = '#5B7CE7'
TERTIARY_COLOUR = '#5BE7C6'

BUTTON_FONT = ('Arial', 16, 'bold')

"""
Before running this code you will need:
A copy of your fonts folder (C:/Windows/Fonts for me) in your project folder inside a directory called fonts
(Alternatively you could point the script at that folder)
An image in your project folder inside a directory called images with filename placeholder.png
"""


def make_transparent(im, opacity):
    rgba = im.convert('RGBA')
    datas = rgba.getdata()
    new_data = []
    for item in datas:
        new_item = (item[0], item[1], item[2], opacity)
        new_data.append(new_item)
    rgba.putdata(new_data)
    return rgba


def rescale(im, max_width):
    ratio = max_width / im.size[0]
    new_size = int(im.size[0] * ratio), max(int(im.size[1] * ratio), 1)
    rescaled_image = im.resize(new_size)
    return rescaled_image


def tile(mark, size, spacing):
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


"""
Now defunct, this used to use a constant alpha across the two images, 
replaced so that only the mark has transparency
def create_composite(im, mark, opacity, spacing):
    tiled_mark = tile(mark, im.size, spacing)
    alpha_composite = Image.blend(im.convert('RGBA'), tiled_mark.convert('RGBA'), opacity)
    return alpha_composite
"""


def get_text_dimensions(text_string, font):
    # https://stackoverflow.com/a/46220683/9263761
    ascent, descent = font.getmetrics()
    text_width = font.getmask(text_string).getbbox()[2]
    text_height = font.getmask(text_string).getbbox()[3] + descent
    return text_width, text_height


def create_text_image(text_string, font, font_colour):
    w, h = get_text_dimensions(text_string, font)
    txt = Image.new(mode='RGBA', size=(w, h))
    draw = ImageDraw.Draw(txt)
    draw.text((0, 0), text_string, font=font, fill=font_colour)
    return txt


class WaterMarker(t.Tk):
    def __init__(self):
        super().__init__()
        self.config(bg=THEME_COLOUR)
        placeholder = rescale(Image.open('images/placeholder.png'), 100)
        self.title('Watermarker')
        self.raw_image = placeholder
        self.raw_watermark = placeholder
        self.image = rescale(self.raw_image, 500).convert('RGBA')
        self.watermark = rescale(self.raw_watermark, 100)
        self.is_watermark_text = False
        self.text = None
        self.import_image_button = t.Button(text='Import Image', command=lambda: self.open_file('image'),
                                            background=SECONDARY_COLOUR, foreground=TERTIARY_COLOUR,
                                            activebackground=TERTIARY_COLOUR, activeforeground=SECONDARY_COLOUR,
                                            font=BUTTON_FONT)
        self.import_watermark_button = t.Button(text='Import Watermark', command=lambda: self.open_file('watermark'),
                                                background=SECONDARY_COLOUR, foreground=TERTIARY_COLOUR,
                                                activebackground=TERTIARY_COLOUR, activeforeground=SECONDARY_COLOUR,
                                                font=BUTTON_FONT)

        self.image_thumbnail = t.Label(borderwidth=5, relief='ridge')
        self.watermark_thumbnail = t.Label(borderwidth=5, relief='ridge')

        self.water_text_entry = t.Entry()
        self.select_font_button = t.Button(text='Select Font', command=self.select_font,
                                           background=SECONDARY_COLOUR, foreground=TERTIARY_COLOUR,
                                           activebackground=TERTIARY_COLOUR, activeforeground=SECONDARY_COLOUR,
                                           font=BUTTON_FONT)
        self.select_text_watermark = t.Button(text='Use Text for Watermark', command=self.use_text_as_watermark,
                                              background=SECONDARY_COLOUR, foreground=TERTIARY_COLOUR,
                                              activebackground=TERTIARY_COLOUR, activeforeground=SECONDARY_COLOUR,
                                              font=BUTTON_FONT)
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

        self.output = None
        self.output_label = t.Label(borderwidth=5, relief='raised', padx=200, pady=20, background=SECONDARY_COLOUR)

        self.save_button = t.Button(text='Save As', command=self.save_image,
                                    background=SECONDARY_COLOUR, foreground=TERTIARY_COLOUR,
                                    activebackground=TERTIARY_COLOUR, activeforeground=SECONDARY_COLOUR,
                                    font=BUTTON_FONT)

        self.opacity = 0.2
        self.font_colour = (0, 0, 0)
        self.opacity_label = t.Label(text='Opacity', font=BUTTON_FONT, fg=SECONDARY_COLOUR, bg=THEME_COLOUR)
        self.opacity_slider = t.Scale(from_=0, to=100, command=self.change_opacity, background=THEME_COLOUR,
                                      relief=t.RAISED, font=BUTTON_FONT, highlightthickness=2,
                                      activebackground=TERTIARY_COLOUR, highlightbackground=TERTIARY_COLOUR,
                                      troughcolor=SECONDARY_COLOUR, foreground=SECONDARY_COLOUR
                                      )
        self.opacity_slider.set(20)
        self.watermark_size = 100
        self.size_label = t.Label(text='Size', font=BUTTON_FONT, fg=SECONDARY_COLOUR, bg=THEME_COLOUR)
        self.size_slider = t.Scale(from_=1, to=100, command=self.change_size, background=THEME_COLOUR,
                                   relief=t.RAISED, font=BUTTON_FONT, highlightthickness=2,
                                   activebackground=TERTIARY_COLOUR, highlightbackground=TERTIARY_COLOUR,
                                   troughcolor=SECONDARY_COLOUR, foreground=SECONDARY_COLOUR)
        self.size_slider.set(20)
        self.spacing = 100
        self.spacing_label = t.Label(text='Spacing', font=BUTTON_FONT, fg=SECONDARY_COLOUR, bg=THEME_COLOUR)
        self.spacing_slider = t.Scale(from_=0, to=100, command=self.change_spacing, background=THEME_COLOUR,
                                      relief=t.RAISED, font=BUTTON_FONT, highlightthickness=2,
                                      activebackground=TERTIARY_COLOUR, highlightbackground=TERTIARY_COLOUR,
                                      troughcolor=SECONDARY_COLOUR, foreground=SECONDARY_COLOUR)
        self.spacing_slider.set(20)

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
        # alpha_composite = create_composite(self.image, self.watermark, self.opacity, self.spacing)
        # marked = ImageTk.PhotoImage(alpha_composite)
        # self.output_label.config(image=marked)
        # self.output_label.image = marked
        if self.is_watermark_text:
            mark = create_text_image(self.text, self.font, (self.font_colour[0],
                                                            self.font_colour[1],
                                                            self.font_colour[2],
                                                            int(self.opacity * 255)))
        else:
            mark = make_transparent(self.raw_watermark, int(self.opacity * 255))
        tiled = tile(rescale(mark, self.watermark_size), self.image.size, self.spacing)
        alpha_composite = Image.alpha_composite(self.image, tiled)
        marked = ImageTk.PhotoImage(alpha_composite)
        self.output_label.config(image=marked)
        self.output_label.image = marked

    def update_images(self):
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
        self.opacity = float(value) / 100
        self.update_images()

    def change_size(self, value):
        self.watermark_size = int(value) * 5
        self.watermark = rescale(self.raw_watermark, self.watermark_size)
        self.update_images()

    def change_spacing(self, value):
        self.spacing = int(value) * 5
        self.update_images()

    def open_file(self, choice):
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
        filename = fd.askopenfilename(filetypes=[('TrueType fonts', '.ttf')], initialdir='fonts')
        if filename:
            self.font = ImageFont.truetype(filename, 500)
        self.use_text_as_watermark()

    def use_text_as_watermark(self):
        text = self.water_text_entry.get()
        if text:
            self.text = text
            self.raw_watermark = create_text_image(text, self.font, self.font_colour)
            self.watermark = rescale(self.raw_watermark, self.watermark_size)
            self.is_watermark_text = True
            self.update_images()

    def select_text_colour(self, _):
        r = int(self.font_red.get())
        g = int(self.font_green.get())
        b = int(self.font_blue.get())
        self.font_colour = (r, g, b)
        self.use_text_as_watermark()

    def save_image(self):
        # width = self.raw_image.size[0]
        # spacing = int(self.spacing * width / 500)
        # mark_width = int(self.watermark_size * width / 500)
        # scaled_watermark = rescale(self.raw_watermark, mark_width)
        # watermarked_image = create_composite(self.raw_image, scaled_watermark, self.opacity, spacing).convert('RGB')
        # print(type(watermarked_image))
        # data = [('Image Files', '.jpg .png'), ('JPEG', '*.jpg'), ('PNG', '.png')]
        # filename = fd.asksaveasfilename(filetypes=data,
        #                                 initialfile='watermarked_image.jpg',
        #                                 initialdir=str(Path.home()),
        #                                 defaultextension='.jpg')
        # if filename:
        #     watermarked_image.save(filename)
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





