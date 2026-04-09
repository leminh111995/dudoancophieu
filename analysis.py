from vnstock import Vnstock
import pandas as pd

# Khởi tạo cổng kết nối
s = Vnstock()

def tinh_toan_toan_san():
    print("🚀 ĐANG QUÉT TOÀN BỘ SÀN HOSE (Khoảng 400 mã)...")
    
    try:
        # Lấy danh sách toàn sàn và lọc mã HOSE
        df_all = s.market.listing()
        df_hose = df_all[df_all['comGroupCode'] == 'HOSE']
        all_tickers = df_hose['ticker'].tolist()
        print(f"✅ Tìm thấy {len(all_tickers)} mã trên sàn HOSE.")
    except:
        print("❌ Lỗi lấy danh sách sàn. Vui lòng kiểm tra lại kết nối.")
        return []

    results = []
    processed_count = 0

    for ticker in all_tickers:
        try:
            # 1. Lấy dữ liệu giá để lọc Penny
            df_price = s.stock_price.khop_lenh_history(symbol=ticker, period='1w')
            if df_price.empty: continue
            
            curr_price = df_price['close'].iloc[-1]
            if curr_price < 10000: continue # Lọc giá trên 10
            
            # 2. Lấy dòng tiền 10 phiên gần nhất
            flow = s.stock_finance.foreign_prop_flow(symbol=ticker, period='daily')
            if flow.empty: continue
            
            f_net = flow['foreign'].tail(10).sum() / 1e6 # Đơn vị: Triệu đồng
            p_net = flow['prop'].tail(10).sum() / 1e6
            
            # ĐIỀU KIỆN: Ngoại mua HOẶC Tự doanh mua
            if f_net > 0 or p_net > 0:
                # Tính RSI để hỗ trợ dự đoán
                df_rsi = s.stock_price.khop_lenh_history(symbol=ticker, period='1y')
                delta = df_rsi['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rsi = 100 - (100 / (1 + (gain / (loss + 1e-9)).iloc[-1]))

                results.append({
                    'Mã': ticker,
                    'Giá': curr_price,
                    'Ngoại_10P(Tr)': round(f_net, 1),
                    'TD_10P(Tr)': round(p_net, 1),
                    'Tổng_Mua(Tr)': f_net + p_net,
                    'RSI': round(rsi, 1)
                })
            
            processed_count += 1
            if processed_count % 50 == 0:
                print(f"--- Đã quét xong {processed_count} mã ---")
        except:
            continue

    # Sắp xếp và lấy 5 mã mạnh nhất
    return sorted(results, key=lambda x: x['Tổng_Mua(Tr)'], reverse=True)[:5]

# XUẤT KẾT QUẢ
top_5 = tinh_toan_toan_san()

if top_5:
    print("\n" + "="*85)
    print(f"{'MÃ':<6} | {'GIÁ':<8} | {'NGOẠI_10P':<10} | {'TD_10P':<10} | {'RSI':<6} | {'DỰ ĐOÁN'}")
    print("-" * 85)
    for m in top_5:
        # Nhận định nhanh
        status = "GOM MẠNH" if m['Ngoại_10P(Tr)'] > 0 and m['TD_10P(Tr)'] > 0 else "TIỀN VÀO"
        if m['RSI'] > 70: status = "QUÁ MUA"
        
        print(f"{m['Mã']:<6} | {m['Giá']:<8,.0f} | {m['Ngoại_10P(Tr)']:>10.1f} | {m['TD_10P(Tr)']:>10.1f} | {m['RSI']:<6} | {status}")
    print("="*85)
else:
    print("\n--- Không tìm thấy mã nào thỏa mãn điều kiện ---")
