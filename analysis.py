from vnstock import Vnstock
import pandas as pd
import numpy as np

# Khởi tạo cổng kết nối
s = Vnstock()

def lay_danh_sach_ma():
    # Thử 3 cách gọi phổ biến nhất của các phiên bản vnstock khác nhau
    try: return s.market.listing() # Cách của bản v3.x mới nhất
    except:
        try: return s.listing_companies() # Cách của bản v2.x
        except:
            try: return s.stock_listing() # Cách của bản v3.0
            except Exception as e:
                print(f"Không tìm thấy lệnh lấy danh sách: {e}")
                return pd.DataFrame()

def tinh_toan_chi_so():
    print("--- ĐANG QUÉT DỮ LIỆU HOSE (Hệ thống tự thích nghi) ---")
    
    df_ls = lay_danh_sach_ma()
    if df_ls.empty:
        # Nếu mọi cách đều lỗi, dùng danh sách Top 20 mã lớn nhất HOSE làm dự phòng
        tickers = ["FPT", "VCB", "HPG", "VNM", "SSI", "VIC", "VRE", "TCB", "MBB", "GAS", "DGC", "MWG", "STB", "VPB", "VJC", "HDB", "TPB", "VIB", "POW", "GVR"]
        print("Sử dụng danh sách mã dự phòng (Top HOSE)...")
    else:
        # Lọc sàn HOSE
        df_hose = df_ls[df_ls['comGroupCode'] == 'HOSE']
        tickers = df_hose['ticker'].tolist()
    
    results = []
    for ticker in tickers:
        try:
            # Lấy giá - Thử nguồn VCI hoặc TCBS
            df = s.stock_price.khop_lenh_history(symbol=ticker, period='1y')
            if df.empty: continue
            
            current_price = df['close'].iloc[-1]
            if current_price < 10000: continue 
            
            # Lấy dòng tiền Smart Money (1 quý)
            flow = s.stock_finance.foreign_prop_flow(symbol=ticker, period='quarter')
            f_net_q = flow['foreign'].sum()
            p_net_q = flow['prop'].sum()
            f_net_5d = flow['foreign'].tail(5).sum()
            p_net_5d = flow['prop'].tail(5).sum()
            
            if f_net_q > 0 and p_net_q > 0:
                # Lấy chỉ số P/E
                try:
                    ratios = s.stock_finance.ratio(ticker, period='year')
                    pe = ratios.loc[ratios['name'] == 'P/E', 'value'].iloc[0]
                except: pe = 0
                
                # Tính biến động & RSI
                price_1w_ago = df['close'].iloc[-6] if len(df) > 6 else df['close'].iloc[0]
                pct_change_1w = ((current_price - price_1w_ago) / price_1w_ago) * 100
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi = 100 - (100 / (1 + (gain / (loss + 1e-9)).iloc[-1]))
                
                results.append({
                    'Mã': ticker, 'Giá': current_price,
                    'SM_QUÝ(B)': (f_net_q + p_net_q) / 1e9,
                    'TỐCĐỘ_5P(B)': (f_net_5d + p_net_5d) / 1e9,
                    'P/E': pe, '1W_%': pct_change_1w, 'RSI': round(rsi, 2)
                })
        except: continue
            
    return sorted(results, key=lambda x: x['SM_QUÝ(B)'], reverse=True)[:5]

# CHẠY VÀ IN KẾT QUẢ
final_list = tinh_toan_chi_so()
if final_list:
    print("\n" + "="*95)
    print(f"{'MÃ':<6} | {'GIÁ':<7} | {'SM_QUÝ(B)':<10} | {'TỐCĐỘ_5P':<9} | {'P/E':<6} | {'1W_%':<7} | {'RSI':<5} | {'DỰ ĐOÁN'}")
    print("-" * 95)
    for m in final_list:
        note = "MUA ĐẸP" if m['TỐCĐỘ_5P(B)'] > 0 and m['1W_%'] < 5 and m['RSI'] < 65 else "THEO DÕI"
        if m['1W_%'] > 10: note = "QUÁ CAO"
        print(f"{m['Mã']:<6} | {m['Giá']:<7,.0f} | {m['SM_QUÝ(B)']:<10.2f} | {m['TỐCĐỘ_5P(B)']:<9.2f} | {m['P/E']:<6.1f} | {m['1W_%']:>6.1f}% | {m['RSI']:<5} | {note}")
    print("="*95)
else:
    print("Không tìm thấy mã đạt tiêu chuẩn hôm nay.")
