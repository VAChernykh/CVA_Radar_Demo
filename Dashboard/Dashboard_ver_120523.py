#!/usr/bin/env python
# coding: utf-8

TEST_MODE = 0

import pandas as pd
import numpy as np

import streamlit as st
import streamlit.components.v1 as components
from st_aggrid import AgGrid

import networkx as netx
from pyvis.network import Network

import openpyxl

input_data_folder = 'Common_data'

company_names = pd.read_excel(f"{input_data_folder}/company_names.xlsx", engine='openpyxl').astype(str)

company_connections = pd.read_excel(f"{input_data_folder}/company_connections.xlsx", engine='openpyxl').astype(str)

company_sanctions = pd.read_excel(f"{input_data_folder}/company_sanctions.xlsx", engine='openpyxl')
company_sanctions['Group'] = company_sanctions['Group'].astype(str)
company_sanctions['score'] = pd.to_numeric(company_sanctions['score'], errors='coerce')

company_info = pd.read_excel(f"{input_data_folder}/company_info.xlsx", engine='openpyxl').astype(str)

company_info = company_info.merge(company_names, left_on='Компания', right_on='ID', how='left')

company_name = 'Исследумая компания'
company_name_id = 'ID'

company_df = company_info[[company_name, company_name_id]].drop_duplicates()
all_companies = company_info[company_name].drop_duplicates()
all_companies_id = company_df[company_name_id].values

company_info_display_1 = company_info.copy()

company_risk_metric = 'Оценка риска'

company_sanctions_display_1 = company_names.merge(
    company_sanctions, left_on='ID', right_on='Group', how='left'
)

company_sanctions_display_1['score'] = company_sanctions_display_1['score'].fillna(0)

company_sanctions_display_2 = (
    company_sanctions_display_1.groupby('ID')['score']
    .mean()
    .reset_index()
    .rename(columns={'score': company_risk_metric})
)

def all_connected_nodes(g, ids):
    result = []
    for i in ids:
        try:
            result += list(netx.shortest_path(g, i).keys())
        except:
            pass
    return list(set(result))

company_connections_display_1 = company_connections.merge(
    company_names, left_on='Группа', right_on='ID', how='left'
)

company_connections_display_2 = company_names.merge(
    company_sanctions_display_2, on='ID', how='left'
)

company_connections_display_2[company_risk_metric] = company_connections_display_2[company_risk_metric].fillna(0)

g = netx.Graph()
for _, row in company_connections_display_1.iterrows():
    g.add_edge(row['A'], row['B'])

group_connections_group = []
group_connections_company = []

for i in all_companies_id:
    for j in all_connected_nodes(g, [i]):
        group_connections_group.append(i)
        group_connections_company.append(j)

group_connections = pd.DataFrame({
    'Main_node': group_connections_group,
    'Node': group_connections_company
})

company_resume_display_1 = group_connections.merge(
    company_sanctions[['Group', 'score']],
    left_on='Node',
    right_on='Group',
    how='left'
)

company_resume_display_1['score'] = company_resume_display_1['score'].fillna(0)

company_resume_display_1['score_group'] = company_resume_display_1.apply(
    lambda x: x.score if x['Main_node'] == x['Group'] else 0, axis=1
)

company_resume_display_2 = company_resume_display_1.merge(
    company_names, left_on='Main_node', right_on='ID', how='left'
)

company_resume_display_2 = (
    company_resume_display_2.groupby(company_name)
    .agg({'Node': 'nunique', 'score_group': 'max', 'score': 'max'})
    .reset_index()
)

company_resume_display_2['score'] = company_resume_display_2['score'].round(2)
company_resume_display_2['score_group'] = company_resume_display_2['score_group'].round(2)

company_resume_display_2.columns = [
    'Исследумая компания',
    'Кол-во связанных компаний',
    'Макс. оценка санц. риска компании',
    'Макс. оценка санц. риска связанных компаний'
]

main_pages = ["Резюме", "Факты о компании", "Связи компаний", "Санкционные риски"]

selected = st.radio("", main_pages, horizontal=True)

company_choice = st.sidebar.multiselect(
    'Выберите компанию:', all_companies, all_companies
)

company_choice_id = company_df[
    company_df[company_name].isin(company_choice)
][company_name_id].values

if selected == "Факты о компании" or TEST_MODE:
    st.write('Источник: orginfo.uz')
    AgGrid(company_info_display_1[
        company_info_display_1[company_name].isin(company_choice)
    ])

if selected == "Связи компаний" or TEST_MODE:
    net = Network(directed=True)

    need_companies = all_connected_nodes(g, company_choice_id)

    df_edges = company_connections_display_1[
        company_connections_display_1['A'].isin(need_companies) |
        company_connections_display_1['B'].isin(need_companies)
    ]

    df_nodes = company_connections_display_2[
        company_connections_display_2['ID'].isin(need_companies)
    ]

    for _, row in df_nodes.iterrows():
        net.add_node(row['ID'], label=row[company_name])

    for _, row in df_edges.iterrows():
        net.add_edge(row['A'], row['B'])

    net.save_graph("graph.html")
    HtmlFile = open("graph.html", 'r', encoding='utf-8')
    components.html(HtmlFile.read(), height=700)

if selected == "Резюме" or TEST_MODE:
    st.write("Демо анализа компаний")
    AgGrid(company_resume_display_2)

if selected == "Санкционные риски" or TEST_MODE:
    st.write("Источник: opensanctions.org")

    need_companies = all_connected_nodes(g, company_choice_id)

    df = company_sanctions_display_1[
        company_sanctions_display_1['ID'].isin(need_companies)
    ]

    AgGrid(df)
