from vnstock import Vnstock
import pandas as pd
import numpy as np

# Khởi tạo
stock = Vnstock()

def tinh_toan_chi_so():
    print("--- ĐANG QUÉT CHUYÊN SÂU SÀN HOSE (Dòng tiền + Cơ bản + Biến động) ---")
    all_hose = stock.market.listing(exchange='HOSE')
    tickers = all_hose['ticker'].tolist()
    
    results = []
    
    for ticker in tickers:
        try:
            # 1. Lấy dữ liệu giá và Kỹ thuật
            df = stock.stock(symbol=ticker, source='VCI').price.history(period='1y')
            current_price = df['close'].iloc[-1]
            if current_price < 10000: continue 
            
            # Tính biến động 1 tuần
            price_1w_ago = df['close'].iloc[-6]
            pct_change_1w = ((current_price - price_1w_ago) / price_1w_ago) * 100
            
            # 2. Lấy Dòng tiền Smart Money
            flow = stock.stock(symbol=ticker, source='TCBS').finance.foreign_prop_flow(period='1Q')
            f_net_q = flow['foreign_net_value'].sum()
            p_net_q = flow['prop_net_value'].sum()
            f_net_5d = flow['foreign_net_value'].tail(5).sum()
            p_net_5d = flow['prop_net_value'].tail(5).sum()
            
            if f_net_q > 0 and p_net_q > 0:
                try:
                    ratios = stock.stock(symbol=ticker, source='TCBS').finance.ratio(period='yearly')
                    pe = ratios.loc[ratios['name'] == 'P/E', 'value'].iloc[0]
                except:
                    pe = 0
                
                results.append({
                    'Mã': ticker, 'Giá': current_price,
                    'SM_QUÝ': (f_net_q + p_net_q) / 1e9,
                    'TỐCĐỘ_5P': (f_net_5d + p_net_5d) / 1e9,
                    'P/E': pe, '1W_%': pct_change_1w,
                    'RSI': round(((df['close'].diff().where(df['close'].diff() > 0, 0)).rolling(14).mean() / 
                                 (df['close'].diff().where(df['close'].diff() < 0, 0)).abs().rolling(14).mean()).map(lambda x: 100 - (100/(1+x))).iloc[-1], 2)
                })
        except:
            continue
    return sorted(results, key=lambda x: x['SM_QUÝ'], reverse=True)[:5]

final_list = tinh_toan_chi_so()
if final_list:
    print("\n" + "="*95)
    print(f"{'MÃ':<6} | {'GIÁ':<7} | {'SM_QUÝ(B)':<10} | {'TỐCĐỘ_5P':<9} | {'P/E':<6} | {'1W_%':<7} | {'RSI':<5} | {'DỰ ĐOÁN'}")
    print("-" * 95)
    for m in final_list:
        note = "THEO DÕI"
        if m['TỐCĐỘ_5P'] > 0 and m['1W_%'] < 5 and m['RSI'] < 65: note = "MUA ĐẸP"
        elif m['1W_%'] > 10: note = "QUÁ CAO"
        print(f"{m['Mã']:<6} | {m['Giá']:<7,.0f} | {m['SM_QUÝ']:<10.2f} | {m['TỐCĐỘ_5P']:<9.2f} | {m['P/E']:<6.1f} | {m['1W_%']:>6.1f}% | {m['RSI']:<5} | {note}")
    print("="*95)
else:
    print("Không tìm thấy mã đạt tiêu chuẩn.")
