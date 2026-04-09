from vnstock import Vnstock
import pandas as pd
import numpy as np

# Khởi tạo
stock = Vnstock()

def tinh_toan_chi_so():
    print("--- ĐANG QUÉT CHUYÊN SÂU SÀN HOSE (Dòng tiền + Cơ bản + Biến động) ---")
    
    # 1. Lấy danh sách mã niêm yết (Lệnh mới đã sửa lỗi)
    all_symbols = stock.listing()
    # Lọc lấy các mã trên sàn HOSE
    all_hose = all_symbols[all_symbols['exchange'] == 'HOSE']
    tickers = all_hose['ticker'].tolist()
    
    results = []
    
    # Quét danh sách
    for ticker in tickers:
        try:
            # 2. Lấy dữ liệu giá (Sử dụng nguồn mặc định để ổn định)
            df = stock.stock(symbol=ticker, source='VCI').price.history(period='1y')
            current_price = df['close'].iloc[-1]
            if current_price < 10000: continue 
            
            # Tính biến động 1 tuần
            price_1w_ago = df['close'].iloc[-6] if len(df) > 6 else df['close'].iloc[0]
            pct_change_1w = ((current_price - price_1w_ago) / price_1w_ago) * 100
            
            # 3. Lấy Dòng tiền Smart Money (TCBS thường ổn định nhất cho dữ liệu này)
            flow = stock.stock(symbol=ticker, source='TCBS').finance.foreign_prop_flow(period='1Q')
            f_net_q = flow['foreign_net_value'].sum()
            p_net_q = flow['prop_net_value'].sum()
            f_net_5d = flow['foreign_net_value'].tail(5).sum()
            p_net_5d = flow['prop_net_value'].tail(5).sum()
            
            # Lọc: Chỉ lấy mã cả 2 cùng mua ròng trong quý
            if f_net_q > 0 and p_net_q > 0:
                try:
                    ratios = stock.stock(symbol=ticker, source='TCBS').finance.ratio(period='yearly')
                    pe = ratios.loc[ratios['name'] == 'P/E', 'value'].iloc[0]
                except:
                    pe = 0
                
                # Tính RSI đơn giản
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs.iloc[-1]))
                
                results.append({
                    'Mã': ticker, 'Giá': current_price,
                    'SM_QUÝ': (f_net_q + p_net_q) / 1e9,
                    'TỐCĐỘ_5P': (f_net_5d + p_net_5d) / 1e9,
                    'P/E': pe, '1W_%': pct_change_1w,
                    'RSI': round(rsi, 2)
                })
        except:
            continue
            
    # Sắp xếp và lấy Top 5
    return sorted(results, key=lambda x: x['SM_QUÝ'], reverse=True)[:5]

# CHẠY VÀ XUẤT BÁO CÁO
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
    print("Không tìm thấy mã đạt tiêu chuẩn hôm nay.")
