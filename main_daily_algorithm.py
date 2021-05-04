from selenium import webdriver
from path import Path
import time
from datetime import date
import os
import pandas as pd
import pytz
import datetime
from htmlcreator import HTMLDocument
from ftplib import FTP
import ftplib
import telegram

from functions_set import make_forecast, testexp_search_params, dataset
from game_sub_funcs import parse_today_cnd, min_define, parse
from game_dicts import todays_matches_links, results_links, champs_archive_data_paths
from game_dicts import map_champ_fullname, map_champ_reduction

import warnings
warnings.filterwarnings("ignore")

LINK_TO_DRIVER = Path('path to folder\chromedriver_89.exe') # link to actual chromedriver version
TODAY = str(date.today())

today_predictions = []
today_champs = []
to_the_telegram = True
update_main_page = True
send_to_telegram = True

for key in sorted(todays_matches_links.keys()):
    # START CHECK TODAYS MATCHES
    print('#' * 5, key, '#' * (78 - 5 - len(key)))
    driver = webdriver.Chrome(LINK_TO_DRIVER)
    driver.get(todays_matches_links[key])
    time.sleep(3)
    try:
        cookies = driver.find_element_by_id(id_='onetrust-accept-btn-handler')
        cookies.click()
    except:
        try:
            time.sleep(5)
            cookies = driver.find_element_by_id(id_='onetrust-accept-btn-handler')
            cookies.click()
        except:
            time.sleep(5)
            cookies = driver.find_element_by_id(id_='onetrust-accept-btn-handler')
            cookies.click()

    elements = driver.find_elements_by_class_name('event__match.event__match--scheduled.event__match--oneLine')
    matches_today = parse_today_cnd(key, elements)

    if not matches_today:
        driver.close()
    # END CHECK TODAYS MATCHES

    # START UPDATE RESULTS
    if matches_today:
        try:
            driver.get(results_links[key])
            YEARS = driver.find_element_by_css_selector('div.teamHeader__text')
            years = YEARS.get_attribute('innerHTML').replace('/', '-')
            time.sleep(5)
        except:
            years = '2020-2021'
            print('error in START UPDATE RESULTS')

        try:
            next_step = driver.find_elements_by_css_selector('a.event__more.event__more--static')
        except:
            continue

        idx = 0
        if next_step:
            for i in range(1, 5, 1):
                try:
                    next_step[-1].click()
                    time.sleep(4)
                    idx = i
                except:
                    break
        else:
            print(f'All data in one page for {key}')

        min_ = min_define(idx)
        elements = driver.find_elements_by_css_selector('div.event__match.event__match--static.event__match--oneLine')

        parse(elements, years, key, min_)

        driver.close()
        # END UPDATE RESULTS

        # START CREATE HTML AND SUMMARY DF
        filenames_list = []
        for _, _, filenames in os.walk(champs_archive_data_paths[key]):
            for filename in filenames:
                if 'statistic' in filename:
                    filenames_list.append(filename)
        filenames_list = sorted(filenames_list)
        for f in filenames_list:
            assert map_champ_reduction[key] in f, 'Wrong data!'

        data = pd.read_csv(f'{champs_archive_data_paths[key]}{filenames_list[0]}', engine='python')
        data['pairs'] = (data['home_team'] + '-' + data['away_team']).apply(lambda x: x.replace(' ', '_'))
        for file in filenames_list:
            if file != filenames_list[0]:
                next_file = pd.read_csv(f'{champs_archive_data_paths[key]}{file}', engine='python')
                next_file['pairs'] = (next_file['home_team'] + '-' + next_file['away_team']).apply(
                    lambda x: x.replace(' ', '_'))
                data = pd.concat([data, next_file], ignore_index=True, axis=0)

        data = data.drop_duplicates()

        tod_mat_path = f'parsed_data/{key}/todays_matches/'
        day_flag = False

        try:
            todays_matches = pd.read_csv(f'{tod_mat_path}{str(date.today())}_matches.csv', engine='python')
            todays_matches['todays_pairs'] = todays_matches[['home_team',
                                                             'away_team']].apply(lambda x: x[0].replace(' ', '_') +
                                                                                           '-' +
                                                                                           x[1].replace(' ', '_'), axis=1)
            todays_matches['home_team'] = todays_matches['home_team'].apply(lambda x: x.replace(' ', '_'))
            todays_matches['away_team'] = todays_matches['away_team'].apply(lambda x: x.replace(' ', '_'))

            home_away = []
            for l in range(len(todays_matches)):
                home_away.append([todays_matches.iloc[l]['home_team'], todays_matches.iloc[l]['away_team']])

            today_pairs_names = list(todays_matches.todays_pairs)
            times = list(todays_matches.time)
            assert len(today_pairs_names) == len(home_away), 'Different len names and home_away'

            if len(today_pairs_names) > 0:
                day_flag = True

        except FileNotFoundError:
            continue

        if day_flag:
            champ_matches_preds = []
            unique_pairs = list(data['pairs'].unique())
            for i in range(len(today_pairs_names)):
                idx = False
                for pair in unique_pairs:
                    if pair == today_pairs_names[i]:
                        idx = unique_pairs.index(today_pairs_names[i])

                if idx:
                    train_data = dataset(data, home_away[i][0], home_away[i][1])

                    if len(train_data) > 9:
                        try:
                            print(f'Predicting for {today_pairs_names[i]} in {map_champ_fullname[key]} in progress')
                            assert home_away[i][0] in today_pairs_names[i], f'Wrong data for {today_pairs_names[i]}'
                            assert home_away[i][1] in today_pairs_names[i], f'Wrong data for {today_pairs_names[i]}'

                            search = testexp_search_params(train_data)
                            predict, corr, zeros, matches_num = make_forecast(train_data,
                                                                              search,
                                                                              today_pairs_names[i],
                                                                              key,
                                                                              html=True)
                            if predict > 0.0:
                                local = pytz.timezone('Europe/Moscow')
                                naive = datetime.datetime.strptime(f"{TODAY} {times[i]}:00", "%Y-%m-%d %H:%M:%S")
                                local_dt = local.localize(naive, is_dst=None)
                                utc_dt = local_dt.astimezone(pytz.utc)
                                day = str(utc_dt.date())
                                hours = str(utc_dt.time().hour)
                                minute = str(utc_dt.time().minute)
                                if len(minute) == 1:
                                    minute = minute * 2
                                if hours == '0':
                                    hours = hours * 2
                                utc_time = hours + ':' + minute
                                champ_matches_preds.append({'TEAMS': today_pairs_names[i],
                                                            'START DATE/TIME (UTC)': f'{day} {utc_time}',
                                                            'MATCHES BEFORE': str(matches_num),
                                                            'ZSM': zeros,
                                                            'TOTAL SCORE': str(predict),
                                                            "PROBABILITY": str(corr)})

                                if map_champ_fullname[key] not in today_champs:
                                    today_champs.append(map_champ_fullname[key])
                            else:
                                print(f'Zero predict for {today_pairs_names[i]} in {map_champ_fullname[key]}')
                        except:
                            print(f'exception for predict {today_pairs_names[i]} in {map_champ_fullname[key]}')
                            continue
                    else:
                        print(f'To small data for {today_pairs_names[i]} in {map_champ_fullname[key]}')
                        continue

            if len(champ_matches_preds) > 0:
                cols = list(champ_matches_preds[0].keys())
                df = pd.DataFrame(champ_matches_preds, columns=cols)
                df.index = df.index + 1

                today_predictions.append({'champ_full_name': map_champ_fullname[key],
                                          'df': df.copy()})

doc = HTMLDocument()
doc.set_title('Zepto Game | Sports forecasting research')
doc.add_header('Zepto Game | Sports forecasting research', level='h1', align='center')

local = pytz.timezone('Europe/Moscow')
time_now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
naive_time = datetime.datetime.strptime(f"{time_now}", "%Y-%m-%d %H:%M:%S")
local_dt_now = local.localize(naive_time, is_dst=None)
utc_dt_now = local_dt_now.astimezone(pytz.utc)

if len(today_champs) > 0:
    doc.add_text(f'Generated {str(utc_dt_now)}', size='14px')
    doc.add_line_break()
    doc.add_header('FOOTBALL', level='h3', align='center')
    for champ_ in today_champs:
        doc.add_header(f'{champ_}', level='h3')
        for pred_ in today_predictions:
            if pred_['champ_full_name'] == champ_:
                doc.add_table(pred_['df'])
                doc.add_line_break()
else:
    for _ in range(5):
        doc.add_line_break()
    doc.add_header('No predictions for today. Try it tomorrow.', level='h2', align='center')
    for _ in range(5):
        doc.add_line_break()

doc.add_line_break()
doc.add_line_break()
doc.add_text('ZSM: ZERO SCORE for this pair of teams in previous MATCHES (% of MATCHES)', size='14px', align='left')
doc.add_line_break()
doc.add_line_break()
doc.add_text('Denial of responsibility: The site is not responsible for the accuracy of these forecasts.', size='14px', align='center')
doc.add_text('The forecasts presented on the page are the result of experimental research.', size='14px', align='center')
doc.add_text('You use (or do not use) them at your own risk.', size='14px', align='center')
doc.add_text(f'zeptogame.com | {str(utc_dt_now.date())}', size='14px', align='center')
doc.add_text('model ver. beta 2020.01S.02', size='14px', align='center') # ver. format year_of_model_creation.model_ver.terms_ver

output_filepath = f'daily_forecasts/{TODAY}_main_page.html'
to_server_output_filepath = f'{TODAY}_main_page.html'
doc.write(output_filepath)
doc.write(to_server_output_filepath)
print(f'{output_filepath} has been saved successfully!')
print(f'{to_server_output_filepath} has been saved successfully!')

if to_the_telegram:
    if len(today_champs) > 0:
        for i in range(len(today_predictions)):
            today_predictions[i]['df']['CHAMP_NAME'] = today_predictions[i]['champ_full_name']

        final_df = today_predictions[0]['df']
        for j in range(1, len(today_predictions)):
            final_df = pd.concat([final_df, today_predictions[j]['df']], ignore_index=True, axis=0)

        final_df.to_csv(f'daily_final_forecasts_csv/{TODAY}_final_forecast.csv', index=False)
        print(f'final .csv file for {TODAY} saved')

    else:
        final_df = pd.DataFrame([], columns=['CHAMP_NAME'])
        final_df.to_csv(f'daily_final_forecasts_csv/{TODAY}_final_forecast.csv', index=False)
        print(f'final EMPTY .csv file for {TODAY} saved')

# END CREATE HTML AND SUMMARY DF

# START CHANGE SITE MAIN PAGE

if update_main_page:
    upload_file_name = f'./{to_server_output_filepath}'
    downloaded_file_name = 'index.html'
    recovery_file_name = './index.html'
    orign_file_name = 'index.html'

    ftp = FTP()
    HOST = 'host IP'
    PORT = 'port number'

    try:
        ftp.connect(HOST, PORT)
        ftp.login(user='user', passwd='password')
        ftp.cwd('cwd')
    except ftplib.all_errors as err:
        print(f'FTP error: {err}')

# copy index.html from server
    try:
        with open(downloaded_file_name, 'w') as d:
            ftp.retrlines('RETR ' + orign_file_name, d.write)
    except ftplib.all_errors as err:
        print(f'step copy FTP error: {err}')

# delete index.html from server
    try:
        ftp.delete(orign_file_name)
    except ftplib.all_errors as err:
        print(f'step delete FTP error: {err}')

# upload next day index.html to server
    try:
        with open(upload_file_name, 'rb') as u:
            ftp.storlines('STOR %s'%upload_file_name, u)
    except ftplib.all_errors as err:
        print(f'step upload FTP error: {err}')

# rename next day index.html on server
    try:
        ftp.rename(upload_file_name, orign_file_name)
    except ftplib.all_errors as err:
        print(f'step rename FTP error: {err}')
        with open(recovery_file_name, 'rb') as u:
            ftp.storlines('STOR %s'%recovery_file_name, u)

    data = ftp.retrlines('LIST')
    print(data)

    ftp.quit()
# END CHANGE SITE MAIN PAGE

# START CREATE AND SEND MESSAGES TO TELEGRAM
success = False
if send_to_telegram:
    bot = telegram.Bot(token='bot token')

    df = pd.read_csv(f'daily_final_forecasts_csv/{TODAY}_final_forecast.csv', engine='python')

    if len(df) > 0:
        champs = list(df['CHAMP_NAME'].unique())
        print(f'Data len: {len(df)}')

        if len(df) > 20:
            for champ in champs:
                kind_of_sport = '\n<b>FOOTBALL</b>\n\n'
                msg = [kind_of_sport]
                title_text = f'<b>{champ}</b>\n\n'
                msg.append(title_text)
                for i in range(len(df)):
                    if df.iloc[i]['CHAMP_NAME'] == champ:
                        stu = df.iloc[i]['START DATE/TIME (UTC)']
                        start_time_utc = f'<b>START DATE/TIME (UTC)</b>: {stu}\n'
                        tms = df.iloc[i]['TEAMS']
                        teams = f'<b>TEAMS</b>: {tms}\n'
                        mbef = df.iloc[i]['MATCHES BEFORE']
                        matches_before = f'<b>MATCHES BEFORE:</b> {mbef}\n'
                        zsm = df.iloc[i]['ZSM']
                        zero_score_matches = f'<b>ZERO SCORE MATCHES:</b> {zsm}\n'
                        ttl = df.iloc[i]['TOTAL SCORE']
                        total = f'<b>TOTAL SCORE</b>: {ttl}\n'
                        pba = df.iloc[i]["PROBABILITY"]
                        proba = f'<b>PROBABILITY</b>: {pba}\n\n'
                        msg.append(start_time_utc)
                        msg.append(teams)
                        msg.append(matches_before)
                        msg.append(zero_score_matches)
                        msg.append(total)
                        msg.append(proba)
                msg.append('\n')
                msg.append('<code>model beta 2020.01S.02</code>')

                text1 = ''.join(msg)
                bot.send_message(chat_id='@chat_id', text=text1, parse_mode=telegram.ParseMode.HTML)
                time.sleep(7)
            success = 'Next day forecast posted to the channel successfully'
            print(success)

        else:
            kind_of_sport = '\n<b>FOOTBALL</b>\n\n'
            msg = [kind_of_sport]
            for champ in champs:
                title_text = f'<b>{champ}</b>\n\n'
                msg.append(title_text)
                for i in range(len(df)):
                    if df.iloc[i]['CHAMP_NAME'] == champ:
                        stu = df.iloc[i]['START DATE/TIME (UTC)']
                        start_time_utc = f'<b>START DATE/TIME (UTC)</b>: {stu}\n'
                        tms = df.iloc[i]['TEAMS']
                        teams = f'<b>TEAMS</b>: {tms}\n'
                        mbef = df.iloc[i]['MATCHES BEFORE']
                        matches_before = f'<b>MATCHES BEFORE:</b> {mbef}\n'
                        zsm = df.iloc[i]['ZSM']
                        zero_score_matches = f'<b>ZERO SCORE MATCHES:</b> {zsm}\n'
                        ttl = df.iloc[i]['TOTAL SCORE']
                        total = f'<b>TOTAL SCORE</b>: {ttl}\n'
                        pba = df.iloc[i]["PROBABILITY"]
                        proba = f'<b>PROBABILITY</b>: {pba}\n\n'
                        msg.append(start_time_utc)
                        msg.append(teams)
                        msg.append(matches_before)
                        msg.append(zero_score_matches)
                        msg.append(total)
                        msg.append(proba)
                msg.append('\n')
            msg.append('<code>model beta 2020.01S.02</code>')

            text = ''.join(msg)
            bot.send_message(chat_id='@chat_id', text=text, parse_mode=telegram.ParseMode.HTML)
            success = 'Next day forecast posted to the channel successfully'
            print(success)

    else:
        msg = ['<b>\nNo predictions for today. Try tomorrow\n\n\n</b>', '<code>model beta 2020.01S.02</code>']
        empty_pred_text = ''.join(msg)
        bot.send_message(chat_id='@chat_id', text=empty_pred_text, parse_mode=telegram.ParseMode.HTML)
        success = 'Next day forecast posted to the channel successfully'
        print(success)

# END CREATE AND SEND MESSAGES TO TELEGRAM

#if success == 'Next day forecast posted to the channel successfully':
#    os.system('shutdown -s -t 0')