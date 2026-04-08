import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components
import networkx as netx
from pyvis.network import Network

st.set_page_config(layout="wide")

input_data_folder = 'Common_data'

@st.cache_data
def load_data():
    names = pd.read_excel(f"{input_data_folder}/company_names.xlsx").astype(str)
    names['ID'] = names['ID'].str.strip()
    
    conn = pd.read_excel(f"{input_data_folder}/company_connections.xlsx").astype(str)
    conn['A'] = conn['A'].str.strip()
    conn['B'] = conn['B'].str.strip()
    
    sanctions = pd.read_excel(f"{input_data_folder}/company_sanctions.xlsx")
    sanctions['Group'] = sanctions['Group'].astype(str).str.strip()
    sanctions['score'] = pd.to_numeric(sanctions['score'], errors='coerce').fillna(0)
    
    info = pd.read_excel(f"{input_data_folder}/company_info.xlsx").astype(str)
    info['Компания'] = info['Компания'].str.strip()
    
    return names, conn, sanctions, info

company_names, company_connections, company_sanctions, company_info = load_data()

company_info = company_info.merge(company_names, left_on='Компания', right_on='ID', how='left')
company_name_col = 'Исследумая компания' 
company_id_col = 'ID'

company_registry = company_info[[company_name_col, company_id_col]].drop_duplicates().dropna()
all_companies_list = sorted(company_registry[company_name_col].unique())

def get_all_connected_ids(connections_df, start_ids):
    g = netx.Graph()
    for _, row in connections_df.iterrows():
        g.add_edge(row['A'], row['B'])
    
    result = set()
    for start_id in start_ids:
        if g.has_node(start_id):
            connected = netx.node_connected_component(g, start_id)
            result.update(connected)
        else:
            result.add(start_id)
    return list(result)

st.sidebar.header("Фильтры")
selected_names = st.sidebar.multiselect(
    'Выберите компании для анализа:', 
    options=all_companies_list,
    default=all_companies_list[:3] if len(all_companies_list) > 0 else None
)

selected_ids = company_registry[company_registry[company_name_col].isin(selected_names)][company_id_col].tolist()
connected_ids = get_all_connected_ids(company_connections, selected_ids)

tabs = st.tabs(["Резюме", "Связи компаний", "Санкционные риски", "Факты о компании"])

with tabs[0]:
    st.subheader("Сводный анализ рисков")
    relevant_sanctions = company_sanctions[company_sanctions['Group'].isin(connected_ids)]
    
    resume_data = []
    for name in selected_names:
        cid = company_registry[company_registry[company_name_col] == name][company_id_col].iloc[0]
        family = get_all_connected_ids(company_connections, [cid])
        
        own_risk = company_sanctions[company_sanctions['Group'] == cid]['score'].max()
        family_risk = company_sanctions[company_sanctions['Group'].isin(family)]['score'].max()
        
        resume_data.append({
            'Компания': name,
            'Кол-во связей': len(family) - 1,
            'Личный риск': round(float(own_risk), 2) if not pd.isna(own_risk) else 0.0,
            'Макс. риск в связях': round(float(family_risk), 2) if not pd.isna(family_risk) else 0.0
        })
    
    st.dataframe(pd.DataFrame(resume_data), use_container_width=True)

with tabs[1]:
    st.subheader("Визуализация графа связей")
    if not connected_ids:
        st.warning("Нет данных для построения графа")
    else:
        net = Network(height="600px", width="100%", directed=False, bgcolor="#ffffff", font_color="black")
        
        net.toggle_physics(True)
        net.barnes_hut(gravity=-3000, central_gravity=0.3, spring_length=200, spring_strength=0.05, damping=0.09)

        relevant_edges = company_connections[
            company_connections['A'].isin(connected_ids) & 
            company_connections['B'].isin(connected_ids)
        ]
        
        node_labels = company_names.set_index('ID')['Исследумая компания'].to_dict()
        
        for node in connected_ids:
            label = node_labels.get(node, node)
            color = "#ff4b4b" if node in selected_ids else "#1f77b4"
            net.add_node(node, label=label, color=color)
            
        for _, row in relevant_edges.iterrows():
            net.add_edge(row['A'], row['B'])
        
        net.save_graph("graph.html")
        with open("graph.html", 'r', encoding='utf-8') as f:
            components.html(f.read(), height=650)

with tabs[2]:
    st.subheader("Детализация санкций")
    risk_df = company_sanctions[company_sanctions['Group'].isin(connected_ids)].copy()
    risk_df = risk_df.merge(company_names, left_on='Group', right_on='ID', how='left')
    st.dataframe(risk_df[['Исследумая компания', 'Group', 'score']], use_container_width=True)

with tabs[3]:
    st.subheader("Данные из orginfo.uz")
    display_info = company_info[company_info[company_id_col].isin(selected_ids)]
    st.dataframe(display_info, use_container_width=True)
