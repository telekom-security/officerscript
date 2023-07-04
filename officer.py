import datetime
import json
import random
import logging

from model import Officer

##########################################################
# INPUT:
START_DATE = datetime.date(day=3, month=7, year=2023)  # has to be a monday
END_DATE = datetime.date(day=28, month=7, year=2023)  # has to be a friday
##########################################################


# define global variables:
holidays = {}  # this dict will contain a list of the official holidays per state
bridging_days = {}  # this dict will contain the bridging days per state (calculated by the official holidays)
officers = []  # this list will be filled with officer objects which holds their static, vacation and dynamic data
selected_officers_for_day = {}  # this dict will contain a list of selected officers per day
officer_times_weekly = {}  # init variable officer_times_weekly which saves the count per officer per week
MAX_DUTIE_PER_WEEK = 3
OFFICERS_PER_DAY = 3


# function which returns the next_monday based on the last_monday
def next_monday(last_monday):
    return last_monday + datetime.timedelta(days=7)


def get_day_str(day):
    return day.strftime("%Y-%m-%d")


# function which is invoked periodically for every week in the selected timeframe
def process_week(monday):
    officer_times_weekly[monday] = {}

    for officer in officers:
        officer_times_weekly[monday][officer] = 0

    #  returns a list of all workdays (mo, di, mi, do, fr) based on the given monday
    days_in_week = [monday + datetime.timedelta(days=delta) for delta in range(0, 5)]

    # as defined by chef, on public holidays in nrw, there are no officers
    holidays_nrw = [datetime.datetime.strptime(day, '%Y-%m-%d').date() for day in holidays.get('DE').get('NW')]
    days_in_week = [day for day in days_in_week if day not in holidays_nrw]

    for day in days_in_week:
        process_day(monday=monday, day=day)


def load_officer_who_could_work(day):
    can_work = []

    for officer in officers:
        # check if officer is on vacation
        if officer.vacation and get_day_str(day) in officer.vacation:
            continue

        # check if officer is in a state where a holiday is ongoing
        if holidays.get(officer.country):
            if get_day_str(day) in holidays.get(officer.country).get(officer.state):
                continue

        if not officer.status:
            continue

        if officer in selected_officers_for_day.get(day, []):
            continue  # skip officer if he was already selected for this day (for partial generation)

        if officer in selected_officers_for_day.get(day - datetime.timedelta(days=1), []):
            continue  # skip officer if he was working yesterday
        if officer in selected_officers_for_day.get(day + datetime.timedelta(days=1), []):
            continue  # skip officer if he will work tomorrow (for partial generation)

        if day.weekday() == 0:  # monday
            if officer in selected_officers_for_day.get(day - datetime.timedelta(days=3), []):
                continue  # skip officer if he was working last friday
            if officer in selected_officers_for_day.get(day - datetime.timedelta(days=7), []):
                continue  # skip officer if he was working last monday
            if officer in selected_officers_for_day.get(day + datetime.timedelta(days=4), []):
                continue  # skip officer if he will be working on next friday (for partial generation)
            if officer in selected_officers_for_day.get(day + datetime.timedelta(days=7), []):
                continue  # skip officer if he will be working on next monday (for partial generation)

        if day.weekday() == 4:  # friday
            if officer in selected_officers_for_day.get(day - datetime.timedelta(days=4), []):
                continue  # skip officer if he was working last monday
            if officer in selected_officers_for_day.get(day - datetime.timedelta(days=7), []):
                continue  # skip officer if he was working last friday
            if officer in selected_officers_for_day.get(day + datetime.timedelta(days=3), []):
                continue  # skip officer if he will work next monday (for partial generation)
            if officer in selected_officers_for_day.get(day + datetime.timedelta(days=7), []):
                continue  # skip officer if he will work next friday (for partial generation)

        if get_day_str(day) in bridging_days.get(officer.country).get(officer.state) and day.weekday() == 1:  # tuesday
            if officer in selected_officers_for_day.get(day - datetime.timedelta(days=4), []):
                continue  # skip officer if he was working last friday
            if officer in selected_officers_for_day.get(day + datetime.timedelta(days=3), []):
                continue  # skip officer if he will be working on next friday (for partial generation)

        if get_day_str(day) in bridging_days.get(officer.country).get(officer.state) and day.weekday() == 3:  # thursday
            if officer in selected_officers_for_day.get(day - datetime.timedelta(days=3), []):
                continue  # skip officer if he was working last monday
            if officer in selected_officers_for_day.get(day + datetime.timedelta(days=4), []):
                continue  # skip officer if he will work next monday (for partial generation)

        # if there is no exclusion criteria
        can_work.append(officer)

    return can_work


# function which is invoked 5 times per process_week call to process the 5 workdays
def process_day(monday, day):
    # init the variable selected_officers_for_day for the day with an empty list, so the officers can be added
    if not selected_officers_for_day.get(day):
        selected_officers_for_day[day] = []

    # init the variable can_work which will contain all officers who can work on the selected date e.g. are not
    # on vacation or on holiday
    # if the selected date is a monday, the officers of last friday are not in the list
    can_work = load_officer_who_could_work(day)

    # init the variable officer_times_weekly_by_count which holds information how many times an officers had duty
    officer_times_weekly_by_count = {i: [] for i in range(0, MAX_DUTIE_PER_WEEK)}

    for officer in can_work:
        officer_times_weekly_by_count[officer_times_weekly[monday].get(officer)].append(officer)

    officers_needed = OFFICERS_PER_DAY - len(selected_officers_for_day[day])
    logging.debug(f'Officers needed for {get_day_str(day)}: {officers_needed}')

    if len(can_work) < officers_needed:
        logging.warning(f'Not enough possible officers for {get_day_str(day)}')

    # try to lower the officer per week rate by choosing the officers which no / fewer duties first
    for x_sessions in range(MAX_DUTIE_PER_WEEK):
        officers_with_x_sessions_this_week = officer_times_weekly_by_count[x_sessions]

        # the list gets shuffled so officer duty does not depend on the position in the alphabet
        random.shuffle(officers_with_x_sessions_this_week)

        # the one with the fewest general officer count is chosen
        sorted_possible_officers = sorted(officers_with_x_sessions_this_week, key=lambda x: x.officer_count)

        # if the day is a week extrema e.g. Friday & Monday, the extrema priority will apply
        if day.weekday() in [0, 4]:
            sorted_possible_officers = sorted(officers_with_x_sessions_this_week,
                                              key=lambda x: x.officer_extreme_count)

        while officers_needed > 0 and sorted_possible_officers:
            possible_officer = sorted_possible_officers.pop(0)

            # check for min one german person per day
            # skip if possible is from outside germany and there is no german officer for this day selected yet
            if possible_officer.country != 'DE' and \
                    not any(officer.country == 'DE' for officer in selected_officers_for_day[day]) and \
                    len(selected_officers_for_day[day]) == OFFICERS_PER_DAY - 1:
                continue

            # choose this officer
            set_officer(monday, day, possible_officer)
            officers_needed -= 1

        if officers_needed == 0:
            break

    if len(selected_officers_for_day[day]) < OFFICERS_PER_DAY:
        logging.warning(f'Just {len(selected_officers_for_day[day])} officer(s) for {get_day_str(day)}')


# function which is executed every time an officer for a day is chosen
# saves the officer for the day, increments the counter for the selected officer generally
# and especially for the weekly counter
# in case of a bridging_day the counter is incremented twice
def set_officer(monday, day, selected_officer: Officer):
    logging.debug(f'{selected_officer.name} is chosen for {get_day_str(day)}')
    selected_officers_for_day[day].append(selected_officer)
    officer_times_weekly[monday][selected_officer] += 1
    selected_officer.officer_count += 1

    # count extreme officer duties (e.g. on Monday & Friday) double
    if day.weekday() in [0, 4] or \
            get_day_str(day) in bridging_days.get(selected_officer.country).get(selected_officer.state):
        selected_officer.officer_extreme_count += 1


def load_officers():
    officer_static_data = json.load(open("data/officer_static.json"))  # source for officer static data
    if not officer_static_data:
        raise Exception('There is no officer static data')

    try:
        officer_vacation_data = json.load(open("data/officer_vacation.json"))  # source for officer vacation data
        logging.info('there IS vacation data which will be used to calculate officer duty')
    except json.decoder.JSONDecodeError:
        officer_vacation_data = {}
        logging.warning('there is NO vacation data which will be used to calculate officer duty')

    try:
        officer_dynamic_data = json.load(open("data/officer_dynamic.json"))  # source for officer dynamic data
        logging.info('there IS dynamic data which will be used to calculate officer duty')
    except FileNotFoundError:
        officer_dynamic_data = {}
        logging.warning('there is NO dynamic data which will be used to calculate officer duty')
    except json.decoder.JSONDecodeError:
        officer_dynamic_data = {}
        logging.warning('there is NO dynamic data which will be used to calculate officer duty')

    for data in officer_static_data:
        _officer_dynamic_data = officer_dynamic_data.get(data.get('name'))

        _officer_count = 0
        _officer_extreme_count = 0

        if _officer_dynamic_data:
            _officer_count = _officer_dynamic_data.get('officer_count')
            _officer_extreme_count = _officer_dynamic_data.get('officer_extreme_count')

        _officer_vacation = officer_vacation_data.get(data.get('name'))

        officers.append(Officer(data,
                                vacation=_officer_vacation,
                                officer_count=_officer_count,
                                officer_extreme_count=_officer_extreme_count))


def load_holidays():
    global holidays
    holidays = json.load(open("data/holidays.json"))
    if not holidays:
        logging.critical('there is NO holidays data')
        exit(-1)

    global bridging_days
    bridging_days = json.load(open("data/bridging_days.json"))
    if not bridging_days:
        logging.critical('there is NO bridging days data')
        exit(-1)


def load_last_selection():
    try:
        _officer_selection = json.load(open("data/officer_selection.json"))
    except FileNotFoundError:
        logging.info("there is NO officer selection")
        return
    except json.decoder.JSONDecodeError:
        logging.info("there is NO officer selection")
        return

    logging.info("there IS an officer selection")

    for day, selected_officers in _officer_selection.items():
        day_obj = datetime.datetime.strptime(day, "%Y-%m-%d").date()
        monday = day_obj - datetime.timedelta(days=day_obj.weekday())
        if not officer_times_weekly.get(monday):
            officer_times_weekly[monday] = {}

        selected_officers_for_day[day_obj] = []
        for _officer in selected_officers:
            officer_obj = get_officer_by_name(_officer)
            if not officer_obj:
                continue
            selected_officers_for_day[day_obj].append(officer_obj)

            if not officer_times_weekly[monday].get(officer_obj):
                officer_times_weekly[monday][officer_obj] = 0
            officer_times_weekly[monday][officer_obj] += 1


def get_officer_by_name(name):
    for officer in officers:
        if officer.name == name:
            return officer


def export_officer_selection():
    formatted_selection = {}

    # python onj -> json exportable obj
    for day, selected_officers in selected_officers_for_day.items():
        formatted_selection[day.strftime("%Y-%m-%d")] = []
        for _officer in selected_officers:
            formatted_selection[day.strftime("%Y-%m-%d")].append(_officer.name)

    # save the generated data
    with open('data/officer_selection.json', 'w') as f:
        f.write(json.dumps(formatted_selection, indent=4))


def export_officer_dynamics():
    officer_dynamic_data = {}

    # count and save the times an officer has duty
    for officer in officers:
        officer_dynamic_data[officer.name] = {'officer_count': officer.officer_count,
                                              'officer_extreme_count': officer.officer_extreme_count}

    with open('data/officer_dynamic.json', 'w') as f:
        f.write(json.dumps(officer_dynamic_data, indent=4))


def main():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%y-%m-%d %H:%M:%S')

    if not START_DATE.weekday() == 0 or not END_DATE.weekday() == 4:
        logging.critical("start date has to be a monday and end date has to be a friday")
        exit(-1)
    if not START_DATE.year == END_DATE.year:
        logging.critical("start date and end date have to be in the same year")
        exit(-1)

    load_officers()

    load_holidays()

    load_last_selection()

    # the following is the centerpiece of the script, because it loops over the selected weeks and chooses an officer
    current_monday = START_DATE
    while current_monday < END_DATE:
        process_week(current_monday)
        current_monday = next_monday(current_monday)

    export_officer_selection()

    export_officer_dynamics()


if __name__ == '__main__':
    main()
