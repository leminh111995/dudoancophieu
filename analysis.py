# Khai báo đích danh các hàm cần dùng từ thư viện vnstock
from vnstock import stock_listing, financial_flow, financial_ratio, stock_historical_data
import pandas as pd
import numpy as np

def tinh_toan_chi_so():
    print("--- ĐANG QUÉT CHUYÊN SÂU SÀN HOSE (Dòng tiền + Cơ bản + Biến động) ---")
    
    # 1. Lấy danh sách toàn bộ mã sàn HOSE
    try:
        df_ls = stock_listing() 
        # Lọc các mã trên sàn HOSE
        df_hose = df_ls[df_ls['comGroupCode'] == 'HOSE']
        tickers = df_hose['ticker'].tolist()
    except Exception as e:
        print(f"Lỗi lấy danh sách mã: {e}")
        return []
    
    results = []
    
    # Quét danh sách mã
    for ticker in tickers:
        try:
            # 2. Lấy giá hiện tại và lịch sử
            df = stock_historical_data(symbol=ticker, interval='1D', type='stock')
            if df.empty: continue
            
            current_price = df['close'].iloc[-1]
            if current_price < 10000: continue # Bỏ mã dưới 10k
            
            # Tính biến động 1 tuần (5 phiên)
            price_1w_ago = df['close'].iloc[-6] if len(df) > 6 else df['close'].iloc[0]
            pct_change_1w = ((current_price - price_1w_ago) / price_1w_ago) * 100
            
            # 3. Lấy Dòng tiền Smart Money (Quý)
            # Hàm này cung cấp dữ liệu Nước ngoài & Tự doanh
            flow = financial_flow(symbol=ticker, report_type='net_flow', report_range='quarterly')
            
            f_net_q = flow['foreign'].sum() # Tổng ngoại mua ròng quý
            p_net_q = flow['prop'].sum()    # Tổng tự doanh mua ròng quý
            
            # Tốc độ dòng tiền 5 phiên gần nhất
            f_net_5d = flow['foreign'].tail(5).sum()
            p_net_5d = flow['prop'].tail(5).sum()
            
            # Lọc: Cả 2 cùng mua ròng trong quý (> 0)
            if f_net_q > 0 and p_net_q > 0:
                # 4. Lấy chỉ số P/E
                try:
                    ratios = financial_ratio(ticker, report_range='yearly', is_all=False)
                    pe = ratios.loc[ratios['name'] == 'P/E', 'value'].iloc[0]
                except:
                    pe = 0
                
                # Tính RSI (Chỉ báo xung lực)
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / (loss + 1e-9)
                rsi = 100 - (100 / (1 + rs.iloc[-1]))
                
                results.append({
                    'Mã': ticker, 'Giá': current_price,
                    'SM_QUÝ(B)': (f_net_q + p_net_q) / 1e9,
                    'TỐCĐỘ_5P(B)': (f_net_5d + p_net_5d) / 1e9,
                    'P/E': pe, '1W_%': pct_change_1w,
                    'RSI': round(rsi, 2)
                })
        except:
            continue
            
    # Sắp xếp theo lực mua ròng và lấy Top 5
    return sorted(results, key=lambda x: x['SM_QUÝ(B)'], reverse=True)[:5]

# CHẠY VÀ XUẤT BÁO CÁO
final_list = tinh_toan_chi_so()

if final_list:
    print("\n" + "="*95)
    print(f"{'MÃ':<6} | {'GIÁ':<7} | {'SM_QUÝ(B)':<10} | {'TỐCĐỘ_5P':<9} | {'P/E':<6} | {'1W_%':<7} | {'RSI':<5} | {'DỰ ĐOÁN'}")
    print("-" * 95)
    for m in final_list:
        note = "THEO DÕI"
        if m['TỐCĐỘ_5P(B)'] > 0 and m['1W_%'] < 5 and m['RSI'] < 65: note = "MUA ĐẸP"
        elif m['1W_%'] > 10: note = "QUÁ CAO"
        print(f"{m['Mã']:<6} | {m['Giá']:<7,.0f} | {m['SM_QUÝ(B)']:<10.2f} | {m['TỐCĐỘ_5P(B)']:<9.2f} | {m['P/E']:<6.1f} | {m['1W_%']:>6.1f}% | {m['RSI']:<5} | {note}")
    print("="*95)
else:
    print("Không tìm thấy mã đạt tiêu chuẩn hôm nay.")
