from PIL import Image, ImageDraw, ImageFont, ImageOps

def write_text(box_width, box_height, text, font, alignment='middle'):
    max_text_height = font.getsize('Äj')[1]
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


#if __name__ == "__main__":
#    import yaml
#    from pathlib import Path
#    config = None
#    home = Path(__file__).absolute().parents[1]
#    with open(str(home /"settings.yaml"), 'r') as stream:
#        try:
#            config = yaml.safe_load(stream)
#            #print(config)
#        except yaml.YAMLError as exc:
#            print(exc)
#    app_style = config['general']['app_style']
#    resources_path = Path(__file__).absolute().parents[1] / 'resources'
#    weekday_style = config['CalenderWidget'][app_style]['weekday']
#    weekday_font = ImageFont.truetype(str(resources_path / (weekday_style['font'])), weekday_style['size'])
#    test_string = 'abc def ghi jkl mno pqr stu vwxyz \nabc def ghi jkl mno pqr stu vwxyz'
#    part = write_line(160, 80, test_string, font=weekday_font, alignment='left')
#    part.show()
#    part = write_text(160, 80, test_string, font=weekday_font, alignment='left')
#    part.show()
