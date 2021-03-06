
import stock_data.kq_stocks as kq
import pandas as pd
import numpy as np
import streamlit as st
import glob
import datetime
import FinanceDataReader as fdr
import pickle

from pathlib import Path
pkl_path = Path(__file__).parents[1]
file_path = str(pkl_path.cwd()) + str("\\")
print(file_path)
# decision_date = input("오늘 정보를 기반으로 내일 매수할 종목을 추천합니다. 오늘 날짜를 YYYY-MM-DD 형태로 입력하세요: ")
# kosdaq_list = pd.read_pickle(file_path + 'kosdaq_code.pkl')
kosdaq_list = fdr.StockListing('KOSDAQ').rename(columns={'Symbol':'code','Name':'name'})

with open('rf', 'rb') as file:
    rf = pickle.load(file)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    st.title('코스닥 주식 어드바이저')
    time_now = datetime.datetime.now()
    st.text(time_now)
    st.text(
        "- 장이 끝난 후 조회해야 오늘 정보가 활용됩니다.\n"
        "- 아래 추천 종목의 차트와 뉴스등을 종합적으로 고려하여 매수 결정을 합니다.\n"
        "- yhat 은 다음 4 영업일 이내로 주가가 급등할 확률입니다.\n"
        "- 예약매수 혹은 매수감시 기능을 활용하여 제안된 매수가격(buy_price)에 매수합니다.\n"
        "- 프로그램 관련 연락처: occam12345@gmail.com")


    decision_date = st.text_input("오늘 날짜를 다음과 같은 포맷으로 입력하세요. 포맷:  YYYY-MM-DD")

    if decision_date:

        if glob.glob(file_path + 'kq_selection_' + decision_date +'.pkl'):
            kq_selection = pd.read_pickle(file_path + 'kq_selection_' + decision_date + '.pkl')
            st.write(kq_selection.sort_values(by='yhat', ascending=False))

        elif time_now > datetime.datetime.strptime(decision_date, '%Y-%m-%d') + datetime.timedelta(hours=7):

            price_data = pd.DataFrame()
            for code in kosdaq_list['code']:
                daily_price = kq.make_price_data(code, 'day', '300')
                price_data = pd.concat([price_data, daily_price], axis=0)
            price_data.index.name = 'date'

            kosdaq_index = kq.kosdaq_index()    #
            price_kosdaq = price_data.merge(kosdaq_index['kosdaq_return'], left_index=True, right_index=True, how='left')  # merge individual stock price data with KOSPI index

            # 인덱스 값과 비교하여 인덱스보다 잘 하난 날 카운트
            return_all = pd.DataFrame()
            for code in kosdaq_list['code']:
                stock_return = price_kosdaq[price_kosdaq['code'] == code].sort_index()
                stock_return['return'] = stock_return['close'] / stock_return['close'].shift(1)
                c1 = (stock_return['kosdaq_return'] < 1)
                c2 = (stock_return['return'] > 1)

                stock_return['win_market'] = np.where((c1 & c2), 1, 0)
                return_all = pd.concat([return_all, stock_return], axis=0)

            outcome_all = kq.strategy_implement(return_all, kosdaq_list, decision_date)
            kq_selection = outcome_all[outcome_all['select'] == 1][['code', 'name', 'buy_price', 'yhat']]

            kq_selection.to_pickle(file_path + 'kq_selection_' + decision_date +'.pkl')
            kq_selection = pd.read_pickle(file_path + 'kq_selection_' + decision_date +'.pkl')
            st.write(kq_selection.sort_values(by='yhat', ascending=False))

        else:
            st.write('오후 4시 이후 조회 부탁드립니다.')

