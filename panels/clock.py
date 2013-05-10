import logging
import datetime
import fontlib
import base


class ClockPanel(base.Panel):
    def __init__(self):
        self.clock_font = fontlib.get('tempesta', 32)
        self.time_format = base.CONFIG['clock_format']
        self.previous_timeofday = None

    def update(self):
        self.timeofday = str(datetime.datetime.now().strftime(self.time_format))
        if self.timeofday != self.previous_timeofday:
            self.previous_timeofday = self.timeofday
            logging.debug('Redrawing the clock')
            self.needs_redraw = True

    def paint(self, framebuffer):
        framebuffer.fill(0)
        framebuffer.center_text(self.clock_font, self.timeofday)

    def up_pressed(self):
        pass

    def down_pressed(self):
        pass

    def center_pressed(self):
        pass
