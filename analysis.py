import streamlit as st
from vnstock import *
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import yfinance as yf

# ==========================================
# 1. HỆ THỐNG BẢO MẬT (PASSWORD)
# ==========================================
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Vui lòng nhập mật mã của Minh:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Sai mật mã! Nhập lại:", type="password", on_change=password_entered, key="password")
        st.error("😕 Mật mã không đúng.")
        return False
    else:
        return True

# ==========================================
# 2. KHỞI CHẠY ỨNG DỤNG CHÍNH
# ==========================================
if check_password():
    st.set_page_config(page_title="Robot Phân Tích 24/7", layout="wide")
    st.title("🛡️ Hệ Thống Chẩn Đoán Siêu Cổ Phiếu")

    # --- HÀM TÍNH TOÁN CHỈ BÁO KỸ THUẬT ---
    def tinh_toan_ky_thuat(df):
        # Bollinger Bands
        df['MA20'] = df['close'].rolling(20).mean()
        df['STD'] = df['close'].rolling(20).std()
        df['Upper'] = df['MA20'] + (df['STD'] * 2)
        df['Lower'] = df['MA20'] - (df['STD'] * 2)
        
        # RSI (14)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/(loss + 1e-9)))
        
        # MACD (12, 26, 9)
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        return df

    # --- HÀM LẤY DỮ LIỆU ĐA NGUỒN (CHỐNG LỖI) ---
    def lay_du_lieu_thong_minh(ticker):
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Thử cách 1: Vnstock Direct
        try:
            df = stock_historical_data(symbol=ticker, start_date=start_date, end_date=end_date, resolution='1D', type='stock')
            if df is not None and not df.empty: return df
        except: pass
        
        # Thử cách 2: Yfinance (Dữ liệu quốc tế cực ổn định)
        try:
            yt = yf.download(f"{ticker}.VN", period="1y", progress=False)
            # Chuẩn hóa tên cột của yfinance về dạng vnstock
            yt.columns = [col[0].lower() if isinstance(col, tuple) else col.lower() for col in yt.columns]
            yt = yt.reset_index().rename(columns={'date': 'date'})
            return yt
        except: return None

    # --- DANH SÁCH MÃ ---
    @st.cache_data(ttl=3600)
    def get_all_tickers():
        try:
            df_ls = stock_listing()
            return df_ls[df_ls['comGroupCode'] == 'HOSE']['ticker'].tolist()
        except:
            return ["FPT","HPG","SSI","TCB","MWG","VNM","VIC","VHM","STB","MSN","DGC","VND","HCM","VCI","HSG"]

    all_tickers = get_all_tickers()

    # --- GIAO DIỆN BÊN TRÁI (SIDEBAR) ---
    st.sidebar.header("🎯 Danh mục theo dõi")
    selected_ticker = st.sidebar.selectbox("Chọn mã muốn soi:", all_tickers, index=0)
    st.sidebar.divider()
    st.sidebar.info("Hệ thống tự động dùng dữ liệu dự phòng nếu server chính bảo trì.")

    # --- NÚT BẤM VÀ HIỂN THỊ ---
    if st.button(f'🚀 BẮT ĐẦU CHẨN ĐOÁN MÃ {selected_ticker}'):
        with st.spinner(f'Đang phân tích sâu {selected_ticker}...'):
            raw_data = lay_du_lieu_thong_minh(selected_ticker)
            
            if raw_data is not None and not raw_data.empty:
                df = tinh_toan_ky_thuat(raw_data)
                last_row = df.iloc[-1]
                
                # 1. Hiển thị các chỉ số chính
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Giá Hiện Tại", f"{last_row['close']:,.0f}")
                    st.write(f"**RSI (14):** {round(last_row['RSI'], 1)}")
                with c2:
                    st.write("**Bollinger Bands**")
                    st.write(f"Upper: {last_row['Upper']:,.0f}")
                    st.write(f"Lower: {last_row['Lower']:,.0f}")
                with c3:
                    macd_status = "TĂNG" if last_row['MACD'] > last_row['Signal'] else "GIẢM"
                    st.write(f"**MACD:** {macd_status}")
                    st.write(f"Tín hiệu: {round(last_row['MACD'], 2)}")
                
                st.divider()
                
                # 2. Nhận định thông minh
                st.write("### 🧠 Nhận định từ Robot:")
                score = 0
                if 30 < last_row['RSI'] < 68: score += 1
                if last_row['MACD'] > last_row['Signal']: score += 1
                if last_row['close'] < last_row['Upper']: score += 1
                
                if score == 3:
                    st.balloons()
                    st.success(f"🌟 **MUA TÍCH LŨY**: {selected_ticker} hội tụ đủ điều kiện bùng nổ. Có thể gom quanh vùng giá này.")
                elif score == 2:
                    st.info(f"⚖️ **THEO DÕI**: {selected_ticker} đang ở trạng thái ổn định. Cần quan sát thêm khối lượng (Volume) ở phiên tới.")
                else:
                    st.warning(f"⚠️ **TẠM ĐỨNG NGOÀI**: Xung lực của {selected_ticker} đang yếu hoặc giá đã chạm vùng cản trên.")
                
                # 3. Vẽ biểu đồ biến động
                st.write(f"### 📈 Biểu đồ giá {selected_ticker} (3 tháng gần nhất)")
                chart_data = df.tail(60).set_index('date')['close']
                st.line_chart(chart_data)
                
            else:
                st.error("Không thể kết nối nguồn dữ liệu. Hãy kiểm tra lại mã cổ phiếu!")

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Cập nhật lúc: {datetime.now().strftime('%H:%M:%S')}")
