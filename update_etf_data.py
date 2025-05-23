import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import os
import io

# yfinance import with error handling
try:
    import yfinance as yf
except ImportError as e:
    st.error(f"yfinance 패키지를 가져올 수 없습니다: {e}")
    st.error("requirements.txt에 yfinance>=0.2.28이 있는지 확인하세요.")
    st.stop()

def load_from_excel(file_path='etf_data.xlsx'):
    """엑셀 또는 CSV 파일 로드 함수"""
    try:
        # CSV 파일 우선 시도
        csv_path = file_path.replace('.xlsx', '.csv')
        if os.path.exists(csv_path):
            return pd.read_csv(csv_path)
        elif os.path.exists(file_path):
            return pd.read_excel(file_path)
        else:
            print(f"파일을 찾을 수 없습니다: {file_path}")
            return None
    except Exception as e:
        print(f"파일 로드 중 오류 발생: {str(e)}")
        return None

def get_etf_data(tickers):
    """Yahoo Finance에서 ETF 데이터 가져오기"""
    if not tickers:
        print("티커 목록이 비어 있습니다.")
        return None
        
    end_date = datetime.now(pytz.timezone('US/Eastern'))
    start_date = end_date - timedelta(days=400)
    
    try:
        data = yf.download(tickers, start=start_date, end=end_date)
        
        if data.empty:
            print("다운로드된 데이터가 비어 있습니다.")
            return None
            
        if isinstance(data.columns, pd.MultiIndex):
            return data.loc[:, ('Close', slice(None))]
        elif 'Adj Close' in data.columns:
            return data['Adj Close']
        else:
            return data['Close']
    except Exception as e:
        print(f"데이터 다운로드 중 오류 발생: {str(e)}")
        return None

def get_previous_week_last_trading_day(base_date, price_series):
    """이전 주의 마지막 거래일 찾기"""
    try:
        date_index = pd.Series(price_series.index.date).drop_duplicates()
        
        if base_date > date_index.iloc[-1]:
            base_date = date_index.iloc[-1]
        
        current_weekday = base_date.weekday()
        
        if current_weekday == 0:
            target_date = base_date - timedelta(days=3)
        elif current_weekday == 4:
            target_date = base_date - timedelta(days=7)
        else:
            days_to_subtract = (current_weekday + 3) % 7
            target_date = base_date - timedelta(days=days_to_subtract)
        
        past_trading_days = date_index[date_index <= target_date]
        
        if past_trading_days.empty:
            return price_series.index[0].date()
            
        return past_trading_days.iloc[-1]
        
    except Exception as e:
        print(f"이전 주 거래일 찾기 중 오류 발생: {str(e)}")
        return price_series.index[0].date()

def get_last_trading_day_of_month(base_date, price_series):
    """해당 월의 마지막 거래일 찾기"""
    try:
        date_index = pd.Series(price_series.index.date).drop_duplicates()
        
        if base_date.month == 12:
            next_month_first_day = base_date.replace(year=base_date.year+1, month=1, day=1)
        else:
            next_month_first_day = base_date.replace(month=base_date.month+1, day=1)
            
        end_of_month = next_month_first_day - timedelta(days=1)
        
        test_date = end_of_month
        while test_date > base_date.replace(day=1) - timedelta(days=1):
            if test_date in date_index.values:
                return test_date
            test_date -= timedelta(days=1)
            
        print(f"해당 월의 마지막 거래일을 찾을 수 없습니다: {base_date.year}-{base_date.month}")
        return date_index.iloc[0]
    except Exception as e:
        print(f"월간 마지막 거래일 찾기 중 오류 발생: {str(e)}")
        return price_series.index[0].date()

def calculate_volatility_and_mdd(price_series, ultra_short_term_days=5, short_term_days=22, long_term_days=252):
    """초단기/단기/장기 변동성과 최대 낙폭을 계산"""
    try:
        if len(price_series) < 2:
            return 0, 0, 0, 0
            
        ultra_short_term_data = price_series.tail(min(ultra_short_term_days, len(price_series)))
        if len(ultra_short_term_data) < 2:
            ultra_short_term_vol = 0
        else:
            daily_returns_ultra_short = ultra_short_term_data.pct_change().dropna()
            ultra_short_term_vol = daily_returns_ultra_short.std() * np.sqrt(252) * 100
            
        short_term_data = price_series.tail(min(short_term_days, len(price_series)))
        if len(short_term_data) < 2:
            short_term_vol = 0
        else:
            daily_returns_short = short_term_data.pct_change().dropna()
            short_term_vol = daily_returns_short.std() * np.sqrt(252) * 100
        
        long_term_data = price_series.tail(min(long_term_days, len(price_series)))
        if len(long_term_data) < 2:
            long_term_vol = 0
        else:
            daily_returns_long = long_term_data.pct_change().dropna()
            long_term_vol = daily_returns_long.std() * np.sqrt(252) * 100
        
        cummax = price_series.cummax()
        drawdown = (price_series - cummax) / cummax * 100
        mdd = drawdown.min()
        
        return ultra_short_term_vol, short_term_vol, long_term_vol, mdd
    except Exception as e:
        print(f"변동성 및 MDD 계산 중 오류 발생: {str(e)}")
        return 0, 0, 0, 0

def calculate_52week_high_drawdown(price_series):
    """52주 고점 대비 수익률 계산"""
    try:
        if len(price_series) < 2:
            return 0
            
        recent_data = price_series.tail(min(252, len(price_series)))
        high_52week = recent_data.max()
        current_price = price_series.iloc[-1]
        drawdown_from_high = ((current_price - high_52week) / high_52week * 100)
        return drawdown_from_high
    except Exception as e:
        print(f"52주 고점 대비 수익률 계산 중 오류 발생: {str(e)}")
        return 0

def calculate_returns(price_series):
    """수익률 계산 함수"""
    try:
        if len(price_series) < 2:
            print("가격 데이터가 충분하지 않습니다.")
            return (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                    datetime.now().strftime('%Y-%m-%d'),
                    datetime.now().strftime('%Y-%m-%d'),
                    datetime.now().strftime('%Y-%m-%d'))
        
        now = datetime.now(pytz.timezone('US/Eastern'))
        current_time = now.time()
        current_date = now.date()

        last_trading_day = min(current_date, price_series.index[-1].date())
        market_open_today = (last_trading_day == current_date) and (current_time >= datetime.strptime("09:30", "%H:%M").time())
        
        latest_idx = -1
        previous_idx = -2
        
        if market_open_today:
            if current_time < datetime.strptime("16:00", "%H:%M").time():
                if len(price_series) > 2:
                    latest_idx = -2
                    previous_idx = -3
                base_date = price_series.index[latest_idx].date()
            else:
                base_date = price_series.index[latest_idx].date()
        else:
            base_date = price_series.index[latest_idx].date()

        latest_close = price_series.iloc[latest_idx]
        previous_close = price_series.iloc[previous_idx] if abs(previous_idx) <= len(price_series) else latest_close

        weekly_base_date = get_previous_week_last_trading_day(base_date, price_series)
        weekly_data = price_series[price_series.index.date == weekly_base_date]
        weekly_base_close = weekly_data.iloc[-1] if not weekly_data.empty else latest_close
        
        last_month = base_date.replace(day=1) - timedelta(days=1)
        monthly_base_date = get_last_trading_day_of_month(last_month, price_series)
        monthly_data = price_series[price_series.index.date == monthly_base_date]
        monthly_base_close = monthly_data.iloc[-1] if not monthly_data.empty else latest_close
        
        last_year = base_date.replace(year=base_date.year-1, month=12, day=31)
        ytd_base_date = get_last_trading_day_of_month(last_year, price_series)
        ytd_data = price_series[price_series.index.date == ytd_base_date]
        ytd_base_close = ytd_data.iloc[-1] if not ytd_data.empty else latest_close
        
        days_22_date = get_previous_week_last_trading_day(base_date - timedelta(days=22), price_series)
        days_132_date = get_previous_week_last_trading_day(base_date - timedelta(days=132), price_series)
        days_264_date = get_previous_week_last_trading_day(base_date - timedelta(days=264), price_series)
        
        days_22_data = price_series[price_series.index.date == days_22_date]
        days_22_close = days_22_data.iloc[-1] if not days_22_data.empty else latest_close
        
        days_132_data = price_series[price_series.index.date == days_132_date]
        days_132_close = days_132_data.iloc[-1] if not days_132_data.empty else latest_close
        
        days_264_data = price_series[price_series.index.date == days_264_date]
        days_264_close = days_264_data.iloc[-1] if not days_264_data.empty else latest_close
        
        ultra_short_term_vol, short_term_vol, long_term_vol, mdd = calculate_volatility_and_mdd(price_series)
        drawdown_from_high = calculate_52week_high_drawdown(price_series)
        
        def safe_return(current, base):
            return ((current - base) / base) * 100 if base != 0 else 0
        
        daily_return = safe_return(latest_close, previous_close)
        weekly_return = safe_return(latest_close, weekly_base_close)
        monthly_return = safe_return(latest_close, monthly_base_close)
        ytd_return = safe_return(latest_close, ytd_base_close)
        days_22_return = safe_return(latest_close, days_22_close)
        days_132_return = safe_return(latest_close, days_132_close)
        days_264_return = safe_return(latest_close, days_264_close)
        
        risk_free_rate = 0.05
        excess_return = days_264_return - risk_free_rate
        sharpe_ratio = excess_return / long_term_vol if long_term_vol != 0 else 0
        
        return (latest_close, daily_return, weekly_return, monthly_return, ytd_return, 
                days_22_return, days_132_return, days_264_return, 
                ultra_short_term_vol, short_term_vol, long_term_vol, mdd,
                drawdown_from_high, sharpe_ratio,
                base_date.strftime('%Y-%m-%d'), weekly_base_date.strftime('%Y-%m-%d'), 
                monthly_base_date.strftime('%Y-%m-%d'))
    except Exception as e:
        print(f"수익률 계산 중 오류 발생: {str(e)}")
        return (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                datetime.now().strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d'))

def process_etf_data():
    try:
        df = load_from_excel()
        if df is None or df.empty:
            return None

        price_data = get_etf_data(df['ETF Ticker'].tolist())
        if price_data is None:
            return None

        results = []
        for ticker in df['ETF Ticker']:
            try:
                if isinstance(price_data.columns, pd.MultiIndex):
                    if ('Close', ticker) in price_data.columns:
                        ticker_data = price_data[('Close', ticker)]
                    else:
                        ticker_data = pd.Series()
                else:
                    if ticker in price_data.columns:
                        ticker_data = price_data[ticker]
                    else:
                        ticker_data = pd.Series()
                
                if ticker_data.empty:
                    results.append((0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                                  datetime.now().strftime('%Y-%m-%d'),
                                  datetime.now().strftime('%Y-%m-%d'),
                                  datetime.now().strftime('%Y-%m-%d')))
                    continue
                
                result = calculate_returns(ticker_data)
                results.append(result)
            except Exception as e:
                results.append((0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                              datetime.now().strftime('%Y-%m-%d'),
                              datetime.now().strftime('%Y-%m-%d'),
                              datetime.now().strftime('%Y-%m-%d')))

        (df['Close'], df['Daily Return (%)'], df['Weekly Return (%)'], 
         df['Monthly Return (%)'], df['YTD Return (%)'], df['22 Days Return (%)'],
         df['132 Days Return (%)'], df['264 Days Return (%)'], 
         df['Ultra-Short Vol (%)'], df['Short-term Vol (%)'], df['Long-term Vol (%)'], df['MDD (%)'],
         df['52W High Drawdown (%)'], df['Sharpe Ratio'],
         df['Base Date'], df['Weekly Base Date'], df['Monthly Base Date']) = zip(*results)

        # CSV로 저장 (Streamlit Cloud 호환성)
        try:
            df.to_csv('etf_data_with_returns.csv', index=False, encoding='utf-8-sig')
        except:
            pass  # 클라우드에서 저장 실패해도 계속 진행
        
        return df
    except Exception as e:
        return None

def main():
    st.set_page_config(
        page_title="ETF 데이터 업데이트",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stButton>button {
            height: 3em;
            font-size: 1.2em;
            font-weight: bold;
        }
        .stDataFrame {
            width: 100% !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🔄 ETF 데이터 업데이트")
    
    # 버튼을 한 줄에 배치
    button_col1, button_col2, _ = st.columns([1, 1, 8])
    update_clicked = False
    df = None
    with button_col1:
        if st.button("🔄 데이터 새로고침", type="primary", use_container_width=True):
            update_clicked = True
            with st.spinner('데이터를 업데이트하는 중...'):
                df = process_etf_data()
    with button_col2:
        # 메모리 기반 다운로드로 변경
        if st.session_state.get('updated_data') is not None:
            df = st.session_state['updated_data']
            
            # 메모리에서 엑셀 파일 생성
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='ETF_Data', index=False)
            output.seek(0)
            
            st.download_button(
                label="📥 데이터 다운로드",
                data=output,
                file_name='etf_data_with_returns.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                use_container_width=True
            )
        elif os.path.exists('etf_data_with_returns.csv'):
            with open('etf_data_with_returns.csv', 'rb') as f:
                st.download_button(
                    label="📥 데이터 다운로드 (CSV)",
                    data=f,
                    file_name='etf_data_with_returns.csv',
                    mime='text/csv',
                    use_container_width=True
                )
                
    # 데이터 표시
    if update_clicked and df is not None:
        # 세션 상태에 저장
        st.session_state['updated_data'] = df
        
        st.markdown("<div style='color:green;font-weight:bold;font-size:1.1em;'>데이터가 업데이트되었습니다.</div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-weight:bold;font-size:1.05em;'>기준일: {df['Base Date'].iloc[0]}</div>", unsafe_allow_html=True)
        display_columns = [
            'ETF Ticker', 'ETF Name', 'Group', 'Close',
            'Daily Return (%)', 'Weekly Return (%)', 'Monthly Return (%)',
            'YTD Return (%)', '22 Days Return (%)', '132 Days Return (%)',
            '264 Days Return (%)', 'Ultra-Short Vol (%)', 'Short-term Vol (%)', 'Long-term Vol (%)', 'MDD (%)', 
            '52W High Drawdown (%)', 'Sharpe Ratio'
        ]
        colf1, colf2 = st.columns(2)
        with colf1:
            all_groups = sorted(df['Group'].unique().tolist())
            selected_group = st.multiselect(
                "그룹 선택",
                options=['전체'] + all_groups,
                default=['전체']
            )
        with colf2:
            sort_by = st.selectbox(
                "정렬 기준",
                options=['Group'] + display_columns[4:],
                index=0
            )
        filtered_df = df.copy()
        if selected_group and '전체' not in selected_group:
            filtered_df = filtered_df[filtered_df['Group'].isin(selected_group)]
        if sort_by == 'Group':
            filtered_df = filtered_df.sort_values(by='Group')
        else:
            filtered_df = filtered_df.sort_values(by=['Group', sort_by], ascending=[True, False], na_position='last')
        st.dataframe(
            filtered_df[display_columns].style
            .format({col: '{:.2f}' for col in display_columns if '%' in col or col == 'Close' or col == 'Sharpe Ratio'})
            .background_gradient(
                subset=[col for col in display_columns if col not in ['ETF Ticker', 'ETF Name', 'Group', 'Close']], 
                cmap='RdYlGn'
            ),
            height=700,
            use_container_width=True
        )

if __name__ == "__main__":
    main() 