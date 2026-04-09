import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

# Thiết lập mã cổ phiếu
ma_co_phieu = "FPT.VN" 

try:
    # 1. Tải dữ liệu
    df = yf.download(ma_co_phieu, start="2025-01-01")
    df.columns = df.columns.get_level_values(0)

    # 2. Tính toán chỉ số
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['STD'] = df['Close'].rolling(window=20).std()
    df['BOL_UP'] = df['MA20'] + (df['STD'] * 2)
    df['BOL_DOWN'] = df['MA20'] - (df['STD'] * 2)

    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()

    # 3. In kết quả và lưu ảnh
    print(f"--- Ket qua cho {ma_co_phieu} ---")
    print(f"Gia: {float(df['Close'].iloc[-1]):,.0f}")
    print(f"RSI: {float(df['RSI'].iloc[-1]):.2f}")
    
    plt.figure(figsize=(10,6))
    plt.plot(df['Close'], label='Price')
    plt.plot(df['MA20'], label='MA20')
    plt.savefig('ket_qua.png')
    print("✅ Thanh cong!")
except Exception as e:
    print(f"❌ Loi: {e}")
