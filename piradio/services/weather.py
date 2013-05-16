# http://openweathermap.org/wiki/API/JSON_API

import urllib2
import json
import logging
import base


class WeatherService(base.AsyncService):
    def __init__(self):
        super(WeatherService, self).__init__(tick_interval=60*60)
        config = json.loads(open('config.json').read())
        self.apikey = config['forecastio_api_key']
        logging.info('WeatherService fcast.io api key = %s', self.apikey)

    def get_forecast(self, lat, lon):
        forecastio_url = ('https://api.forecast.io/forecast/%s/%f,%f?units=si'
                          % (self.apikey, lat, lon))
        try:
            data = json.load(urllib2.urlopen(forecastio_url))
            return data['hourly']['icon'], data['hourly']['summary']
        except:
            return 'error', 'Error pulling forecast data o_O'

    def tick(self):
        super(WeatherService, self).tick()
        locations = self.subscriptions.keys()
        logging.info('%s: Pulling weather data for %i locations',
                     self.__class__.__name__, len(locations))
        for lat, lon in locations:
            logging.info('Pulling weather for %f, %f...', lat, lon)
            icon, summary = self.get_forecast(lat, lon)
            logging.info('%f,%f: %s, %s', lat, lon, icon, summary)
            self.notify_subscribers((lat, lon), icon, summary)

_instance = None


def instance():
    if not _instance:
        logging.info('Creating WeatherService instance')
        global _instance
        _instance = WeatherService()
        _instance.start()
    return _instance
