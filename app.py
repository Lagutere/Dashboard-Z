import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# --- FICHIER DE SAUVEGARDE PERSISTANTE ---
CONFIG_FILE = "config_ziggy.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_config():
    config = {
        'obj_colis_val': st.session_state.get('obj_colis_val', "1500"),
        'defi_val': st.session_state.get('defi_val', "Zéro erreur de picking sur les références sensibles + Fluidité sur l'emballage."),
        'amelioration_val': st.session_state.get('amelioration_val', "Positif : Bonne cadence globale entre 8h et 11h. Amélioration : Réduire le temps de pause."),
        'qualite_val': st.session_state.get('qualite_val', "RAS ce matin. Vigilance sur les sacs percés."),
        'obj_delai_lundi': st.session_state.get('obj_delai_lundi', 1.40),
        'obj_delai_autre': st.session_state.get('obj_delai_autre', 0.80),
        'obj_temps_lundi': st.session_state.get('obj_temps_lundi', 80.0),
        'obj_temps_autre': st.session_state.get('obj_temps_autre', 90.0),
        'obj_prod': st.session_state.get('obj_prod', 18.0)
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

saved_data = load_config()

# --- CONFIGURATION DE LA PAGE & DESIGN ZIGGY ---
st.set_page_config(page_title="Dashboard Logistique - Ziggy", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f7f9f6; }
    
    /* Grand bandeau titre principal */
    .main-title-banner {
        background-color: #1a4d2e;
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        font-size: 2.2em;
        font-weight: bold;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        font-family: 'Helvetica Neue', sans-serif;
    }

    /* Arrière-plans globaux très légèrement teintés */
    .bg-section-veille {
        background-color: rgba(26, 77, 46, 0.03);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 30px;
    }

    .bg-section-jour {
        background-color: rgba(64, 224, 208, 0.08);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 30px;
    }

    /* Titres avec fond surligné */
    .title-highlight-veille {
        background-color: rgba(26, 77, 46, 0.15);
        color: #1a4d2e;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 1.5em;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 15px;
        font-family: 'Helvetica Neue', sans-serif;
    }

    .title-highlight-jour {
        background-color: #7fffd4;
        color: #1a4d2e;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 1.5em;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 15px;
        font-family: 'Helvetica Neue', sans-serif;
    }

    h2, h3 { color: #1a4d2e !important; font-family: 'Helvetica Neue', sans-serif; }
    .stButton>button { background-color: #1a4d2e; color: white; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# Titre dans un bandeau de couleur
st.markdown('<div class="main-title-banner">🐾 Dashboard Logistique & Préparation - Ziggy</div>', unsafe_allow_html=True)

# --- 1. INITIALISATION DE LA MÉMOIRE (SESSION STATE AVEC CHARGEMENT FICHIER) ---
if 'obj_colis_val' not in st.session_state:
    st.session_state.obj_colis_val = saved_data.get('obj_colis_val', "1500")
if 'defi_val' not in st.session_state:
    st.session_state.defi_val = saved_data.get('defi_val', "Zéro erreur de picking sur les références sensibles + Fluidité sur l'emballage.")
if 'amelioration_val' not in st.session_state:
    st.session_state.amelioration_val = saved_data.get('amelioration_val', "Positif : Bonne cadence globale entre 8h et 11h. Amélioration : Réduire le temps de pause.")
if 'qualite_val' not in st.session_state:
    st.session_state.qualite_val = saved_data.get('qualite_val', "RAS ce matin. Vigilance sur les sacs percés.")

if 'obj_delai_lundi' not in st.session_state:
    st.session_state.obj_delai_lundi = saved_data.get('obj_delai_lundi', 1.40)
if 'obj_delai_autre' not in st.session_state:
    st.session_state.obj_delai_autre = saved_data.get('obj_delai_autre', 0.80)
if 'obj_temps_lundi' not in st.session_state:
    st.session_state.obj_temps_lundi = saved_data.get('obj_temps_lundi', 80.0)
if 'obj_temps_autre' not in st.session_state:
    st.session_state.obj_temps_autre = saved_data.get('obj_temps_autre', 90.0)
if 'obj_prod' not in st.session_state:
    st.session_state.obj_prod = saved_data.get('obj_prod', 18.0)

# --- CALLBACK DE SAUVEGARDE AUTOMATIQUE ---
def update_config():
    save_config()

# --- 2. IMPORTATION DU CSV ---
st.sidebar.header("📁 Données WMS / CSV")
uploaded_file = st.sidebar.file_uploader("Importer le CSV quotidien", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-16', sep=None, engine='python')
    except:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding='utf-8', sep=None, engine='python')
    
    df.columns = df.columns.str.strip()

    # --- SÉLECTION DES DATES ---
    df['Date_parsed'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
    valid_dates = df['Date_parsed'].dropna().dt.date.unique()
    
    if len(valid_dates) > 0:
        default_date = valid_dates[-1]
    else:
        default_date = pd.Timestamp.today().date()

    selected_date = st.sidebar.date_input("📅 Sélectionner la date du point", value=default_date)

    df_selected = df[df['Date_parsed'].dt.date == selected_date]
    
    if df_selected.empty:
        idx_selected = len(df) - 1
        row_veille = df.iloc[-1]
    else:
        idx_selected = df_selected.index[0]
        row_veille = df_selected.iloc[0]

    # Détermination du jour de la semaine (0 = Lundi, etc.)
    day_of_week = pd.to_datetime(selected_date).dayofweek
    is_lundi = (day_of_week == 0)

    # Objectifs actifs du jour
    obj_delai_actif = st.session_state.obj_delai_lundi if is_lundi else st.session_state.obj_delai_autre
    obj_temps_actif = st.session_state.obj_temps_lundi if is_lundi else st.session_state.obj_temps_autre

    # ==========================================
    # BLOC 1 : BILAN & INDICATEURS DE LA VEILLE
    # ==========================================
    st.markdown('<div class="bg-section-veille">', unsafe_allow_html=True)
    st.markdown('<div class="title-highlight-veille">🐱 Bilan & Indicateurs de la Veille</div>', unsafe_allow_html=True)

    top_c1, top_c2, top_c3 = st.columns(3)

    # COLONNE 1 : Colis Expédiés + Reste à Fabriquer
    with top_c1:
        col_colis_exp = 'COLIS préparés (Shipment)' if 'COLIS préparés (Shipment)' in df.columns else df.columns[11]
        val_colis = pd.to_numeric(row_veille.get(col_colis_exp, 0), errors='coerce')
        if pd.isna(val_colis): val_colis = 0
        max_colis = pd.to_numeric(df[col_colis_exp], errors='coerce').max()
        if pd.isna(max_colis) or max_colis == 0: max_colis = 1646
        
        is_record_colis = (val_colis >= max_colis) and (val_colis > 0)

        bg_header = "#b8860b" if is_record_colis else "#1a4d2e"
        title_text = "🏆 RECORD COLIS EXPÉDIÉS" if is_record_colis else "📦 Colis Expédiés"
        
        with st.container(border=True):
            st.markdown(f"<div style='background-color: {bg_header}; color: white; padding: 8px; font-weight: bold; border-radius: 5px; text-align: center; margin-bottom: 5px;'>{title_text}</div>", unsafe_allow_html=True)
            st.markdown(f"<h1 style='color: {bg_header}; text-align: center; font-size: 2.0em; margin: 0;'>{val_colis:,.0f}</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: right; color: #666; margin: 0 0 2px 0; font-size: 0.8em;'>Record : {max_colis:,.0f}</p>", unsafe_allow_html=True)

            fig_record = go.Figure()
            fig_record.add_trace(go.Bar(
                y=['Colis'], x=[max_colis], orientation='h', marker_color='#d3d3d3', hoverinfo='skip'
            ))
            fig_record.add_trace(go.Bar(
                y=['Colis'], x=[val_colis], orientation='h', marker_color='#1a4d2e', hoverinfo='skip'
            ))
            fig_record.update_layout(
                barmode='overlay',
                xaxis=dict(range=[0, max(max_colis, val_colis) * 1.05], showgrid=False, visible=False),
                yaxis=dict(showgrid=False, visible=False),
                height=45,
                margin=dict(t=0, b=0, l=0, r=0),
                plot_bgcolor='white', paper_bgcolor='white', showlegend=False
            )
            st.plotly_chart(fig_record, use_container_width=True)

        col_n = 'Colis Expédiés physiquement' if 'Colis Expédiés physiquement' in df.columns else df.columns[13]
        col_p = 'RAF (Cdes)' if 'RAF (Cdes)' in df.columns else df.columns[14]

        val_fabrique = pd.to_numeric(row_veille.get(col_n, 0), errors='coerce')
        if pd.isna(val_fabrique): val_fabrique = 0
        val_raf = pd.to_numeric(row_veille.get(col_p, 0), errors='coerce')
        if pd.isna(val_raf): val_raf = 0

        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 8px; font-weight: bold; border-radius: 5px; margin-bottom: 5px;'>📦 Reste à Fabriquer (Commandes)</div>", unsafe_allow_html=True)
            
            fig_donut = go.Figure(data=[go.Pie(
                labels=['Fabriqué (Cde)', 'Restant à fabriquer / RAF (Cde)'],
                values=[val_fabrique, val_raf],
                hole=.6,
                marker_colors=['#1a4d2e', '#ff9999'],
                textinfo='label+value',
                hoverinfo='label+value'
            )])
            fig_donut.update_layout(
                height=165, margin=dict(t=0, b=0, l=0, r=0), showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_donut, use_container_width=True)

    # COLONNE 2 : Préparées à Temps
    col_taux_temps = 'KPI : % CDES préparées à temps' if 'KPI : % CDES préparées à temps' in df.columns else df.columns[15]
    val_taux_raw = pd.to_numeric(row_veille.get(col_taux_temps, 0), errors='coerce')
    if pd.isna(val_taux_raw): val_taux_raw = 0
    val_taux_pct = val_taux_raw * 100 if val_taux_raw <= 2.0 else val_taux_raw
    val_gauge_display = min(100.0, val_taux_pct)

    col_af_name = df.columns[31] if len(df.columns) > 31 else col_taux_temps
    df['temp_day_of_week'] = df['Date_parsed'].dt.dayofweek
    df_working_30 = df[df['temp_day_of_week'] < 5].tail(30)
    
    s_af_days = pd.to_numeric(df_working_30[col_af_name], errors='coerce')
    s_af_days_pct = s_af_days.apply(lambda x: x * 100 if x <= 2.0 else x)
    mean_af_days = s_af_days_pct[s_af_days_pct > 0].mean()
    if pd.isna(mean_af_days): mean_af_days = val_taux_pct

    with top_c2:
        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>⏱️ Préparées à Temps</div>", unsafe_allow_html=True)
            
            oc1, oc2 = st.columns(2)
            with oc1:
                st.number_input("Obj. Lundi (%)", step=1.0, key='obj_temps_lundi', on_change=update_config)
            with oc2:
                st.number_input("Obj. Autre (%)", step=1.0, key='obj_temps_autre', on_change=update_config)

            is_temps_ok = val_taux_pct >= obj_temps_actif
            gauge_bar_color = "#2e7d32" if is_temps_ok else "#8b0000"

            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = val_gauge_display,
                number = {'suffix': "%", 'valueformat': ".1f" if val_taux_pct > 100 else ".0f", 'font': {'color': gauge_bar_color, 'size': 24}},
                title = {'text': f"<span style='font-size:11px; color:gray;'>Réel : {val_taux_pct:.1f}% | Moy. Jours : {mean_af_days:.1f}%</span>"},
                gauge = {
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "gray"},
                    'bar': {'color': gauge_bar_color},
                    'bgcolor': "white",
                    'steps': [
                        {'range': [0, obj_temps_actif], 'color': '#ffebee'},
                        {'range': [obj_temps_actif, 100], 'color': '#e8f5e9'}
                    ],
                    'threshold': {
                        'line': {'color': "#8b008b", 'width': 4},
                        'thickness': 0.8,
                        'value': obj_temps_actif
                    }
                }
            ))
            fig_gauge.update_layout(height=145, margin=dict(t=5, b=0, l=10, r=10))
            st.plotly_chart(fig_gauge, use_container_width=True)

            target_j_labels = ['J-3', 'J-2', 'J-1', 'J+0', 'J+1']
            found_cols = []
            for tj in target_j_labels:
                match = [c for c in df.columns if tj.lower() in str(c).lower().replace(' ', '')]
                if match:
                    found_cols.append(match[0])
                else:
                    found_cols.append(None)

            if all(c is None for c in found_cols) and len(df.columns) > 24:
                found_cols = [df.columns[20], df.columns[21], df.columns[22], df.columns[23], df.columns[24]]

            j_vals = []
            for col in found_cols:
                if col is not None and col in row_veille:
                    raw_v = pd.to_numeric(row_veille[col], errors='coerce')
                    if pd.isna(raw_v): raw_v = 0.0
                    pct_val = raw_v * 100 if raw_v <= 2.0 else raw_v
                    j_vals.append(pct_val)
                else:
                    j_vals.append(0.0)

            # Identification exacte des colonnes CSV
            col_tot_cdes = df.columns[11] if len(df.columns) > 11 else None     # Colonne L (Total CDES du jour)
            col_fab_precedant = df.columns[29] if len(df.columns) > 29 else None # Colonne AD (Fabriqué veille)
            
            # Colonnes # CDES préparées de J-3 à J+0 (Index 26 à 29)
            col_cdes_prep = [df.columns[26], df.columns[27], df.columns[28], df.columns[29]] if len(df.columns) > 29 else [None]*4

            # --- CORRECTION EXACTE DU CALCUL ---
            def calc_reste_exact(offset, prep_col_idx):
                target_row_idx = idx_selected + offset
                if target_row_idx < 0 or target_row_idx >= len(df):
                    return 0
                r_target = df.iloc[target_row_idx]
                
                # 1. Total commandes du jour J-N
                tot_c = pd.to_numeric(r_target.get(col_tot_cdes, 0), errors='coerce')
                if pd.isna(tot_c): tot_c = 0
                
                # 2. Déjà fabriqué avant ce jour (ligne encore avant)
                prev_row_idx = target_row_idx - 1
                fab_prev_val = 0
                if prev_row_idx >= 0 and col_fab_precedant in df.columns:
                    fab_prev_val = pd.to_numeric(df.iloc[prev_row_idx].get(col_fab_precedant, 0), errors='coerce')
                    if pd.isna(fab_prev_val): fab_prev_val = 0

                # 3. Préparé le jour J (dans la ligne sélectionnée actuelle)
                prep_c = pd.to_numeric(row_veille.get(col_cdes_prep[prep_col_idx], 0), errors='coerce')
                if pd.isna(prep_c): prep_c = 0

                res = tot_c - fab_prev_val - prep_c
                return int(max(0, res))

            reste_j3 = calc_reste_exact(-3, 0)
            reste_j2 = calc_reste_exact(-2, 1)
            reste_j1 = calc_reste_exact(-1, 2)
            reste_j0 = calc_reste_exact(0, 3)
            reste_j_plus1 = 0

            reste_vals = [reste_j3, reste_j2, reste_j1, reste_j0, reste_j_plus1]

            # --- CRÉATION DE L'HISTOGRAMME AVEC TEXTE BICOLORE ---
            annotations = []
            for i, (label, v) in enumerate(zip(target_j_labels, j_vals)):
                txt_pct = f"<b>{v:.0f}%</b>"
                if v >= 20:
                    annotations.append(dict(
                        x=label, y=v / 2, text=txt_pct,
                        showarrow=False, font=dict(color="white", size=15, family="Arial Black"),
                        xanchor="center", yanchor="middle"
                    ))
                else:
                    annotations.append(dict(
                        x=label, y=v + 8, text=txt_pct,
                        showarrow=False, font=dict(color="#1a4d2e", size=15, family="Arial Black"),
                        xanchor="center", yanchor="bottom"
                    ))

            fig_j = go.Figure()
            fig_j.add_trace(go.Bar(
                x=target_j_labels, y=[100]*5, marker_color='#e0e0e0', hoverinfo='skip', showlegend=False
            ))
            fig_j.add_trace(go.Bar(
                x=target_j_labels, y=j_vals, marker_color='#1a4d2e', showlegend=False, hoverinfo='skip'
            ))
            fig_j.update_layout(
                barmode='overlay', height=105, margin=dict(t=15, b=5, l=5, r=5),
                annotations=annotations,
                xaxis=dict(showgrid=False, tickfont=dict(size=12, family='Arial Black')),
                yaxis=dict(range=[0, 110], showgrid=False, visible=False),
                plot_bgcolor='white', paper_bgcolor='white'
            )
            st.plotly_chart(fig_j, use_container_width=True)

            # --- AFFICHAGE SOUS LES ÉTIQUETTES J-3 à J+1 ---
            c_j3, c_j2, c_j1, c_j0, c_j1p = st.columns(5)
            cols_list = [c_j3, c_j2, c_j1, c_j0, c_j1p]
            for col_widget, r_val in zip(cols_list, reste_vals):
                with col_widget:
                    if r_val > 0:
                        st.markdown(f"<div style='text-align: center; color: #8b0000; font-weight: bold; font-size: 0.9em; margin-top: -10px;'>{r_val}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='text-align: center; height: 20px;'></div>", unsafe_allow_html=True)

    # COLONNE 3 : Délais d'Expédition
    col_delai = [c for c in df.columns if 'Délai moyen d\'expé' in str(c) or 'Délai moyen d’expédition' in str(c)]
    raw_delai = row_veille.get(col_delai[0] if col_delai else '', 0)
    val_delai_num = pd.to_numeric(raw_delai, errors='coerce')
    if pd.isna(val_delai_num): val_delai_num = 0.0

    min_af_val = None
    if col_af_name is not None and col_af_name in df.columns:
        s_af = pd.to_numeric(df[col_af_name], errors='coerce')
        if not s_af.dropna().empty:
            min_af_val = s_af[s_af > 0].min()

    if min_af_val is None and col_delai:
        s_delai_all = pd.to_numeric(df[col_delai[0]], errors='coerce')
        min_af_val = s_delai_all[s_delai_all > 0].min()

    if pd.isna(min_af_val): 
        min_af_val = val_delai_num

    with top_c3:
        header_delai_title = "🏆 DÉLAI D'EXPÉDITION"
        header_delai_bg = "#1a4d2e"
        with st.container(border=True):
            st.markdown(f"<div style='background-color: {header_delai_bg}; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px; text-align: center;'>{header_delai_title}</div>", unsafe_allow_html=True)
            
            sub_c_inputs, sub_c_chart = st.columns([1.1, 1])

            with sub_c_inputs:
                st.number_input("Obj. Lundi (<)", step=0.05, key='obj_delai_lundi', on_change=update_config)
                st.number_input("Obj. Autre (<)", step=0.05, key='obj_delai_autre', on_change=update_config)

                is_delai_ok = val_delai_num <= obj_delai_actif
                status_delai_txt = "✅ OK" if is_delai_ok else "❌ Dépassé"
                st.markdown(f"**Délai Réel :**<br>{val_delai_num:.1f}j ({status_delai_txt})", unsafe_allow_html=True)
                st.markdown(f"**Record MIN :** {min_af_val:.1f}j", unsafe_allow_html=True)

            with sub_c_chart:
                bar_color = "#2e7d32" if is_delai_ok else "#8b0000"

                fig_bar_vert = go.Figure()
                fig_bar_vert.add_trace(go.Bar(
                    x=['Délai'], y=[2.0], marker_color='#d3d3d3', hoverinfo='skip'
                ))
                fig_bar_vert.add_trace(go.Bar(
                    x=['Délai'], y=[val_delai_num], marker_color=bar_color,
                    text=f"{val_delai_num:.1f}j", textposition='inside', insidetextanchor='middle',
                    textfont=dict(color='white', size=14, family='Arial Black')
                ))

                fig_bar_vert.add_shape(
                    type="line", x0=-0.5, x1=0.5, y0=obj_delai_actif, y1=obj_delai_actif,
                    line=dict(color="#8b008b", width=3, dash="solid")
                )

                fig_bar_vert.update_layout(
                    barmode='overlay',
                    yaxis=dict(range=[0, 2.0], showgrid=False, zeroline=False, tickvals=[0, 0.5, 1, 1.5, 2]),
                    xaxis=dict(showgrid=False, visible=False),
                    height=210,
                    margin=dict(t=5, b=5, l=10, r=5),
                    plot_bgcolor='white', paper_bgcolor='white', showlegend=False
                )
                st.plotly_chart(fig_bar_vert, use_container_width=True)

    # GRAPHIQUES MID
    mid_c1, mid_c2 = st.columns(2)

    col_prod_p2 = 'Productivité P2' if 'Productivité P2' in df.columns else [c for c in df.columns if 'Productivité P2' in str(c)][0]
    val_prod = pd.to_numeric(row_veille.get(col_prod_p2, 0), errors='coerce')
    if pd.isna(val_prod): val_prod = 0.0

    with mid_c1:
        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>📊 Productivité P2 - 15 Derniers Jours</div>", unsafe_allow_html=True)
            st.number_input("🎯 Objectif Productivité P2 (saisie manuelle)", step=0.5, key='obj_prod', on_change=update_config)
            obj_prod = st.session_state.obj_prod

            df_hist_p2 = df.tail(15).copy()
            if not df_hist_p2.empty:
                dates_p2 = df_hist_p2['Date_parsed'].dt.strftime('%d/%m').fillna(df_hist_p2['Date'].astype(str))
                vals_p2 = pd.to_numeric(df_hist_p2[col_prod_p2], errors='coerce').fillna(0)

                colors_p2 = []
                for idx, row in df_hist_p2.iterrows():
                    d_parsed = row['Date_parsed']
                    is_selected_day = (not pd.isna(d_parsed) and d_parsed.date() == selected_date) or (str(row['Date']) == str(row_veille.get('Date', '')))
                    v_val = pd.to_numeric(row.get(col_prod_p2, 0), errors='coerce')
                    if pd.isna(v_val): v_val = 0.0

                    if is_selected_day:
                        colors_p2.append('#2e7d32' if v_val >= obj_prod else '#8b0000')
                    else:
                        colors_p2.append('#1a4d2e')

                fig_p2 = go.Figure()
                fig_p2.add_trace(go.Bar(
                    x=dates_p2, y=vals_p2, text=vals_p2.round(1), textposition='outside', marker_color=colors_p2
                ))
                fig_p2.add_shape(
                    type="line", x0=-0.5, x1=len(dates_p2) - 0.5, y0=obj_prod, y1=obj_prod,
                    line=dict(color="#8b008b", width=2, dash="solid"), layer="below"
                )
                fig_p2.update_layout(
                    plot_bgcolor='white', paper_bgcolor='white', height=270,
                    margin=dict(t=20, b=20, l=20, r=20), showlegend=False
                )
                st.plotly_chart(fig_p2, use_container_width=True)

    with mid_c2:
        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>📈 Cadence Heure par Heure (vs Moyennes 30j & Jour)</div>", unsafe_allow_html=True)
            
            hour_cols = [c for c in df.columns if any(h in str(c) for h in ['07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00'])]
            if not hour_cols and len(df.columns) > 106:
                hour_cols = df.columns[97:107]

            if len(hour_cols) > 0:
                row_hours = row_veille[hour_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
                hours_labels = [f"{7 + i}h00" for i in range(len(hour_cols))]

                df['day_of_week'] = df['Date_parsed'].dt.dayofweek
                df_working = df[df['day_of_week'] < 5].tail(30)
                col_target = 'Colis/h préparés' if 'Colis/h préparés' in df.columns else df.columns[33]
                s_vals = pd.to_numeric(df_working[col_target], errors='coerce')
                mean_filtered_30 = s_vals[s_vals > 0].mean()
                if pd.isna(mean_filtered_30): mean_filtered_30 = 146.0

                mean_today = round(row_hours.mean())

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=hours_labels, y=[mean_filtered_30] * len(hours_labels), mode='lines',
                    name=f'Moyenne 30j ouvrés ({mean_filtered_30:.0f})',
                    line=dict(color='rgba(46, 125, 50, 0.4)', width=2, dash='dash')
                ))
                fig.add_trace(go.Scatter(
                    x=hours_labels, y=[mean_today] * len(hours_labels), mode='lines',
                    name=f'Moyenne du jour ({mean_today:.0f})',
                    line=dict(color='rgba(0, 0, 139, 0.4)', width=3, dash='solid')
                ))
                fig.add_annotation(
                    x=hours_labels[-1], y=mean_filtered_30, text=f"Moy. 30j: {mean_filtered_30:.0f}",
                    showarrow=False, xanchor="left", yanchor="bottom", yshift=5, xshift=5,
                    font=dict(color="rgba(46, 125, 50, 0.8)", size=11, family="Arial Black")
                )
                fig.add_annotation(
                    x=hours_labels[-1], y=mean_today, text=f"Moy. Jour: {mean_today:.0f}",
                    showarrow=False, xanchor="left", yanchor="bottom", yshift=22, xshift=5,
                    font=dict(color="rgba(0, 0, 139, 0.8)", size=11, family="Arial Black")
                )

                max_historical_hour = df[hour_cols].apply(pd.to_numeric, errors='coerce').max().max()
                if pd.isna(max_historical_hour): max_historical_hour = row_hours.max()

                bar_colors = ['#ffd700' if val >= max_historical_hour and val > 0 else '#1a4d2e' for val in row_hours.values]

                fig.add_trace(go.Bar(
                    x=hours_labels, y=row_hours.values, name=str(selected_date),
                    text=row_hours.values, textposition='outside', marker_color=bar_colors
                ))
                
                fig.update_layout(
                    plot_bgcolor='white', paper_bgcolor='white', height=330,
                    margin=dict(t=25, b=20, l=20, r=70), showlegend=True,
                    xaxis=dict(type='category'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)  # Fin du fond de section Veille


    # ==========================================
    # BLOC 2 : PILOTAGE DU JOUR & ALIGNEMENT
    # ==========================================
    st.markdown('<div class="bg-section-jour">', unsafe_allow_html=True)
    st.markdown('<div class="title-highlight-jour">🐱 Pilotage du Jour & Alignement</div>', unsafe_allow_html=True)

    bot_c1, bot_c2 = st.columns(2)

    with bot_c1:
        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>🎯 Objectif Colis du Jour</div>", unsafe_allow_html=True)
            st.text_input("Saisir l'objectif de colis du jour", key='obj_colis_val', label_visibility="collapsed", on_change=update_config)

        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>🔥 Défi Collectif & Focus du Jour</div>", unsafe_allow_html=True)
            st.text_area("Saisir le défi collectif", key='defi_val', label_visibility="collapsed", on_change=update_config)

    with bot_c2:
        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>✨ Point Positif & Amélioration de la Veille</div>", unsafe_allow_html=True)
            st.text_area("À maintenir ou corriger", key='amelioration_val', label_visibility="collapsed", on_change=update_config)

        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>🛡️ Encart Qualité & Incidents</div>", unsafe_allow_html=True)
            st.text_area("Notes qualité", key='qualite_val', label_visibility="collapsed", on_change=update_config)

    st.markdown('</div>', unsafe_allow_html=True)  # Fin du fond de section Jour

else:
    st.info("👈 Veuillez importer votre fichier CSV quotidien via le menu de gauche.")
