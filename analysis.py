import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import os

# 1. Cấu hình mã cổ phiếu
# Nếu chạy trên GitHub (robot), mặc định lấy FPT.VN. Nếu chạy tay trên máy, có thể đổi ở đây.
ma_co_phieu = "FPT.VN" 

print(f"--- Đang phân tích mã: {ma_co_phieu} ---")

try:
    # 2. Tải dữ liệu
    df = yf.download(ma_co_phieu, start="2025-01-01")
    df.columns = df.columns.get_level_values(0)

    # 3. Tính toán các chỉ số (BOL, RSI, MACD)
    # Bollinger Bands
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['STD'] = df['Close'].rolling(window=20).std()
    df['BOL_UP'] = df['MA20'] + (df['STD'] * 2)
    df['BOL_DOWN'] = df['MA20'] - (df['STD'] * 2)

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # 4. Xuất kết quả ra dòng lệnh (Để robot ghi lại nhật ký)
    gia_cuoi = float(df['Close'].iloc[-1])
    rsi_cuoi = float(df['RSI'].iloc[-1])
    macd_cuoi = float(df['MACD'].iloc[-1])
    sig_cuoi = float(df['Signal'].iloc[-1])

    print(f"Gia hien tai: {gia_cuoi:,.0f} VND")
    print(f"RSI: {rsi_cuoi:.2f}")
    print(f"MACD: {'Tang' if macd_cuoi > sig_cuoi else 'Giam'}")
    
    # 5. Lưu biểu đồ thành file ảnh (Quan trọng để robot không bị treo)
    plt.figure(figsize=(10,6))
    plt.plot(df['Close'], label='Price')
    plt.plot(df['MA20'], label='MA20')
    plt.title(f'Analysis {ma_co_phieu}')
    plt.savefig('ket_qua.png') # Lưu thành ảnh thay vì plt.show()
    print("✅ Da luu bieu do vao file ket_qua.png")

except Exception as e:
    print(f"❌ Loi: {e}")
