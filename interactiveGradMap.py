#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
sys.stderr = open("er.txt", 'w')  # for debugging

import gimp, gimpplugin, math
pdb = gimp.pdb
from gimpenums import *

import gtk, gimpui, gimpcolor, gobject

def make_label(text, show = True):
    label = gtk.Label(text)
    label.set_use_underline(True)
    label.set_alignment(1.0, 0.5)
    if show:
      label.show()
    return label

class GradientMapPlugin(gimpplugin.plugin):
  shelfkey = "gradientmap-vars"
  desaturation_modes = ( DESATURATE_LIGHTNESS, DESATURATE_LUMA, DESATURATE_AVERAGE, DESATURATE_LUMINANCE, DESATURATE_VALUE )
  
  def start(self):
    gimp.main(self.init, self.quit, self.query, self._run)
    
  def init(self):
    pass

  def quit(self):
    pass

  def query(self):
    authorname = "Tyler Johnson"
    copyrightname = "Tyler Johnson"
    menupath = "<Image>/Colors/Interactive Gradient Map..."
    date = "October 2024"
  
    gradient_map_description = "Remaps the colors in the layer to a gradient using luminance."
    gradient_map_help = "Remaps the colors in the layer to a gradient using luminance."
    gradient_map_params = (
      (PDB_INT32,    "run_mode",      "Run mode"),
      (PDB_IMAGE,    "image",         "Input image"),
      (PDB_DRAWABLE, "drawable",      "Input drawable"),
    )
    gimp.install_procedure(
      "python_gradient_map",
      gradient_map_description,
      gradient_map_help,
      authorname,
      copyrightname,
      date,
      menupath,
      "RGB*, GRAY*",
      PLUGIN,
      gradient_map_params,
      []
    )
    
  def make_desturation_mode_box(self):
    return gimpui.IntComboBox((
      "Luminance", DESATURATE_LUMINANCE,
      "Luma",      DESATURATE_LUMA,
      "Lightness", DESATURATE_LIGHTNESS,
      "Average",   DESATURATE_AVERAGE,
      "Value",     DESATURATE_VALUE,
    ))
  
  def python_gradient_map(self, runmode, img, drawable):
    self.img = img
    self.drawable = drawable
    
    dialog = gimpui.Dialog("Gradient Map", "gradientmapdialog")
    
    # can create a copy of drawable for preview by using drawable.copy()
    # this will be saved for preview purposes.
    # If preview mode is selected, we'll just render directly to existing drawable
    
    # get selection bounds from drawable.mask_bounds
    # get pixel regions with drawable.get_pixel_rgn(fill with data from bounds)
    # edit pixel regions with array notation: rgn[x1:x2, y1:y2]
    
    # convert to grayscale: pdb.gimp_drawable_desaturate(drawable, DESATURATION_MODE)
    # NEED TO RESEARCH THIS MORE, seems to break occasionally.
    
    self.original = drawable.copy()
    
    # Desaturation selectionS
    self.desaturate_hbox = gtk.HBox(False, 5)
    self.desaturate_hbox.show()
    dialog.vbox.add(self.desaturate_hbox)
    
    self.desaturation_label = make_label("Desaturation Mode:")
    self.desaturation_mode_selector = self.make_desturation_mode_box()
    self.desaturation_mode_selector.show()
    self.desaturation_mode_selector.set_active(DESATURATE_LUMINANCE)
    self.desaturation_mode_selector.connect("changed", self.preview) # Trigger afterwards so we don't get any problems
    self.desaturate_hbox.add(self.desaturation_label)
    self.desaturate_hbox.add(self.desaturation_mode_selector)
    
    # Color selection
    self.color_hbox = gtk.HBox(False, 3)
    
    self.color1Label = make_label("Dark Color:")
    self.color1 = gimpui.ColorButton("Dark Color", 80, 0, pdb.gimp_context_get_foreground())
    self.color1.set_update(True) # continuously update as color is changed
    self.color1.connect("color-changed", self.preview)
    self.color1.show()
    self.color_hbox.add(self.color1Label)
    self.color_hbox.add(self.color1)
    
    self.color2Label = make_label("Light Color:")
    self.color2 = gimpui.ColorButton("Light Color", 80, 0, pdb.gimp_context_get_background())
    self.color2.set_update(True) # continuously update as color is changed
    self.color2.connect("color-changed", self.preview)
    self.color2.show()
    self.color_hbox.add(self.color2Label)
    self.color_hbox.add(self.color2)
    
    self.color_hbox.show()
    dialog.vbox.add(self.color_hbox)
    
    # Preview toggle
    self.previewCheck = gtk.CheckButton("Preview")
    self.previewCheck.connect("toggled", self.preview)
    self.previewCheck.set_active(True)
    self.previewCheck.show()
    dialog.vbox.add(self.previewCheck)
    
    # Dialog buttons
    if gtk.alternative_dialog_button_order():
      ok_button = dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
      cancel_button = dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
    else:
      cancel_button = dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
      ok_button = dialog.add_button(gtk.STOCK_OK, gtk.RESPONSE_OK)
    ok_button.connect("clicked", self.ok_button)
    
    
    dialog.show()
    self.preview(None)  # Call once to load preview
    if dialog.run() != gtk.RESPONSE_OK:
      self.removePreview()
        
    dialog.destroy()
    
    gimp.displays_flush()
    # Extra check to make sure undo is re-enabled after plugin runs
    if not pdb.gimp_image_undo_is_enabled(self.img):
      pdb.gimp_image_undo_thaw(self.img)
  
  def preview(self, widget):
    if self.previewCheck.get_active():
      if pdb.gimp_image_undo_is_enabled(self.img):
        pdb.gimp_image_undo_freeze(self.img)
      self.apply(
                 self.img, 
                 self.drawable,
                 self.desaturation_mode_selector.get_active(),
                 self.color1.get_color(),
                 self.color2.get_color()
                )
    else:
      self.removePreview()
      gimp.displays_flush()
      
  def ok_button(self, widget):
    if not pdb.gimp_image_undo_is_enabled(self.img):
      pdb.gimp_image_undo_thaw(self.img)
    self.apply(
               self.img, 
               self.drawable,
               self.desaturation_mode_selector.get_active(),
               self.color1.get_color(),
               self.color2.get_color()
              )
  
  def apply(self, img, drawable, desaturation_mode, dark_color, light_color):
    pdb.gimp_image_undo_group_start(self.img)
    
    self.removePreview()
    
    orig_foreground = pdb.gimp_context_get_foreground()
    orig_background = pdb.gimp_context_get_background()
    
    pdb.gimp_context_set_foreground(self.color1.get_color())
    pdb.gimp_context_set_background(self.color2.get_color())
    
    pdb.gimp_drawable_desaturate(self.drawable, self.desaturation_mode_selector.get_active())
    
    pdb.plug_in_gradmap(self.img, self.drawable)
    
    pdb.gimp_context_set_foreground(orig_foreground)
    pdb.gimp_context_set_background(orig_background)
    
    pdb.gimp_image_undo_group_end(self.img)
    
    gimp.displays_flush()
   
  def removePreview(self):
    mask_bounds = self.drawable.mask_bounds
    org_rgn = self.original.get_pixel_rgn(mask_bounds[0], mask_bounds[1], mask_bounds[2] - mask_bounds[0], mask_bounds[3] - mask_bounds[1])
    tgt_rgn = self.drawable.get_pixel_rgn(mask_bounds[0], mask_bounds[1], mask_bounds[2] - mask_bounds[0], mask_bounds[3] - mask_bounds[1])
    # biiiiiig copy
    tgt_rgn[mask_bounds[0]:mask_bounds[2], mask_bounds[1]:mask_bounds[3]] \
      = org_rgn[mask_bounds[0]:mask_bounds[2], mask_bounds[1]:mask_bounds[3]]
    self.drawable.update(tgt_rgn.x, tgt_rgn.y, tgt_rgn.w, tgt_rgn.h)
    
   
if __name__ == "__main__":
  GradientMapPlugin().start()

sys.stderr = open(os.path.devnull, 'a')  # restore stderr