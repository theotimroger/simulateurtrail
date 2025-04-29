import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from utils import (
    process_gpx,
    trouver_vitesse_plate,
    compute_cumulative_time,
    format_time,
    compute_paces,
    calculate_deniv,
    trouver_vitesse_plate_strava,
    compute_cumulative_time_strava,
    compute_paces_strava,
    vitesse_to_allure,
    adjusted_speed_minetti,
    adjusted_speed_strava
)

st.title("Analyse de trace GPX - Allure ajustée à la pente")
st.info(
    """
    🏔️ **Bienvenue sur le simulateur d'allure ajustée à la pente !**

    Cette application vous permet d'analyser une trace GPX en tenant compte de votre **temps total espéré**,
 

    ➡️ L'algorithme calcule alors :
    - votre **allure constante équivalente sur du plat**,
    - votre **profil d'allure ajustée** tout au long du parcours,
    - et vos **temps de passage estimés** à chaque point.

    2 Modèles sont proposés ici: celui de Minetti et celui de Strava (détails en bas de page).

    **Chargez simplement votre fichier GPX et entrez votre objectif de temps.**
    """
)

uploaded_file = st.file_uploader("Chargez votre fichier GPX", type=["gpx"])

if uploaded_file is not None:
## -- AFFICHAGE DES INFOS RELATIVE AU PARCOURS --
    gpx_content = uploaded_file.read().decode("utf-8")

    # Lecture brute : distances et altitudes
    distances, elevations, distances_pace = process_gpx(gpx_content)
    d_plus, d_moins = calculate_deniv(elevations)

    st.markdown("""
    <div style='background-color: rgba(255,0,0,0.25); padding: 0px; border-radius: 10px; margin-bottom: 0px;'>
        <div style='text-align: center; margin-bottom: 0px;'>
            <h4 style='margin: 0 0 0 0; color: rgba(255,0,0,1);'>Résumé de la trace</h4>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("<h4 style='text-align: center; color: black;'>Distance</h4>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: center; font-size: 16px; color: black; margin-bottom: 10;'>{distances[-1]:.1f} km</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<h4 style='text-align: center; color: black;'>D+</h4>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: center; font-size: 16px; color: black; margin-bottom: 10;'>{d_plus} m</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<h4 style='text-align: center; color: black;'>D-</h4>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: center; font-size: 16px; color: black; margin-bottom: 10;'>{d_moins} m</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)  # fermeture du cadre

    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.markdown(
            """
            <div style="display: flex; align-items: center; justify-content: flex-end; height: 40px;">
                <p style="font-weight: bold; margin: 0;">Temps espéré (hh:mm:ss)</p>
            </div>
            """, 
            unsafe_allow_html=True
        )

    with col_b:
        temps_espere = st.text_input("", value="06:15:30", label_visibility="collapsed")

## -- CALCUL DE L'ALLURE AU COURS DU TEMPS
if uploaded_file is not None and temps_espere:


    # Conversion temps espéré en secondes
    try:
        h, m, s = map(int, temps_espere.split(":"))
        temps_espere_sec = h * 3600 + m * 60 + s
    except ValueError:
        st.error("Format invalide. Utilisez hh:mm:ss")
        st.stop()

    # Trouver la vitesse sur plat correcte
    flat_speed = trouver_vitesse_plate(distances, elevations, temps_espere_sec)
    flat_speed_strava = trouver_vitesse_plate_strava(distances, elevations, temps_espere_sec)


    # Calcul de l'allure correspondante

    allure_plat_str = vitesse_to_allure(flat_speed)

    allure_plat_str_strava = vitesse_to_allure(flat_speed_strava)

    st.markdown("""
    <div style='background-color: rgba(0,255,0,0.25); padding: 0px; border-radius: 10px; margin-bottom: 0px;'>
        <div style='text-align: center; margin-bottom: 0px;'>
            <h4 style='margin: 0 0 0 0; color: rgba(0,255,0,1);'>Allure ajustée à la pente</h4>
        </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<h5 style='text-align: center; color: black;'>Modèle Minetti</h5>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: center; font-size: 16px; color: black;'>{allure_plat_str} min/km</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<h5 style='text-align: center; color: black;'>Modèle Strava</h5>", unsafe_allow_html=True)
        st.markdown(f"<div style='text-align: center; font-size: 16px; color: black;'>{allure_plat_str_strava} min/km</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
        
    ## TABLEAU DES ALLURES EN FONCTION DES PENTES

    pentes = list(range(-30, 35, 1))  # de -30% à +35% tous les 5%

        # Construire les listes d'allures
    allures_minetti = []
    allures_strava = []

    for pente in pentes:
        v_minetti = adjusted_speed_minetti(flat_speed, pente)
        v_strava = adjusted_speed_strava(flat_speed, pente)
        allure_minetti = vitesse_to_allure(v_minetti)
        allure_strava = vitesse_to_allure(v_strava)
        allures_minetti.append(allure_minetti)
        allures_strava.append(allure_strava)

    def allure_to_seconds(allure_str):
        minutes, seconds = map(int, allure_str.split(":"))
        return minutes * 60 + seconds

    y_minetti = [allure_to_seconds(a) for a in allures_minetti]
    y_strava = [allure_to_seconds(a) for a in allures_strava]

    # Fonction pour reformatter en mm:ss
    def seconds_to_mmss(x):
        m = int(x // 60)
        s = int(x % 60)
        return f"{m}:{s:02d}"

    # 📈 Tracer avec Plotly
    fig = go.Figure()

    # Courbe Minetti
    fig.add_trace(go.Scatter(
        x=pentes,
        y=y_minetti,
        mode='lines',
        name='Minetti',
        customdata=list(zip(allures_minetti, allures_strava)),  # ⚡ ATTENTION on met les 2 allures ensemble !
        hovertemplate=(
            "Pente: %{x}%<br>" +
            "Allure Minetti: %{customdata[0]}<br>" +
            "Allure Strava: %{customdata[1]}<extra></extra>"
        ),
        line=dict(color='blue')
    ))

    # Courbe Strava
    fig.add_trace(go.Scatter(
        x=pentes,
        y=y_strava,
        mode='lines',
        name='Strava',
        customdata=list(zip(allures_minetti, allures_strava)),  # ⚡ ATTENTION on met les 2 allures ensemble !
        hovertemplate=(
            "Pente: %{x}%<br>" +
            "Allure Minetti: %{customdata[0]}<br>" +
            "Allure Strava: %{customdata[1]}<extra></extra>"
        ),
        line=dict(color='orange', dash='dash'),

    ))

    min_val = int(min(min(y_minetti), min(y_strava)) // 60) * 60
    max_val = int(max(max(y_minetti), max(y_strava)) // 60 + 2) * 60  # arrondi au dessus

    # Modifier l'axe y pour afficher mm:ss
    fig.update_layout(
        title="Allure ajustée en fonction de la pente",
        xaxis_title="Pente (%)",
        yaxis_title="Allure (min/km)",
        height=500,
        legend=dict(x=0.05, y=0.95),
        yaxis=dict(
            autorange='reversed',
            tickmode='array',
            tickvals=list(range(min_val, max_val + 1, 120)),  # ici pas 30 mais 120
            ticktext=[seconds_to_mmss(v) for v in range(min_val, max_val + 1, 120)]
        ),
        hovermode="x",  # <<< ici la ligne suit l'axe x
        hoverdistance=100,  # Distance pour activer l'hover même si pas exactement sur un point
        spikedistance=1000,  # Permet de déclencher le spike sur tout le graphe
        xaxis=dict(
            showspikes=True,       # Affiche la ligne verticale
            spikecolor="grey",     # Couleur de la ligne
            spikethickness=1,      # Épaisseur
            spikedash="dot",       # Style : pointillé, ou solid
            spikemode="across",    # La spike traverse tout verticalement
        )
    )

    # Streamlit affichage
    st.plotly_chart(fig, use_container_width=True)

    # Recalcul du temps cumulé avec la bonne vitesse
    cumulative_time = compute_cumulative_time(flat_speed, distances, elevations)
    cumulative_time_strava = compute_cumulative_time_strava(flat_speed_strava, distances, elevations)

    # Tracer les graphes
    fig = go.Figure()

    paces = compute_paces(distances, elevations, flat_speed)
    paces_strava = compute_paces_strava(distances, elevations, flat_speed_strava)

    # Profil Altitude
    fig.add_trace(go.Scatter(
        x=distances_pace,
        y=elevations[1:],  # pour correspondre aux distances_pace
        mode='lines',
        name='Altitude',
        hovertemplate=(
            'Distance: %{x:.2f} km<br>'
            'Altitude: %{y:.0f} m<br>'
            'Temps (Minetti): %{customdata[0]}<br>'
            'Temps (Strava): %{customdata[1]}'
        ),
        customdata=[[format_time(t), format_time(ts)] for t, ts in zip(cumulative_time, cumulative_time_strava)]
    ))

    # Configuration des axes
    fig.update_layout(
        title="Profil Altitude et Temps estimé",
        xaxis=dict(title='Distance (km)'),
        yaxis=dict(title='Altitude (m)', side='left'),
        legend=dict(x=0, y=1),
        height=300,
    )

    st.plotly_chart(fig, use_container_width=True)
    # Profil Allure

    fig2 = go.Figure()

    # 1. Courbe Minetti (bleu)
    fig2.add_trace(go.Scatter(
        x=distances_pace,
        y=paces,
        mode='lines',
        name='Allure Minetti',
        line=dict(color='blue'),
        hovertemplate='Distance: %{x:.2f} km<br>Allure Minetti: %{y:.1f} min/km'
    ))

    # 2. Courbe Strava (orange)
    fig2.add_trace(go.Scatter(
        x=distances_pace,
        y=paces_strava,
        mode='lines',
        name='Allure Strava',
        line=dict(color='orange', dash='dash'),  # tirets pour différencier
        hovertemplate='Distance: %{x:.2f} km<br>Allure Strava: %{y:.1f} min/km'
    ))

    # Configuration générale
    fig2.update_layout(
        title="Comparaison des Allures Ajustées",
        xaxis=dict(title='Distance (km)'),
        yaxis=dict(title='Allure (min/km)', overlaying='y', side='left', autorange='reversed'),
        legend=dict(x=0, y=1),
        height=400,
    )

    st.plotly_chart(fig2, use_container_width=True)

    # Temps de passage

with st.expander("Voir explication du calcul"):
    st.markdown(
        """
        ### Comment fonctionne ce simulateur ?

        L'algorithme repose sur **le modèle biomécanique de Minetti**<sup>1</sup>, qui estime le **coût énergétique** de la course à pied en fonction de la pente, et **le modèle fréquence cardiaque identique de Strava**<sup>2</sup>, qui estime l'allure ajustée en fonction de la fréquence cardiaque.
        

        ➡️ **Sur terrain plat**, le coût énergétique est minimal.\n
        ➡️ **En montée**, le coût énergétique augmente (on dépense plus pour s'élever), la fréquence cardiaque aussi.\n
        ➡️ **En descente**, le coût diminue... mais on ne peut pas courir infiniment vite sans limite physique.

        ### Calculs effectués :

        - L'algorithme cherche une **vitesse ajustée à la pente (VAP)**<sup>3</sup> qui vous permettrait d'atteindre ce temps,
          tout en tenant compte :
            - du profil de pente de votre trace GPX,
            - du temps total espéré

        - Pour chaque segment du parcours :
            - Le coût (énergétique ou en fréquence cardiaque) est calculé selon la pente locale,
            - La vitesse instantanée est adaptée en fonction de ce coût,
            - En descente, la vitesse est plafonnée à 1.3 x VAP pour le modèle de Minetti<sup>4</sup>.

        - Différence entre les 2 modèles :
            - Le modèle Minetti se base sur le coût énergétique et les tests ont été réalisés en laboratoire. Il est très généreux sur la vitesse en descente.
            - Le modèle de Strava se base sur sa base de données d'activités de traileurs du monde entier. L'estimation est donc issue d'activités en conditions "réelles". Ce modèle reflète sûrement mieux l'aspect technique des descentes.

        <hr>
        <p style="font-size: 0.8em;">
        <sup>1</sup> Minetti AE, Moia C, Roi GS, Susta D, Ferretti G. (2002), *Energy cost of walking and running at extreme uphill and downhill slopes*, Journal of Applied Physiology.<br>
        <sup>2</sup> <a href="https://medium.com/strava-engineering/an-improved-gap-model-8b07ae8886c3" target="_blank">Source Strava Engineering</a><br>
        <sup>3</sup> Pour les utilisateurs de Strava, cette allure est également disponible dans les rapports d'activité.<br>
        <sup>4</sup> Le modèle de Minetti est basé uniquement sur la dépense énergétique. Selon ce modèle, courir à un peu plus de 20 km/h sur une pente de -15% correspond à environ 11km/h sur du plat. Cette limitation n'a été validée par aucune expérience et peut être discutée. J'ai essayée ici de prendre en compte la technicité des chemins et les limites biomécaniques des traileurs.
        </p>
        <hr>
        """,
        unsafe_allow_html=True
    )

