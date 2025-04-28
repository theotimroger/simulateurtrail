import streamlit as st
import plotly.graph_objects as go
from utils import (
    process_gpx,
    trouver_vitesse_plate,
    compute_cumulative_time,
    format_time,
    compute_paces,
    calculate_deniv
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

    **Chargez simplement votre fichier GPX, entrez votre objectif de temps et votre allure maximale.**
    """
)

uploaded_file = st.file_uploader("Chargez votre fichier GPX", type=["gpx"])

if uploaded_file is not None:
## -- AFFICHAGE DES INFOS RELATIVE AU PARCOURS --
    gpx_content = uploaded_file.read().decode("utf-8")

    # Lecture brute : distances et altitudes
    distances, elevations, distances_pace = process_gpx(gpx_content)
    d_plus, d_moins = calculate_deniv(elevations)
    st.info(f"Distance: {distances[-1]:.2f} km")
    st.info(f"D+: {d_plus[-1]} m  D-: {d_moins[-1]}")

temps_espere = st.text_input("Temps espéré (format hh:mm:ss)", value="06:15:30")

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
    flat_speed = trouver_vitesse_plate(distances_pace, elevations, temps_espere_sec)

    # Calcul de l'allure correspondante
    sec_per_km = 1000 / flat_speed
    minutes = int(sec_per_km // 60)
    seconds = int(sec_per_km % 60)
    allure_plat_str = f"{minutes:02d}:{seconds:02d}"

    st.info(f"Allure constant équivalente sur du plat: {allure_plat_str} min/km")
    

    # Recalcul complet avec la bonne vitesse
    cumulative_time = compute_cumulative_time(flat_speed, distances, elevations)

    # Tracer les graphes
    fig = go.Figure()

    paces = compute_paces(distances, elevations, flat_speed)
    # Profil Altitude
    fig.add_trace(go.Scatter(
        x=distances_pace,
        y=elevations[1:],  # pour correspondre aux distances_pace
        mode='lines',
        name='Altitude',
        hovertemplate=(
            'Distance: %{x:.2f} km<br>'
            'Altitude: %{y:.0f} m<br>'
            'Temps: %{customdata[0]}'
        ),
        customdata=[[format_time(t)] for t in cumulative_time]
    ))

    # Configuration des axes
    fig.update_layout(
        title="Profil Altitude et Allure Ajustée",
        xaxis=dict(title='Distance (km)'),
        yaxis=dict(title='Altitude (m)', side='left'),
        legend=dict(x=0, y=1),
        height=300,
    )

    st.plotly_chart(fig, use_container_width=True)
    # Profil Allure

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=distances_pace,
        y=paces,
        mode='lines',
        name='Allure ajustée',
        yaxis="y2",
        hovertemplate='Distance: %{x:.2f} km<br>Allure: %{y:.1f} min/km'
    ))

    # Configuration des axes
    fig2.update_layout(
        title="Profil Altitude et Allure Ajustée",
        xaxis=dict(title='Distance (km)'),
        yaxis=dict(title='Allure (min/km)', overlaying='y', side='left', autorange='reversed'),
        legend=dict(x=0, y=1),
        height=300,
    )

    st.plotly_chart(fig2, use_container_width=True)

    # Temps de passage
    distance_target = st.number_input(
        "Distance (en km) pour connaître le temps de passage estimé", 
        min_value=0.0, 
        format="%.2f"
    )

    if distance_target > 0:
        total_time_sec = 0
        for i in range(1, len(distances_pace)):
            d = (distances_pace[i] - distances_pace[i-1]) * 1000  # mètres
            v = 1000 / (paces[i] * 60)  # vitesse locale m/s
            if distances_pace[i] >= distance_target:
                d_remain = (distance_target - distances_pace[i-1]) * 1000
                total_time_sec += d_remain / v
                break
            else:
                total_time_sec += d / v

        h = int(total_time_sec // 3600)
        m = int((total_time_sec % 3600) // 60)
        s = int(total_time_sec % 60)

        st.success(f"Temps estimé au km {distance_target:.2f} : {h:02d}:{m:02d}:{s:02d}")

with st.expander("Voir explication du calcul"):
    st.markdown(
        """
        ### Comment fonctionne ce simulateur ?

        L'algorithme repose sur **le modèle biomécanique de Minetti**,
        qui estime le **coût énergétique** de la course à pied en fonction de la pente.

        ➡️ **Sur terrain plat**, le coût énergétique est minimal.\n
        ➡️ **En montée**, le coût énergétique augmente (on dépense plus pour s'élever).\n
        ➡️ **En descente**, le coût diminue... mais on ne peut pas courir infiniment vite sans limite physique.

        ### Calculs effectués :

        - L'algorithme cherche une **vitesse ajustée à la pente (VAP)** qui vous permettrait d'atteindre ce temps,
          tout en tenant compte :
            - du profil de pente de votre trace GPX,
            - du temps total espéré

        - Pour chaque segment du parcours :
            - Le coût énergétique est recalculé selon la pente locale,
            - La vitesse instantanée est adaptée en fonction de ce coût,
            - En descente, la vitesse est plafonnée à 1.3 x VAP<sup>1</sup>.

        ### Conséquences :

        - Si votre vitesse max en descente est faible ➔ l'allure sur plat et en montée devra être plus rapide pour compenser.
        - Plus votre objectif de temps est ambitieux ➔ plus la vitesse globale devra être élevée.

        ---
        Modèle utilisé :  
        Minetti AE, Moia C, Roi GS, Susta D, Ferretti G. (2002)  
        *Energy cost of walking and running at extreme uphill and downhill slopes*  
        Journal of Applied Physiology.
        ---
        <sup>1</sup> Le modèle doit encore être ajusté à ce niveau. Le modèle de Minetti ne prenant pas en compte la technicité du terrain, il estime qu'atteindre 20km/h sur une descente de pente comprise entre -13% et -20% est équivalent à courir à 11.2 km/h sur du plat.

        """,
        unsafe_allow_html=True
    )

