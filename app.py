import streamlit as st

st.set_page_config(page_title="Ek İskonto Hesaplayıcı", layout="centered")

st.title("Ek İskonto Hesaplayıcı (2025 GFL ↔ 2026 GFL)")
st.caption("Varsayım: 2026 liste fiyatı = 2025 liste fiyatı × 1.08")

PRICE_FACTOR_2026_OVER_2025 = 1.08

def list_ratio(current_year: int, target_year: int) -> float:
    """
    ratio = (target_list_price) / (current_list_price)
    """
    if current_year == target_year:
        return 1.0
    if current_year == 2025 and target_year == 2026:
        return PRICE_FACTOR_2026_OVER_2025
    if current_year == 2026 and target_year == 2025:
        return 1.0 / PRICE_FACTOR_2026_OVER_2025
    raise ValueError("Sadece 2025 ve 2026 destekleniyor.")

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

def fmt_tr_percent(x: float, decimals: int = 2) -> str:
    # x: 0.0741 -> "%7,41"
    return f"%{x*100:.{decimals}f}".replace(".", ",")

def fmt_tr_number(x: float, decimals: int = 4) -> str:
    return f"{x:.{decimals}f}".replace(".", ",")

# --- Inputs ---
col1, col2 = st.columns(2)
with col1:
    current_year = st.selectbox("Mevcut liste fiyatı yılı", [2025, 2026], index=0)
    current_disc_pct = st.number_input(
        "Mevcut iskonto (%)", min_value=0.0, max_value=100.0, value=45.0, step=0.1
    )
with col2:
    target_year = st.selectbox("Talep edilen liste fiyatı yılı", [2025, 2026], index=1)
    target_disc_pct = st.number_input(
        "Talep edilen iskonto (%)", min_value=0.0, max_value=100.0, value=45.0, step=0.1
    )

d_current = current_disc_pct / 100.0
d_target = target_disc_pct / 100.0

# --- Core calc ---
ratio = list_ratio(current_year, target_year)

# Equivalent total discount needed on current year's list to match target net:
# d_equiv = 1 - ratio * (1 - d_target)
d_equiv_raw = 1.0 - ratio * (1.0 - d_target)
d_equiv = clamp01(d_equiv_raw)

# Additional sequential discount beyond current discount:
# extra = 1 - (1 - d_equiv) / (1 - d_current)
extra_raw = None
if (1.0 - d_current) > 1e-12:
    extra_raw = 1.0 - (1.0 - d_equiv) / (1.0 - d_current)

# For display: if extra is negative -> show 0
extra_pos = max(0.0, extra_raw) if extra_raw is not None else 0.0
multiplier = 1.0 - extra_pos  # multiply net price by this

delta_points = (d_equiv - d_current) * 100.0  # in points

# --- UI ---
st.divider()
st.subheader("Sonuçlar")

warnings = []
if d_equiv_raw < 0:
    warnings.append("Talep edilen net fiyat mevcut liste fiyatından yüksek çıkıyor (negatif iskonto gerektiriyor).")
if d_equiv_raw > 1:
    warnings.append("Talep edilen net fiyat 0'ın altına düşüyor (>%100 iskonto gerektiriyor).")
if extra_raw is not None and extra_raw < 0:
    warnings.append("Mevcut iskonto zaten yeterli. İlave iskonto gerekmiyor (gerekirse iskonto azaltılmalı).")

for w in warnings:
    st.warning(w)

st.metric("Mevcut liste yılında gerekli TOPLAM iskonto (%)", f"{d_equiv*100:.2f}")
st.metric("İlave iskonto (sequential)", fmt_tr_percent(extra_pos, 2))

st.write(f"Bu ilave iskontoyu uygulamak için net fiyatta **{fmt_tr_number(multiplier, 4)}** ile çarpın.")
st.write("**Puan farkı (toplam iskonto puanı):** ", f"{delta_points:+.2f} puan")

with st.expander("Detay (hesap mantığı)"):
    st.write(
        f"""
- 2026/2025 fiyat farkı: **{PRICE_FACTOR_2026_OVER_2025:.2f}x**
- Liste oranı (target/current): **{ratio:.6f}**
- Eşdeğer toplam iskonto: `d_equiv = 1 - ratio × (1 - d_target)`
- İlave iskonto (sequential): `extra = 1 - (1 - d_equiv)/(1 - d_current)`
- Net çarpan: `multiplier = 1 - extra`
"""
    )

st.divider()
st.caption("Not: İlave iskonto 'mevcut iskontolu net fiyata ayrıca uygulanan ek iskonto' (sequential) olarak hesaplanır.")
