#

import json

################################################################
# INPUT
STATIC = "../data/officer_static.json"
DYNAMICS = "../data/officer_dynamic.json"
################################################################

if __name__ == "__main__":
    with open(STATIC, "r") as f:
        officer_static_data = json.load(f)
    officer_static = {officer.pop('name'): officer for officer in officer_static_data}

    with open(DYNAMICS, "r") as f:
        dynamics = json.load(f)

    lowest_count = -1
    lowest_extreme_count = -1

    for officer_name, officer_data in dynamics.items():
        if officer_name not in officer_static or not officer_static[officer_name].get('status'):
            continue  # skip officers that are not active (do not activate people that have score 0)
        if officer_data.get('officer_count') < lowest_count or lowest_count == -1:
            lowest_count = officer_data.get('officer_count')
        if officer_data.get('officer_extreme_count') < lowest_extreme_count or lowest_extreme_count == -1:
            lowest_extreme_count = officer_data.get('officer_extreme_count')

    for officer_name, officer_data in dynamics.items():
        if officer_name not in officer_static or not officer_static[officer_name].get('status'):
            continue
        officer_data['officer_count'] = officer_data.get('officer_count') - lowest_count
        officer_data['officer_extreme_count'] = officer_data.get('officer_extreme_count') - lowest_extreme_count
        dynamics[officer_name] = officer_data

    with open(DYNAMICS, "w") as f:
        json.dump(dynamics, f, indent=4)
