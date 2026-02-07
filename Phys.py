import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
from io import BytesIO
from PIL import Image

st.set_page_config(layout="wide", page_title="Temps vs Position")
st.title("Temps vs Position 📊 (Temps réel)")

# =====================
# INITIALISATION
# =====================
if "df" not in st.session_state:
    n_points_init = 21  # x0 à x20
    st.session_state.df = pd.DataFrame({
        "ID": [f"x{i}" for i in range(n_points_init)],
        "Temps": [round(0.05 * i, 2) for i in range(n_points_init)],
        "Position": [0.0 for _ in range(n_points_init)]
    })
    st.session_state.t = st.session_state.df["Temps"].max()
    st.session_state.next_id = len(st.session_state.df)

col1, col2 = st.columns([2, 3])

# =====================
# TABLEAU
# =====================
with col1:
    st.subheader("Tableau des données")

    if st.button("➕ Ajouter un point"):
        st.session_state.t = round(st.session_state.t + 0.05, 2)
        nouvelle_position = 0.0
        st.session_state.df.loc[len(st.session_state.df)] = [
            f"x{st.session_state.next_id}",
            st.session_state.t,
            nouvelle_position
        ]
        st.session_state.next_id += 1

    st.session_state.df["Temps"] = st.session_state.df["Temps"].round(2)
    st.session_state.df["Position"] = st.session_state.df["Position"].round(3)

    df_editor = st.data_editor(
        st.session_state.df,
        column_config={
            "ID": {"editable": True},
            "Temps": {"editable": True, "format": "%.2f"},
            "Position": {"editable": True, "format": "%.3f"}
        },
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True
    )
    st.session_state.df = df_editor
    st.session_state.df["Temps"] = st.session_state.df["Temps"].round(2)
    st.session_state.df["Position"] = st.session_state.df["Position"].round(3)

# =====================
# GRAPHIQUE
# =====================
with col2:
    st.subheader("Nuage de points + droite moyenne")

    df = st.session_state.df.dropna()

    if len(df) >= 2:
        t = df["Temps"]
        p = st.session_state.df["Position"]

        # Régression linéaire
        a, b = np.polyfit(t, p, 1)
        t_line = np.linspace(t.min(), t.max(), 100)
        p_line = a * t_line + b

        # Graphique interactif Plotly pour l'application
        fig = px.scatter(
            df,
            x="Temps",
            y="Position",
            text="ID",
            hover_data={"ID": True, "Temps": ":.2f", "Position": ":.3f"}
        )
        fig.add_scatter(x=t_line, y=p_line, mode="lines", name="Droite moyenne")
        fig.update_traces(textposition="top center")
        fig.update_layout(xaxis_title="Temps (s)", yaxis_title="Position (m)")

        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Droite moyenne : Position = {a:.3f} × Temps + {b:.3f}")

        # =====================
        # EXPORT PNG COMBINÉ (matplotlib)
        # =====================
        st.subheader("📥 Télécharger tableau + graphique en une seule image")

        # --- 1️⃣ Tableau en image ---
        buffer_table = BytesIO()
        fig_width_inch = 8
        fig_height_inch = 5
        fig_table, ax = plt.subplots(figsize=(fig_width_inch, fig_height_inch))
        ax.axis('off')
        tbl = ax.table(
            cellText=df.values,
            colLabels=df.columns,
            cellLoc='center',
            loc='center'
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(12)
        tbl.scale(1.5, 2)
        plt.tight_layout()
        fig_table.savefig(buffer_table, format='png', dpi=200)
        buffer_table.seek(0)
        plt.close(fig_table)
        img_table = Image.open(buffer_table)

        # --- 2️⃣ Graphique en image matplotlib pour export ---
        buffer_fig = BytesIO()
        plt.figure(figsize=(8,5))
        plt.scatter(df["Temps"], df["Position"], label="Points")
        plt.plot(t_line, p_line, color='red', label="Droite moyenne")
        plt.xlabel("Temps (s)")
        plt.ylabel("Position (m)")
        plt.title("Temps vs Position")
        plt.legend()
        plt.tight_layout()
        plt.savefig(buffer_fig, format='png', dpi=200)
        plt.close()
        buffer_fig.seek(0)
        img_fig = Image.open(buffer_fig)

        # --- 3️⃣ Combiner tableau + graphique verticalement ---
        total_height = img_table.height + img_fig.height
        total_width = max(img_table.width, img_fig.width)
        combined_img = Image.new('RGB', (total_width, total_height), color='white')
        combined_img.paste(img_table, (0,0))
        combined_img.paste(img_fig, (0,img_table.height))

        # --- 4️⃣ Bouton de téléchargement ---
        buf_combined = BytesIO()
        combined_img.save(buf_combined, format='PNG')
        buf_combined.seek(0)

        st.download_button(
            label="Télécharger le tableau + graphique",
            data=buf_combined,
            file_name="tableau_graphique.png",
            mime="image/png"
        )

    else:
        st.info("Ajoute au moins 2 points")

