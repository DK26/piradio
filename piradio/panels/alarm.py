from piradio.panels import base
from .. import fonts
from .. import lcd
from ..services import audio
import time


class AlarmPanel(base.Panel):
    def __init__(self, audio_service):
        super(AlarmPanel, self).__init__()
        self.font = fonts.get('tempesta', 32)
        self.prev_timestr = None
        self.countdown = 60 * 3
        self.alarmtime = None
        self.countdown_str = self.countdownstring()
        self.state = 'SET_TIME'
        self.stepsize = 60
        self.audio_service = audio_service

    def fire_alarm(self):
        self.state = 'ALARM'
        self.alarmtime = None
        self.audio_service.playfile('assets/alarm.mp3')

    def countdownstring(self):
        remaining = int(self.alarmtime - time.time()
                        if self.alarmtime else self.countdown)
        minutes = remaining / 60
        seconds = remaining - minutes * 60
        return '%.2i:%.2i' % (minutes, seconds)

    def update(self):
        if self.state == 'COUNTDOWN':
            if self.alarmtime and time.time() >= self.alarmtime:
                self.fire_alarm()
        elif self.state == 'ALARM':
            lcd.set_backlight_enabled(bool(int(time.time()) % 2 == 0))
        if self.countdown_str != self.countdownstring():
            self.countdown_str = self.countdownstring()
            self.set_needs_repaint()

    def paint(self, surface):
        surface.fill(0)
        surface.center_text(self.font, self.countdown_str)

    def up_pressed(self):
        self.countdown += self.stepsize
        self.set_needs_repaint()

    def down_pressed(self):
        self.countdown = max(0, self.countdown - self.stepsize)
        self.set_needs_repaint()

    def center_pressed(self):
        if self.state == 'SET_TIME':
            self.state = 'COUNTDOWN'
            self.alarmtime = (time.time() + self.countdown
                              if not self.alarmtime else None)
        elif self.state == 'ALARM':
            lcd.set_backlight_enabled(True)
            self.state = 'SET_TIME'
        self.set_needs_repaint()
