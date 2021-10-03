import datetime
import json
from bs4 import BeautifulSoup
import requests
from dataclasses import dataclass


#First, I create helper functions and a class definition to faciliate some of the later code.
def get_confirmation(message):
    answer = input(message)
    while answer not in ['y', 'n']:
        answer = input('Oops! Please enter lower-case \'y\' or \'n\'.')
    if answer == 'y':
        return True
    elif answer == 'n':
        return False
    
def get_date_input(prompt_string):
    date_string = input(prompt_string)
    try:
        datetime_object = datetime.datetime.strptime(date_string, '%Y-%m-%d')
        date = datetime_object.date()
        return date 
    except:
        return False
    
def date_string_to_date(date_string):
    datetime_object = datetime.datetime.strptime(date_string, '%Y-%M-%d')
    date = datetime_object.date()
    return date

def prefix_to_date(string, year):
    [month, day] = string.split(' ')
    if len(day) < 2:
        day = '0' + day
    converted_datetime = datetime.datetime.strptime(month + day + str(year), '%b%d%Y')
    converted_date = converted_datetime.date()
    return converted_date

def get_week_number(date):
    #print(type(date.strftime('%V')))
    return int(date.strftime('%V'))

def getHTML(url):
    response = requests.get(url)
    return response.text

def main_menu():
    print("\nHoliday Menu\n================\n1. Add a Holiday\n2. Remove a Holiday\n3. Save Holiday List\n4. View Holidays\n5. Exit")
    choice = input('What would you like to do?')
    while choice not in ['1', '2', '3', '4', '5']:
        choice = input('Please choose a number between 1 and 5 to select an option from the menu.')
    return choice

@dataclass 
class Holiday:
    name: str
    date: datetime.date
    
    def __str__ (self):
        return f'{self.name} ({self.date})'
    
    def get_dict(self):
        return {'name': self.name, 'date':self.date.strftime('%Y-%m-%d')}
    
#Next, I create functions to modularize the app's features. First, here's a function that loads in the JSON.

def load_holiday_json(file_name):
    f = open(file_name, 'r')
    data = json.load(f)
    for holiday in data['holidays']:
        #print(holiday)
        name = holiday['name']
        date = date_string_to_date(holiday['date'])
        holiday_list.append(Holiday(name, date))
    f.close()
    
#The following functions use Beautiful Soup to load in the holiday information from the web.
    
def scrape_web(year):
    scrape_holder = []
    url = 'https://www.timeanddate.com/holidays/us/' + str(year)
    html = getHTML(url)
    soup = soup = BeautifulSoup(html,'html.parser')
    table = soup.find('table', attrs={'id':'holidays-table'})
    for row in table.find_all_next('tr'):
        date = row.find('th')
        if date is None:
            continue
        date = date.contents[0]
        cells = row.find_all_next('td')
        name = cells[1].contents[0].contents[0]
        if [date, name] not in scrape_holder:
            scrape_holder.append([date, name])
    scrape_holder.remove(scrape_holder[0])
    return scrape_holder
    
def load_scrape(scrape_holder, year):
    for entry in scrape_holder:
        date = prefix_to_date(entry[0], year)
        name = entry[1]
        holiday_list.append(Holiday(name, date))
    
def get_holidays_from_web():
    for i in range(2020, 2025):
        scrape_holder = scrape_web(i)
        load_scrape(scrape_holder, i)
    return 

#This code makes the 'View Holiday' feature work. It also contacts the weather API, when apropriate.
def filter_holidays(year, week_number):
    holidays = filter(lambda x: get_week_number(x.date) == week_number and x.date.year == year, holiday_list)
    return list(holidays)

def view_current_week():
    viewing_list = []
    show_weather = get_confirmation('Do you want to see the weather forecast for this week? [y/n]')
    try:
        weather = requests.get('https://api.openweathermap.org/data/2.5/onecall?lat=44.9&lon=-93.2&exclude=current,minutely,hourly,alerts&appid={API ID HERE}')
        dailies = weather.json()['daily']
        for daily in dailies:
            day = datetime.datetime.fromtimestamp(daily['dt']).date()
            weather = daily['weather'][0]['description']
            current_holidays = list(filter(lambda x: x.date == day, holiday_list))
            for holiday in current_holidays:
                if show_weather:
                    viewing_list.append(f'{holiday} - {weather}')
                else:
                    viewing_list.append(holiday)
    except:
        print('Oops! There was an error loading the weather data. Instead, here is the holiday information for this week without forecasts.')
        current_week = get_week_number(datetime.datetime.now())
        current_year = datetime.datetime.now().year
        current_holidays = filter_holidays(current_year, current_week)
        for holiday in current_holidays:
            viewing_list.append(holiday)
    return viewing_list

    
def view_holidays():
    print('\nView Holidays\n=================\n\n(In the menu below, Week 53 represents all of the days between the end of the 52nd week of a year and Jan 4th of the next year.) \n')
    year = input('Which year?: ')
    while year not in ['2020', '2021', '2022', '2023', '2024']:
        year = input("Please choose a year between 2020 and 2024.")
    week = input('Which week [#1 - 53, blank for current week]?: ')
    while week != '' and week not in [str(x) for x in range(1, 54)]:
        week = input("Please choose a number between 1 and 53 or leave this option blank.")
    if week == "":
        viewing_list = view_current_week()
    else: 
        week = int(week)
        year = int(year)
        viewing_list = filter_holidays(year, week)
        viewing_list = sorted(viewing_list, key=lambda z: z.date)
    print('\n')
    for holiday in viewing_list:
            print(holiday)
    return

#Next, here's the code for adding and deleting holidays, including an implementation with decorators for deletion messages.

def add_holiday():
    global changed 
    print('\nAdd a Holiday\n=============')
    name = input('Holiday: ')
    date = get_date_input('Date [YYYY-mm-dd]: ')
    if type(date) != bool:
        new_holiday = Holiday(name, date)
        holiday_list.append(new_holiday)
        print(f'\nSuccess!\n{new_holiday} has been added to the holiday list.')
        changed = True
    else:
        print('\nError:\nThat\'s an invalid date. Please try again.')
        

def print_delete_message(func):
    def inner():
        [name,success] = func()
        if success is True:
            print(f'\nSuccess:\nYou have deleted {name} from the list.')
        else:
            print(f'\nError:\n{name} could not be found.')
        return 
    return inner

@print_delete_message        
def remove_holiday():
    global holiday_list
    global changed
    print('\nRemove a Holiday\n================')
    name = input('Holiday name: ')
    successful = False
    for holiday in holiday_list:
        if holiday.name == name:
            holiday_list.remove(holiday)
            successful = True
            changed = True
    return [name, successful]


#Finally, here is a function to save the list to data to a json.
def save_to_json():
    print('\nSaving Holiday List\n====================')
    confirm = get_confirmation('Are you sure you want to save the holiday list?[y/n] ')
    if confirm:
        saveable_list = []
        for holiday in holiday_list:
            saveable_list.append(holiday.get_dict())
        saveable_dict = {'holidays':saveable_list}
        try:
            file = open('saved_holiday_list.json', 'w')
            json.dump(saveable_dict, file)
            file.close()
            print('\nHoliday list successfully saved!')
        except:
            print('Oops! There was an error saving the file.')
    else:
        print('\nHoliday list save canceled.')
        
#Now, I implement the code that loads the data, runs the UI, and calls the functions for each of the features.

def main():
    global holiday_list
    holiday_list = []
    global changed 
    changed = False
    print('Welcome! Please wait while we retrieve holiday data.')
    load_holiday_json('holidays.json')
    get_holidays_from_web()
    print(f'There are currently {len(holiday_list)} holidays loaded into the list.')
    user_active = True
    while user_active:
        choice = main_menu()
        if choice == '1':
            add_holiday()
        elif choice == '2':
            remove_holiday()
        elif choice == '3':
            save_to_json()
        elif choice == '4':
            view_holidays()
        elif choice == '5':
            if changed:
                print('\nYour changes will not be saved.')
            user_active = not get_confirmation('Are you sure you would you like to quit?[y/n]')
    print('Goodbye!')
    
holiday_list = []
changed = False
main()    
