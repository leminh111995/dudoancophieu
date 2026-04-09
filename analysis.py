from vnstock3 import Vnstock

# 1. Thiết lập mã cổ phiếu cần xem (Ví dụ mã FPT)
ma_co_phieu = 'FPT'

# 2. Lấy dữ liệu lịch sử
stock = Vnstock().stock(symbol=ma_co_phieu, source='VCI')
df = stock.quote.history(start='2024-01-01', end='2026-04-09')

# 3. In ra màn hình 5 ngày gần nhất để kiểm tra
print(f"Dữ liệu cổ phiếu {ma_co_phieu}:")
print(df.tail())
