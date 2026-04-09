from vnstock import Vnstock
import pandas as pd

# Khởi tạo cổng kết nối
s = Vnstock()

def tinh_toan():
    print("--- HỆ THỐNG TRA CỨU DÒNG TIỀN HOSE (Bản nới lỏng bộ lọc) ---")
    
    # Danh sách các mã trụ cột và tiềm năng sàn HOSE
    tickers = ["FPT", "VCB", "HPG", "VNM", "SSI", "MSN", "TCB", "MWG", "DGC", "STB", 
               "VPB", "MBB", "VIC", "VRE", "VJC", "GAS", "HDB", "TPB", "VIB", "GVR"]
    results = []

    for ticker in tickers:
        try:
            # 1. Lấy dữ liệu giá
            df = s.stock_price.khop_lenh_history(symbol=ticker, period='1y')
            if df.empty: continue
            
            # 2. Lấy dòng tiền Smart Money (Quý)
            flow = s.stock_finance.foreign_prop_flow(symbol=ticker, period='quarter')
            f_net_q = flow['foreign'].sum() / 1e9 # Đơn vị: Tỷ đồng
            p_net_q = flow['prop'].sum() / 1e9    # Đơn vị: Tỷ đồng
            
            # ĐIỀU KIỆN MỚI: Chỉ cần 1 trong 2 bên mua ròng > 0
            if f_net_q > 0 or p_net_q > 0:
                curr_price = df['close'].iloc[-1]
                ma20 = df['close'].rolling(20).mean().iloc[-1]
                
                # Tính RSI
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi = 100 - (100 / (1 + (gain / (loss + 1e-9)).iloc[-1]))

                results.append({
                    'Mã': ticker, 
                    'Giá': curr_price,
                    'Ngoại_Q': f_net_q,
                    'TựDoanh_Q': p_net_q,
                    'Tổng_SM': f_net_q + p_net_q,
                    'RSI': round(rsi, 1),
                    '%_MA20': round(((curr_price - ma20) / ma20) * 100, 1)
                })
        except: continue

    # Sắp xếp theo tổng tiền Smart Money (Ngoại + Tự doanh) gom nhiều nhất
    return sorted(results, key=lambda x: x['Tổng_SM'], reverse=True)[:5]

# XUẤT BÁO CÁO
top_5 = tinh_toan()

if top_5:
    print("\n" + "="*95)
    print(f"{'MÃ':<6} | {'GIÁ':<7} | {'NGOẠI_Q':<9} | {'TD_Q':<8} | {'RSI':<5} | {'%_MA20':<7} | {'NHẬN ĐỊNH'}")
    print("-" * 95)
    for m in top_5:
        # Logic nhận định thông minh hơn
        status = "THEO DÕI"
        if m['Ngoại_Q'] > 0 and m['TựDoanh_Q'] > 0 and m['RSI'] < 65:
            status = "MUA ĐẸP" # Cả 2 cùng đồng thuận
        elif m['Ngoại_Q'] > 50 or m['TựDoanh_Q'] > 50:
            status = "TIỀN VÀO MẠNH" # Một bên gom cực khủng
            
        if m['RSI'] > 70: status = "QUÁ MUA"
        if m['Ngoại_Q'] < 0: status = "NGOẠI XẢ"
        
        print(f"{m['Mã']:<6} | {m['Giá']:<7,.0f} | {m['Ngoại_Q']:>8.1f}B | {m['TựDoanh_Q']:>7.1f}B | {m['RSI']:<5} | {m['%_MA20']:>6}% | {status}")
    print("="*95)
    print("\n💡 GỢI Ý: Hãy ưu tiên mã có 'MUA ĐẸP' hoặc '%_MA20' thấp (dưới 3%) để có điểm vào an toàn.")
else:
    print("\n--- Không tìm thấy mã nào thỏa mãn điều kiện mua ròng hôm nay ---")
