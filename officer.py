import datetime
import json
import random

from model import Officer

##########################################################
# INPUT:
START_DATE = datetime.date(day=1, month=5, year=2023)  # has to be a monday
END_DATE = datetime.date(day=30, month=6, year=2023)  # has to be a friday
##########################################################


# define global variables:
officers = []  # this list will be filled with officer objects which holds their static, vacation and dynamic data
selected_officers_for_day = {}  # this dict will contain a list of selected officers per day
holidays = {}  # this dict will contain a list of the official holidays per state
bridging_days = {}  # this dict will contain the bridging days per state (calculated by the official holidays)
officer_times_weekly = {}  # init variable officer_times_weekly which saves the count per officer per week
last_friday_officers = []  # init variable to save the officers for last friday


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

    global last_friday_officers

    for day in days_in_week:
        if day.weekday() == 0:
            process_day(monday, day, last_friday_officers)
        else:
            process_day(monday, day)

        if day.weekday() == 4:
            last_friday_officers = selected_officers_for_day.get(day)


def load_officer_who_could_work(day, excepted_officers=None):
    can_work = []

    for officer in officers:

        # check if officer is on vacation
        if officer.vacation and get_day_str(day) in officer.vacation:
            continue

        # check if officer is in a state where a holiday is ongoing
        if get_day_str(day) in holidays.get(officer.country).get(officer.state):
            continue

        # check if the officer was working on the last friday if a monday is to be checked
        if excepted_officers and officer in excepted_officers:
            continue

        if not officer.status:
            continue

        # if there is no exclusion criteria
        can_work.append(officer)

    return can_work


# todo: try refactor this function so the code is more readable and the count of officers per day is variable
# function which is invoked 5 times per process_week call to process the 5 workdays
def process_day(monday, day, excepted_officers=None):
    # init the variable selected_officers_for_day for the day with an empty list, so the officers can be added
    selected_officers_for_day[day] = []

    # init the variable can_work which will contain all officers who can work on the selected date e.g. are not
    # on vacation or on holiday
    # if the selected date is a monday, the officers of last friday are not in the list
    can_work = load_officer_who_could_work(day, excepted_officers)

    if not can_work or len(can_work) == 1:
        print(f'No officer / only one officer for {get_day_str(day)} because of vacation and holidays')
        return

    # init the variable officer_times_weekly_by_count which holds information how many times an officers had duty
    officer_times_weekly_by_count = {0: [], 1: [], 2: []}

    for officer in can_work:
        if officer_times_weekly[monday].get(officer) == 0:
            officer_times_weekly_by_count[0].append(officer)
        elif officer_times_weekly[monday].get(officer) == 1:
            officer_times_weekly_by_count[1].append(officer)
        elif officer_times_weekly[monday].get(officer) == 2:
            officer_times_weekly_by_count[2].append(officer)

    # the need_just_one_more holds information if there was already one officer chosen and just one more is needed
    need_just_one_more = False

    # try to lower the officer per week rate by choosing the officers which no / fewer duties first
    for x_sessions in range(0, 2 + 1):
        officers_with_x_sessions_this_week = officer_times_weekly_by_count[x_sessions]

        # the list gets shuffled so officer duty does not depend on the position in the alphabet
        random.shuffle(officers_with_x_sessions_this_week)

        if len(officers_with_x_sessions_this_week) >= 2:
            # if there are 2 or more officers qualifying for the day
            # the one with the fewest general officer count is chosen
            sorted_possible_officers = sorted(officers_with_x_sessions_this_week, key=lambda x: x.officer_count)

            # if the day is a week extrema e.g. Friday & Monday, the extrema priority will apply
            if day.weekday() in [0, 4]:
                sorted_possible_officers = sorted(officers_with_x_sessions_this_week,
                                                  key=lambda x: x.officer_extreme_count)

            if need_just_one_more:
                if selected_officers_for_day[day][0].country == 'DE' or \
                        sorted_possible_officers[0].country == 'DE':
                    set_officer(monday, day, sorted_possible_officers[0])
                    break  # this means the officers for this day were successfully chosen
                else:
                    sorted_possible_officers.pop(0)
                    while sorted_possible_officers:
                        if sorted_possible_officers[0].country == 'DE':
                            set_officer(monday, day, sorted_possible_officers[0])
                            break
                        else:
                            sorted_possible_officers.pop(0)
                    if sorted_possible_officers:
                        break

            else:
                set_officer(monday, day, sorted_possible_officers[0])
                if sorted_possible_officers[0].country == 'DE' or sorted_possible_officers[1].country == 'DE':
                    set_officer(monday, day, sorted_possible_officers[1])
                    break  # this means the officers for this day were successfully chosen
                else:
                    sorted_possible_officers.pop(0)
                    sorted_possible_officers.pop(1)
                    while sorted_possible_officers:
                        if sorted_possible_officers[0].country == 'DE':
                            set_officer(monday, day, sorted_possible_officers[0])
                            break
                        else:
                            sorted_possible_officers.pop(0)
                    if sorted_possible_officers:
                        break

        elif len(officers_with_x_sessions_this_week) == 1:
            # if there is only one qualifying person, he will be officer
            if need_just_one_more:
                # if already selected officer is not from de, the officer who is currently checked should be from de
                if selected_officers_for_day[day][0].country == 'DE' or \
                        officers_with_x_sessions_this_week[0].country == 'DE':
                    set_officer(monday, day, officers_with_x_sessions_this_week[0])
                    break  # this means the officers for this day were successfully chosen
            else:
                set_officer(monday, day, officers_with_x_sessions_this_week[0])
                need_just_one_more = True  # this means there is one more officer needed for the day

    if len(selected_officers_for_day[day]) == 0:
        print(f'[WARNING] No officer officer for {get_day_str(day)}')
        # because of week limit of max 3 and/or the rule that min. 1 officer has to be from de

    if len(selected_officers_for_day[day]) == 1:
        print(f'[WARNING] Just one officer for {get_day_str(day)}')
        # because of week limit of max 3 and/or the rule that min. 1 officer has to be from de


# function which is executed every time an officer for a day is chosen
# saves the officer for the day, increments the counter for the selected officer generally
# and especially for the weekly counter
# in case of a bridging_day the counter is incremented twice
def set_officer(monday, day, selected_officer):
    selected_officers_for_day[day].append(selected_officer)
    officer_times_weekly[monday][selected_officer] += 1
    selected_officer.officer_count += 1

    # count extreme officer duties (e.g. on Monday & Friday) double
    if day.weekday() in [0, 4] or day.strftime("YYYY-MM-DD") in bridging_days:
        selected_officer.officer_extreme_count += 1


def load_officers():
    officer_static_data = json.load(open("data/officer_static.json"))  # source for officer static data
    if not officer_static_data:
        raise Exception('There is no officer static data')

    try:
        officer_vacation_data = json.load(open("data/officer_vacation.json"))  # source for officer vacation data
        print('[INFO]: there IS vacation data which will be used to calculate officer duty')
    except json.decoder.JSONDecodeError:
        officer_vacation_data = {}
        print('[WARNING]: there is NO vacation data which will be used to calculate officer duty')

    try:
        officer_dynamic_data = json.load(open("data/officer_dynamic.json"))  # source for officer dynamic data
        print('[INFO]: there IS dynamic data which will be used to calculate officer duty')
    except FileNotFoundError:
        officer_dynamic_data = {}
        print('[WARNING]: there is NO dynamic data which will be used to calculate officer duty')
    except json.decoder.JSONDecodeError:
        officer_dynamic_data = {}
        print('[WARNING]: there is NO dynamic data which will be used to calculate officer duty')

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
    holidays = json.load(open("data/holidays.json"))  # source for holidays
    if not holidays:
        raise Exception('There is no holidays data')

    global bridging_days
    bridging_days = json.load(open("data/bridging_days.json"))  # source for bridging_days
    if not bridging_days:
        raise Exception('There is no bridging days data')


def load_last_friday_officers():
    try:
        _officer_selection = json.load(open("data/officer_selection.json"))
    except FileNotFoundError:
        print("[INFO]: there is NO officer selection, so the last friday can't be loaded")
        return
    except json.decoder.JSONDecodeError:
        print("[INFO]: there is NO officer selection, so the last friday can't be loaded")
        return

    print("[INFO]: there IS an officer selection, so the last friday can be loaded")
    global last_friday_officers

    last_friday_officers_names = _officer_selection[sorted(list(_officer_selection))[-1]]
    for last_friday_officers_name in last_friday_officers_names:
        if get_officer_by_name(last_friday_officers_name):
            last_friday_officers.append(get_officer_by_name(last_friday_officers_name))


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
    if not START_DATE.weekday() == 0 or not END_DATE.weekday() == 4:
        exit(-1)  # start date has to be a monday and end date has to be a friday
    if not START_DATE.year == END_DATE.year:
        exit(-1)  # start and end date have to be in the same year

    load_officers()

    load_holidays()

    load_last_friday_officers()

    # the following is the centerpiece of the script, because it loops over the selected weeks and chooses an officer
    current_monday = START_DATE
    while current_monday < END_DATE:
        process_week(current_monday)
        current_monday = next_monday(current_monday)

    export_officer_selection()

    export_officer_dynamics()


if __name__ == '__main__':
    main()
