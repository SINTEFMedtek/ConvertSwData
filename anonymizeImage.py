from PIL import Image  
import os
import sys

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
    
    
def _convertFolder(folderPathIn):
    for root, dirs, files in os.walk(folderPathIn):
        for file_i in files:
            filePath = os.path.join(root, file_i)
 
            imData = readImage(filePath)
            if imData:
                print "Image file: " +  os.path.basename(filePath)
                filePathOut = filePath
                try:
                    imDataOut = anonymizeImage(imData, pixelsX=range(230, 1500), pixelsY=range(7, 43), color=(190, 192, 194))
                    saveImage(filePathOut, imDataOut)
                except Exception as e:
                    print str(e)
                    print "File: "+ filePath
  
if __name__ == '__main__':
    
    print sys.argv
    if len(sys.argv)==2:
        _convertFolder(sys.argv[1])