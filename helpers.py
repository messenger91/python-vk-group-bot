import datetime
datetime.datetime.today()
datetime.datetime(2012, 3, 23, 23, 24, 55, 173504)


def day_of_week(week_day: str) -> int:
    week = {'понедельник': 0, 'вторник': 1, 'среда': 2,
            'четверг': 3, 'пятница': 4, 'суббота': 5, 'воскресенье': 6}
    return week[week_day]


def week_day(num: int) -> str:
    days = {0: 'понедельник', 1: 'вторник', 2: 'среда',
            3: 'четверг', 4: 'пятница', 5: 'суббота', 6: 'воскресенье'}
    return days[num]


def current_week_of_day():
    week_day_num = datetime.datetime.today().weekday()
    return week_day(week_day_num)