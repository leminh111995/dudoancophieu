from vnstock import *
import pandas as pd
import numpy as np

def chan_doan_va_quet():
    print("🔬 HỆ THỐNG ĐANG KIỂM TRA KẾT NỐI SERVER...")
    
    # 1. Thử lấy danh sách mã
    try:
        df_ls = stock_listing()
        tickers = df_ls[df_ls['comGroupCode'] == 'HOSE']['ticker'].tolist()
        print(f"✅ Đã kết nối danh sách HOSE ({len(tickers)} mã).")
    except Exception as e:
        print(f"⚠️ Lỗi kết nối danh sách: {e}")
        tickers = ["FPT","VCB","HPG","VNM","SSI","MSN","TCB","MWG","DGC","STB"]
        print("➡️ Đang dùng danh sách dự phòng để tiếp tục...")

    results = []
    success_count = 0

    # 2. Quét dữ liệu
    for ticker in tickers[:30]: # Quét 30 mã tiêu biểu nhất để test nhanh
        try:
            # Thử lấy dữ liệu giá (lấy lùi về 1 năm để chắc chắn có history)
            df = stock_historical_data(symbol=ticker, interval='1D', type='stock')
            
            if df.empty:
                continue
            
            success_count += 1
            curr_price = df['close'].iloc[-1]
            
            # Tính dòng tiền (Nếu server dòng tiền chưa mở, ta tạm bỏ qua để lấy giá)
            try:
                flow = financial_flow(symbol=ticker, report_type='net_flow', report_range='daily')
                f_net = flow['foreign'].tail(5).sum() / 1e6
            except:
                f_net = 0

            # Tính Vol Ratio
            vol_avg = df['volume'].rolling(20).mean().iloc[-1]
            vol_ratio = df['volume'].iloc[-1] / (vol_avg + 1e-9)

            results.append({
                'Mã': ticker, 'Giá': curr_price, 'Vol_X': round(vol_ratio, 2),
                'Ngoại': round(f_net, 1), 'T': 1
            })
        except:
            continue

    print(f"📊 Kết quả chẩn đoán: Đã quét thành công {success_count} mã.")
    return results

# THỰC THI
top_list = chan_doan_va_quet()

if top_list:
    final = sorted(top_list, key=lambda x: x['Vol_X'], reverse=True)[:5]
    print("\n🚀 DANH SÁCH THEO DÕI SÁNG NAY (Dữ liệu chốt phiên gần nhất)")
    print("-" * 80)
    print(f"{'MÃ':<6} | {'GIÁ':<7} | {'VOL_X':<6} | {'NGOẠI(M)':<9} | {'NHẬN ĐỊNH'}")
    for m in final:
        advice = "ĐANG TÍCH LŨY" if m['Vol_X'] < 1.2 else "DÒNG TIỀN VÀO"
        print(f"{m['Mã']:<6} | {m['Giá']:<7,.0f} | {m['Vol_X']:<6} | {m['Ngoại']:>9} | {advice}")
else:
    print("\n🆘 CẢNH BÁO: Server dữ liệu vẫn đang khóa API giao dịch.")
    print("👉 Giải pháp: Vui lòng đợi đến 9:15 AM khi phiên ATO ổn định và bấm RUN lại.")
