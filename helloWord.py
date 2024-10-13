#!/usr/bin/python
import math
from gimpfu import *

def python_clothify(timg, tdrawable, bx=9, by=9,
		    azimuth=135, elevation=45, depth=3):
	bx = 9 ; by = 9 ; azimuth = 135 ; elevation = 45 ; depth = 3
	width = tdrawable.width
	height = tdrawable.height
	img = pdb.gimp_image_new(width, height, RGB)
	layer_one = pdb.gimp_layer_new(img, width, height, RGB_IMAGE, "X Dots",
			       100, NORMAL_MODE)
	img.add_layer(layer_one, 0)
	img.disable_undo()
	pdb.gimp_edit_fill(layer_one, FILL_FOREGROUND)
	pdb.plug_in_noisify(img, layer_one, 0, 0.7, 0.7, 0.7, 0.7)
	layer_two = layer_one.copy()
	layer_two.mode = MULTIPLY_MODE
	layer_two.name = "Y Dots"
	img.add_layer(layer_two, 0)
	pdb.plug_in_gauss_rle(img, layer_one, bx, 1, 0)
	pdb.plug_in_gauss_rle(img, layer_two, by, 0, 1)
	img.flatten()
	bump_layer = img.active_layer
	pdb.plug_in_c_astretch(img, bump_layer)
	pdb.plug_in_noisify(img, bump_layer, 0, 0.2, 0.2, 0.2, 0.2)
	pdb.plug_in_bump_map(img, tdrawable, bump_layer, azimuth,
			     elevation, depth, 0, 0, 0, 0, TRUE, FALSE, 0)
	gimp.delete(img)

register(
	"python_my_plugin",
	"Make the specified layer look like it is printed on cloth",
	"Make the specified layer look like it is printed on cloth",
	"James Henstridge",
	"James Henstridge",
	"1997-1999",
	"<Image>/Filters/Misc",
	"RGB*, GRAY*",
	[
		(PF_INT, "x_blur", "X Blur", 9),
		(PF_INT, "y_blur", "Y Blur", 9),
		(PF_INT, "azimuth", "Azimuth", 135),
		(PF_INT, "elevation", "elevation", 45),
		(PF_INT, "depth", "Depth", 3)
	],
	[],
	python_clothify)

main()