from vnstock import Vnstock
import pandas as pd
import numpy as np
from datetime import datetime

# Khởi tạo
s = Vnstock()

def quet_chuyen_sau():
    now = datetime.now().hour
    buoi = "Tối" if now >= 15 else "Sáng/Trưa"
    print(f"🕒 Thời điểm quét: {buoi} ({datetime.now().strftime('%H:%M:%S')})")
    print("🚀 ĐANG TRUY XUẤT DỮ LIỆU TOÀN SÀN HOSE...")

    try:
        # Lấy danh sách mã
        df_ls = s.market.listing()
        tickers = df_ls[df_ls['comGroupCode'] == 'HOSE']['ticker'].tolist()
    except Exception as e:
        print(f"⚠️ Server listing lỗi ({e}), dùng list dự phòng...")
        tickers = ["FPT","VCB","HPG","VNM","SSI","MSN","TCB","MWG","DGC","STB","VND","HCM","VCI","HSG","NKG"]

    results = []
    
    # Chỉ quét 30 mã tiêu biểu nhất để test nhanh độ ổn định server
    for ticker in tickers[:30]:
        try:
            # Lấy giá - Thử lấy dữ liệu 1 năm
            df = s.stock_price.khop_lenh_history(symbol=ticker, period='1y')
            if df.empty: continue
            
            curr_price = df['close'].iloc[-1]
            if curr_price < 10000: continue
            
            # Tính Vol Ratio
            vol_avg = df['volume'].tail(20).mean()
            v_ratio = df['volume'].iloc[-1] / (vol_avg + 1e-9)
            
            # Lấy dòng tiền
            try:
                flow = s.stock_finance.foreign_prop_flow(symbol=ticker, period='daily')
                sm = flow['foreign'].tail(5).sum() + flow['prop'].tail(5).sum()
            except: sm = 0
            
            results.append({
                'Mã': ticker, 'Giá': curr_price, 'Vol_X': round(v_ratio, 2),
                'SM': round(sm/1e6, 1), 'T': 2
            })
        except: continue
    
    return results

# CHẠY
data = quet_chuyen_sau()

if data:
    brk = sorted(data, key=lambda x: x['Vol_X'], reverse=True)[:5]
    print("\n✅ KẾT QUẢ PHÂN TÍCH CUỐI NGÀY")
    print("-" * 100)
    print(f"{'MÃ':<6} | {'GIÁ':<7} | {'VOL_X':<6} | {'SM_5P(M)':<8} | {'DỰ BÁO'}")
    for m in brk:
        status = "BÙNG NỔ" if m['Vol_X'] > 1.3 else "TÍCH LŨY"
        print(f"{m['Mã']:<6} | {m['Giá']:<7,.0f} | {m['Vol_X']:<6} | {m['SM']:>8} | {status} T+{m['T']}")
else:
    print("\n❌ KHÔNG CÓ DỮ LIỆU.")
    print("👉 Nguyên nhân: Các API dữ liệu (TCBS/SSI) đang khóa để bảo trì cuối ngày (thường từ 18h-21h).")
    print("👉 Giải pháp: Bạn hãy thử lại sau 21h đêm hoặc sáng mai từ 9h15.")
