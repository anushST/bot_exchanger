import cairosvg


with open('svg.svg', 'r') as svg_file:
    svg_content = svg_file.read()


cairosvg.svg2png(bytestring=svg_content, write_to='svg.png')


from PIL import Image
image = Image.open('svg.png')
rgb_image = image.convert('RGB')
rgb_image.save('svg1.jpeg', quality=95)
