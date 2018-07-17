from flask import json


def do_alert(driver):
    script = "alert(pause)"
    driver.execute_script(script)


def inject_data(driver, data):
    driver.execute_script("pasteJson(%s)" % json.dumps(data))


simple_data = [['Ethnicity', 'Value'],
               ['Asian', 5], ['Black', 4], ['Mixed', 3], ['White', 2], ['Other', 1]]

granular_data = [
    ['Ethnicity', 'Value'],
    ['Bangladeshi', 5], ['Indian', 4], ['Pakistani', 3], ['Asian other', 2],
    ['Black African', 1], ['Black Caribbean', 4], ['Black other', 3],
    ['Mixed White/Asian', 7], ['Mixed White/Black African', 6], ['Mixed White/Black Caribbean', 4], ['Mixed other', 7],
    ['White British', 1], ['White Irish', 4], ['White other', 3],
    ['Chinese', 8], ['Any other', 4]
]

granular_with_parent_data = [
    ['Ethnicity', 'Value'],
    ['Asian', 4], ['Bangladeshi', 5], ['Indian', 4], ['Pakistani', 3], ['Asian other', 2],
    ['Black', 4], ['Black African', 1], ['Black Caribbean', 4], ['Black other', 3],
    ['Mixed', 4], ['Mixed White/Asian', 7], ['Mixed White/Black African', 6], ['Mixed White/Black Caribbean', 4],
    ['Mixed other', 7],
    ['White', 4], ['White British', 1], ['White Irish', 4], ['White other', 3],
    ['Other inc Chinese', 6], ['Chinese', 8], ['Any other', 4]
]

ethnicity_by_gender_data = [['Ethnicity', 'Gender', 'Value'],
                            ['Asian', 'M', 5], ['Black', 'M', 4], ['Mixed', 'M', 3],
                            ['White', 'M', 2], ['Other', 'M', 1],
                            ['Asian', 'F', 4], ['Black', 'F', 1], ['Mixed', 'F', 5],
                            ['White', 'F', 4], ['Other', 'F', 2]]

ethnicity_by_time_data = [['Ethnicity', 'Time', 'Value'],
                          ['Asian', '1', 5], ['Black', '1', 4], ['Mixed', '1', 3], ['White', '1', 2], ['Other', '1', 1],
                          ['Asian', '2', 4], ['Black', '2', 1], ['Mixed', '2', 5], ['White', '2', 4], ['Other', '2', 2],
                          ['Asian', '3', 4], ['Black', '3', 1], ['Mixed', '3', 5], ['White', '3', 4], ['Other', '3', 2]]
