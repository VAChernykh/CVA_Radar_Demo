#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#get_ipython().system('jupyter nbconvert --to script Dashboard_ver_120523.ipynb')


# In[62]:


TEST_MODE = 0


# In[63]:


import pandas as pd
import numpy as np
# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)

import streamlit as st
import streamlit.components.v1 as components
from streamlit_option_menu import option_menu
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode

import networkx as netx
import matplotlib.pyplot as plt
from pyvis.network import Network

import openpyxl


# In[ ]:





# ##### Сбор данных

# In[66]:


input_data_folder = 'Common_data'
#input_data_folder = '../Common_data'


# In[68]:


input_data_file = "company_names.xlsx"
company_names = pd.read_excel(input_data_folder + '/' + input_data_file, engine='openpyxl')
company_names = company_names.astype(str)

if len(company_names['ID']) != len(company_names['ID']) or len(company_names['Исследумая компания']) != len(company_names['Исследумая компания']):
    print('Ошибка сбора данных')
    st.write('Ошибка:', 'сбора данных')
    
company_names.describe()


# In[ ]:





# In[69]:


input_data_file = "company_connections.xlsx"
company_connections = pd.read_excel(input_data_folder + '/' + input_data_file, engine='openpyxl')
company_connections = company_connections.astype(str)
company_connections.head(1)


# In[ ]:





# In[70]:


input_data_file = "company_sanctions.xlsx"
company_sanctions = pd.read_excel(input_data_folder + '/' + input_data_file, engine='openpyxl')
company_sanctions = company_sanctions.astype(str)
company_sanctions['score'] = company_sanctions['score'].astype(float)
company_sanctions.head(1)


# In[ ]:





# In[71]:


input_data_file = "company_info.xlsx"
company_info = pd.read_excel(input_data_folder + '/' + input_data_file, engine='openpyxl')
company_info = company_info.astype(str)
company_info.head(1)


# In[72]:


#данные по компаниям
company_info = company_info.merge(company_names
                   , left_on='Компания'
                   , right_on = 'ID'
                   , how = 'left')
company_info.head(1)


# In[ ]:





# ##### Расчет

# - Блок фильтров

# In[73]:


company_name = 'Исследумая компания'
company_name_id = 'ID'
company_df = company_info[[company_name, company_name_id]].drop_duplicates()

all_companies = company_info[company_name].drop_duplicates()
all_companies_id = company_df[company_name_id].values


# In[ ]:





# - Блок базовых данных

# In[74]:


#данные по компаниям
company_info_display_1 = company_info.copy()
company_info_display_1.head(1)


# In[ ]:





# - Блок санкции

# In[75]:


company_risk_metric = 'Оценка риска'


# In[76]:


company_sanctions_display_1 = company_names.merge(company_sanctions
                   , left_on='ID'
                   , right_on = 'Group'
                   , how = 'left')
company_sanctions_display_1['score'] = company_sanctions_display_1['score'].fillna(0) 


# In[77]:


company_sanctions_display_2 = company_sanctions_display_1.groupby('ID')['score'].agg(['mean'])\
                                                    .rename({'mean': company_risk_metric}, axis=1)\
                                                    .reset_index()
company_sanctions_display_2.describe()


# In[ ]:





# - Блок связям

# In[78]:


def all_connected_nodes(g, ids):
    result = []
    for id in ids:
        result += list(netx.shortest_path(g, id).keys())
    return list(set(result))


# In[ ]:





# In[79]:


#данные по связям
company_connections_display_1 = company_connections.merge(company_names
                   , left_on='Группа'
                   , right_on = 'ID'
                   , how = 'left')
company_connections_display_1.head(1)


# In[ ]:





# In[80]:


#данные по нодам
company_connections_display_2 = company_names.merge(company_sanctions_display_2
                   , on='ID'
                   , how = 'left')
company_connections_display_2.fillna(0, inplace=True)
company_connections_display_2.head()


# In[81]:


company_connections_display_2.describe()


# In[ ]:





# In[82]:


company_connections_net = company_connections_display_1.copy()
company_names_net = company_connections_display_2.copy()

g = netx.Graph()

for index, row in company_connections_net.iterrows():
    g.add_edge(row['A'], row['B'])
    
netx.draw_networkx(g)


# In[ ]:





# - Блок резюме

# In[83]:


group_connections_group = []
group_connections_company = []

for i in all_companies_id:
    for j in all_connected_nodes(g, [i]):
        group_connections_group.append(i)
        group_connections_company.append(j)
        
group_connections = pd.DataFrame(list(zip(group_connections_group, group_connections_company)),
              columns=['Main_node','Node'])

group_connections.describe()


# In[84]:


company_sanctions_resume_1 = company_sanctions[['Group', 'score']]
company_resume_display_1 = group_connections.merge(company_sanctions_resume_1
                   , left_on='Node'
                   , right_on = 'Group'
                   , how = 'left')

company_resume_display_1.fillna(0, inplace=True)

company_resume_display_1['score_group'] = company_resume_display_1.apply(lambda x: x.score if x['Main_node'] == x['Group'] else 0, axis=1)
company_resume_display_1.head()


# In[ ]:





# In[85]:


company_resume_display_2 = company_resume_display_1.merge(company_names
                   , left_on='Main_node'
                   , right_on = 'ID'
                   , how = 'left')
company_resume_display_2.head()


# In[86]:


company_resume_display_2 = company_resume_display_2.groupby(company_name).agg({'Node':'nunique'
                                                    , 'score_group': 'max'
                                                    , 'score':'max'}).reset_index()
company_resume_display_2['score'] = [round(i, 2) for i in company_resume_display_2['score'].values]
company_resume_display_2['score_group'] = [round(i, 2) for i in company_resume_display_2['score_group'].values]


# In[87]:


need_columns = ['Исследумая компания'
                , 'Кол-во связанных компаний'
                , 'Макс. оценка санц. риска компании'
                , 'Макс. оценка санц. риска связанных компаний']
company_resume_display_2.columns = need_columns
company_resume_display_2.head()


# In[ ]:





# ##### Визуализация

# In[88]:


main_pages = ["Резюме", "Факты о компании", "Связи компаний", "Санкционные риски"]


# In[89]:


def streamlit_menu(example=3):
    if example == 1:
        # 1. as sidebar menu
        with st.sidebar:
            selected = option_menu(
                menu_title="Main Menu",  # required
                options=["Home", "Projects", "Contact"],  # required
                icons=["house", "book", "envelope"],  # optional
                menu_icon="cast",  # optional
                default_index=0,  # optional
            )
        return selected

    if example == 2:
        # 2. horizontal menu w/o custom style
        selected = option_menu(
            menu_title=None,  # required
            options=["Home", "Projects", "Contact"],  # required
            icons=["house", "book", "envelope"],  # optional
            menu_icon="cast",  # optional
            default_index=0,  # optional
            orientation="horizontal",
        )
        return selected

    if example == 3:
        # 2. horizontal menu with custom style
        selected = option_menu(
            menu_title= None, #"Агрегация данных о компаниях для оценки рисков",  # required
            options= main_pages,  # required
            icons=["compass", "house", "bezier", "bell"],  # optional
            menu_icon=None,  # optional
            default_index=0,  # optional
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#fafafa"},
                "icon": {"font-size": "15px"},
                "nav-link": {
                    "font-size": "12px",
                    "text-align": "center",
                    "margin": "0px",
                    "--hover-color": "#eeeeee",
                },
                "nav-link-selected": {"background-color": "#fc4c4c"},
            },
        )
        return selected


# In[90]:


selected = streamlit_menu()
# with st.spinner("Loading..."):
#     time.sleep(1)
#st.title('Агрегация данных о компаниях для оценки рисков')


# - Блок фильтров

# In[91]:


company_choice = st.sidebar.multiselect('Выберите компанию:', all_companies, all_companies)
company_choice_id = company_df[company_df[company_name].isin(company_choice)][company_name_id].values


# In[ ]:





# - Блок базовых данных

# In[92]:


if (selected == main_pages[1]) or (TEST_MODE == 1):
    try:
        with st.expander("Подробнее"):
            st.write('Источник:', "orginfo.uz")
            
        need_columns = ['Исследумая компания'
                        , 'Пункт'
                        , 'Данные']
        AgGrid(company_info_display_1[(company_info_display_1[company_name].isin(company_choice))][need_columns])
        print("Успешно")
        
    except Exception as e:
        print('Ошибка: {}'.format(e))
        st.write('Ошибка:', str(e))


# In[ ]:





# - Блок карты

# In[93]:


net = Network(directed=True)
result_html_filename = r'company_network_analysis.html'


# In[94]:


need_companies = all_connected_nodes(g, company_choice_id)

company_connections_net_display = company_connections_net[company_connections_net['A'].isin(need_companies)
                            | company_connections_net['B'].isin(need_companies)].reset_index(drop=True)
company_names_net_display = company_names_net[company_names_net['ID'].isin(need_companies)].reset_index(drop=True)

company_names_net_display['ID'] = ['id' + str(i) for i in company_names_net_display['ID'].values]
company_connections_net_display['A'] = ['id' + str(i) for i in company_connections_net_display['A'].values]
company_connections_net_display['B'] = ['id' + str(i) for i in company_connections_net_display['B'].values]


# In[95]:


if (selected == main_pages[2]) or (TEST_MODE == 1):
    try:
        with st.expander("Подробнее"):
            st.write("Картинка в формате html.Объекты можно передвигать, увеличивать и уменьшать. При наведении появится доп. информация")
            st.write('Оценка санкционных рисков основана на релевантности объектов в базе opensanctions.org: 1-высокий/красный, 0-низкий/белый')
            st.write('Источник:', "orginfo.uz")
        #nodes
        for i in range(len(company_names_net_display)):
            #параметры нода
            if company_names_net_display[company_name][i] in company_choice:
                shape = "diamond"
            else:
                shape = "dot"
            value = round(company_names_net_display[company_risk_metric][i], 2)

            #описание
            i_title = "ЮЛ: {}.\nДата регс: {}.\nCтатус: {}.\nСанкционный. риск: {}".format(company_names_net_display[company_name][i]
                                                                    , company_names_net_display['Регистрация'][i]
                                                                    , company_names_net_display['Статус'][i]
                                                                    , value)
            
            net.add_node(
                company_names_net_display[company_name_id][i]
                , label=company_names_net_display[company_name][i]
                , title=i_title
                , shape=shape
                , color = f"rgb(255, {round((1-value)*255)}, {round((1-value)*255)})"
            )

        #edges
        for index, row in company_connections_net_display.iterrows():
            row_title = "Доля владения (владелец->собственность): {}".format(row['Доля']+'%') 
            net.add_edge(row['A'], row['B'], label=row['Доля']+'%', title = row_title, color = 'grey')

        net.repulsion(
            node_distance=200,
            central_gravity=0.2,
            spring_length=200,
            spring_strength=0.05,
            damping=0.09,
        )
        
        net.save_graph(result_html_filename)
        HtmlFile = open(result_html_filename, 'r', encoding='utf-8')
        components.html(HtmlFile.read(), scrolling=True, height=700)
        print("Успешно")
        
    except Exception as e:
        print('Ошибка: {}'.format(e))
        st.write('Ошибка:', str(e))


# In[ ]:





# - Блок резюме

# In[96]:


if (selected == main_pages[0]) or (TEST_MODE == 1):
    try:
        st.write("Это демо инструмента для сбора данных о компаниях для оценки рисков на примере 3 компаний из UZ. Результаты представлены на страницах выше")
        with st.expander("Подробнее"):
            st.write("В таблице ниже доступен поиск, фильтрация, выбор столбцов")
            st.write('Источник:', "Оценка санкционных рисков основана на релевантности объектов в базе opensanctions.org")
            
        AgGrid(company_resume_display_2)
        print("Успешно")
        
    except Exception as e:
        print('Ошибка: {}'.format(e))
        st.write('Ошибка:', str(e))


# In[ ]:





# - Блок санкции

# In[97]:

risk_treshold = 0
if (selected == main_pages[3]) or (TEST_MODE == 1):
    try:
        with st.expander("Подробнее"):
            st.write("Оценка санкционных рисков основана на релевантности объектов в базе opensanctions.org. В таблице ниже доступен поиск, фильтрация, выбор столбцов")
            st.write('Источник:', "api.opensanctions.org")
            
        need_columns_dict = {company_name : "Связанная компания"
                        , "properties.name" : "Релевантный объект"
                        , "score" : "Релевантность"
                        , "properties.jurisdiction" : "Юрисдикция"
                        , "schema" : "Тип объекта"
                        , "datasets" : "Источник"
                        , "referents" : "Ссылки"}
        
        need_columns = list(need_columns_dict.keys())
        need_companies = all_connected_nodes(g, company_choice_id)
        company_sanctions_relevant = company_sanctions_display_1[company_sanctions_display_1[company_name_id].isin(need_companies)]
        
        company_sanctions_relevant['score'] = [round(float(i), 2) for i in company_sanctions_relevant['score'].values]
        company_sanctions_relevant = company_sanctions_relevant[company_sanctions_relevant['score'] > risk_treshold]
        company_sanctions_relevant = company_sanctions_relevant.sort_values(by='score', ascending=False)
        company_sanctions_relevant = company_sanctions_relevant[need_columns].rename(need_columns_dict, axis=1)
        
        AgGrid(company_sanctions_relevant)
        print("Успешно")

    except Exception as e:
        print('Ошибка: {}'.format(e))
        st.write('Ошибка:', str(e))


# In[ ]:





# In[ ]:


# #drafts
# def options_select():
#     if "selected_options" in st.session_state:
#         if -1 in st.session_state["selected_options"]:
#             st.session_state["selected_options"] = available_options[0]
#             st.session_state["max_selections"] = 1
#         else:
#             st.session_state["max_selections"] = len(available_options)
            
# def display_options_select(available_options):
    
#     if "max_selections" not in st.session_state:
#         st.session_state["max_selections"] = len(available_options)

#     st.multiselect(
#         label="Select an Option",
#         options=available_options,
#         key="selected_options",
#         max_selections=st.session_state["max_selections"],
#         on_change=options_select,
#         format_func=lambda x: "All" if x == -1 else f"Option {x}",
#     )

#     return st.write(available_options[1:] if st.session_state["max_selections"] == 1 else st.session_state["selected_options"])


# In[ ]:


# if selected == main_pages[1]:
#     try:
#         st.write('Источник:', "orginfo.uz")

#         company_connections_net = company_connections_display_1[company_connections_display_1[company_name].isin(company_choice)].reset_index(drop=True)
#         need_companies = list(set(list(company_connections_net['A'].values) + list(company_connections_net['B'].values)))
#         company_names_net = company_names[company_names['ID'].isin(need_companies)].reset_index(drop=True)

#         #обработка данных
#         company_names_net['ID'] = ['id_' + str(i) for i in company_names_net['ID'].values]
#         company_connections_net['A'] = ['id_' + str(i) for i in company_connections_net['A'].values]
#         company_connections_net['B'] = ['id_' + str(i) for i in company_connections_net['B'].values]

#         #nodes
#         titles = []
#         for i in range(len(company_names_net)):
#             i_title = "Компания/ИП: {}.\nДата регс: {}.\nCтатус: {}".format(company_names_net[company_name][i]
#                                                                        , company_names_net['Регистрация'][i]
#                                                                        , company_names_net['Статус'][i])
#             titles.append(i_title)

#         net.add_nodes(
#             company_names_net['ID'].values
#             , label=company_names_net[company_name].values
#             , title=titles
#             , color=company_names_net['Цвет'].values
#         )

#         #edges
#         for index, row in company_connections_net.iterrows():
#             net.add_edge(row['A'], row['B'], title=row['Доля'], label=row['Доля'], color = 'grey')

#         net.repulsion(
#             node_distance=200,
#             central_gravity=0.2,
#             spring_length=200,
#             spring_strength=0.05,
#             damping=0.09,
#         )

#         net.save_graph(result_html_filename)
#         HtmlFile = open(result_html_filename, 'r', encoding='utf-8')
#         components.html(HtmlFile.read(), scrolling=True, height=700)
    
#     except Exception as e:
#         print('Ошибка: {}'.format(e))
#         st.write('Ошибка:', str(e))


# In[ ]:


# if selected == main_pages[1]:
#     try:
#         st.write('Источник:', "orginfo.uz")

#         company_connections_net = company_connections_display_1[company_connections_display_1[company_name].isin(company_choice)].reset_index(drop=True)
#         need_companies = list(set(list(company_connections_net['A'].values) + list(company_connections_net['B'].values)))
#         company_names_net = company_names[company_names['ID'].isin(need_companies)].reset_index(drop=True)

#         #обработка данных
#         company_names_net['ID'] = ['id_' + str(i) for i in company_names_net['ID'].values]
#         company_connections_net['A'] = ['id_' + str(i) for i in company_connections_net['A'].values]
#         company_connections_net['B'] = ['id_' + str(i) for i in company_connections_net['B'].values]

#         #nodes
#         titles = []
#         for i in range(len(company_names_net)):
#             i_title = "Компания/ИП: {}.\nДата регс: {}.\nCтатус: {}".format(company_names_net[company_name][i]
#                                                                        , company_names_net['Регистрация'][i]
#                                                                        , company_names_net['Статус'][i])
#             titles.append(i_title)

#         net.add_nodes(
#             company_names_net['ID'].values
#             , label=company_names_net[company_name].values
#             , title=titles
#             , color=company_names_net['Цвет'].values
#         )

#         #edges
#         for index, row in company_connections_net.iterrows():
#             net.add_edge(row['A'], row['B'], title=row['Доля'], label=row['Доля'], color = 'grey')

#         net.repulsion(
#             node_distance=200,
#             central_gravity=0.2,
#             spring_length=200,
#             spring_strength=0.05,
#             damping=0.09,
#         )

#         net.save_graph(result_html_filename)
#         HtmlFile = open(result_html_filename, 'r', encoding='utf-8')
#         components.html(HtmlFile.read(), scrolling=True, height=700)
    
#     except Exception as e:
#         print('Ошибка: {}'.format(e))
#         st.write('Ошибка:', str(e))

