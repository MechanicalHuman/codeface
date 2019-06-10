#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2015  Andrew Kensler
# Modifications Copyright 2017 David van Gemeren and Christopher Simpkins
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

# Render dark on light
#    python render_highlight.py -t specimen/samplecode.c -x 2175 -i ../images/hack-light.png -f "Hack 14" -p 20 --style light

# Render light on dark
#    python render_highlight.py -t specimen/samplecode.c -x 2175 -i ../images/hack-dark.png -f "Hack 14" -p 20 --style dark

import sys
import argparse
import re
import cairo
import pango
import pangocairo

from styles.colors import SyntaxHighlighter
from specimens.sourcecode import c_specimen
from utilities.ink import Template, Renderer

RESOLUTION = 144

# Basic argument parsing
parser = argparse.ArgumentParser(
    description = "Render sample images of fonts using Pango/Cairo.",
    formatter_class = argparse.ArgumentDefaultsHelpFormatter )
parser.add_argument( "-t", "--text", default = "sample.txt",
                     help = "name of sample text to render" )
parser.add_argument( "-r", "--regular", action="store_true",
                     help = "regular only, ignore bold and italic in style" )
parser.add_argument( "-i", "--image", default = "sample.png",
                     help = "name of image to write" )
parser.add_argument( "-f", "--font", default = "monospace 15",
                     help = "Pango specification for font to use" )
parser.add_argument( "-m", "--mode", default = "subpixel",
                     choices = [ "grey", "bilevel", "subpixel" ],
                     help = "antialiasing mode" )
parser.add_argument( "-p", "--pad", default = 4, type = int,
                     help = "padding in pixels around image" )
parser.add_argument( "-x", "--width", default = 0, type = int,
                     help = "minimum width of image to generate" )
parser.add_argument( "-y", "--height", default = 0, type = int,
                     help = "minimum height of image to generate" )

parser.add_argument( "-s", "--style", default = "light",
                     help = "Custom style to render sample in",
                     choices = ['light', 'dark'] )

args = parser.parse_args()

# Set style_keys via the 'style' argument
syntax_highlighter = SyntaxHighlighter()
if args.style == 'light':
    style_keys = syntax_highlighter.light
elif args.style == 'dark':
    style_keys = syntax_highlighter.dark
else:
    sys.stderr.write("ERROR: Please include 'light' or 'dark' as the argument to the style option in your command")
    sys.exit(1)

# Parse tags in code specimen template and replace with appropriate definitions
specimen_template = Template(c_specimen)
specimen_renderer = Renderer(specimen_template, style_keys)
text = specimen_renderer.render()

# Substitute Pango markup formatting
text = re.sub( "style=\"color: (#[0-9A-Fa-f]{6})(?:; )?",
               "foreground=\"\\1\" style=\"", text )
if args.regular:
    text = re.sub( "style=\"font-weight: bold(?:; )?",
                   "style=\"", text )
    text = re.sub( "style=\"font-style: italic(?:; )?",
                   "style=\"", text )
else:
    text = re.sub( "style=\"font-weight: bold(?:; )?",
                   "weight=\"bold\" style=\"", text )
    text = re.sub( "style=\"font-style: italic(?:; )?",
                   "style=\"italic\" style=\"", text )
text = re.sub( "style=\"background-color: (#[0-9A-Fa-f]{6})(?:; )?",
               "background=\"\\1\" style=\"", text )
text = re.sub( "style=\"\"", "", text )
text = text.strip()

# First pass, find image size to hold the text.
mode = { "grey" : -1,
         "bilevel" : cairo.ANTIALIAS_NONE,
         "subpixel" : cairo.ANTIALIAS_SUBPIXEL
       }[ args.mode ]
pangocairo.cairo_font_map_get_default().set_resolution( RESOLUTION )
surface = cairo.ImageSurface( cairo.FORMAT_ARGB32, 0, 0 )
context = pangocairo.CairoContext( cairo.Context( surface ) )
layout = context.create_layout()
options = cairo.FontOptions()
options.set_antialias( mode )
pangocairo.context_set_font_options( layout.get_context(), options )
layout.set_font_description( pango.FontDescription( args.font ) )
layout.set_markup( text )
width = max( layout.get_pixel_size()[ 0 ] + args.pad * 2, args.width )
height = max( layout.get_pixel_size()[ 1 ] + args.pad * 2, args.height )

# Second pass, render actual image and save it.
surface = cairo.ImageSurface( cairo.FORMAT_ARGB32, width, height )
context = pangocairo.CairoContext( cairo.Context( surface ) )
layout = context.create_layout()
options = cairo.FontOptions()
options.set_antialias( mode )
pangocairo.context_set_font_options( layout.get_context(), options )
layout.set_font_description( pango.FontDescription( args.font ) )
layout.set_markup( text )

# Set background_color to value defined by the chosen style.
# The alpha-channel for the background defaults to 100%
background_color = style_keys['bg']
context.set_source_rgba(
    int( background_color[ 1 : 3 ], 16 ) / 255.0,
    int( background_color[ 3 : 5 ], 16 ) / 255.0,
    int( background_color[ 5 : 7 ], 16 ) / 255.0,
    1)
context.rectangle( 0, 0, width, height )
context.fill()

context.set_source_rgb( 0, 0, 0 )
context.translate( args.pad, args.pad )
context.update_layout( layout )
context.show_layout( layout )
with open( args.image, "wb" ) as result:
    surface.write_to_png( result )
