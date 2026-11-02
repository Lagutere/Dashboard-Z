import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION DE LA PAGE & DESIGN ZIGGY ---
st.set_page_config(page_title="Dashboard Logistique - Ziggy", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f7f9f6; }
    h1, h2, h3 { color: #1a4d2e !important; font-family: 'Helvetica Neue', sans-serif; }
    .metric-card {
        background-color: #ffffff;
        border: 2px solid #1a4d2e;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-card-record {
        background-color: #fffdf0;
        border: 2px solid #ffd700;
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 6px 12px rgba(255, 215, 0, 0.2);
        text-align: center;
    }
    .stButton>button { background-color: #1a4d2e; color: white; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("🐾 Dashboard Logistique & Préparation - Ziggy")

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

    # Filtrer les données pour la date sélectionnée
    df_selected = df[df['Date_parsed'].dt.date == selected_date]
    
    if df_selected.empty:
        st.warning(f"Aucune ligne exacte trouvée pour {selected_date}. Affichage de la dernière ligne disponible par défaut.")
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

        # Colis expédiés (Colonne M / index 11)
        col_colis_exp = 'COLIS préparés (Shipment)' if 'COLIS préparés (Shipment)' in df.columns else df.columns[11]
        val_colis = pd.to_numeric(row_veille.get(col_colis_exp, 0), errors='coerce')
        if pd.isna(val_colis): val_colis = 0
        
        max_colis = pd.to_numeric(df[col_colis_exp], errors='coerce').max()
        is_record_colis = (val_colis >= max_colis) and (val_colis > 0)

        # % Commandes préparées à temps (Colonne Q / index 15)
        col_taux_temps = 'KPI : % CDES préparées à temps' if 'KPI : % CDES préparées à temps' in df.columns else df.columns[15]
        val_taux_raw = pd.to_numeric(row_veille.get(col_taux_temps, 0), errors='coerce')
        val_taux_str = f"{val_taux_raw * 100:.1f}%" if val_taux_raw <= 1 else f"{val_taux_raw:.1f}%"

        # 4 ENCARTS DE LA VEILLE
        c1, c2 = st.columns(2)
        
        with c1:
            if is_record_colis:
                st.markdown(f"""
                    <div class="metric-card-record">
                        <h3>🏆 RECORD COLIS ! 🏆</h3>
                        <h1 style="color: #b8860b; font-size: 2.3em;">{val_colis:,.0f}</h1>
                        <p style="color: #b8860b; font-weight: bold;">Colis expédiés (Record battu)</p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div class="metric-card">
                        <h3 style="color: #1a4d2e;">Colis Expédiés</h3>
                        <h1 style="color: #1a4d2e; font-size: 2.3em;">{val_colis:,.0f}</h1>
                        <p style="color: #666;">Max historique : {max_colis:,.0f}</p>
                    </div>
                """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
                <div class="metric-card">
                    <h3 style="color: #1a4d2e;">Préparées à Temps</h3>
                    <h1 style="color: #2e7d32; font-size: 2.3em;">{val_taux_str}</h1>
                    <p style="color: #666;">Objectif qualité service</p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ENCART 2 : PRODUCTIVITÉ P2 & OBJECTIF
        st.markdown("### ⚡ Productivité P2 & Délais")
        
        col_prod_p2 = 'Productivité P2' if 'Productivité P2' in df.columns else [c for c in df.columns if 'Productivité P2' in str(c)][0]
        val_prod = pd.to_numeric(row_veille.get(col_prod_p2, 0), errors='coerce')
        if pd.isna(val_prod): val_prod = 0.0

        obj_prod = st.number_input("🎯 Objectif Productivité P2 (saisie manuelle)", value=15.0, step=0.5)
        
        is_prod_ok = val_prod >= obj_prod
        prod_color = "#2e7d32" if is_prod_ok else "#c62828"
        prod_bg = "#e8f5e9" if is_prod_ok else "#ffebee"
        status_text = "✅ OK" if is_prod_ok else "❌ À améliorer"

        st.markdown(f"""
            <div style="background-color: {prod_bg}; border: 2px solid {prod_color}; border-radius: 10px; padding: 12px; text-align: center;">
                <span style="font-size: 1.1em; font-weight: bold; color: {prod_color};">
                    Productivité Réelle P2 : {val_prod} (Objectif : {obj_prod}) -> {status_text}
                </span>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ENCART 3 : DÉLAI D'EXPÉDITION & RAF
        col_delai = [c for c in df.columns if 'Délai moyen d\'expé' in str(c) or 'Délai moyen d’expédition' in str(c)]
        col_raf = 'RAF (Cdes)' if 'RAF (Cdes)' in df.columns else df.columns[14]

        val_delai = row_veille.get(col_delai[0] if col_delai else '', "N/A")
        val_raf_num = row_veille.get(col_raf, 0)

        d1, d2 = st.columns(2)
        with d1:
            st.metric("⏱️ Délai Moyen Expédition", val_delai)
        with d2:
            st.metric("📦 Reste à faire / Retard (RAF)", val_raf_num)

        st.divider()

        # --- GRAPHIQUE HEURE PAR HEURE ---
        st.markdown("### 📈 Cadence Heure par Heure")
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

            fig = px.bar(
                df_chart, x='Heure', y='Colis', text='Colis',
                title=f"Nombre de colis par heure ({selected_date})"
            )
            colors = ['#ffd700' if val == max_val_hour and val > 0 else '#1a4d2e' for val in df_chart['Colis']]
            fig.update_traces(marker_color=colors, textposition='outside')
            fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Colonnes horaires non détectées.")

    # ==========================================
    # COLONNE DROITE : PILOTAGE DU JOUR & DÉFIS
    # ==========================================
    with col_right:
        st.subheader("🎯 Pilotage du Jour & Alignement")

        st.markdown("#### 🎯 Objectif Colis du Jour")
        obj_colis_jour = st.text_input("Saisir l'objectif de colis du jour", value="1500")

        st.markdown("#### 🔥 Défi Collectif & Focus du Jour")
        defi_texte = st.text_area("Saisir le défi collectif ou l'objectif qualitatif", value="Zéro erreur de picking sur les références sensibles + Fluidité sur l'emballage.")

        st.markdown("#### ✨ Point Positif / Amélioration de la Veille")
        amelioration_texte = st.text_area("À maintenir ou corriger aujourd'hui", value="Positif : Bonne cadence globale entre 8h et 11h. Amélioration : Réduire le temps de pause inter-sessions.")

        st.markdown("#### 🛡️ Encart Qualité & Incidents")
        qualite_texte = st.text_area("Notes qualité / Retours / Casse", value="RAS ce matin. Vigilance sur les sacs percés.")

        st.markdown("---")
        st.success("💡 **Conseil Point d'Équipe :** Utilisez cet écran à 8h30 pour fixer les caps de la journée !")

else:
    st.info("👈 Veuillez importer votre fichier CSV quotidien via le menu de gauche.")
