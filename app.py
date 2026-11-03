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

# --- 1. INITIALISATION DE LA MÉMOIRE (SESSION STATE) ---
if 'obj_colis_val' not in st.session_state:
    st.session_state.obj_colis_val = "1500"
if 'defi_val' not in st.session_state:
    st.session_state.defi_val = "Zéro erreur de picking sur les références sensibles + Fluidité sur l'emballage."
if 'amelioration_val' not in st.session_state:
    st.session_state.amelioration_val = "Positif : Bonne cadence globale entre 8h et 11h. Amélioration : Réduire le temps de pause."
if 'qualite_val' not in st.session_state:
    st.session_state.qualite_val = "RAS ce matin. Vigilance sur les sacs percés."

# Objectifs de délai d'expédition persistants
if 'obj_delai_lundi' not in st.session_state:
    st.session_state.obj_delai_lundi = 1.35
if 'obj_delai_autre' not in st.session_state:
    st.session_state.obj_delai_autre = 0.80

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
        row_veille = df.iloc[-1]
    else:
        row_veille = df_selected.iloc[0]

    # Détermination du jour de la semaine (0 = Lundi, etc.)
    day_of_week = pd.to_datetime(selected_date).dayofweek
    is_lundi = (day_of_week == 0)
    obj_actif = st.session_state.obj_delai_lundi if is_lundi else st.session_state.obj_delai_autre

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

        # Encart Productivité P2 (Arrondi à 1 chiffre après la virgule)
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
                        Productivité Réelle : {val_prod:.1f} (Objectif : {obj_prod:.1f}) -> {status_text}
                    </span>
                </div>
            """, unsafe_allow_html=True)

        # Encart Délais d'expédition (Histogramme à plat)
        col_delai = [c for c in df.columns if 'Délai moyen d\'expé' in str(c) or 'Délai moyen d’expédition' in str(c)]
        raw_delai = row_veille.get(col_delai[0] if col_delai else '', 0)
        val_delai_num = pd.to_numeric(raw_delai, errors='coerce')
        if pd.isna(val_delai_num): val_delai_num = 0.0

        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>🚚 Délais d'Expédition</div>", unsafe_allow_html=True)
            
            col_o1, col_o2 = st.columns(2)
            with col_o1:
                st.session_state.obj_delai_lundi = st.number_input("🎯 Obj. Lundi (<)", value=st.session_state.obj_delai_lundi, step=0.05)
            with col_o2:
                st.session_state.obj_delai_autre = st.number_input("🎯 Obj. Autre jour (<)", value=st.session_state.obj_delai_autre, step=0.05)

            is_delai_ok = val_delai_num <= obj_actif
            bar_color = "#2e7d32" if is_delai_ok else "#8b0000"

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=[val_delai_num],
                y=['Délai Réel'],
                orientation='h',
                marker_color=bar_color,
                text=f"{val_delai_num:.1f} (Obj: < {obj_actif})",
                textposition='inside',
                insidetextanchor='middle',
                textfont=dict(color='white', size=14, family='Arial Black')
            ))
            fig_bar.update_layout(
                xaxis=dict(range=[0, max(2.0, val_delai_num * 1.2)], showgrid=False, zeroline=False),
                yaxis=dict(showgrid=False),
                height=80,
                margin=dict(t=5, b=5, l=5, r=5),
                plot_bgcolor='white',
                paper_bgcolor='white',
                showlegend=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)

            status_delai_txt = "✅ OK" if is_delai_ok else "❌ Dépassé"
            st.markdown(f"**Délai Réel :** {val_delai_num:.1f} ({status_delai_txt})")

        # --- ENCART RESTANT À FAIRE (DONUT CHART / CAMEMBERT CREUX : COL N vs COL P) ---
        col_n = 'Colis Expédiés physiquement' if 'Colis Expédiés physiquement' in df.columns else df.columns[13]
        col_p = 'RAF (Cdes)' if 'RAF (Cdes)' in df.columns else df.columns[14]

        val_fabrique = pd.to_numeric(row_veille.get(col_n, 0), errors='coerce')
        if pd.isna(val_fabrique): val_fabrique = 0
        
        val_raf = pd.to_numeric(row_veille.get(col_p, 0), errors='coerce')
        if pd.isna(val_raf): val_raf = 0

        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>📦 Reste à Fabriqué / Répartition (Fabriqué vs RAF)</div>", unsafe_allow_html=True)
            
            fig_donut = go.Figure(data=[go.Pie(
                labels=['Fabriqué (Col. N)', 'Restant à fabriquer / RAF (Col. P)'],
                values=[val_fabrique, val_raf],
                hole=.6,
                marker_colors=['#1a4d2e', '#e056fd'], # Vert foncé Ziggy et Rose peps
                textinfo='label+value',
                hoverinfo='label+value'
            )])
            fig_donut.update_layout(
                height=240,
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        # --- GRAPHIQUE HEURE PAR HEURE (MOYENNE 30J OUVRÉS HORS ZÉROS) ---
        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>📈 Cadence Heure par Heure (vs Moyenne 30j ouvrés hors zéros)</div>", unsafe_allow_html=True)
            
            hour_cols = [c for c in df.columns if any(h in str(c) for h in ['05:00', '06:00', '07:00', '08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00'])]
            if not hour_cols and len(df.columns) > 106:
                hour_cols = df.columns[95:107]

            if len(hour_cols) > 0:
                row_hours = row_veille[hour_cols].apply(pd.to_numeric, errors='coerce').fillna(0)
                hours_labels = [str(h).split()[0] for h in hour_cols]

                df['day_of_week'] = df['Date_parsed'].dt.dayofweek
                df_working = df[df['day_of_week'] < 5].tail(30)
                
                col_target = 'Colis/h préparés' if 'Colis/h préparés' in df.columns else df.columns[33]
                s_vals = pd.to_numeric(df_working[col_target], errors='coerce')
                mean_filtered_30 = s_vals[s_vals > 0].mean()
                if pd.isna(mean_filtered_30): mean_filtered_30 = 146.0

                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=hours_labels,
                    y=[mean_filtered_30] * len(hours_labels),
                    mode='lines',
                    name=f'Moyenne 30j ouvrés ({mean_filtered_30:.0f})',
                    line=dict(color='rgba(26, 77, 46, 0.6)', width=3, dash='dash')
                ))

                max_val_hour = row_hours.max()
                bar_colors = ['#ffd700' if val == max_val_hour and val > 0 else '#1a4d2e' for val in row_hours.values]

                fig.add_trace(go.Bar(
                    x=hours_labels,
                    y=row_hours.values,
                    name=str(selected_date),
                    text=row_hours.values,
                    textposition='outside',
                    marker_color=bar_colors
                ))

                fig.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    height=290,
                    margin=dict(t=20, b=20, l=20, r=20),
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Colonnes horaires non détectées.")

    # ==========================================
    # COLONNE DROITE : PILOTAGE DU JOUR & DÉFIS (PERSISTANCE)
    # ==========================================
    with col_right:
        st.subheader("🎯 Pilotage du Jour & Alignement")

        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>🎯 Objectif Colis du Jour</div>", unsafe_allow_html=True)
            st.session_state.obj_colis_val = st.text_input("Saisir l'objectif de colis du jour", value=st.session_state.obj_colis_val)

        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>🔥 Défi Collectif & Focus du Jour</div>", unsafe_allow_html=True)
            st.session_state.defi_val = st.text_area("Saisir le défi collectif", value=st.session_state.defi_val)

        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>✨ Point Positif & Amélioration de la Veille</div>", unsafe_allow_html=True)
            st.session_state.amelioration_val = st.text_area("À maintenir ou corriger", value=st.session_state.amelioration_val)

        with st.container(border=True):
            st.markdown("<div style='background-color: #1a4d2e; color: white; padding: 10px; font-weight: bold; border-radius: 5px; margin-bottom: 10px;'>🛡️ Encart Qualité & Incidents</div>", unsafe_allow_html=True)
            st.session_state.qualite_val = st.text_area("Notes qualité", value=st.session_state.qualite_val)

        st.success("💡 **Conseil Point d'Équipe :** Utilisez cet écran à 8h30 pour fixer les caps avec l'équipe !")

else:
    st.info("👈 Veuillez importer votre fichier CSV quotidien via le menu de gauche.")
