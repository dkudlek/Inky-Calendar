from PIL import Image, ImageDraw, ImageFont, ImageOps

def get_line_height(font):
    return font.getsize('Äj')[1]

def write_text(box_width, box_height, text, font, alignment='middle'):
    max_text_height = get_line_height(font)
    sections = text.splitlines()  # split on new line
    num_lines = int(box_height / max_text_height)
    y = int((box_height - (num_lines * max_text_height))/2.)
    lines = []
    for section in sections:
        words = section.split()
        line = words[0]
        for word in words[1:]:
            if font.getsize("{} {}".format(line, word))[0] < box_width:
                line = "{} {}".format(line, word)
            else:
                lines.append(line)
                line = word
        lines.append(line)
    image = Image.new('RGB', (box_width, box_height), color='white')
    for i in range(num_lines):
        if i < len(lines):
            if i < (num_lines - 1):
                subimage = write_line(box_width, max_text_height, lines[i], font, alignment=alignment)
                image.paste(subimage, (0, y))
                y += max_text_height
            else:
                subimage = write_line(box_width, max_text_height, ' '.join(lines[i:]), font, alignment=alignment)
                image.paste(subimage, (0, y))
    return image

def write_line(box_width, box_height, text, font, alignment='middle'):
    text_width, text_height = font.getsize(text)
    if text_width > box_width:
        letters = int(box_width / (text_width / len(text)))
        text=text[0:letters-3] + '...'
        text_width, text_height = font.getsize(text)
    x = 0 if alignment is 'left' else int((box_width / 2) - (text_width / 2))
    y = int((box_height / 2) - (text_height / 1.7))
    space = Image.new('RGB', (box_width, box_height), color='white')
    ImageDraw.Draw(space).text((x, y), text, fill='black', font=font)
    return space
