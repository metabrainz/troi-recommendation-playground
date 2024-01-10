# coding=utf-8
from glob import glob
from os.path import isfile, realpath, dirname
import json
from pprint import pprint


class CountryInfo:
    """To access one of the country properties available

    Example:
        country = CountryInfo('singapore')
        pprint(country.info())
    """

    def __init__(self, country_name=None):
        """constructor method

        :param country_name: str
            pass country name
        """
        self.__country_name = country_name.lower() if country_name else ''
        # get the files path
        __file_dir_path = dirname(realpath(__file__))
        __country_files = __file_dir_path + '/data/'
        __files_path = [files for files in glob(__country_files + '*.json')]
        self.__countries = {}
        for file_path in __files_path:
            if isfile(file_path):
                with open(file_path, encoding='utf-8') as file:
                    country_info = json.load(file)
                    # pprint(country_info)
                    if country_info.get('name', None):
                        self.__countries[country_info['name'].lower()] = country_info
                        # Update country name if it is one of alt spellings.
                        if self.__country_name in map(lambda an: an.lower(), country_info.get('altSpellings', [])):
                            self.__country_name = country_info['name'].lower()

    def info(self):
        """Returns all available information for a specified country.

        :return: dict
        """
        if self.__country_name:
            _all = self.__countries[self.__country_name]
            # pprint(_all)

            return _all

    def provinces(self):
        """return provinces list

        :return: list
        """
        if self.__country_name:
            _provinces = self.__countries[self.__country_name]['provinces']
            # pprint(_provinces)

            return _provinces

    def iso(self, alpha=None):
        """Returns ISO codes for a specified country

        :param alpha: int

        :return: dict or str
            based on param
        """
        if self.__country_name:
            _iso = self.__countries[self.__country_name]['ISO']
            # pprint(_iso)

            if alpha == 2:
                return _iso.get('alpha2')
            elif alpha == 3:
                return _iso.get('alpha3')

            return _iso

    def alt_spellings(self):
        """Returns alternate spellings for the name of a specified country

        :return: list
        """
        if self.__country_name:
            try:
                _alt_spellings = self.__countries[self.__country_name]['altSpellings']
                # pprint(_alt_spellings)

                return _alt_spellings
            except KeyError:
                return []

    def area(self):
        """Returns area (km²) for a specified country

        :return: int
        """
        if self.__country_name:
            _area = self.__countries[self.__country_name]['area']
            # pprint(_area)

            return _area

    def borders(self):
        """Returns bordering countries (ISO3) for a specified country

        :return: list
        """
        if self.__country_name:
            _borders = self.__countries[self.__country_name]['borders']
            # pprint(_borders)

            return _borders

    def calling_codes(self):
        """Returns international calling codes for a specified country

        :return: list
        """
        if self.__country_name:
            _calling_codes = self.__countries[self.__country_name]['callingCodes']
            # pprint(_calling_codes)

            return _calling_codes

    def capital(self):
        """Returns capital city for a specified country

        :return: str
        """
        if self.__country_name:
            _capital = self.__countries[self.__country_name]['capital']
            # pprint(_capital)

            return _capital

    def capital_latlng(self):
        """Returns capital city latitude and longitude for a specified country

        :return: str
        """
        if self.__country_name:
            _capital_latlng = self.__countries[self.__country_name]['capital_latlng']
            # pprint(_capital)

            return _capital_latlng

    def currencies(self):
        """Returns official currencies for a specified country

        :return: list
        """
        if self.__country_name:
            _currencies = self.__countries[self.__country_name]['currencies']
            # pprint(_currencies)

            return _currencies

    def demonym(self):
        """Returns the demonyms for a specified country

        :return: str
        """
        if self.__country_name:
            _demonym = self.__countries[self.__country_name]['demonym']
            # pprint(_demonym)

            return _demonym

    def flag(self):
        """Returns SVG link of the official flag for a specified country

        :return: str
            it will return an URL if available
        """
        if self.__country_name:
            _flag = self.__countries[self.__country_name]['flag']
            # pprint(_flag)

            return _flag

    def geo_json(self):
        """Returns geoJSON for a specified country

        :return: dict
        """
        if self.__country_name:
            _geo_json = self.__countries[self.__country_name]['geoJSON']
            # pprint(_geo_json)

            return _geo_json

    def languages(self):
        """Returns official languages for a specified country

        :return: list
        """
        if self.__country_name:
            _languages = self.__countries[self.__country_name]['languages']
            # pprint(_languages)

            return _languages

    def latlng(self):
        """Returns approx latitude and longitude for a specified country

        :return: list
        """
        if self.__country_name:
            _latlng = self.__countries[self.__country_name]['latlng']
            # pprint(_latlng)

            return _latlng

    def name(self):
        """Returns the english name of the country as registered in the library

        :return: str
        """
        return self.__country_name

    def native_name(self):
        """Returns the name of the country in its native tongue

        :return: str
        """
        if self.__country_name:
            _native_name = self.__countries[self.__country_name].get('nativeName')
            # pprint(_native_name)

            return _native_name

    def population(self):
        """Returns approximate population for a specified country

        :return: int
        """
        if self.__country_name:
            _population = self.__countries[self.__country_name]['population']
            # pprint(_population)

            return _population

    def region(self):
        """Returns general region for a specified country

        :return: str
        """
        if self.__country_name:
            _region = self.__countries[self.__country_name]['region']
            # pprint(_region)

            return _region

    def subregion(self):
        """Returns a more specific region for a specified country

        :return: str
        """
        if self.__country_name:
            _subregion = self.__countries[self.__country_name]['subregion']
            # pprint(_subregion)

            return _subregion

    def timezones(self):
        """Returns all timezones for a specified country

        :return: list
        """
        if self.__country_name:
            _timezones = self.__countries[self.__country_name]['timezones']
            # pprint(_timezones)

            return _timezones

    def tld(self):
        """Returns official top level domains for a specified country

        :return: list
        """
        if self.__country_name:
            _tld = self.__countries[self.__country_name]['tld']
            # pprint(_tld)

            return _tld

    def translations(self):
        """Returns translations for a specified country name in popular languages

        :return: dict
        """
        if self.__country_name:
            try:
                _translations = self.__countries[self.__country_name]['translations']
                # pprint(_translations)

                return _translations
            except KeyError:
                return []

    def wiki(self):
        """Returns link to wikipedia page for a specified country

        :return: str
            return wiki url if available
        """
        if self.__country_name:
            _wiki = self.__countries[self.__country_name]['wiki']
            # pprint(_wiki)

            return _wiki

    def all(self):
        """return all of the countries information

        :return: dict
        """
        _all = self.__countries
        # pprint(_all)

        return _all


if __name__ == '__main__':
    country = CountryInfo('Singapore')
    pprint(country.all())

