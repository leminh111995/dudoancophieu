from vnstock import Vnstock
import pandas as pd
import numpy as np

# 1. Khởi tạo thực thể duy nhất
s = Vnstock()

def tinh_chu_ky_no(ticker):
    try:
        df = s.stock_price.khop_lenh_history(symbol=ticker, period='1y')
        if len(df) < 50: return 22, 0, 0, df
        
        # Định nghĩa 'Nổ': Giá tăng > 3% và Vol > 1.3 lần trung bình
        df['vol_20'] = df['volume'].rolling(20).mean()
        df['is_explosion'] = (df['close'].pct_change() > 0.03) & (df['volume'] > df['vol_20'] * 1.3)
        exp_idx = df.index[df['is_explosion']].tolist()
        
        # Tính khoảng cách trung bình giữa các lần nổ
        durs = [exp_idx[i] - exp_idx[i-1] for i in range(1, len(exp_idx)) if 5 < exp_idx[i] - exp_idx[i-1] < 60]
        avg_cycle = int(np.mean(durs)) if durs else 22
        
        # Tính độ nén hiện tại (biến động hẹp < 5% trong 10 phiên)
        prices = df['close'].tail(10).values
        nen_days = 0
        if (np.max(prices) - np.min(prices)) / np.min(prices) < 0.05:
            nen_days = 10 # Tạm tính nén tốt
            
        vol_ratio = df['volume'].iloc[-1] / (df['vol_20'].iloc[-1] + 1e-9)
        return avg_cycle, nen_days, round(vol_ratio, 2), df
    except:
        return 22, 0, 0, pd.DataFrame()

def thuc_thi_quet_da_chien_thuat():
    print("🚀 BẮT ĐẦU QUÉT TOÀN SÀN HOSE - CHIẾN THUẬT ĐA TẦNG...")
    
    # Lấy danh sách mã HOSE
    try:
        df_ls = s.market.listing()
        df_hose = df_ls[df_ls['comGroupCode'] == 'HOSE']
        sector_map = dict(zip(df_hose['ticker'], df_hose['icbName3']))
        tickers = df_hose['ticker'].tolist()
        print(f"✅ Đã kết nối {len(tickers)} mã HOSE.")
    except:
        tickers = ["FPT","VCB","HPG","VNM","SSI","MSN","TCB","MWG","DGC","STB","VND","HCM","VCI","HSG","NKG"]
        sector_map = {t: "Trụ cột HOSE" for t in tickers}
        print("⚠️ Server danh sách lỗi, đang quét 15 mã trụ cột...")

    all_data = []
    
    # Chỉ quét 50 mã đầu tiên để test nhanh (Bạn có thể bỏ [:50] khi đã chạy ổn)
    for ticker in tickers[:100]:
        try:
            # 1. Tính chu kỳ và giá
            cycle, nen, v_ratio, df_hist = tinh_chu_ky_no(ticker)
            if df_hist.empty: continue
            
            curr_price = df_hist['close'].iloc[-1]
            if curr_price < 10000: continue
            
            # 2. Dòng tiền Smart Money (10 phiên)
            try:
                flow = s.stock_finance.foreign_prop_flow(symbol=ticker, period='daily')
                sm_10p = flow['foreign'].tail(10).sum() + flow['prop'].tail(10).sum()
            except: sm_10p = 0
            
            # 3. Định giá P/E
            try:
                pe = s.stock_finance.ratio(ticker, period='year').loc[lambda x: x['name'] == 'P/E', 'value'].iloc[0]
            except: pe = 0

            all_data.append({
                'Mã': ticker, 'Ngành': sector_map.get(ticker, "Khác"),
                'Giá': curr_price, 'Vol_X': v_ratio, 'SM': sm_10p / 1e6,
                'PE': round(pe, 1), 'T_No': max(1, cycle - nen), 'Nen': nen
            })
        except: continue

    return all_data

# XUẤT BÁO CÁO
data = thuc_thi_quet_da_chien_thuat()

if data:
    # Nhóm 1: Đột biến Vol (Săn Breakout)
    brk = sorted(data, key=lambda x: x['Vol_X'], reverse=True)[:5]
    print("\n🚀 NHÓM 1: TOP 5 MÃ ĐỘT BIẾN KHỐI LƯỢNG (Săn nổ)")
    print("-" * 125)
    print(f"{'MÃ':<6} | {'GIÁ':<7} | {'VOL_X':<6} | {'T+ NỔ':<7} | {'NGÀNH':<18} | {'LÝ DO & DỰ BÁO'}")
    for m in brk:
        advice = "TIỀN VÀO MẠNH" if m['Vol_X'] > 1.3 else "ĐANG TÍCH LŨY"
        print(f"{m['Mã']:<6} | {m['Giá']:<7,.0f} | {m['Vol_X']:<6} | T+{m['T_No']:<5} | {m['Ngành']:<18} | {advice}")

    # Nhóm 2: Định giá rẻ (Gom hàng)
    val = sorted([x for x in data if x['PE'] > 0], key=lambda x: x['PE'])[:5]
    print("\n💎 NHÓM 2: TOP 5 MÃ ĐỊNH GIÁ RẺ (Gom tích lũy)")
    print("-" * 125)
    print(f"{'MÃ':<6} | {'GIÁ':<7} | {'P/E':<6} | {'T+ NỔ':<7} | {'NGÀNH':<18} | {'LÝ DO & DỰ BÁO'}")
    for v in val:
        advice = f"P/E thấp, nền nén {v['Nen']} ngày"
        print(f"{v['Mã']:<6} | {v['Giá']:<7,.0f} | {v['PE']:<6} | T+{v['T_No']:<5} | {v['Ngành']:<18} | {advice}")
else:
    print("\n🆘 Server dữ liệu chưa sẵn sàng. Vui lòng thử lại sau 9:15 AM.")
