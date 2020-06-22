"""Provide utilities for working with the solids.

At this time it supports basic colouring.
"""

COLOURS = {
    'darkblue':             '#00008B',
    'darkcyan':             '#008B8B',
    'darkgoldenrod':        '#B8860B',
    'darkgray':             '#A9A9A9',
    'darkgreen':            '#006400',
    'darkkhaki':            '#BDB76B',
    'darkmagenta':          '#8B008B',
    'darkolivegreen':       '#556B2F',
    'darkorange':           '#FF8C00',
    'darkorchid':           '#9932CC',
    'darkred':              '#8B0000',
    'darksalmon':           '#E9967A',
    'darkseagreen':         '#8FBC8F',
    'darkslateblue':        '#483D8B',
    'darkslategray':        '#2F4F4F',
    'darkturquoise':        '#00CED1',
    'darkviolet':           '#9400D3',
    'deeppink':             '#FF1493',
    'deepskyblue':          '#00BFFF',
}

def rgb_colours():
    for hex_string in COLOURS.values():
        yield hex_to_rgb(hex_string)

def hex_to_rgb(hex_string):
    if hex_string.startswith('#'):
        hex_string = hex_string[1:]

    red = int(hex_string[0:2], base=16)
    green = int(hex_string[2:4], base=16)
    blue  = int(hex_string[4:6], base=16)
    return red, green, blue
