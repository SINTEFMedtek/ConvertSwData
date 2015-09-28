from PIL import Image  

def readImage(filePathIn):
    try:
        picture = Image.open(filePathIn)
    except IOError:
        return None
        # filename not an image file
    return picture

def saveImage(filePathOut, picture):
    # save picture
    picture.save(filePathOut)

def anonymizeImage(picture, pixelsX=None, pixelsY=None, color=(0, 0, 0)):

    pixels = picture.load()

    # Get the size of the image
    width, height = picture.size

    if not pixelsX:
        pixelsX = range(width)

    if not pixelsY:
        pixelsY = range(height)

    # Process given pixels
    for x in pixelsX:
        if x >= width:
            continue
        for y in pixelsY:
            if y >= height:
                continue
            pixels[x, y] = color
    return picture