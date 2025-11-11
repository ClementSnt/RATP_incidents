import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(layout="wide", page_title="Dashboard incidents RATP")

# Import des données
df = pd.read_csv(r"/data/historique_incidents_theme.csv", sep=";")

# Renommer les colonnes
df = df.rename(columns={
        'date journee': 'date',
        "date de début de l'incident": 'date_debut',
        "date de fin de l'incident": 'date_fin',
        "duree incident total (minutes)": 'duree_minute'
})

# Dates
df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
df['date_debut'] = pd.to_datetime(df['date_debut'], dayfirst=True, errors='coerce')
df['date_fin'] = pd.to_datetime(df['date_fin'], dayfirst=True, errors='coerce')

# Durées des incidents
df['duree_minute'] = pd.to_numeric(df['duree_minute'], errors='coerce')
missing_minutes = df['duree_minute'].isna()
if missing_minutes.any():
    df.loc[missing_minutes, 'duree_minute'] = (
        (df.loc[missing_minutes, 'date_fin'] - df.loc[missing_minutes, 'date_debut']).dt.total_seconds() / 60
    )
df['duree_hour'] = (df['duree_minute'] / 60).fillna(0)

# Variables temporelles
df['mois'] = df['date'].dt.to_period('M').astype(str)
df['jour_semaine'] = df['date'].dt.day_name()
df['heure_debut'] = df['date_debut'].dt.hour.fillna(-1).astype(int)



# Sidebar - filtres
st.sidebar.title("Filtres")

# Filtre des lignes
all_lignes = sorted(df['ligne'].dropna().unique())
lignes_sel = st.sidebar.multiselect("Lignes", options=all_lignes, default=all_lignes)

# Filtre des causes
all_types = sorted(df['theme_final'].dropna().unique())
types_sel = st.sidebar.multiselect("Types d'incident", options=all_types, default=all_types)

# Filtre par mois/année (multi-sélection)
all_mois = sorted(df['mois'].unique())
mois_sel = st.sidebar.multiselect("Mois à inclure (mois/année)", options=all_mois, default=[all_mois[-1]])

df_f = df[
    (df['ligne'].isin(lignes_sel)) &
    (df['theme_final'].isin(types_sel)) &
    (df['mois'].isin(mois_sel))
].copy()

# Calcul période couverte
period_dates = pd.date_range(df_f['date'].min(), df_f['date'].max(), freq='D') if not df_f.empty else []
total_days = len(period_dates)


# Totaux par ligne

st.title("🚇 Dashboard incidents RATP")

st.markdown("### Totaux par ligne sur la période sélectionnée")
agg = df_f.groupby('ligne', as_index=False).agg(
    nb_incidents=('theme_final', 'count'),
    duree_hours=('duree_hour', 'sum'),
    jours_avec_incident=('date', lambda s: s.dt.normalize().nunique())
)

agg['pct_jours_avec_incident'] = (agg['jours_avec_incident'] / total_days * 100).round(1) if total_days else 0


agg_display = agg[['ligne', 'nb_incidents', 'duree_hours', 'jours_avec_incident',
                   'pct_jours_avec_incident']].rename(columns={
                       'duree_hours': 'duree_hours_total',
                       'jours_avec_incident': 'nb_jours_avec_incident'
                   }).sort_values('nb_incidents', ascending=False)

st.dataframe(agg_display.style.format({
    'nb_incidents': '{:,.0f}',
    'duree_hours_total': '{:,.1f} h',
    'nb_jours_avec_incident': '{:,.0f}',
    'pct_jours_avec_incident': '{:.1f} %',
}), use_container_width=True)


# Comparaison entre lignes => lineplot

st.markdown("### Comparaison entre lignes")
col1, col2 = st.columns([3,1])
with col2:
    use_duration = st.checkbox("Afficher durée totale (heures)", value=False)

with col1:
    df_line = df_f.copy()
    df_line['date_day'] = df_line['date'].dt.normalize()
    if use_duration:
        df_agg_line = df_line.groupby(['date_day','ligne'], as_index=False).agg(y=('duree_hour','sum'))
        y_title = "Durée (heures)"
    else:
        df_agg_line = df_line.groupby(['date_day','ligne'], as_index=False).agg(y=('theme_final','count'))
        y_title = "Nombre d'incidents"

    fig_line = px.line(df_agg_line, x='date_day', y='y', color='ligne', markers=True,
                       title=f"{y_title} par jour et par ligne")
    fig_line.update_layout(height=520, xaxis_title="Date", yaxis_title=y_title, legend_title="Ligne")
    st.plotly_chart(fig_line, use_container_width=True)


# Comparaisons temporelles

st.markdown("### Comparaisons temporelles")

# histogramme empilé
st.markdown("**Nombre d'incidents par mois et par cause**")
df_bar = df_f.groupby(['mois', 'theme_final'], as_index=False).size().rename(columns={'size':'nb_incidents'})
fig_bar = px.bar(df_bar, x='mois', y='nb_incidents', color='theme_final',
                 title="Incidents par mois et type (empilé)", labels={'nb_incidents':'Nombre incidents','mois':'Mois'})
fig_bar.update_layout(height=480, xaxis_tickangle=-45)
st.plotly_chart(fig_bar, use_container_width=True)

# % jours avec problème par jour de la semaine
st.markdown("**% de jours avec problème par jour de la semaine**")
dates_df = pd.DataFrame({"date": period_dates})
dates_df['weekday'] = dates_df['date'].dt.day_name()

weekday_stats = []
for ligne in lignes_sel:
    df_l = df_f[df_f['ligne']==ligne]
    days_with_inc = df_l['date'].dt.normalize().unique() if not df_l.empty else []
    days_with_inc_df = pd.DataFrame({"date": pd.to_datetime(days_with_inc)})
    days_with_inc_df['weekday'] = days_with_inc_df['date'].dt.day_name()
    counts = days_with_inc_df.groupby('weekday', as_index=False).size().rename(columns={'size':'nb_days_with_incident'})
    for wd in dates_df['weekday'].unique():
        val = int(counts[counts['weekday']==wd]['nb_days_with_incident'].iloc[0]) if (counts['weekday']==wd).any() else 0
        weekday_stats.append({"ligne": ligne, "weekday": wd, "nb_days_with_incident": val})

weekday_df = pd.DataFrame(weekday_stats)
weekday_total_counts = dates_df.groupby('weekday').size().reset_index(name='days_possible_in_period')
weekday_df = weekday_df.merge(weekday_total_counts, on='weekday', how='left')
weekday_df['pct_days_with_incident'] = weekday_df['nb_days_with_incident'] / weekday_df['days_possible_in_period'] * 100

fig_week = px.bar(weekday_df, x='weekday', y='pct_days_with_incident', color='ligne', barmode='group',
                  title="% jours avec incident par jour de la semaine", labels={'pct_days_with_incident':'% jours avec incident','weekday':'Jour'})
fig_week.update_layout(height=420)
st.plotly_chart(fig_week, use_container_width=True)

# Heatmap
st.markdown("Heatmap : fréquence incidents par jour de la semaine et par heures")
df_f['jour_semaine'] = df_f['date'].dt.day_name()
df_f['heure_debut'] = df_f['date_debut'].dt.hour
df_f['tranche_2h'] = (df_f['heure_debut'] // 2) * 2

jours_ordre = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
tranches = list(range(0, 24, 2))
grille = pd.MultiIndex.from_product([jours_ordre, tranches], names=['jour_semaine', 'tranche_2h']).to_frame(index=False)

df_heat = df_f.groupby(['jour_semaine', 'tranche_2h']).size().reset_index(name='nb_incidents')
df_heat = grille.merge(df_heat, on=['jour_semaine', 'tranche_2h'], how='left').fillna(0)
df_heat['nb_incidents'] = df_heat['nb_incidents'].astype(int)

fig_heat = px.imshow(
    df_heat.pivot(index='jour_semaine', columns='tranche_2h', values='nb_incidents').loc[jours_ordre],
    color_continuous_scale='Blues',
    aspect='auto',
    labels=dict(x="Tranche horaire (2h)", y="Jour", color="Nb incidents"),
    title="Incidents par tranche de 2h et jour de la semaine"
)

fig_heat.update_xaxes(side="top", tickmode='array', tickvals=tranches, ticktext=[f"{t:02d}-{t+2:02d}" for t in tranches])
fig_heat.update_layout(height=520)
st.plotly_chart(fig_heat, use_container_width=True)


# Export des données
st.markdown("Exporter les données")

csv = df_f.to_csv(index=False).encode('utf-8')
st.download_button("Télécharger CSV", data=csv, file_name="incidents_filtered.csv", mime="text/csv")
