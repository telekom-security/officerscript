#

import json

################################################################
# INPUT
SELECTION_ONE = "../data/officer_selection_real.json"
SELECTION_TWO = "../data/officer_selection.json"
################################################################

if __name__ == '__main__':
    compared_dates = []

    officer_selection_one = json.load(open(SELECTION_ONE))
    if not officer_selection_one:
        raise Exception('There is no officer selection data')

    officer_selection_two = json.load(open(SELECTION_TWO))
    if not officer_selection_two:
        raise Exception('There is no officer selection data')

    for day, officers_one in officer_selection_one.items():
        officers_two = officer_selection_two.get(day)
        compared_dates.append(day)

        if not officers_two:
            print(f'{day} is only in officers one')
            continue

        officers_one = sorted(officers_one)
        officers_two = sorted(officers_two)

        if officers_one == officers_two:
            # print(f'{day} is in both selections and the officers are the same')
            continue

        cleaned_officers_one = [officer for officer in officers_one if officer not in officers_two]
        cleaned_officers_two = [officer for officer in officers_two if officer not in officers_one]

        print(f'{day} is in both selections but the officers are different '
              f'[ONE: {", ".join(cleaned_officers_one)}] [TWO: {", ".join(cleaned_officers_two)}]')

    for day, officers_two in officer_selection_two.items():
        if day in compared_dates:
            continue

        # print(f'{day} is only in officers two')
