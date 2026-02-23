import streamlit as st

st.set_page_config(page_title="Ek İskonto Hesaplayıcı", layout="centered")

st.title("Ek İskonto Hesaplayıcı (2025 GFL ↔ 2026 GFL)")
st.caption("2026 liste fiyatı = 2025 liste fiyatı × 1.08 varsayımıyla hesaplar.")

# --- Constants ---
PRICE_FACTOR_2026_OVER_2025 = 1.08

def list_ratio(from_year: int, to_year: int) -> float:
    """
    ratio = (target_list_price) / (current_list_price)
    """
    if from_year == to_year:
        return 1.0
    if from_year == 2025 and to_year == 2026:
        return PRICE_FACTOR_2026_OVER_2025
    if from_year == 2026 and to_year == 2025:
        return 1.0 / PRICE_FACTOR_2026_OVER_2025
    raise ValueError("Sadece 2025 ve 2026 destekleniyor.")

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

col1, col2 = st.columns(2)
with col1:
    current_year = st.selectbox("Mevcut liste fiyatı yılı", [2025, 2026], index=0)
    current_disc_pct = st.number_input("Mevcut iskonto (%)", min_value=0.0, max_value=100.0, value=45.0, step=0.1)
with col2:
    target_year = st.selectbox("Talep edilen liste fiyatı yılı", [2025, 2026], index=1)
    target_disc_pct = st.number_input("Talep edilen iskonto (%)", min_value=0.0, max_value=100.0, value=45.0, step=0.1)

d_current = current_disc_pct / 100.0
d_target = target_disc_pct / 100.0

ratio = list_ratio(current_year, target_year)

# Equivalent total discount needed on current year's list to match target net
d_equiv = 1.0 - ratio * (1.0 - d_target)

# If d_equiv is outside [0,1], it means target net is impossible (e.g., negative price or >list)
d_equiv_raw = d_equiv
d_equiv = clamp01(d_equiv)

# Additional sequential discount needed beyond current discount
# extra = 1 - (1 - d_equiv) / (1 - d_current)
if (1.0 - d_current) <= 1e-12:
    extra = 0.0
    extra_raw = None
else:
    extra_raw = 1.0 - (1.0 - d_equiv) / (1.0 - d_current)
    extra = extra_raw

delta_points = (d_equiv - d_current)

st.divider()

st.subheader("Sonuçlar")

# Validation / messaging
warnings = []
if d_equiv_raw < 0:
    warnings.append("Talep edilen net fiyat mevcut liste fiyatından yüksek çıkıyor (negatif iskonto gerektiriyor).")
if d_equiv_raw > 1:
    warnings.append("Talep edilen net fiyat 0'ın altına düşüyor (>%100 iskonto gerektiriyor).")

if extra_raw is not None and extra_raw < 0:
    warnings.append("Mevcut iskonto zaten yeterli/iyi. İlave iskonto gerekmiyor (hatta iskonto azaltılmalı).")

if warnings:
    for w in warnings:
        st.warning(w)

st.metric("Mevcut liste yılında gerekli TOPLAM iskonto (%)", f"{d_equiv*100:.2f}")
st.metric("İlave iskonto (sequential, %) ", f"{max(0.0, extra)*100:.2f}")

st.write("**Puan farkı (toplam iskonto puanı):** ", f"{delta_points*100:+.2f} puan")

with st.expander("Hesap mantığı (kısa)"):
    st.write(
        f"""
- 2026/2025 fiyat farkı: **{PRICE_FACTOR_2026_OVER_2025:.2f}x**
- Liste oranı (target/current): **{ratio:.6f}**
- Hedef net oranı (current listeye göre): `ratio × (1 - d_target)`
- Eşdeğer toplam iskonto: `d_equiv = 1 - ratio × (1 - d_target)`
- İlave iskonto (sequential): `extra = 1 - (1 - d_equiv)/(1 - d_current)`
"""
    )

st.divider()
st.caption("Not: İlave iskonto burada 'mevcut iskontolu net fiyata ayrıca uygulanan ek iskonto' olarak hesaplanır (sequential).")
