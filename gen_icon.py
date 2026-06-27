from PIL import Image, ImageDraw, ImageFont

# 512x512 icon
img = Image.new('RGBA', (512, 512), (15, 23, 42, 255))
draw = ImageDraw.Draw(img)

# Draw a bolt symbol
draw.rounded_rectangle([96, 64, 416, 448], radius=64, fill=(30, 58, 138, 255))

# Lightning bolt polygon
bolt = [(272, 96), (176, 288), (240, 288), (224, 416), (336, 224), (272, 224), (288, 96)]
draw.polygon(bolt, fill=(245, 158, 11, 255))

img.save('simulator/icon-512.png')

# 192x192
img192 = img.resize((192, 192), Image.LANCZOS)
img192.save('simulator/icon-192.png')

print('Icons generated')
