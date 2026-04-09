from vnstock import *
import pandas as pd
import numpy as np

# Khởi tạo cổng kết nối
s = Vnstock()

def tinh_chu_ky(df):
    df['vol_20'] = df['volume'].rolling(20).mean()
    df['is_explosion'] = (df['close'].pct_change() > 0.03) & (df['volume'] > df['vol_20'] * 1.3)
    exp_idx = df.index[df['is_explosion']].tolist()
    durs = [exp_idx[i] - exp_idx[i-1] for i in range(1, len(exp_idx)) if 5 < exp_idx[i] - exp_idx[i-1] < 60]
    return int(np.mean(durs)) if durs else 22

def phan_tich_full_hose():
    print("🔍 BẮT ĐẦU QUÉT TOÀN SÀN HOSE...")
    try:
        df_ls = stock_listing()
        df_hose = df_ls[df_ls['comGroupCode'] == 'HOSE']
        sector_map = dict(zip(df_hose['ticker'], df_hose['icbName3']))
        tickers = df_hose['ticker'].tolist()
        print(f"✅ Tìm thấy {len(tickers)} mã. Bắt đầu rà soát từng mã...")
    except:
        tickers = ["FPT","VCB","HPG","VNM","SSI","MSN","TCB","MWG","DGC","STB"]
        sector_map = {t: "Trụ cột" for t in tickers}
        print("⚠️ Không lấy được danh sách sàn, dùng list dự phòng.")

    final_results = []
    count = 0

    for ticker in tickers:
        try:
            count += 1
            if count % 50 == 0: print(f"--- Đã xử lý {count}/{len(tickers)} mã ---")
            
            # Lấy giá 1 năm
            df = s.stock_price.khop_lenh_history(symbol=ticker, period='1y')
            if len(df) < 40 or df['close'].iloc[-1] < 10000: continue
            
            # Lấy dòng tiền
            flow = s.stock_finance.foreign_prop_flow(symbol=ticker, period='daily')
            if flow.empty: continue
            
            f_net_10 = flow['foreign'].tail(10).sum() / 1e6
            p_net_10 = flow['prop'].tail(10).sum() / 1e6
            
            # Tính chỉ số
            avg_cycle = tinh_chu_ky(df)
            curr_price = df['close'].iloc[-1]
            vol_ratio = curr_price # Temp
            vol_ratio = df['volume'].iloc[-1] / (df['volume'].rolling(20).mean().iloc[-1] + 1e-9)
            
            # Đo độ nén
            prices = df['close'].values
            squeeze = 0
            for j in range(len(prices)-1, 0, -1):
                window = prices[max(0, j-10) : j+1]
                if (np.max(window) - np.min(window)) / np.min(window) < 0.05: squeeze += 1
                else: break

            try:
                pe = s.stock_finance.ratio(ticker, period='year').loc[lambda x: x['name'] == 'P/E', 'value'].iloc[0]
            except: pe = 0

            final_results.append({
                'Mã': ticker, 'Ngành': sector_map.get(ticker, "N/A"),
                'Giá': curr_price, 'Ngoại': f_net_10, 'TD': p_net_10,
                'Tổng': f_net_10 + p_net_10, 'Vol_X': round(vol_ratio, 2),
                'PE': round(pe, 1), 'Chu_Ky': avg_cycle, 'Nen': squeeze,
                'T_No': max(1, avg_cycle - squeeze)
            })
        except: continue

    if not final_results:
        print("❌ Không thu thập được dữ liệu nào từ thị trường.")
        return [], []

    # Nhóm 1: Sắp xếp theo dòng tiền mạnh nhất (kể cả âm nếu thị trường xấu)
    breakout = sorted(final_results, key=lambda x: x['Tổng'], reverse=True)[:5]
    # Nhóm 2: Định giá rẻ
    value = sorted([x for x in final_results if x['PE'] > 0], key=lambda x: x['PE'])[:5]
    
    return breakout, value

# THỰC THI VÀ IN BÁO CÁO
brk, val = phan_tich_full_hose()

if brk:
    print("\n🚀 NHÓM 1: TOP 5 MÃ DÒNG TIỀN TỐT NHẤT")
    print("-" * 130)
    print(f"{'MÃ':<6} | {'GIÁ':<7} | {'VOL_X':<6} | {'SM_10P':<8} | {'T+ NỔ':<7} | {'NHẬN ĐỊNH'}")
    for m in brk:
        note = "DÒNG TIỀN DƯƠNG" if m['Tổng'] > 0 else "BÁN RÒNG ÍT"
        print(f"{m['Mã']:<6} | {m['Giá']:<7,.0f} | {m['Vol_X']:<6} | {m['Tổng']:>7.0f}M | T+{m['T_No']:<5} | {note}")

if val:
    print("\n💎 NHÓM 2: TOP 5 MÃ ĐỊNH GIÁ RẺ NHẤT")
    print("-" * 130)
    print(f"{'MÃ':<6} | {'GIÁ':<7} | {'P/E':<6} | {'ĐỘ NÉN':<7} | {'T+ NỔ':<7} | {'NHẬN ĐỊNH'}")
    for v in val:
        note = f"Nền nén {v['Nen']} ngày"
        print(f"{v['Mã']:<6} | {v['Giá']:<7,.0f} | {v['PE']:<6} | {v['Nen']:<7} | T+{v['T_No']:<5} | {note}")
else:
    print("\n⚠️ Không có đủ dữ liệu để hiển thị bảng.")
