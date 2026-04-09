import yfinance as yf
import matplotlib.pyplot as plt

# 1. Lấy dữ liệu
ma_co_phieu = "FPT.VN"
df = yf.download(ma_co_phieu, start="2025-01-01")

# SỬA LỖI: Làm phẳng dữ liệu để dễ tính toán
df.columns = df.columns.get_level_values(0)

# 2. TÍNH TOÁN (Đường trung bình 20 ngày)
df['MA20'] = df['Close'].rolling(window=20).mean()

# 3. VẼ BIỂU ĐỒ
plt.figure(figsize=(12,6))
plt.plot(df['Close'], label='Giá thực tế', color='blue')
plt.plot(df['MA20'], label='Đường xu hướng (MA20)', color='orange')
plt.title(f'Bieu do co phieu {ma_co_phieu}')
plt.legend()
plt.grid(True) # Thêm lưới cho dễ nhìn
plt.show()

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
