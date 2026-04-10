from vnstock import *
import pandas as pd
import numpy as np
from datetime import datetime

def phan_tich_cuoi_cung():
    # 1. Xác định thời gian (Chuyển về giờ Việt Nam nếu chạy trên server quốc tế)
    now_hour = (datetime.now().hour + 7) % 24 
    print(f"🕒 Giờ hệ thống (VN): {now_hour}h")
    
    print("🚀 ĐANG TRUY XUẤT DỮ LIỆU TOÀN SÀN HOSE...")

    # 2. Lấy danh sách mã (Dùng lệnh trực tiếp, không qua object s)
    try:
        df_ls = stock_listing()
        df_hose = df_ls[df_ls['comGroupCode'] == 'HOSE']
        tickers = df_hose['ticker'].tolist()
        print(f"✅ Kết nối thành công. Tìm thấy {len(tickers)} mã trên HOSE.")
    except:
        tickers = ["FPT","VCB","HPG","VNM","SSI","MSN","TCB","MWG","DGC","STB","VND","HCM","VCI","HSG","NKG"]
        print("⚠️ Server bận, đang dùng danh sách 15 mã trụ cột...")

    results = []
    
    # 3. Quét dữ liệu (Giới hạn 100 mã để tránh quá tải server buổi sáng)
    for ticker in tickers[:100]:
        try:
            # Lấy giá 1 năm
            df = stock_historical_data(symbol=ticker, interval='1D', type='stock')
            if df.empty: continue
            
            curr_price = df['close'].iloc[-1]
            if curr_price < 10000: continue
            
            # Tính Vol Ratio (So với trung bình 20 phiên)
            vol_avg = df['volume'].tail(20).mean()
            v_ratio = df['volume'].iloc[-1] / (vol_avg + 1e-9)
            
            # Tính dòng tiền (Smart Money)
            try:
                flow = financial_flow(symbol=ticker, report_type='net_flow', report_range='daily')
                sm = flow['foreign'].tail(5).sum() + flow['prop'].tail(5).sum()
            except: sm = 0
            
            results.append({
                'Mã': ticker, 'Giá': curr_price, 'Vol_X': round(v_ratio, 2),
                'SM': round(sm/1e6, 1), 'T': 2
            })
        except: continue
    
    return results

# THỰC THI
data = phan_tich_cuoi_cung()

if data:
    brk = sorted(data, key=lambda x: x['Vol_X'], reverse=True)[:5]
    print("\n📊 BẢNG PHÂN TÍCH CHIẾN THUẬT")
    print("-" * 100)
    print(f"{'MÃ':<6} | {'GIÁ':<7} | {'VOL_X':<6} | {'SM_5P(M)':<8} | {'DỰ BÁO'}")
    for m in brk:
        status = "BÙNG NỔ" if m['Vol_X'] > 1.3 else "TÍCH LŨY"
        print(f"{m['Mã']:<6} | {m['Giá']:<7,.0f} | {m['Vol_X']:<6} | {m['SM']:>8} | {status} T+{m['T']}")
else:
    print("\n❌ HIỆN TẠI KHÔNG CÓ DỮ LIỆU.")
    print("👉 Lý do: Server TCBS/SSI đang bảo trì cuối ngày (18h-21h).")
    print("👉 Hành động: Hãy bấm RUN lại sau 21h đêm nay hoặc 9h15 sáng mai.")
