#

import datetime

import holidays
import json

loaded_holidays = {}
loaded_bridging_days = {}

################################################################
# INPUT
YEAR = 2023
################################################################


if __name__ == '__main__':
    officer_static_data = json.load(open("../data/officer_static.json"))  # source for officer static data
    if not officer_static_data:
        raise Exception('There is no officer static data')

    country_with_states = {}

    for officer in officer_static_data:
        if officer.get('country') not in country_with_states:
            country_with_states[officer.get('country')] = []
        if officer.get('state') not in country_with_states[officer.get('country')]:
            country_with_states[officer.get('country')].append(officer.get('state'))

    for country, states in country_with_states.items():
        loaded_holidays[country] = {}
        loaded_bridging_days[country] = {}

        for state in states:
            loaded_bridging_days[country][state] = []
            loaded_holidays[country][state] = list(holidays.country_holidays(
                country,
                subdiv=state,
                years=YEAR))

            for day in loaded_holidays[country][state]:
                if day.weekday() == 0:  # monday
                    loaded_bridging_days[country][state].append(day + datetime.timedelta(days=1))
                if day.weekday() == 4:  # friday
                    loaded_bridging_days[country][state].append(day - datetime.timedelta(days=1))

    with open('../data/holidays.json', 'w') as f:
        f.write(json.dumps(loaded_holidays, indent=4, default=str))

    with open('../data/bridging_days.json', 'w') as f:
        f.write(json.dumps(loaded_bridging_days, indent=4, default=str))
