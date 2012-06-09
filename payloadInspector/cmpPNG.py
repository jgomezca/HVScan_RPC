#!/usr/bin/python

import glob
import os
import sys
import binascii

from PIL import Image, ImageChops, ImageDraw, ImageFont
from os import chdir, path


#########
def __rgbColorFinder(rgbImg, colormin=(0,0,0), colormax=(255,255,255), allbands=1, rmode='1'):
    '''analyzes an RGB image, returns an image of the same size where each pixel is
            WHITE if the pixel in rgbImage MATCHES the color range colormin-to-colormax, or 
            BLACK if the pixel in rgbImage DOES NOT MATCH the color range.
        a pixel is MATCHES the color range
            if allbands!=0 and if for EVERY color pixel[i],
                colormin[i]<=pixel[i] and pixel[i]<=colormax[i], or
            if allbands==0 and if for ANY color pixel[i],
                colormin[i]<=pixel[i] and pixel[i]<=colormax[i].
        rmode determines the mode of the returned image ("1", "L" or "RGB")
    '''
    rgbImg.load()
    inbands = rgbImg.split()
    outbands = []
    for srcband, cmin, cmax in zip(inbands, colormin, colormax):
        outbands.append(srcband.point(lambda v1, v2=cmin, v3=cmax: v2<=v1 and v1<=v3 and 255))
    if allbands==0:
        tband = ImageChops.lighter(ImageChops.lighter(outbands[0], outbands[1]), outbands[2])
    else:
        tband = ImageChops.darker(ImageChops.darker(outbands[0], outbands[1]), outbands[2])
    if rmode=='L':
        return tband
    elif rmode=='RGB':
        return Image.merge('RGB', (tband, tband, tband)) # 'RGB'
    else:  # rmode=='1'
        return tband.convert('1')


def __rgbColorReplacer(rgbImg, colormin=(0,0,0), colormax=(32,32,32), colornew=(255,255,255), allbands=1):
    '''analyzes an RGB image,
    finds all colors in the range colormin-to-colormax (see colorFinder()),
    creates and returns, with all found colors replaced by colornew
    '''
    colorMask = __rgbColorFinder(rgbImg, colormin, colormax, allbands=allbands)
    rplImg = Image.new(rgbImg.mode, rgbImg.size, colornew)
    return Image.composite(rplImg, rgbImg, colorMask)

def __txt2img(fileName = "get_plot1.png", text="Hacked by Wirusiux", pos = (10, 10), bg="#ffffff",fg="#000000",font="DejaVuLGCSans-Bold.ttf",FontSize=56):
    """
Writes some text to image file
    """

    font_dir = "/usr/share/fonts/dejavu-lgc/"
    font_size = FontSize
    fnt = ImageFont.truetype(font_dir+font, font_size)
    lineWidth = 20
    img = fileName
    #try:
    #img = Image.open(fileName, 'png')
    #except:
    #    img = fileName
    imgbg = Image.new('RGBA', img.size, "#000000") # make an entirely black image
    mask = Image.new('L',img.size,"#000000")       # make a mask that masks out all
    draw = ImageDraw.Draw(img)                     # setup to draw on the main image
    drawmask = ImageDraw.Draw(mask)                # setup to draw on the mask
    drawmask.line((0, lineWidth/2, img.size[0],lineWidth/2),
                  fill="#999999", width=10)        # draw a line on the mask to allow some bg through
    img.paste(imgbg, mask=mask)                    # put the (somewhat) transparent bg on the main
    draw.text(pos, text, font=fnt, fill=bg)      # add some text to the main
    del draw 
    #img.save(fileName, "PNG")  
    return img

def CmpTrackerSubtr(fileName1 = "get_plot1.png",
               fileName2 = "get_plot2.png",
               result = "difference.png",
               offset = 0,
               debug = False):
    """
    Compares two images
    """
    if debug: print "open ", fileName1
    im1 = Image.open(fileName1)

    if debug: print "open ", fileName2
    im2 = Image.open(fileName2)
    if debug:
        print "sizes: ", im1.size, " " , im2.size
        print "info: " ,im1.info , " " , im2.info
        print "mode: " ,im1.mode , " ", im2.mode

    im1replaced = __rgbColorReplacer(im1, colormin=(0,0,0), colormax=(0,0,0), colornew=(255,255,255), allbands=1)
    im3 = ImageChops.subtract(im1replaced, im2, offset=offset)
    
    im3.save(result)
    __txt2img(result, "The more lighter plots, the higher the difference." ,FontSize=15, pos = (530, 65))
    __txt2img(result, "More RED = First plot values higher, more BLUE = Second plot values higher.", FontSize=15, pos = (530, 85))    
    return result

def CmpTrackerDiff(fileName1 = "get_plot1.png",
               fileName2 = "get_plot2.png",
               result = "difference.png",
               txt = "The more lighter plots, the higher the difference(Absolute difference).",
               debug = False):
    """
    Compares two images
    """
    if debug: print "open ", fileName1
    im1 = Image.open(fileName1)

    if debug: print "open ", fileName2
    im2 = Image.open(fileName2)
    if debug:
        print "sizes: ", im1.size, " " , im2.size
        print "info: " ,im1.info , " " , im2.info
        print "mode: " ,im1.mode , " ", im2.mode

    im1replaced = __rgbColorReplacer(im1, colormin=(0,0,0), colormax=(0,0,0), colornew=(255,255,255), allbands=1)
    im3 = ImageChops.difference(im1replaced, im2)
    #im3.save(result, 'png')
    __txt2img(im3, txt,FontSize=20, pos = (150, 70)).save(result, 'png')
    return result
    
def CmpPlots(fileName1 = "get_plot1.png",
               fileName2 = "get_plot2.png",
               result = "multiply.png",
               debug = False):
    """
    Compares two images
    """
    if debug: print "open ", fileName1
    im1 = Image.open(fileName1)

    if debug: print "open ", fileName2
    im2 = Image.open(fileName2)
    if debug:
        print "sizes: ", im1.size, " " , im2.size
        print "info: " ,im1.info , " " , im2.info
        print "mode: " ,im1.mode , " ", im2.mode

    im1replaced = __rgbColorReplacer(im1, colormin=(0,0,0), colormax=(0,0,0), colornew=(255,0,0), allbands=1)
    im2replaced = __rgbColorReplacer(im2, colormin=(0,0,0), colormax=(0,0,0), colornew=(0,255,0), allbands=1)
    im3 = ImageChops.multiply(im1replaced, im2replaced)
    im3.save(result)
    __txt2img(result, "RED = First plot,  GREEN = Second plot, BLACK = both plots.", FontSize=11, pos = (20, 425), bg="#0000ff",fg="#ff0000")    

if __name__ =="__main__":
    CmpTrackerDiff(fileName1 = "get_plot1.png", fileName2 = "get_plot2.png", result = "difference.png",
                   txt = "ABSOLUTE DIFFERENCE  (The more lighter plots, the higher the difference.)",
                   debug = True)
    CmpTrackerSubtr(fileName1 = "get_plot2.png", fileName2 = "get_plot1.png", result = "subtract.png", debug = True)
    CmpTrackerSubtr(fileName1 = "get_plot1.png", fileName2 = "get_plot2.png", result = "subtract128.png", offset=128, debug = True)
    CmpPlots(fileName1 = "1.png", fileName2 = "2.png", result = "multiply.png", debug = True)
    
