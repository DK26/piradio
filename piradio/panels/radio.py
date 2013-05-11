from piradio.panels import base
from .. import fonts
from .. import ui
from .. import commons
from ..services import audio
import logging
import json

GLYPH_PLAYING = '0'


class RadioPanel(base.Panel):
    def __init__(self):
        super(RadioPanel, self).__init__()
        self.font = fonts.get('tempesta', 8)
        self.glyph_font = fonts.get('pixarrows', 10)
        self.stations = json.loads(open('stations.json').read())

        self.cy = 0
        self.currstation = ''
        self.prev_timestr = ''
        self.timestr = None
        self.needs_redraw = True

    def update(self):
        self.update_clock()

    def paint(self, surface):
        # Clear the surface
        surface.fill(0)

        # If necessary, draw the 'playing' icon and the
        # current station's name.
        if self.currstation:
            surface.text(self.glyph_font, -3, 0, GLYPH_PLAYING)
            surface.text(self.font, 7, 2, self.currstation)

        # Draw the clock
        w, h, baseline = self.font.text_dimensions(self.timestr)
        surface.text(self.font, surface.width - w, 2, self.timestr)

        # Draw separator between the 'status area' and the station selector
        surface.hline(11)

        # Draw the station selector
        ui.render_list(surface, 2, 14, self.font, self.stations.keys(),
                       self.cy, minheight=12, maxvisible=4)

    def up_pressed(self):
        self.cy -= 1
        self.cy = commons.clamp(self.cy, 0, len(self.stations) - 1)
        self.needs_redraw = True

    def down_pressed(self):
        self.cy += 1
        self.cy = commons.clamp(self.cy, 0, len(self.stations) - 1)
        self.needs_redraw = True

    def center_pressed(self):
        if self.currstation == self.stations.keys()[self.cy]:
            logging.debug('Stopping playback')
            audio.stop()
            self.currstation = ''
        else:
            logging.debug('Switching station')
            audio.playstream(self.stations.values()[self.cy], fade=False)
            self.currstation = self.stations.keys()[self.cy]
        self.needs_redraw = True

    def update_clock(self):
        self.timestr = commons.timeofday()
        if self.timestr != self.prev_timestr:
            self.prev_timestr = self.timestr
            logging.debug('Redrawing the clock')
            self.needs_redraw = True
