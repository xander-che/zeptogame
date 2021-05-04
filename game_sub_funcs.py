from bs4 import BeautifulSoup
import pandas as pd
from datetime import date


def get_table(elems, years):

    table = []
    for el in elems:
        html = el.get_attribute('innerHTML')
        soup = BeautifulSoup(html, 'html.parser')
        date = soup.find('div', class_='class name').get_text(strip=True)
        home_team = soup.find('div', class_='class name').get_text(strip=True)
        away_team = soup.find('div', class_='class name').get_text(strip=True)
        score = soup.find('div', class_='class name').get_text(strip=True)
        if len(score) == 3:
            table.append({'years': years,
                          'date': date[:5].replace('.', '-'),
                          'home_team': home_team,
                          'away_team': away_team,
                          'score': score,
                          'total': int(score[0]) + int(score[2])})
        elif len(score) == 4:
            try:
                if type(int(score[1])) == int:
                    table.append({'years': years,
                                  'date': date[:5].replace('.', '-'),
                                  'home_team': home_team,
                                  'away_team': away_team,
                                  'score': score,
                                  'total': int(score[0:2]) + int(score[3])})
            except:
                table.append({'years': years,
                              'date': date[:5].replace('.', '-'),
                              'home_team': home_team,
                              'away_team': away_team,
                              'score': score,
                              'total': int(score[0]) + int(score[2:])})
        elif len(score) == 5:
            table.append({'years': years,
                          'date': date[:5].replace('.', '-'),
                          'home_team': home_team,
                          'away_team': away_team,
                          'score': score,
                          'total': int(score[0:2]) + int(score[3:])})
        elif len(score) >= 10:
            idx_start = 0
            idx_end = 0
            for i in range(len(score)):
                if score[i] == '(':
                    idx_start = i
                elif score[i] == ')':
                    idx_end = i
            new_score =  score[idx_start+1:idx_end]
            if len(new_score) == 3:
                table.append({'years': years,
                              'date': date[:5].replace('.', '-'),
                              'home_team': home_team,
                              'away_team': away_team,
                              'score': new_score,
                              'total': int(new_score[0]) + int(new_score[2])})
            elif len(new_score) == 4:
                try:
                    if type(int(new_score[1])) == int:
                        table.append({'years': years,
                                      'date': date[:5].replace('.', '-'),
                                      'home_team': home_team,
                                      'away_team': away_team,
                                      'score': new_score,
                                      'total': int(new_score[0:2]) + int(new_score[3])})
                except:
                    table.append({'years': years,
                                  'date': date[:5].replace('.', '-'),
                                  'home_team': home_team,
                                  'away_team': away_team,
                                  'score': new_score,
                                  'total': int(new_score[0]) + int(new_score[2:])})
            elif len(new_score) == 5:
                table.append({'years': years,
                              'date': date[:5].replace('.', '-'),
                              'home_team': home_team,
                              'away_team': away_team,
                              'score': new_score,
                              'total': int(new_score[0:2]) + int(new_score[3:])})

    return table


def parse(elements, years, key, min):

    from game_dicts import map_champ_reduction

    table = get_table(elements, years)
    print('Table len ', len(table))
    print('Elements list len ', len(elements))
    if len(table) >= min:
        season_stat = pd.DataFrame(table)
        season_stat.to_csv(f'parsed_data/{key}/archive/{map_champ_reduction[key]}_season_{years}_statistic.csv', index=False)
        print(f'Statistics for {years} years are collected. CSV file saved')
        print('')
    else:
        print(f'There are no statistics for {years}, len table < {min}, CSV file not saved')
        print('')


def get_todays_matches(elems):

    table = []
    for el in elems:
        html = el.get_attribute('innerHTML')
        soup = BeautifulSoup(html, 'html.parser')
        home_team = soup.find('div', class_='class name').get_text(strip=True)
        away_team = soup.find('div', class_='class name').get_text(strip=True)
        try:
            event_time = soup.find('div', class_='class name').get_text(strip=True)
        except:
            event_time = ' '
        if len(event_time) == 5:
            table.append({'home_team': home_team,
                          'away_team': away_team,
                          'time': event_time})

    return table


def parse_today(key, elements):

    table = get_todays_matches(elements)
    print('Table len ', len(table))
    print('Elements list len ', len(elements))
    today_date = str(date.today())
    if len(table) > 0:
        todays_matches = pd.DataFrame(table)
        todays_matches.to_csv(f'parsed_data/{key}/todays_matches/{today_date}_matches.csv', index=False)
        print(f'Matches for {today_date} are collected. CSV file saved')
        print('')
    else:
        print(f'No matches for {key} today')
        print('')


def parse_today_cnd(key, elements):

    table = get_todays_matches(elements)
    print('Table len ', len(table))
    print('Elements list len ', len(elements))
    today_date = str(date.today())
    if len(table) > 0:
        todays_matches = pd.DataFrame(table)
        todays_matches.to_csv(f'parsed_data/{key}/todays_matches/{today_date}_matches.csv', index=False)
        print(f'Matches for {today_date} are collected. CSV file saved')
        print('')
        return True
    else:
        print(f'No matches for {key} today')
        print('')
        return False


def min_define(idx):

    if idx == 0:
        min_ = 1
    elif idx == 1:
        min_ = 20
    elif idx == 2:
        min_ = 130
    elif idx == 3:
        min_ = 230
    else:
        min_ = 430

    return min_
