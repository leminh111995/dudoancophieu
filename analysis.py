from vnstock import Vnstock
import pandas as pd
import numpy as np

s = Vnstock()

def tinh_toan_chi_so(ticker):
    try:
        # Lấy lịch sử 1 tháng (ngắn hơn để tăng tốc độ và độ ổn định buổi sáng)
        df = s.stock_price.khop_lenh_history(symbol=ticker, period='1y')
        if df.empty or len(df) < 20: return None
        
        curr_price = df['close'].iloc[-1]
        if curr_price < 10000: return None # Lọc giá trên 10
        
        # Tính Vol Ratio
        vol_avg = df['volume'].tail(20).mean()
        v_ratio = df['volume'].iloc[-1] / (vol_avg + 1e-9)
        
        # Tính độ nén (Squeeze)
        prices = df['close'].tail(10).values
        nen = 1 if (np.max(prices) - np.min(prices)) / np.min(prices) < 0.05 else 0
        
        # Thử lấy dòng tiền, nếu lỗi thì đặt bằng 0 chứ không dừng lại
        try:
            flow = s.stock_finance.foreign_prop_flow(symbol=ticker, period='daily')
            sm = flow['foreign'].tail(5).sum() + flow['prop'].tail(5).sum()
        except:
            sm = 0
            
        return {
            'Mã': ticker, 'Giá': curr_price, 'Vol_X': round(v_ratio, 2),
            'SM': round(sm/1e6, 1), 'T_No': 2, 'Nen': nen
        }
    except:
        return None

def quet_hose():
    print("🚀 ĐANG TRUY XUẤT DỮ LIỆU TOÀN SÀN HOSE...")
    try:
        df_ls = s.market.listing()
        tickers = df_ls[df_ls['comGroupCode'] == 'HOSE']['ticker'].tolist()
    except:
        tickers = ["FPT","VCB","HPG","VNM","SSI","MSN","TCB","MWG","DGC","STB","VND","HCM","VCI","HSG","NKG"]
        print("⚠️ Dùng danh sách dự phòng...")

    results = []
    # Quét 50 mã lớn nhất để đảm bảo luôn có kết quả
    for ticker in tickers[:50]: 
        res = tinh_toan_chi_so(ticker)
        if res: results.append(res)
    
    return results

# CHẠY VÀ IN BÁO CÁO
data = quet_hose()

if data:
    brk = sorted(data, key=lambda x: x['Vol_X'], reverse=True)[:5]
    print("\n🚀 TOP 5 MÃ CÓ TÍN HIỆU DÒNG TIỀN MẠNH NHẤT")
    print("-" * 100)
    print(f"{'MÃ':<6} | {'GIÁ':<7} | {'VOL_X':<6} | {'SM_5P(M)':<8} | {'DỰ BÁO'}")
    for m in brk:
        status = "TIỀN VÀO" if m['Vol_X'] > 1.2 else "TÍCH LŨY"
        print(f"{m['Mã']:<6} | {m['Giá']:<7,.0f} | {m['Vol_X']:<6} | {m['SM']:>8} | {status} T+{m['T_No']}")
else:
    print("\n🆘 Hiện tại các sàn đang chốt dữ liệu sáng sớm. Vui lòng bấm RUN lại sau 15-20 phút nữa!")
