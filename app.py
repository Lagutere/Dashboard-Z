import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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

    h2, h3 { color: #1a4d2e !important; font-family: 'Helvetica Neue', sans-serif; }
    .stButton>button { background-color: #1a4d2e; color: white; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# Titre dans un bandeau de couleur
st.markdown('<div class="main-title-banner">🐾 Dashboard Logistique & Préparation - Ziggy</div>', unsafe_allow_html=True)

# --- 1. IMPORTATION DU CSV ---
st.sidebar.header("📁 Données WMS / CSV")
uploaded_file = st.sidebar.file_uploader("Importer le CSV quotidien", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-16', sep=None, engine='python')
    except:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding='utf-8', sep=None, engine='python')
    
    df.columns = df.columns.str.strip()

    # --- 2. SÉLECTION DES DATES ---
    df['Date_parsed'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
    valid_dates = df['Date_parsed'].dropna().dt.date.unique()
    
    if len(valid_dates) > 0:
        default_date = valid_dates[-1]
    else:
        default_date = pd.Timestamp.today().date()

    selected_date = st.sidebar.date_input("📅 Sélectionner la date du point", value=default_date)

    df_selected = df[df['Date_parsed'].dt.date == selected_date]
    
    if df_selected.empty:
        row_veille = df.iloc[-1]
    else:
        row_veille = df_selected.iloc[0]

    # --- 3. MISE EN PAGE PRINCIPALE : 2 COLONNES ---
    col_left, col_right = st.columns([1.3, 1])

    # ==========================================
    # COLONNE GAUCHE : BILAN DE LA VEILLE & SUIVI
    # ==========================================
    with col_left:
        st.subheader("📊 Bilan & Indicateurs de la Veille")

        col_colis_exp = 'COLIS préparés (Shipment)' if 'COLIS préparés (Shipment)' in df.columns else df.columns[11]
        val_colis = pd.to_numeric(row_veille.get(col_colis_exp, 0), errors='coerce')
        if pd.isna(val_colis): val_colis = 0
        
        max_colis = pd.to_numeric(df[col_colis_exp], errors='coerce').max()
        is_record_colis = (val_colis >= max_colis) and (val_colis > 0)

        # % Commandes préparées à temps
        col_taux_temps = 'KPI : % CDES préparées à temps' if 'KPI : % CDES préparées à temps' in df.columns else df.columns[15]
        val_taux_raw = pd.to_numeric(row_veille.get(col_taux_temps, 0), errors='coerce')
        val_taux_pct = val_taux_raw * 100 if val_taux_raw <= 1 else val_taux_raw

        c1, c2 = st.columns(2)
        
        # Encart Colis
        with c1:
            bg_header = "#b8860b" if is_record_colis else "#1a4d2e"
            title_text = "🏆 RECORD COLIS EXPÉDIÉS" if is_record_colis else "📦 Colis Expédiés"
            with st.container(border=True):
                st.markdown(f"<div style='background-color: {bg_header}; color: white; padding: 10px; font-weight: bold; border-radius: 5px; text-align: center; margin-bottom: 10px;'>{title_text}</div>", unsafe_allow_html=True)
                st.markdown(f"<h1 style='color: {bg_header}; text-align: center; font-size: 2.2em; margin: 0;'>{val_colis:,.0f}</h1>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center; color: #666; margin: 5px 0 0 0;'>Max historique : {max_colis:,.0f}</p>", unsafe_allow_html=True)

        # Encart Taux de service (Jauge demi-cercle)
        with c2:
            with st.container(border=True):
                st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; text-align: center; margin-bottom: 5px;'>⏱️ Préparées à Temps</div>", unsafe_allow_html=True)
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = val_taux_pct,
                    number = {'suffix': "%", 'font': {'color': '#1a4d2e', 'size': 22}},
                    gauge = {
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "gray"},
                        'bar': {'color': "#1a4d2e"},
                        'bgcolor': "white",
                        'steps': [
                            {'range': [0, 80], 'color': '#ffebee'},
                            {'range': [80, 100], 'color': '#e8f5e9'}
                        ],
                    }
                ))
                fig_gauge.update_layout(height=135, margin=dict(t=5, b=5, l=10, r=10))
                st.plotly_chart(fig_gauge, use_container_width=True)

        # Encart Productivité P2
        col_prod_p2 = 'Productivité P2' if 'Productivité P2' in df.columns else [c for c in df.columns if 'Productivité P2' in str(c)][0]
        val_prod = pd.to_numeric(row_veille.get(col_prod_p2, 0), errors='coerce')
        if pd.isna(val_prod): val_prod = 0.0

        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>⚡ Productivité P2 & Objectif</div>", unsafe_allow_html=True)
            obj_prod = st.number_input("🎯 Objectif Productivité P2 (saisie manuelle)", value=15.0, step=0.5)
            is_prod_ok = val_prod >= obj_prod
            prod_color = "#2e7d32" if is_prod_ok else "#c62828"
            prod_bg = "#e8f5e9" if is_prod_ok else "#ffebee"
            status_text = "✅ OK" if is_prod_ok else "❌ À améliorer"

            st.markdown(f"""
                <div style="background-color: {prod_bg}; border: 2px solid {prod_color}; border-radius: 8px; padding: 10px; text-align: center; margin-top: 10px;">
                    <span style="font-size: 1.05em; font-weight: bold; color: {prod_color};">
                        Productivité Réelle : {val_prod} (Objectif : {obj_prod}) -> {status_text}
                    </span>
                </div>
            """, unsafe_allow_html=True)

        # Encart Délais & RAF
        col_delai = [c for c in df.columns if 'Délai moyen d\'expé' in str(c) or 'Délai moyen d’expédition' in str(c)]
        col_raf = 'RAF (Cdes)' if 'RAF (Cdes)' in df.columns else df.columns[14]
        
        raw_delai = row_veille.get(col_delai[0] if col_delai else '', 0)
        val_delai_num = pd.to_numeric(raw_delai, errors='coerce')
        val_delai_str = f"{val_delai_num:.1f}" if not pd.isna(val_delai_num) else str(raw_delai)
        
        val_raf_raw = pd.to_numeric(row_veille.get(col_raf, 0), errors='coerce')
        val_raf_str = f"{val_raf_raw:,.0f}".replace(",", " ") if not pd.isna(val_raf_raw) else "0"

        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>🚚 Délais & Reste à Faire (RAF)</div>", unsafe_allow_html=True)
            d1, d2 = st.columns(2)
            with d1:
                st.metric("⏱️ Délai Moyen Expédition", val_delai_str)
            with d2:
                st.metric("📦 Reste à faire (RAF)", val_raf_str)

        # --- GRAPHIQUE HEURE PAR HEURE ---
        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>📈 Cadence Heure par Heure</div>", unsafe_allow_html=True)
            
            hour_cols = [c for c in df.columns if any(h in str(c) for h in ['05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00'])]
            if not hour_cols and len(df.columns) > 106:
                hour_cols = df.columns[95:107]

            if len(hour_cols) > 0:
                row_hours = row_veille[hour_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
                df_chart = pd.DataFrame({
                    'Heure': [str(h).split()[0] for h in hour_cols],
                    'Colis': row_hours.values
                })
                max_val_hour = df_chart['Colis'].max()

                fig = px.bar(df_chart, x='Heure', y='Colis', text='Colis')
                colors = ['#ffd700' if val == max_val_hour and val > 0 else '#1a4d2e' for val in df_chart['Colis']]
                fig.update_traces(marker_color=colors, textposition='outside')
                fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=270, margin=dict(t=20, b=20, l=20, r=20))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Colonnes horaires non détectées.")

    # ==========================================
    # COLONNE DROITE : PILOTAGE DU JOUR & DÉFIS
    # ==========================================
    with col_right:
        st.subheader("🎯 Pilotage du Jour & Alignement")

        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>🎯 Objectif Colis du Jour</div>", unsafe_allow_html=True)
            obj_colis_jour = st.text_input("Saisir l'objectif de colis du jour", value="1500")

        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>🔥 Défi Collectif & Focus du Jour</div>", unsafe_allow_html=True)
            defi_texte = st.text_area("Saisir le défi collectif", value="Zéro erreur de picking sur les références sensibles + Fluidité sur l'emballage.")

        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>✨ Point Positif & Amélioration de la Veille</div>", unsafe_allow_html=True)
            amelioration_texte = st.text_area("À maintenir ou corriger", value="Positif : Bonne cadence globale entre 8h et 11h. Amélioration : Réduire le temps de pause.")

        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>🛡️ Encart Qualité & Incidents</div>", unsafe_allow_html=True)
            qualite_texte = st.text_area("Notes qualité", value="RAS ce matin. Vigilance sur les sacs percés
