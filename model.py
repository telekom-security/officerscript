#

class Officer:
    def __init__(self, static_data, vacation, officer_count, officer_extreme_count):
        self.__name = static_data.get('name')
        self.__status = static_data.get('status')
        self.__country = static_data.get('country')
        self.__state = static_data.get('state')
        self.__vacation = vacation
        self.__officer_count = officer_count
        self.__officer_extreme_count = officer_extreme_count

    @property
    def name(self):
        return self.__name

    @property
    def status(self):
        return self.__status

    @property
    def country(self):
        return self.__country

    @property
    def state(self):
        return self.__state

    @property
    def vacation(self):
        return self.__vacation

    @property
    def officer_count(self):
        return self.__officer_count

    @officer_count.setter
    def officer_count(self, officer_count):
        self.__officer_count = officer_count

    @property
    def officer_extreme_count(self):
        return self.__officer_extreme_count

    @officer_extreme_count.setter
    def officer_extreme_count(self, officer_extreme_count):
        self.__officer_extreme_count = officer_extreme_count
