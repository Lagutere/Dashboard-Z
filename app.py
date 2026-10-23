import streamlit as st
import duckdb
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Dashboard Production & Logistique", layout="wide")

st.title("📦 Tableau de Bord Production & Logistique (Multi-Tables)")

# --- 1. IMPORTATION DES FICHIERS CSV MULTIPLES ---
st.sidebar.header("📁 Import des fichiers Shippingbo")
uploaded_shipments = st.sidebar.file_uploader("1. Importer le CSV shipment", type=["csv"])
uploaded_orders = st.sidebar.file_uploader("2. Importer le CSV order", type=["csv"])
uploaded_returns = st.sidebar.file_uploader("3. Importer le CSV returnorder", type=["csv"])

# Connexion DuckDB en mémoire
con = duckdb.connect(database=':memory:')

data_loaded = False

if uploaded_shipments is not None:
    # Charger le CSV shipment proprement via pandas vers DuckDB
    df_shipments = pd.read_csv(uploaded_shipments)
    con.register('shipments', df_shipments)
    data_loaded = True

if uploaded_orders is not None:
    df_orders = pd.read_csv(uploaded_orders)
    con.register('orders', df_orders)

if uploaded_returns is not None:
    df_returns = pd.read_csv(uploaded_returns)
    con.register('returnorders', df_returns)

if data_loaded:
    st.success("Données chargées avec succès dans la base de données SQL !")

    # --- 2. EXEMPLE DE REQUÊTE SQL : CADENCE DE PRÉPARATION ---
    st.subheader("📊 Préparation par Heure (Basé sur shipments)")

    query_cadence = """
        SELECT 
            EXTRACT(HOUR FROM CAST(sentAt AS TIMESTAMP)) AS Heure,
            COUNT(orderId) AS Total_Colis,
            COUNT(DISTINCT preparator) AS Nb_Preparateurs
        FROM shipments
        WHERE sentAt IS NOT NULL
        GROUP BY Heure
        ORDER BY Heure
    """
    
    df_cadence = con.execute(query_cadence).df()

    col1, col2 = st.columns([1, 2])
    with col1:
        st.write("Résultat SQL :")
        st.dataframe(df_cadence, use_container_width=True)
    
    with col2:
        fig_bar = px.bar(
            df_cadence, 
            x="Heure", 
            y="Total_Colis", 
            title="Nombre de colis préparés par heure",
            text_auto=True,
            color_discrete_sequence=['#2b5c8f']
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # --- 3. CHRONOGRAMME DE PRODUCTION ---
    st.subheader("⏱️ Chronogramme de Production (Arrêts vs Mouvements)")
    
    seuil_arret = st.slider("Seuil de détection d'arrêt (minutes sans colis)", 1, 15, 3)

    query_chrono = f"""
        WITH ordered_events AS (
            SELECT 
                CAST(sentAt AS TIMESTAMP) AS ts,
                LAG(CAST(sentAt AS TIMESTAMP)) OVER (ORDER BY CAST(sentAt AS TIMESTAMP)) AS prev_ts
            FROM shipments
            WHERE sentAt IS NOT NULL
        ),
        gaps AS (
            SELECT 
                prev_ts AS debut,
                ts AS fin,
                DATE_DIFF('minute', prev_ts, ts) AS duree_minutes
            FROM ordered_events
            WHERE prev_ts IS NOT NULL
        )
        SELECT 
            debut, 
            fin, 
            duree_minutes,
            CASE 
                WHEN duree_minutes >= {seuil_arret} THEN 'Arrêt / Pause' 
                ELSE 'En Production' 
            END AS statut
        FROM gaps
        ORDER BY debut
    """

    df_chrono = con.execute(query_chrono).df()

    if not df_chrono.empty:
        color_map = {'En Production': '#2ca02c', 'Arrêt / Pause': '#d62728'}
        fig_timeline = px.timeline(
            df_chrono, 
            x_start="debut", 
            x_end="fin", 
            y=[0]*len(df_chrono), 
            color="statut",
            color_discrete_map=color_map,
            title=f"Chronogramme d'activité (Seuil : {seuil_arret} min)"
        )
        fig_timeline.update_yaxes(visible=False)
        fig_timeline.update_layout(height=180, showlegend=True)
        st.plotly_chart(fig_timeline, use_container_width=True)
    else:
        st.warning("Pas assez de données pour afficher le chronogramme.")

else:
    st.info("👈 Veuillez importer au moins le fichier CSV `shipment` dans le panneau de gauche pour commencer.")
