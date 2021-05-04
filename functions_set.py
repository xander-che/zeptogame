from statsmodels.tsa.statespace.sarimax import SARIMAX
from datetime import datetime
import pandas as pd
import numpy as np
import os


def train_predict(data, p, d, q):
    try:
        model = SARIMAX(endog=data,
                        order=(p, d, q),
                        use_exact_diffuse=True,
                        enforce_stationarity=True,
                        enforce_invertibility=True
                        )
        start_params = np.r_[[0] * (model.k_params - 1), 1]
        model_fit = model.fit(start_params=start_params, disp=False)
        predicted = model_fit.predict(len(data), len(data))
    except:
        try:
            model = SARIMAX(endog=data,
                            order=(p, d, q),
                            simple_differencing=True,
                            use_exact_diffuse=True,
                            enforce_stationarity=True,
                            enforce_invertibility=True
                            )
            start_params = np.r_[[0] * (model.k_params - 1), 1]
            model_fit = model.fit(start_params=start_params, disp=False)
            predicted = model_fit.predict(len(data), len(data))
        except:
            model = SARIMAX(endog=data,
                            order=(p, d, q),
                            trend='c',
                            simple_differencing=True,
                            use_exact_diffuse=True,
                            enforce_stationarity=True,
                            enforce_invertibility=True
                            )
            start_params = np.r_[[0] * (model.k_params - 1), 1]
            model_fit = model.fit(start_params=start_params, disp=False)
            predicted = model_fit.predict(len(data), len(data))

    return predicted[0], model_fit.aic


def date_preprocessing(years, date):
    month = date[3:]
    day = date[:2]
    year1 = years[:4]
    year2 = years[5:]
    if month[0] == '0':
        month = month[1]
    if day[0] == '0':
        day = day[1]
    if int(month) < 8:
        full_date = year2 + '-' + month + '-' + day
    else:
        full_date = year1 + '-' + month + '-' + day

    return datetime.strptime(full_date, '%Y-%m-%d')


def search_params(train_data, name):
    p = [0, 1, 2, 3]
    d = [0, 1]
    q = [0, 1, 2, 3]

    split_idx = int(len(train_data) / 2)
    ted = train_data[split_idx:].tolist() # train eval data

    true_positive = [1 for x in range(len(ted))]
    res = []
    for i in range(len(d)):
        for j in range(len(p)):
            for k in range(len(q)):
                trd = train_data[:split_idx].tolist() # train data
                result = []
                binary_markers = []
                means = []
                for _ in range(len(ted)):
                    trd = train_data[:len(trd) + 1]
                    pred_, _ = train_predict(trd, p[j], d[i], q[k])
                    result.append(round(pred_))
                for m in range(len(ted)):
                    if ted[m] - result[m] >= 0:
                        binary_markers.append(1)
                    else:
                        binary_markers.append(0)
                try:
                    model_score = sum(binary_markers) / sum(true_positive)
                    model_accuracy = sum(result) / sum(ted)
                    predict, _ = train_predict(train_data, p[j], d[i], q[k])
                except:
                    model_score = sum(binary_markers) / sum(true_positive)
                    model_accuracy = sum(result) / (sum(ted)+1.0)
                    predict, _ = train_predict(train_data, p[j], d[i], q[k])
                for n in range(len(ted)):
                    means.append(ted[n] - result[n])
                res.append({'p': p[j],
                            'd': d[i],
                            'q': q[k],
                            'score': model_score,
                            'accuracy': model_accuracy,
                            'predict': predict,
                            'mean_error': np.mean(means)})

    return res


def corr_pred_1(orign_pred):
    if orign_pred > 1.0:
        var = orign_pred - 1.0
    else:
        var = orign_pred
    return int(var)


def corr_pred_1_4(orign_pred):
    if orign_pred > 1.0 and orign_pred < 4.0:
        var = orign_pred - 1.0
    elif orign_pred >= 4.0:
        var = orign_pred - 2.0
    else:
        var = orign_pred
    return int(var)


def corr_pred_1_5(orign_pred):
    if orign_pred > 1.0 and orign_pred < 5.0:
        var = orign_pred - 1.0
    elif orign_pred >= 5.0:
        var = orign_pred - 2.0
    else:
        var = orign_pred
    return int(var)


def zero_results(data):
    len_data = len(data)
    zero_counter = 0
    for i in range(len_data):
        if data[i] == 0:
            zero_counter += 1
    return "{} %".format(np.around(zero_counter/len_data*100, decimals=1))


def make_forecast(train_data, search, name, key, html=False):
    pred = testexp_predict(search)
    err_ratio = 0
    if pred > 3:
        pred = 0
    if pred > 0:
        for _, _, files in os.walk('champs_add_stat/'):
            for file in files:
                if file == f'{key}_orign_preds_add_statistics.csv':
                    df_ = pd.read_csv(f'champs_add_stat/{key}_orign_preds_add_statistics.csv')
                    err_ratio = df_[str(pred)].iloc[2]
                    if err_ratio == 0.0:
                        err_ratio = 0.03

        correctness = np.around(1 - err_ratio, decimals=2)
        zeros = zero_results(train_data)

        if html:
            return pred, correctness, zeros, len(train_data)
        else:
            print(f'Matches qty: {len(train_data)}')
            print('-' * 80)
            print(f'{name} TOTAL {pred}, Correctness {correctness}, ZSM {zeros}')
            print('-' * 80)
    else:
        print(f'Zero forecasting for {name}')


def test_search_params(train_data):
    p = [0, 1, 2, 3]
    d = [0, 1]
    q = [0, 1, 2, 3]

    split_idx = int(len(train_data) / 2 - 1)
    ted = train_data[split_idx:]

    true_positive = [1 for x in range(len(ted))]
    res = []
    for i in range(len(d)):
        for j in range(len(p)):
            for k in range(len(q)):
                trd = train_data[:split_idx]
                result = []
                binary_markers = []
                means = []
                for _ in range(len(ted)):
                    trd = train_data[:len(trd) + 1]
                    pred_, _ = train_predict(trd, p[j], d[i], q[k])
                    result.append(round(pred_))
                for m in range(len(ted)):
                    if ted[m] - result[m] >= 0:
                        binary_markers.append(1)
                    else:
                        binary_markers.append(0)
                model_score = sum(binary_markers) / sum(true_positive)
                model_acuracy = sum(result) / sum(ted)
                predict, _ = train_predict(train_data, p[j], d[i], q[k])
                for n in range(len(ted)):
                    means.append(ted[n] - result[n])
                res.append({'p': p[j],
                            'd': d[i],
                            'q': q[k],
                            'score': model_score,
                            'accuracy': model_acuracy,
                            'predict': predict,
                            'mean_error': np.mean(means)})

    return res


#def test_predict(train_data, search):
def test_predict(search):
    ones = []
    ones_predict = []
    for i in range(len(search)):
        if search[i]['score'] <= 1.0 and search[i]['predict'] >= 0.0:
            ones.append(search[i])
            ones_predict.append(search[i]['predict'])

    unique_val = []
    for i in range(len(ones)):
        if round(ones[i]['predict']) not in unique_val:
            unique_val.append(round(ones[i]['predict']))
    unique_val = sorted(unique_val)

    val_counter = []
    for i in range(len(unique_val)):
        counter = 0
        for j in range(len(ones)):
            if round(ones[j]['predict']) == unique_val[i]:
                counter += 1
        val_counter.append(counter)

    models_mean_predict = []
    for val in unique_val:
        class_predict = []
        for i in range(len(ones)):
            if round(ones[i]['predict']) == val:
                class_predict.append(ones[i]['predict'])
        models_mean_predict.append(np.mean(class_predict))

    day_matches_and_preds = []
    for i in range(len(unique_val)):
        percent = np.around(val_counter[i] / len(ones), decimals=2)
        day_matches_and_preds.append({'predicted_total': models_mean_predict[i],
                                      'forecasts_distribution': percent})

    final_forecasting = []
    for i in range(len(day_matches_and_preds)):
        res = day_matches_and_preds[i]['predicted_total'] * day_matches_and_preds[i]['forecasts_distribution']
        final_forecasting.append(res)

    return round(sum(final_forecasting))


def testexp_search_params(train_data):
    p = [0, 1, 2, 3]
    d = [0, 1]
    q = [0, 1, 2, 3]

    for i in range(len(train_data)):
        if train_data[i] > 3:
            train_data[i] = 3

    search = []
    for i in range(len(d)):
        for j in range(len(p)):
            for k in range(len(q)):
                predict, aic = train_predict(train_data, p[j], d[i], q[k])
                search.append({'aic': aic,
                               'predict': predict})

    return search


def testexp_predict(search):
    best_aic = float("inf")
    predict = 0
    for i in range(len(search)):
        if search[i]['aic'] < best_aic:
            best_aic = search[i]['aic']
            predict = search[i]['predict']
    if predict < 0:
        predict = 0

    return int(predict)


def dataset(data, home_team, away_team):
    ds = []
    for i in range(len(data)):
        if home_team in data.iloc[i]['pairs'] and away_team in data.iloc[i]['pairs']:
            ds.append(data.iloc[i]['total'])
    return ds
