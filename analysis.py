from vnstock import Vnstock
import pandas as pd
import numpy as np

s = Vnstock()

def phan_tich_chuyen_sau():
    print("🔍 ĐANG QUÉT TOÀN SÀN HOSE - PHÂN TÁCH 2 CHIẾN THUẬT...")
    
    try:
        df_ls = s.market.listing()
        df_hose = df_ls[df_ls['comGroupCode'] == 'HOSE']
        sector_map = dict(zip(df_hose['ticker'], df_hose['icbName3']))
        tickers = df_hose['ticker'].tolist()
    except:
        tickers = ["FPT","VCB","HPG","VNM","SSI","MSN","TCB","MWG","DGC","STB"]
        sector_map = {t: "Trụ cột" for t in tickers}

    group_breakout = [] # Nhóm đột biến khối lượng
    group_value = []    # Nhóm định giá rẻ

    for ticker in tickers:
        try:
            # 1. Dữ liệu giá & Khối lượng (1 năm để tính trung bình)
            df = s.stock_price.khop_lenh_history(symbol=ticker, period='1y')
            if len(df) < 30: continue
            
            curr_price = df['close'].iloc[-1]
            if curr_price < 10000: continue # Lọc giá trên 10

            # 2. Dòng tiền Smart Money (10 phiên)
            flow = s.stock_finance.foreign_prop_flow(symbol=ticker, period='daily')
            f_net_10 = flow['foreign'].tail(10).sum() / 1e6
            p_net_10 = flow['prop'].tail(10).sum() / 1e6
            
            # ĐIỀU KIỆN CẦN: Có dòng tiền Smart Money vào (Ngoại hoặc Tự doanh > 0)
            if f_net_10 > 0 or p_net_10 > 0:
                # 3. Chỉ số kỹ thuật & Định giá
                vol_avg_20 = df['volume'].rolling(20).mean().iloc[-1]
                vol_ratio = df['volume'].iloc[-1] / vol_avg_20
                
                try:
                    ratios = s.stock_finance.ratio(ticker, period='year')
                    pe = ratios.loc[ratios['name'] == 'P/E', 'value'].iloc[0]
                except: pe = 99 # Mặc định nếu không có dữ liệu

                # Tính độ nén (Nền giá): Biến động trong 20 phiên gần nhất
                recent_prices = df['close'].tail(20)
                price_range = (recent_prices.max() - recent_prices.min()) / recent_prices.min()
                
                # Dự đoán ngày bùng nổ: Nền càng dài và càng chặt thì bùng nổ càng gần
                # Giả định: Trung bình một nhịp tích lũy kéo dài 20-30 ngày
                accum_days = 20 # Mặc định
                pred_days = max(1, 10 - int(price_range * 100)) # Biến động càng nhỏ, ngày bùng nổ càng gần

                data = {
                    'Mã': ticker, 'Ngành': sector_map.get(ticker, "N/A"),
                    'Giá': curr_price, 'Ngoại_10P': f_net_10, 'TD_10P': p_net_10,
                    'Vol_Ratio': round(vol_ratio, 2), 'P/E': round(pe, 1),
                    'Do_Nen': round(price_range * 100, 1), 'Du_Doan_T': pred_days
                }

                # Phân loại vào 2 nhóm
                group_breakout.append(data)
                if pe < 12 and pe > 0: # Tiêu chuẩn định giá rẻ (P/E < 12)
                    group_value.append(data)

        except: continue

    # Lấy Top 5 mỗi nhóm
    top_breakout = sorted(group_breakout, key=lambda x: x['Vol_Ratio'], reverse=True)[:5]
    top_value = sorted(group_value, key=lambda x: x['P/E'])[:5]
    
    return top_breakout, top_value

# XUẤT BÁO CÁO
breakout, value = phan_tich_chuyen_sau()

print("\n🚀 NHÓM 1: TOP 5 MÃ ĐỘT BIẾN KHỐI LƯỢNG (Dòng tiền nóng)")
print("="*105)
print(f"{'MÃ':<6} | {'GIÁ':<7} | {'VOL_X':<6} | {'NGOẠI(M)':<8} | {'TD(M)':<6} | {'NGÀNH':<20} | {'TRẠNG THÁI'}")
for m in breakout:
    status = "BREAKOUT" if m['Vol_Ratio'] > 1.5 else "ĐANG CHÚ Ý"
    print(f"{m['Mã']:<6} | {m['Giá']:<7,.0f} | {m['Vol_Ratio']:<6} | {m['Ngoại_10P']:>7.0f} | {m['TD_10P']:>5.0f} | {m['Ngành']:<20} | {status}")

print("\n💎 NHÓM 2: TOP 5 MÃ ĐỊNH GIÁ RẺ (Giá trị & Tích lũy)")
print("="*105)
print(f"{'MÃ':<6} | {'GIÁ':<7} | {'P/E':<6} | {'ĐỘ NÉN%':<7} | {'DỰ KIẾN T+':<8} | {'NGÀNH':<20} | {'NHẬN ĐỊNH'}")
for v in value:
    status = "NỀN CHẶT" if v['Do_Nen'] < 3 else "ĐANG TÍCH LŨY"
    print(f"{v['Mã']:<6} | {v['Giá']:<7,.0f} | {v['P/E']:<6} | {v['Do_Nen']:<7}% | {v['Du_Doan_T']:<8} | {v['Ngành']:<20} | {status}")
