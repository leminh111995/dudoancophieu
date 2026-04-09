import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

# 1. Tải dữ liệu
ma_input = input("Nhập mã cổ phiếu (ví dụ: FPT, VCB, HPG): ")
ma_co_phieu = ma_input.upper() + ".VN"
df = yf.download(ma_co_phieu, start="2025-01-01")
df.columns = df.columns.get_level_values(0)

# 2. TÍNH TOÁN CÁC CHỈ SỐ
# Bollinger Bands
df['MA20'] = df['Close'].rolling(window=20).mean()
df['STD'] = df['Close'].rolling(window=20).std()
df['BOL_UP'] = df['MA20'] + (df['STD'] * 2)
df['BOL_DOWN'] = df['MA20'] - (df['STD'] * 2)

# RSI (14 ngày)
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

# 3. VẼ BIỂU ĐỒ (3 phần riêng biệt)
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12), sharex=True)

# Biểu đồ giá và Bollinger Bands
ax1.plot(df['Close'], label='Giá thực tế', color='blue', alpha=0.6)
ax1.plot(df['BOL_UP'], label='Dải trên (BOL)', color='red', linestyle='--', alpha=0.3)
ax1.plot(df['BOL_DOWN'], label='Dải dưới (BOL)', color='green', linestyle='--', alpha=0.3)
ax1.fill_between(df.index, df['BOL_DOWN'], df['BOL_UP'], color='gray', alpha=0.1)
ax1.set_title(f'Phân tích mã {ma_co_phieu}')
ax1.legend()

# Biểu đồ RSI
ax2.plot(df['RSI'], label='RSI (Sức mạnh mua/bán)', color='purple')
ax2.axhline(70, color='red', linestyle='--') # Vùng quá mua
ax2.axhline(30, color='green', linestyle='--') # Vùng quá bán
ax2.set_ylim(0, 100)
ax2.legend()

# Biểu đồ MACD
ax3.plot(df['MACD'], label='Đường MACD', color='blue')
ax3.plot(df['Signal'], label='Đường Tín hiệu', color='orange')
ax3.bar(df.index, df['MACD'] - df['Signal'], color='gray', alpha=0.2) # Cột sóng
ax3.legend()

plt.tight_layout()
plt.show()

# 4. TỔNG HỢP NHẬN ĐỊNH
gia_cuoi = float(df['Close'].iloc[-1])
rsi_cuoi = float(df['RSI'].iloc[-1])
macd_cuoi = float(df['MACD'].iloc[-1])
sig_cuoi = float(df['Signal'].iloc[-1])

print(f"--- NHẬN ĐỊNH KỸ THUẬT CHO {ma_co_phieu} ---")
print(f"1. Bollinger Bands: Giá đang ở mức {gia_cuoi:,.0f} VNĐ")
print(f"2. RSI: {rsi_cuoi:.2f} ({'Quá mua - Rủi ro' if rsi_cuoi > 70 else 'Quá bán - Cơ hội' if rsi_cuoi < 30 else 'Trung bình'})")
print(f"3. MACD: {'Xu hướng TĂNG' if macd_cuoi > sig_cuoi else 'Xu hướng GIẢM'}")

# 4. ĐƯA RA LỜI KHUYÊN
# Lấy giá trị cuối cùng và chuyển về số thực (float) để in ra
gia_hien_tai = float(df['Close'].iloc[-1])
gia_du_bao = float(df['MA20'].iloc[-1])

print(f"--- KẾT QUẢ ---")
print(f"Giá đóng cửa gần nhất: {gia_hien_tai:,.0f} VNĐ")

if gia_hien_tai > gia_du_bao:
    print("👉 DỰ ĐOÁN: XU HƯỚNG TĂNG. Có thể cân nhắc MUA.")
else:
    print("👉 DỰ ĐOÁN: XU HƯỚNG GIẢM. Nên THẬN TRỌNG.")
