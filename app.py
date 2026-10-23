import streamlit as st
import duckdb
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Dashboard Production & Logistique", layout="wide")

st.title("📦 Tableau de Bord Production & Logistique")

# --- 1. IMPORTATION DES FICHIERS CSV ---
uploaded_file = st.sidebar.file_uploader("Importer le CSV Shipment (Shippingbo)", type=["csv"])

if uploaded_file is not None:
    # Charger le CSV dans une table SQL temporaire en mémoire avec DuckDB
    # DuckDB détecte automatiquement les types de colonnes et les dates
    con = duckdb.connect(database=':memory:')
    con.execute("CREATE TABLE shipments AS SELECT * FROM read_csv_auto(?)", [uploaded_file.name])

    st.success("Fichier chargé et indexé en SQL avec succès !")

    # --- 2. EXEMPLE DE REQUÊTE SQL : CADENCE DE PRÉPARATION PAR HEURE ---
    st.subheader("📊 Préparation par Heure (Requête SQL)")

    # Tu peux écrire n'importe quelle requête SQL ANSI standard ici
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

    # Affichage du tableau SQL et du graphique
    col1, col2 = st.columns([1, 2])
    with col1:
        st.write("Résultat de la requête SQL :")
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

    # --- 3. CHRONOGRAMME DE PRODUCTION (TEMPS DE MARCHE VS ARRÊTS) ---
    st.subheader("⏱️ Chronogramme de Production (Analyse d'Inactivité)")

    seuil_arret_minutes = st.slider("Seuil de détection d'arrêt (minutes sans colis)", 1, 15, 3)

    # Requête SQL pour calculer l'écart de temps entre 2 colis consécutifs
    query_chronogramme = f"""
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
                WHEN duree_minutes >= {seuil_arret_minutes} THEN 'Arrêt / Pause' 
                ELSE 'En Production' 
            END AS statut
        FROM gaps
        ORDER BY debut
    """

    df_chrono = con.execute(query_chronogramme).df()

    # Visualisation du Chronogramme avec Plotly Gantt / Timeline
    color_map = {'En Production': '#2ca02c', 'Arrêt / Pause': '#d62728'}
    
    fig_timeline = px.timeline(
        df_chrono, 
        x_start="debut", 
        x_end="fin", 
        y=[0]*len(df_chrono), 
        color="statut",
        color_discrete_map=color_map,
        title=f"Chronogramme d'activité (Arrêt défini si pas de colis pendant > {seuil_arret_minutes} min)"
    )
    
    # Épurer l'axe Y pour ressembler à la bannière de la photo
    fig_timeline.update_yaxes(visible=False)
    fig_timeline.update_layout(height=180, showlegend=True)
    st.plotly_chart(fig_timeline, use_container_width=True)

else:
    st.info("Veuillez importer votre fichier CSV de Shippingbo dans le panneau de gauche pour démarrer.")
