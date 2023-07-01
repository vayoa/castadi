import random
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO


def draw_rectangles(images, locations, bubbles=None, outline_width=5,
                    canvas_size=(1080, 1920),
                    default_font_size=12,
                    default_bubble_color=(20, 20, 20),
                    default_text_color="white",
                    default_font='C:\Windows\Fonts\CascadiaMonoPL-ExtraLight.ttf',
                    b_big_var=0.3, b_small_var=0.15,
                    ):
    canvas_width, canvas_height = canvas_size

    # Create a blank canvas
    canvas = Image.new("RGB", (canvas_width, canvas_height), "white")
    draw = ImageDraw.Draw(canvas)

    for image, location, bubble_list in zip(images or [None] * len(locations), locations, bubbles or [None] * len(locations)):
        x, y, width, height = location

        if image:
            # Load the image from base64 encoding
            img = Image.open(BytesIO(image))

            # Resize the image to fit within the specified width and height
            img = img.resize((width, height), Image.ANTIALIAS)

            # Paste the image onto the canvas at the specified location
            canvas.paste(img, (x, y))

        # Calculate the coordinates of the rectangle
        top_left = (x, y)
        bottom_right = (x + width, y + height)

        # Draw the rectangle outline with increased width
        draw.rectangle([top_left, bottom_right],
                       outline="black", width=outline_width)

        if bubble_list is not None:
            b_positions = [(x, y)]
            for bubble_i, bubble in enumerate(bubble_list):
                bubble_text, bubble_font_size, bubble_color, font_color, font_name = bubble

                bubble_color = bubble_color or default_bubble_color
                font_color = font_color or default_text_color
                font_name = font_name or default_font
                bubble_font_size = bubble_font_size or default_font_size

                last_x, last_y = b_positions[-1]

                # Calculate the coordinates and size of the speech bubble
                # Vary x-coordinate within left 30% of the panel
                mod = 1 if bubble_i == 0 else 0.5

                width_bigger = width > height
                bubble_x = random.randint(
                    last_x, last_x + int(width * mod * (b_big_var if width_bigger else b_small_var)))
                # Vary y-coordinate within top 30% of the panel
                bubble_y = random.randint(
                    last_y, last_y + int(height * mod * (b_small_var if width_bigger else b_big_var)))
                bubble_width = 0.75 * bubble_font_size  # Initial width for auto-sizing
                bubble_height = 0.55 * bubble_font_size  # Initial height for auto-sizing

                # Update the bubble size to fit the text
                bubble_font = ImageFont.truetype(font_name, bubble_font_size)
                bubble_text_width, bubble_text_height = draw.textsize(
                    bubble_text, font=bubble_font)
                bubble_width += bubble_text_width + 10  # Add padding
                bubble_height += bubble_text_height + 10  # Add padding

                # Draw the speech bubble rectangle with the specified color
                bubble_top_left = (bubble_x, bubble_y)
                bubble_bottom_right = (
                    bubble_x + bubble_width, bubble_y + bubble_height)
                draw.rectangle(
                    [bubble_top_left, bubble_bottom_right], fill=bubble_color)

                b_positions.append((bubble_x, int(bubble_y + bubble_height)))

                # Add text inside the speech bubble with the specified font color
                text_x = bubble_x + 10  # Add padding
                text_y = bubble_y + 10  # Add padding
                draw.text((text_x, text_y), bubble_text,
                          fill=font_color, font=bubble_font)

    return canvas


def split_rec(rec, min_size, split_on_width=None):
    x, y, width, height = rec
    min_width, min_height = min_size

    # Check if the rectangle is too small to split
    if width <= min_width and height <= min_height:
        return [rec]

    # Calculate the maximum width and height for splitting
    max_width = width - min_width
    max_height = height - min_height

    # Adjust the range for splitting if necessary
    split_width = max(min_width, max_width)
    split_height = max(min_height, max_height)

    # Decide whether to split on width or height
    if split_width < min_width and split_height < min_height:
        # Unable to split, return the original rectangle
        return [rec]
    else:
        can_split_width = split_width >= min_width
        split_on_width = split_on_width if split_on_width is not None and can_split_width else not can_split_width or (
            split_height >= min_height and random.choice([True, False]))

    if split_on_width:
        # Split on height
        split_point = height if height == min_height else random.randint(
            min_height, height - min_height)
        return [
            (x, y, width, split_point),
            (x, y + split_point, width, height - split_point)
        ]
    else:
        # Split on width
        split_point = width if width == min_width else random.randint(
            min_width, width - min_width)
        return [
            (x, y, split_point, height),
            (x + split_point, y, width - split_point, height)
        ]


def get_panels(n, panels=[(0, 0, 1080, 1920)], min_size=(227, 225),
               split_on_width=None):
    if n == 1:
        return sorted(panels, key=lambda p: (p[0], p[1]))

    min_width, min_height = min_size

    split = None
    bound_stracture = False
    if split_on_width is not None:
        spliter = split_on_width.pop(0)
        if spliter is not None:
            split = spliter
            bound_stracture = True

    if len(panels) == 1 or not bound_stracture:
        available_panels = []
        for i, panel in enumerate(panels):
            if panel[2] - min_width >= min_width or panel[3] - min_height >= min_height:
                available_panels.append(i)

        if not available_panels:
            return panels
    else:
        available_panels = list(range(1, len(panels)))

    i = random.choice(available_panels)
    to_split = panels.pop(i)
    panels.extend(split_rec(to_split, min_size, split_on_width=split))

    return get_panels(n-1, panels, min_size, split_on_width)
