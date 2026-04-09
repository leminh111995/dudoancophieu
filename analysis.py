from vnstock import Vnstock
import pandas as pd
import numpy as np

s = Vnstock()

def phan_tich_chu_ky_lich_su(df):
    """Tính toán chu kỳ tích lũy trung bình trước khi nổ trong quá khứ"""
    # Định nghĩa 'Nổ': Giá tăng > 3% và Vol > 1.3 lần trung bình 20 phiên
    df['vol_20'] = df['volume'].rolling(20).mean()
    df['is_explosion'] = (df['close'].pct_change() > 0.03) & (df['volume'] > df['vol_20'] * 1.3)
    
    explosion_indices = df.index[df['is_explosion']].tolist()
    durations = []
    
    for i in range(1, len(explosion_indices)):
        # Tính khoảng cách giữa 2 lần nổ
        dist = explosion_indices[i] - explosion_indices[i-1]
        if 5 < dist < 60: # Chỉ lấy các chu kỳ tích lũy hợp lý (1 tuần đến 3 tháng)
            durations.append(dist)
            
    return int(np.mean(durations)) if durations else 20 # Mặc định 20 ngày nếu ko có dữ liệu

def phan_tich_tong_luc():
    print("🔍 ĐANG QUÉT HOSE - PHÂN TÍCH CHU KỲ LỊCH SỬ & DÒNG TIỀN...")
    try:
        df_ls = s.market.listing()
        df_hose = df_ls[df_ls['comGroupCode'] == 'HOSE']
        sector_map = dict(zip(df_hose['ticker'], df_hose['icbName3']))
        tickers = df_hose['ticker'].tolist()
    except:
        tickers = ["FPT","VCB","HPG","VNM","SSI","MSN","TCB","MWG","DGC","STB"]
        sector_map = {t: "Trụ cột" for t in tickers}

    final_results = []

    for ticker in tickers:
        try:
            # 1. Dữ liệu giá 1 năm
            df = s.stock_price.khop_lenh_history(symbol=ticker, period='1y')
            if len(df) < 40: continue
            
            curr_price = df['close'].iloc[-1]
            if curr_price < 10000: continue 

            # 2. Dòng tiền Smart Money (10 phiên)
            flow = s.stock_finance.foreign_prop_flow(symbol=ticker, period='daily')
            f_net_10 = flow['foreign'].tail(10).sum() / 1e6
            p_net_10 = flow['prop'].tail(10).sum() / 1e6
            
            # 3. Tính toán chu kỳ & Độ nén hiện tại
            avg_cycle = phan_tich_chu_ky_lich_su(df)
            
            # Tính số ngày đang tích lũy hiện tại (giá biến động hẹp < 4%)
            prices = df['close'].values
            current_squeeze_days = 0
            for j in range(len(prices)-1, 0, -1):
                window = prices[j-10 : j+1] # Xét cửa sổ 10 phiên
                if len(window) < 10: break
                if (np.max(window) - np.min(window)) / np.min(window) < 0.05:
                    current_squeeze_days += 1
                else: break

            vol_ratio = df['volume'].iloc[-1] / (df['volume'].rolling(20).mean().iloc[-1] + 1e-9)
            try:
                pe = s.stock_finance.ratio(ticker, period='year').loc[lambda x: x['name'] == 'P/E', 'value'].iloc[0]
            except: pe = 0

            final_results.append({
                'Mã': ticker, 'Ngành': sector_map.get(ticker, "N/A"),
                'Giá': curr_price, 'Ngoại_10P': f_net_10, 'TD_10P': p_net_10,
                'Tổng_SM': f_net_10 + p_net_10, 'Vol_Ratio': round(vol_ratio, 2),
                'P/E': round(pe, 1), 'Chu_Ky_Cu': avg_cycle,
                'Dang_Nen': current_squeeze_days,
                'Du_Doan_T': max(1, avg_cycle - current_squeeze_days)
            })
        except: continue

    # Tách 2 nhóm
    top_breakout = sorted(final_results, key=lambda x: x['Vol_Ratio'], reverse=True)[:5]
    top_value = sorted([x for x in final_results if 0 < x['P/E'] < 15], key=lambda x: x['Du_Doan_T'])[:5]
    
    return top_breakout, top_value

def in_bao_cao(m, kieu):
    if kieu == "breakout":
        ly_do = f"Tiền vào mạnh (Vol x{m['Vol_Ratio']}). Smart Money: {m['Tổng_SM']:.1f}M."
        if m['Ngoại_10P'] > 0 and m['TD_10P'] > 0: ly_do += " Đồng thuận mua ròng."
        return ly_do
    else:
        ly_do = f"P/E rẻ ({m['P/E']}). Lịch sử tích lũy {m['Chu_Ky_Cu']} ngày, hiện đã nén {m['Dang_Nen']} ngày."
        return ly_do

# THỰC THI
breakout, value = phan_tich_tong_luc()

print("\n🚀 NHÓM 1: TOP 5 MÃ ĐỘT BIẾN KHỐI LƯỢNG (Bắt sóng nổ)")
print("-" * 130)
print(f"{'MÃ':<6} | {'GIÁ':<7} | {'VOL_X':<6} | {'T+ NỔ':<7} | {'LÝ DO & DỰ BÁO'}")
for m in breakout:
    print(f"{m['Mã']:<6} | {m['Giá']:<7,.0f} | {m['Vol_Ratio']:<6} | T+{m['Du_Doan_T']:<5} | {in_bao_cao(m, 'breakout')}")

print("\n💎 NHÓM 2: TOP 5 MÃ ĐỊNH GIÁ RẺ (Gom theo chu kỳ lịch sử)")
print("-" * 130)
print(f"{'MÃ':<6} | {'GIÁ':<7} | {'P/E':<6} | {'T+ NỔ':<7} | {'LÝ DO & DỰ BÁO'}")
for v in value:
    print(f"{v['Mã']:<6} | {v['Giá']:<7,.0f} | {v['P/E']:<6} | T+{v['Du_Doan_T']:<5} | {in_bao_cao(m, 'value')}")
