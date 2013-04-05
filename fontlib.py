#!/usr/bin/env python
# -*- coding: utf-8 -*-
import freetype
import graphics

class Bitmap(object):
    """
    A 2D bitmap image represented as a list of byte values. Each byte indicates the state
    of a single pixel in the bitmap. A value of 0 indicates that the pixel is `off`
    and any other value indicates that it is `on`.
    """
    def __init__(self, width, height, pixels=None):
        self.width = width
        self.height = height
        self.pixels = pixels or bytearray(width * height)

    def __repr__(self):
        """Return a string representation of the bitmap's pixels."""
        rows = ''
        for y in range(self.height):
            for x in range(self.width):
                rows += '*' if self.pixels[y * self.width + x] else '.'
            rows += '\n'
        return rows

    def bitblt(self, src, x, y):
        """Copy all pixels from `src` into this bitmap"""
        srcpixel = 0
        dstpixel = y * self.width + x
        row_offset = self.width - src.width

        for sy in xrange(src.height):
            for sx in xrange(src.width):
                # Perform an OR operation on the destination pixel and the source pixel
                # because glyph bitmaps may overlap if character kerning is applied, e.g.
                # in the string "AVA", the "A" and "V" glyphs must be rendered with
                # overlapping bounding boxes.
                self.pixels[dstpixel] = self.pixels[dstpixel] or src.pixels[srcpixel]
                srcpixel += 1
                dstpixel += 1
            dstpixel += row_offset

class Glyph(object):
    def __init__(self, pixels, width, height, top, advance_x):
        self.bitmap = Bitmap(width, height, pixels)

        # The glyph bitmap's top-side bearing, i.e. the vertical distance from the
        # baseline to the bitmap's top-most scanline.
        self.top = top

        # The glyph's advance width in pixels.
        self.advance_x = advance_x

    @property
    def width(self):
        return self.bitmap.width

    @property
    def height(self):
        return self.bitmap.height

    @staticmethod
    def from_glyphslot(slot):
        """Construct and return a Glyph object from a FreeType GlyphSlot."""
        pixels = Glyph.unpack_mono_bitmap(slot.bitmap)
        width, height = slot.bitmap.width, slot.bitmap.rows
        top = slot.bitmap_top

        # The advance width is given in FreeType's 26.6 fixed point format,
        # which means that the pixel values are multiples of 64.
        advance_x = slot.advance.x / 64

        return Glyph(pixels, width, height, top, advance_x)

    @staticmethod
    def unpack_mono_bitmap(bitmap):
        """
        Unpack a freetype FT_LOAD_TARGET_MONO glyph bitmap into a bytearray where each
        pixel is represented by a single byte.
        """
        # Allocate a bytearray of sufficient size to hold the glyph bitmap.
        data = bytearray(bitmap.rows * bitmap.width)

        # Iterate over every byte in the glyph bitmap. Note that we're not
        # iterating over every pixel in the resulting unpacked bitmap --
        # we're iterating over the packed bytes in the input bitmap.
        for y in range(bitmap.rows):
            for byte_index in range(bitmap.pitch):

                # Read the byte that contains the packed pixel data.
                byte_value = bitmap.buffer[y * bitmap.pitch + byte_index]

                # We've processed this many bits (=pixels) so far. This determines
                # where we'll read the next batch of pixels from.
                num_bits_done = byte_index * 8

                # Pre-compute where to write the pixels that we're going
                # to unpack from the current byte in the glyph bitmap.
                rowstart = y * bitmap.width + byte_index * 8

                # Iterate over every bit (=pixel) that's still a part of the
                # output bitmap. Sometimes we're only unpacking a fraction of a byte
                # because glyphs may not always fit on a byte boundary. So we make sure
                # to stop if we unpack past the current row of pixels.
                for bit_index in range(0, min(8, bitmap.width - num_bits_done)):

                    # Unpack the next pixel from the current glyph byte.
                    bit = byte_value & (1 << (7 - bit_index))

                    # Write the pixel to the output bytearray. We ensure that `off`
                    # pixels have a value of 0 and `on` pixels have a value of 1.
                    data[rowstart + bit_index] = 1 if bit else 0

        return data

class Font(object):
    def __init__(self, filename, size):
        self.face = freetype.Face(filename)
        self.face.set_pixel_sizes(0, size)
        self.glyphcache = {}

    def glyph_for_character(self, char):
        # Let FreeType load the glyph for the given character and tell it to render
        # a monochromatic bitmap representation.
        if char in self.glyphcache:
            return self.glyphcache[char]

        print 'Loading char', char
        self.face.load_char(char, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_TARGET_MONO)
        glyph = Glyph.from_glyphslot(self.face.glyph)
        self.glyphcache[char] = glyph

        return glyph

    def render_character(self, char):
        glyph = self.glyph_for_character(char)
        return glyph.bitmap

    def kerning_offset(self, previous_char, char):
        """
        Return the horizontal kerning offset in pixels when rendering `char`
        after `previous_char`.

        Use the resulting offset to adjust the glyph's drawing position to
        reduces extra diagonal whitespace, for example in the string "AV" the
        bitmaps for "A" and "V" may overlap slightly with some fonts. In this
        case the glyph for "V" has a negative horizontal kerning offset as it is
        moved slightly towards the "A".
        """
        kerning = self.face.get_kerning(previous_char, char)

        # The kerning offset is given in FreeType's 26.6 fixed point format,
        # which means that the pixel values are multiples of 64.
        return kerning.x / 64

    def text_dimensions(self, text):
        """Return (width, height, baseline) of `text` rendered in the current font."""
        width, height, baseline = 0, 0, 0
        previous_char = None

        # For each character in the text string we load its glyph bitmap
        # and update TODO
        for char in text:
            glyph = self.glyph_for_character(char)

            # Update the overall height and baseline.
            height = max(height, glyph.height)
            baseline = max(baseline, max(0, glyph.height - glyph.top))

            kerning_x = self.kerning_offset(previous_char, char)

            # The advance width may be less than the width of the glyph's bitmap.
            # Make sure we compute the total width so that all of the glyph's pixels
            # fit into the returned dimensions.
            width += max(glyph.advance_x + kerning_x, glyph.width + kerning_x)

            previous_char = char

        return (width, height + baseline, baseline)

    def render_text(self, text, width=None, height=None, baseline=None):
        """
        Render the given `text` into a Bitmap and return it.

        If `width`, `height`, and `baseline` are not specified they are computed using
        the `text_extents' function.
        """
        if width is None or height is None or baseline is None:
            width, height, baseline = self.text_dimensions(text)

        x, y = 0, 0
        previous_char = None
        outbuffer = Bitmap(width, height)

        for char in text:
            # Adjust the glyph's drawing position if kerning information in the
            # font tells us so. This reduces extra diagonal whitespace, for example
            # in the string "AV" the bitmaps for "A" and "V" overlap slightly.
            x += self.kerning_offset(previous_char, char)

            glyph = self.glyph_for_character(char)
            y = height - baseline - min(glyph.top, glyph.height)

            outbuffer.bitblt(glyph.bitmap, x, y)

            x += glyph.advance_x

            previous_char = char

        return outbuffer

    def text_extents(self, text):
        return self.text_dimensions(text)

    def render(self, text, width=None, height=None, baseline=None):
        bmp = self.render_text(text, width, height, baseline)
        return graphics.Surface(bmp.width, bmp.height, pixels=bmp.pixels)


if __name__ == '__main__':
    f = Font('test-apps/font4.ttf', 16)
    text = u'22:50'
    # text = 'T,'
    width, height, baseline = f.text_extents(text)
    print '"%s": width=%i height=%i baseline=%i' % (text, width, height, baseline)
    print f
    print repr(f.render(text))
    # print f.size

    # global unpack_mono_bitmap
    # global unpack_mono_bitmapX
    # tmp = unpack_mono_bitmap
    # unpack_mono_bitmap = unpack_mono_bitmapX
    # unpack_mono_bitmapX = tmp
    # f = Font('test-apps/font4.ttf', 16)
    # print repr(f.render(text))

    import random
    import string
    def random_string(l):
        return ''.join( random.choice(string.ascii_letters + string.digits) for n in xrange(l) )

    def benchmark():
        # for c in string.ascii_letters + string.digits:
        #     f.render(c)
        for i in xrange(500):
            f.render(random_string(30))

    import cProfile
    import pstats
    cProfile.run('benchmark()', 'fontbench.profile')
    p = pstats.Stats('fontbench.profile')
    print p.sort_stats('cumulative').print_stats(20)
    print p.sort_stats('time').print_stats(20)