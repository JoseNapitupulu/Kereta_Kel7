import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time

st.set_page_config(
    page_title="Kereta Api Jabodetabek – Monte Carlo",
    page_icon="🚆",
    layout="wide"
)

# ── STYLING ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  body { font-family: 'Segoe UI', sans-serif; }
  .main-title { font-size: 2.2rem; font-weight: 800; color: #1a3c6b; text-align: center; padding: 1rem 0 0.2rem; }
  .sub-title  { font-size: 1rem; color: #555; text-align: center; margin-bottom: 1.5rem; }
  .metric-card {
    background: linear-gradient(135deg, #1a3c6b, #2563eb);
    border-radius: 12px; padding: 1rem 1.4rem; color: white; margin-bottom: 0.5rem;
  }
  .metric-card h3 { font-size: 0.85rem; margin: 0; opacity: .8; }
  .metric-card p  { font-size: 1.7rem; font-weight: 700; margin: 0; }
  .result-correct   { background:#d1fae5; border-left: 5px solid #10b981; padding:.5rem 1rem; border-radius:6px; margin:.3rem 0; }
  .result-incorrect { background:#fee2e2; border-left: 5px solid #ef4444; padding:.5rem 1rem; border-radius:6px; margin:.3rem 0; }
  .section-header { font-size:1.3rem; font-weight:700; color:#1a3c6b; border-bottom:2px solid #2563eb; padding-bottom:0.3rem; margin:1.2rem 0 0.8rem; }
  .rn-table th { background:#1a3c6b!important; color:white!important; }
  .stProgress > div > div > div { background: #2563eb; }
</style>
""", unsafe_allow_html=True)

# ── STATIC DATA ───────────────────────────────────────────────────────────────
MONTHS = ["Januari","Februari","Maret","April","Mei","Juni",
          "Juli","Agustus","September","Oktober","November","Desember"]

ACTUAL = {
    2022: [14484,10499,15735,15890,17075,18326,19467,19388,20587,21807,21589,23118],
    2023: [22717,20811,23856,21402,23716,23292,25211,24979,25082,26793,26171,26861],
    2024: [26848,24617,26012,25543,27057,26739,29241,28209,27608,29933,27522,28825],
    2025: [27522,27204,26974,27552,28561,28205,31401,28947,28741,31777,30373,31640],
}

# Prediksi dari spreadsheet (random number yang tertera)
EXCEL_PRED = {
    2023: [14484,18326,15890,15735,17075,19467,21807,19388,23118,19388,21589,17075],
    2024: [22717,23292,21402,23856,21402,25211,25082,25211,26861,25211,26171,21402],
    2025: [26848,27057,26012,24617,25543,26739,27608,29241,28825,29241,27522,25543],
    2026: [None,28561,26974,27204,27552,28205,28741,31401,30373,31401,30373,27552],
}

# Tabel distribusi Monte Carlo (dari spreadsheet)
DIST_TABLES = {
    2022: {  # untuk prediksi 2023
        "frek": [14484,10499,15735,15890,17075,18326,19467,19388,20587,21807,21589,23118],
        "pb":   [0.066451,0.048168,0.07219,0.072902,0.078338,0.084078,0.089313,0.08895,0.094451,0.100048,0.099048,0.106063],
        "dk":   [0.066451,0.114619,0.18681,0.259711,0.33805,0.422127,0.51144,0.60039,0.694841,0.794889,0.893937,1.0],
        "batas_bawah": [0,8,12,20,27,35,43,52,61,70,80,90],
        "batas_atas":  [7,11,19,26,34,42,51,60,69,79,89,100],
    },
    2023: {  # untuk prediksi 2024
        "frek": [22717,20811,23856,21402,23716,23292,25211,24979,25082,26793,26171,26861],
        "pb":   [0.078095,0.071542,0.08201,0.073574,0.081529,0.080071,0.086668,0.085871,0.086225,0.092107,0.089968,0.09234],
        "dk":   [0.078095,0.149637,0.231647,0.305221,0.38675,0.466821,0.553489,0.63936,0.725584,0.817691,0.90766,1.0],
        "batas_bawah": [0,9,16,24,32,40,48,56,65,74,83,92],
        "batas_atas":  [8,15,23,31,39,47,55,64,73,82,91,100],
    },
    2024: {  # untuk prediksi 2025
        "frek": [26848,24617,26012,25543,27057,26739,29241,28209,27608,29933,27522,28825],
        "pb":   [0.081815,0.075017,0.079268,0.077838,0.082452,0.081483,0.089108,0.085963,0.084131,0.091216,0.083869,0.08784],
        "dk":   [0.081815,0.156832,0.2361,0.313938,0.39639,0.477873,0.566981,0.652943,0.737075,0.828291,0.91216,1.0],
        "batas_bawah": [0,9,17,25,32,41,49,58,66,75,84,92],
        "batas_atas":  [8,16,24,31,40,48,57,65,74,83,91,100],
    },
    2025: {  # untuk prediksi 2026
        "frek": [27522,27204,26974,27552,28561,28205,31401,28947,28741,31777,30373,28825],
        "pb":   [0.079525,0.078606,0.077941,0.079611,0.082527,0.081498,0.090733,0.083642,0.083047,0.091819,0.087762,0.08329],
        "dk":   [0.079525,0.15813,0.236071,0.315682,0.398209,0.479707,0.57044,0.654082,0.737129,0.828948,0.91671,1.0],
        "batas_bawah": [0,9,17,25,33,41,49,58,66,75,84,93],
        "batas_atas":  [8,16,24,32,40,48,57,65,74,83,92,100],
    },
}

# Random numbers dari spreadsheet
RANDOM_NUMBERS = {
    2023: [4,40,24,16,28,48,70,52,92,54,88,30],   # beberapa dari spreadsheet (baris 30-35)
    2024: [4,40,24,16,28,48,70,52,92,54,88,30],
    2025: [4,40,24,16,28,48,70,52,92,54,88,30],
    2026: [4,40,24,16,28,48,70,52,92,54,88,30],
}

# ── HELPER FUNCTIONS ──────────────────────────────────────────────────────────

def lookup_prediction(rn: int, dist: dict) -> int:
    """Cari prediksi berdasarkan random number dan tabel distribusi."""
    for i, (bl, bu) in enumerate(zip(dist["batas_bawah"], dist["batas_atas"])):
        if bl <= rn <= bu:
            return dist["frek"][i]
    return dist["frek"][-1]

def run_monte_carlo(base_year: int, random_numbers: list) -> list:
    """Jalankan simulasi Monte Carlo untuk 12 bulan."""
    dist = DIST_TABLES[base_year]
    predictions = []
    for rn in random_numbers:
        pred = lookup_prediction(rn, dist)
        predictions.append(pred)
    return predictions

def accuracy_pct(pred: list, actual: list) -> float:
    correct = sum(1 for p, a in zip(pred, actual) if p == a)
    return correct / len(actual) * 100

def mape(pred: list, actual: list) -> float:
    errors = [abs(p - a) / a * 100 for p, a in zip(pred, actual) if a != 0]
    return np.mean(errors) if errors else 0

def color_accuracy(pct):
    if pct >= 80: return "#10b981"
    if pct >= 50: return "#f59e0b"
    return "#ef4444"

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "sim_done" not in st.session_state:
    st.session_state.sim_done = {}
if "user_rn" not in st.session_state:
    st.session_state.user_rn = {}

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">🚆 Kereta Api Jabodetabek</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Simulasi Monte Carlo – Prediksi Jumlah Penumpang 2023–2026</div>', unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Data Aktual", "🎲 Simulasi Monte Carlo", "📈 Ringkasan & Grafik"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 – DATA AKTUAL
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Data Penumpang Aktual (ribuan penumpang/bulan)</div>', unsafe_allow_html=True)

    rows = []
    for m in MONTHS:
        row = {"Bulan": m}
        for yr in [2022, 2023, 2024, 2025]:
            row[str(yr)] = f"{ACTUAL[yr][MONTHS.index(m)]:,}"
        rows.append(row)

    df_actual = pd.DataFrame(rows)
    st.dataframe(df_actual, use_container_width=True, hide_index=True)

    # Totals
    cols = st.columns(4)
    for i, yr in enumerate([2022, 2023, 2024, 2025]):
        total = sum(ACTUAL[yr])
        cols[i].markdown(f"""
        <div class="metric-card">
          <h3>Total {yr}</h3>
          <p>{total:,}</p>
        </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">Grafik Tren Bulanan per Tahun</div>', unsafe_allow_html=True)
    fig = go.Figure()
    colors = ["#94a3b8","#2563eb","#10b981","#f59e0b"]
    for i, yr in enumerate([2022,2023,2024,2025]):
        fig.add_trace(go.Scatter(
            x=MONTHS, y=ACTUAL[yr], mode="lines+markers",
            name=str(yr), line=dict(color=colors[i], width=2.5),
            marker=dict(size=7)
        ))
    fig.update_layout(
        title="Jumlah Penumpang Kereta Api Jabodetabek 2022–2025",
        xaxis_title="Bulan", yaxis_title="Penumpang",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        height=430, plot_bgcolor="white",
        yaxis=dict(gridcolor="#e5e7eb"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Tabel distribusi
    st.markdown('<div class="section-header">Tabel Distribusi Probabilitas (digunakan Monte Carlo)</div>', unsafe_allow_html=True)
    for base_yr in [2022,2023,2024,2025]:
        pred_yr = base_yr + 1
        with st.expander(f"📋 Distribusi dari data {base_yr} → untuk prediksi {pred_yr}"):
            d = DIST_TABLES[base_yr]
            df_d = pd.DataFrame({
                "Bulan": MONTHS,
                "Frekuensi": d["frek"],
                "Pb": [f"{v:.6f}" for v in d["pb"]],
                "Dk (kumulatif)": [f"{v:.6f}" for v in d["dk"]],
                "Batas Bawah RN": d["batas_bawah"],
                "Batas Atas RN": d["batas_atas"],
            })
            st.dataframe(df_d, use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 – SIMULASI MONTE CARLO
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### Cara Kerja Monte Carlo")
    st.info(
        "1️⃣ Hitung distribusi probabilitas dari data tahun sebelumnya\n"
        "2️⃣ Tentukan interval random number (0-100) untuk setiap bulan\n"
        "3️⃣ Bangkitkan / masukkan random number\n"
        "4️⃣ Petakan RN → prediksi bulan berdasarkan tabel interval\n"
        "5️⃣ Bandingkan prediksi dengan data aktual"
    )

    st.divider()

    for target_year in [2023, 2024, 2025, 2026]:
        base_year = target_year - 1
        actual_available = target_year in ACTUAL

        st.markdown(f'<div class="section-header">🎯 Prediksi Tahun {target_year} (berbasis data {base_year})</div>', unsafe_allow_html=True)

        # Input mode
        col_opt1, col_opt2 = st.columns([2,3])
        with col_opt1:
            rn_mode = st.radio(
                f"Sumber Random Number {target_year}:",
                ["📋 Gunakan RN dari spreadsheet", "🎲 Bangkitkan otomatis (acak)", "✏️ Input manual"],
                key=f"mode_{target_year}",
                horizontal=False,
            )

        rn_list = None

        if rn_mode == "📋 Gunakan RN dari spreadsheet":
            # Ambil RN yang tertera di Excel (subset, sisanya generate)
            # Dari spreadsheet: row 30-46 ada angka di col 0 & 1
            # Mapping manual sesuai analisis file
            EXCEL_RN = {
                2023: [4,40,24,16,28,48,70,52,92,54,88,30],
                2024: [4,40,24,16,28,48,70,52,92,54,88,30],
                2025: [4,40,24,16,28,48,70,52,92,54,88,30],
                2026: [4,40,24,16,28,48,70,52,92,54,88,30],
            }
            if EXCEL_RN.get(target_year):
                # Fill None dengan random
                rns = []
                for v in EXCEL_RN[target_year]:
                    rns.append(v if v is not None else np.random.randint(0,101))
                rn_list = rns
                st.success(f"Random number dari spreadsheet (None = dibangkitkan): [4,40,24,16,28,48,70,52,92,54,88,30]")
            else:
                st.warning("Random number dari spreadsheet (None = dibangkitkan): [4,40,24,16,28,48,70,52,92,54,88,30]")
                rn_list = [np.random.randint(0, 101) for _ in range(12)]

        elif rn_mode == "🎲 Bangkitkan otomatis (acak)":
            if st.button(f"🔀 Generate Random Numbers {target_year}", key=f"gen_{target_year}"):
                st.session_state.user_rn[target_year] = [np.random.randint(0, 101) for _ in range(12)]
            rn_list = st.session_state.user_rn.get(target_year, [np.random.randint(0,101) for _ in range(12)])

        else:  # Manual
            with st.expander(f"✏️ Input 12 Random Number untuk {target_year} (0–100)"):
                manual_rns = []
                cols_rn = st.columns(6)
                for i, m in enumerate(MONTHS):
                    with cols_rn[i % 6]:
                        v = st.number_input(m[:3], 0, 100, value=np.random.randint(0,101), key=f"rn_{target_year}_{i}")
                        manual_rns.append(v)
                rn_list = manual_rns

        # ── RUN SIMULATION ──
        if st.button(f"▶️ Jalankan Simulasi {target_year}", key=f"run_{target_year}", type="primary"):
            with st.spinner("Menjalankan simulasi..."):
                progress_bar = st.progress(0)
                predictions = []
                dist = DIST_TABLES[base_year]

                for i, rn in enumerate(rn_list):
                    time.sleep(0.05)
                    pred = lookup_prediction(rn, dist)
                    predictions.append(pred)
                    progress_bar.progress((i + 1) / 12)

                st.session_state.sim_done[target_year] = {
                    "rn": rn_list,
                    "pred": predictions,
                }
                progress_bar.empty()
                st.success("✅ Simulasi selesai!")

        # ── SHOW RESULTS ──
        if target_year in st.session_state.sim_done:
            res = st.session_state.sim_done[target_year]
            rns_used = res["rn"]
            preds = res["pred"]

            st.markdown("#### 🔢 Random Numbers yang digunakan")
            df_rn = pd.DataFrame([rns_used], columns=MONTHS, index=["RN"])
            st.dataframe(df_rn, use_container_width=True)

            st.markdown("#### 📊 Hasil Prediksi vs Aktual")

            if actual_available:
                actual = ACTUAL[target_year]
                rows_result = []
                exact_match = 0
                for i, m in enumerate(MONTHS):
                    p = preds[i]
                    a = actual[i]
                    selisih = p - a
                    pct_err = abs(selisih) / a * 100
                    pct_benar = max(0, 100 - pct_err)
                    if p == a:
                        exact_match += 1
                    rows_result.append({
                        "Bulan": m,
                        "RN": rns_used[i],
                        "Prediksi": f"{p:,}",
                        "Aktual": f"{a:,}",
                        "Selisih": f"{selisih:+,}",
                        "Error %": f"{pct_err:.1f}%",
                        "% Benar": f"{pct_benar:.1f}%",
                    })

                df_res = pd.DataFrame(rows_result)
                st.dataframe(df_res, use_container_width=True, hide_index=True)

                # Accuracy metrics
                acc_exact = exact_match / 12 * 100
                mape_val = mape(preds, actual)
                close_match = sum(1 for p, a in zip(preds, actual) if abs(p-a)/a < 0.05)
                close_pct = close_match / 12 * 100

                mc1, mc2, mc3 = st.columns(3)
                with mc1:
                    st.metric("🎯 Tepat Sama (Exact Match)", f"{exact_match}/12", f"{acc_exact:.1f}%")
                with mc2:
                    st.metric("📏 Dalam ±5% Error", f"{close_match}/12", f"{close_pct:.1f}%")
                with mc3:
                    st.metric("📉 MAPE (Mean Abs % Error)", f"{mape_val:.2f}%")

                # Bar chart comparison
                fig_cmp = go.Figure()
                fig_cmp.add_trace(go.Bar(name="Prediksi", x=MONTHS, y=preds, marker_color="#2563eb", opacity=0.85))
                fig_cmp.add_trace(go.Bar(name="Aktual", x=MONTHS, y=actual, marker_color="#10b981", opacity=0.85))
                fig_cmp.update_layout(
                    title=f"Prediksi vs Aktual {target_year}",
                    barmode="group", height=380,
                    yaxis_title="Penumpang", plot_bgcolor="white",
                    textfont=dict(color="black"),
                    yaxis=dict(gridcolor="#e5e7eb"),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                )
                st.plotly_chart(fig_cmp, use_container_width=True)

                # Accuracy bar per bulan
                err_pcts = [abs(preds[i]-actual[i])/actual[i]*100 for i in range(12)]
                colors_bar = ["#10b981" if e < 5 else "#f59e0b" if e < 15 else "#ef4444" for e in err_pcts]
                fig_err = go.Figure(go.Bar(
                    x=MONTHS, y=err_pcts, marker_color=colors_bar,
                    text=[f"{v:.1f}%" for v in err_pcts], textposition="outside",textfont=dict(color="black"),
                ))
                fig_err.add_hline(y=5, line_dash="dash", line_color="#10b981", annotation_text="5% threshold")
                fig_err.update_layout(
                    title=f"Error Persentase per Bulan – {target_year}",
                    yaxis_title="Error (%)", height=340, plot_bgcolor="white",
                    yaxis=dict(gridcolor="#111827"),
                )
                st.plotly_chart(fig_err, use_container_width=True)

            else:
                # 2026 – no actual data
                st.info("ℹ️ Data aktual tahun 2026 belum tersedia. Berikut hasil prediksi:")
                df_pred_only = pd.DataFrame({
                    "Bulan": MONTHS,
                    "RN": rns_used,
                    "Prediksi 2026": [f"{p:,}" for p in preds],
                })
                st.dataframe(df_pred_only, use_container_width=True, hide_index=True)

                fig_2026 = go.Figure(go.Bar(
                    x=MONTHS, y=preds, marker_color="#7c3aed",
                    text=[f"{p:,}" for p in preds], textposition="outside",textfont=dict(color="black"),
                ))
                fig_2026.update_layout(
                    title="Prediksi Penumpang Kereta Api Jabodetabek 2026",
                    yaxis_title="Penumpang", height=380, plot_bgcolor="white",
                    yaxis=dict(gridcolor="#e5e7eb"),
                )
                st.plotly_chart(fig_2026, use_container_width=True)

                st.metric("📊 Total Prediksi 2026", f"{sum(preds):,}")

        st.divider()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 – RINGKASAN
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">📈 Grafik Tren Lengkap + Prediksi</div>', unsafe_allow_html=True)

    fig_all = go.Figure()
    colors_yr = {2022:"#94a3b8", 2023:"#2563eb", 2024:"#10b981", 2025:"#f59e0b"}

    for yr, clr in colors_yr.items():
        fig_all.add_trace(go.Scatter(
            x=MONTHS, y=ACTUAL[yr], mode="lines+markers",
            name=f"Aktual {yr}", line=dict(color=clr, width=2.5),
        ))

    # Overlay prediksi jika sudah ada
    pred_colors = {2023:"#1e40af",2024:"#065f46",2025:"#92400e",2026:"#6d28d9"}
    for yr, clr in pred_colors.items():
        if yr in st.session_state.sim_done:
            preds = st.session_state.sim_done[yr]["pred"]
            fig_all.add_trace(go.Scatter(
                x=MONTHS, y=preds, mode="lines+markers",
                name=f"Prediksi {yr}", line=dict(color=clr, width=2, dash="dash"),
                marker=dict(symbol="diamond", size=8),
            ))

    fig_all.update_layout(
        title="Tren Penumpang Kereta Api Jabodetabek (Aktual & Prediksi Monte Carlo)",
        xaxis_title="Bulan", yaxis_title="Penumpang",
        height=480, plot_bgcolor="white",
        yaxis=dict(gridcolor="#e5e7eb"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    st.plotly_chart(fig_all, use_container_width=True)

    # ── Ringkasan akurasi ──
    st.markdown('<div class="section-header">📋 Ringkasan Akurasi Simulasi</div>', unsafe_allow_html=True)

    sim_years = [y for y in [2023,2024,2025] if y in st.session_state.sim_done]
    if not sim_years:
        st.info("⬅️ Jalankan simulasi di tab **Simulasi Monte Carlo** terlebih dahulu.")
    else:
        summary_rows = []
        for yr in sim_years:
            preds = st.session_state.sim_done[yr]["pred"]
            actual = ACTUAL[yr]
            exact = sum(1 for p,a in zip(preds,actual) if p==a)
            close = sum(1 for p,a in zip(preds,actual) if abs(p-a)/a < 0.05)
            mape_v = mape(preds, actual)
            summary_rows.append({
                "Tahun": yr,
                "Exact Match": f"{exact}/12 ({exact/12*100:.0f}%)",
                "Dalam ±5%": f"{close}/12 ({close/12*100:.0f}%)",
                "MAPE": f"{mape_v:.2f}%",
                "Prediksi Total": f"{sum(preds):,}",
                "Aktual Total": f"{sum(actual):,}",
                "Selisih Total": f"{sum(preds)-sum(actual):+,}",
            })

        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

        # MAPE bar chart
        fig_mape = go.Figure(go.Bar(
            x=[str(r["Tahun"]) for r in summary_rows],
            y=[float(r["MAPE"].replace("%","")) for r in summary_rows],
            text=[r["MAPE"] for r in summary_rows],
            textposition="outside",
            marker_color=["#2563eb","#10b981","#f59e0b"][:len(summary_rows)],
        ))
        fig_mape.update_layout(
            title="MAPE per Tahun Prediksi",
            yaxis_title="MAPE (%)", height=320, plot_bgcolor="white",
            yaxis=dict(gridcolor="#e5e7eb"),
        )
        st.plotly_chart(fig_mape, use_container_width=True)

    # ── Annual totals comparison ──
    st.markdown('<div class="section-header">📊 Perbandingan Total Tahunan</div>', unsafe_allow_html=True)
    yr_labels = []
    totals_actual = []
    totals_pred = []
    for yr in [2022,2023,2024,2025]:
        yr_labels.append(str(yr))
        totals_actual.append(sum(ACTUAL[yr]))
        if yr in st.session_state.sim_done and yr in ACTUAL:
            totals_pred.append(sum(st.session_state.sim_done[yr]["pred"]))
        else:
            totals_pred.append(None)

    fig_yr = go.Figure()
    fig_yr.add_trace(go.Bar(name="Aktual", x=yr_labels, y=totals_actual, marker_color="#2563eb"))
    pred_vals = [v for v in totals_pred if v is not None]
    pred_lbls = [yr_labels[i] for i,v in enumerate(totals_pred) if v is not None]
    if pred_vals:
        fig_yr.add_trace(go.Bar(name="Prediksi MC", x=pred_lbls, y=pred_vals, marker_color="#10b981", opacity=0.8))
    fig_yr.update_layout(
        title="Total Penumpang per Tahun – Aktual vs Prediksi Monte Carlo",
        barmode="group", height=380, plot_bgcolor="white",
        yaxis=dict(gridcolor="#e5e7eb"),
    )
    st.plotly_chart(fig_yr, use_container_width=True)

    # Footer
    st.markdown("---")
    st.caption("📌 Simulasi Monte Carlo | Data: Kereta Api Jabodetabek 2022–2025 | Prediksi 2023–2026")
    st.caption("Metode: Distribusi Probabilitas Empiris → Interval Random Number → Pemetaan Prediksi")
