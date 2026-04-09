from vnstock3 import Vnstock
import pandas as pd
import numpy as np

# Khởi tạo
stock = Vnstock()

def tinh_toan_chi_so():
    print("--- ĐANG QUÉT CHUYÊN SÂU SÀN HOSE (Dòng tiền + Cơ bản + Biến động) ---")
    all_hose = stock.market.listing(exchange='HOSE')
    tickers = all_hose['ticker'].tolist()
    
    results = []
    
    # Chỉ quét thử nghiệm một số mã hoặc quét toàn bộ tùy cấu hình
    # Để tránh quá tải GitHub, chúng ta dùng try-except chặt chẽ
    for ticker in tickers:
        try:
            # 1. Lấy dữ liệu giá và Kỹ thuật
            df = stock.stock(symbol=ticker, source='VCI').price.history(period='1y')
            current_price = df['close'].iloc[-1]
            if current_price < 10000: continue # Bỏ mã dưới 10k
            
            # Tính biến động 1 tuần (5 phiên)
            price_1w_ago = df['close'].iloc[-6]
            pct_change_1w = ((current_price - price_1w_ago) / price_1w_ago) * 100
            
            # 2. Lấy Dòng tiền Smart Money (1 quý & 5 phiên gần nhất)
            flow = stock.stock(symbol=ticker, source='TCBS').finance.foreign_prop_flow(period='1Q')
            f_net_q = flow['foreign_net_value'].sum()
            p_net_q = flow['prop_net_value'].sum()
            
            # Tốc độ dòng tiền (5 phiên gần nhất)
            f_net_5d = flow['foreign_net_value'].tail(5).sum()
            p_net_5d = flow['prop_net_value'].tail(5).sum()
            
            # Lọc: Chỉ lấy mã Ngoại & Tự doanh mua ròng trong quý
            if f_net_q > 0 and p_net_q > 0:
                
                # 3. Lấy chỉ số cơ bản (P/E)
                # Lưu ý: Một số mã có thể thiếu dữ liệu này, ta đặt mặc định là 0
                try:
                    ratios = stock.stock(symbol=ticker, source='TCBS').finance.ratio(period='yearly')
                    pe = ratios.loc[ratios['name'] == 'P/E', 'value'].iloc[0]
                except:
                    pe = 0
                
                results.append({
                    'Mã': ticker,
                    'Giá': current_price,
                    'SmartMoney_Q(B)': (f_net_q + p_net_q) / 1e9,
                    'TốcĐộ_5P(B)': (f_net_5d + p_net_5d) / 1e9,
                    'P/E': pe,
                    'BiếnĐộng_1W': pct_change_1w,
                    'RSI': round(((df['close'].diff().where(df['close'].diff() > 0, 0)).rolling(14).mean() / 
                                 (df['close'].diff().where(df['close'].diff() < 0, 0)).abs().rolling(14).mean()).map(lambda x: 100 - (100/(1+x))).iloc[-1], 2)
                })
        except:
            continue

    # Sắp xếp theo Tổng Smart Money Quý và lấy Top 5
    return sorted(results, key=lambda x: x['SmartMoney_Q(B)'], reverse=True)[:5]

# CHẠY VÀ XUẤT BẢO CÁO
final_list = tinh_toan_chi_so()

if final_list:
    print("\n" + "="*95)
    print(f"{'MÃ':<6} | {'GIÁ':<7} | {'SM_QUÝ(B)':<10} | {'TỐCĐỘ_5P':<9} | {'P/E':<6} | {'1W_%':<7} | {'RSI':<5} | {'DỰ ĐOÁN'}")
    print("-" * 95)
    for m in final_list:
        # Logic dự đoán đơn giản
        note = "THEO DÕI"
        if m['TốcĐộ_5P(B)'] > 0 and m['BiếnĐộng_1W'] < 5 and m['RSI'] < 65:
            note = "MUA ĐẸP"
        elif m['BiếnĐộng_1W'] > 10:
            note = "QUÁ CAO"
            
        print(f"{m['Mã']:<6} | {m['Giá']:<7,.0f} | {m['SmartMoney_Q(B)']:<10.2f} | {m['TốcĐộ_5P(B)']:<9.2f} | {m['P/E']:<6.1f} | {m['BiếnĐộng_1W']:>6.1f}% | {m['RSI']:<5} | {note}")
    print("="*95)
    print("\n💡 GIẢI THÍCH DỰ ĐOÁN:")
    print("- MUA ĐẸP: Tiền đang vào (5P > 0), giá chưa tăng quá gắt trong tuần (<5%) và chưa quá mua (RSI < 65).")
    print("- QUÁ CAO: Cổ phiếu đã tăng nóng trong tuần, vào bây giờ dễ dính nhịp chỉnh.")
else:
    print("Không tìm thấy mã đạt tiêu chuẩn.")
