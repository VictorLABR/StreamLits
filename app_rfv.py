import os
import numpy as np 
import pandas as pd
import streamlit as st

from datetime import datetime
from PIL import Image
from io import BytesIO

custom_params = {'axes.spines.right': False, 'axes.spines.top': False}

@st.cache_data
def convert_df(df):
    return df.to_csv(index= False).encode('utf-8')

@st.cache_data
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    output.seek(0)
    return output

def recency_class(x, r, q_dict):
    """Classifies the lowest quartile as the best
       x = row value,
       r = recency,
       q_dict = quartile dictionary   
    """
    if x <= q_dict[r][0.25]:
        return 'A'
    elif x <= q_dict[r][0.50]:
        return 'B'
    elif x <= q_dict[r][0.75]:
        return 'C'
    else:
        return 'D'


def freq_val_class(x, fv, q_dict):
    """Classifies the highest quartile as the best
       x = row value,
       fv = frequency or value,
       q_dict = quartile dictionary   
    """
    if x <= q_dict[fv][0.25]:
        return 'D'
    elif x <= q_dict[fv][0.50]:
        return 'C'
    elif x <= q_dict[fv][0.75]:
        return 'B'
    else:
        return 'A'

def main():
    st.set_page_config(page_title= 'Telemkt analisys', \
                       layout='wide',
                       initial_sidebar_state='expanded'
                       )
    st.write("""# Classification RFV
             
             RFV means Recency, Frequency & Value. It's used to Client Segmentation based on the Shopping Behaviour
             and group them by Similiar Clusters. Using this argument, we can create better focused MKT and CRM actions,
             improving on the customization of the material and even retaing more clients.
             
             For each client, we must calculate the following components:
             
             - Recency (R) = Number of days since the last purchase;
             - Frequency (F) = Number of total purchases in the period;
             - Value (V) = Total amount spent in the period;""")
    st.markdown("---")

    image = Image.open('Bank-Branding.jpg')
    st.sidebar.image(image)

    st.sidebar.write("## Upload the file")
    data_file_1 = st.sidebar.file_uploader("Bank mkt data", type = ['csv', 'xlsx'])

    if (data_file_1 is not None):
        df_purchases = pd.read_csv(data_file_1, infer_datetime_format= True, parse_dates=['PurchaseDay'])

        current = df_purchases['PurchaseDay'].max()
        st.write('Max day on DB:', current)

        df_recency = df_purchases.groupby(by='CustomerID', as_index=False)['PurchaseDay'].max()
        df_recency.columns = ['CustomerID', 'LastPurchase']
        df_recency['Recency'] = df_recency['LastPurchase'].apply(lambda x: (current - x).days)

        df_recency.drop('LastPurchase', axis=1, inplace=True)

        df_frequency = df_purchases[['CustomerID', 'PurchaseCode']].groupby('CustomerID').count().reset_index()
        df_frequency.columns = ['CustomerID', 'Frequency']

        df_value = df_purchases[['CustomerID', 'TotalValue']].groupby('CustomerID').sum().reset_index()
        df_value.columns = ['CustomerID', 'Value']

        st.write('## RFV Table Preview')
        df_RFV = df_recency.merge(df_frequency, on='CustomerID').merge(df_value, on='CustomerID').set_index('CustomerID')
        st.write(df_RFV.head())

        st.write('## Segmentation of clients')

        st.write('Quartiles recon')
        quartile = df_RFV.quantile(q=[0.25, 0.5, 0.75])
        st.write(quartile)

        st.write('RFV Ranking Preview')
        df_RFV['R_Quartile'] = df_RFV['Recency'].apply(recency_class, args=('Recency', quartile))
        df_RFV['F_Quartile'] = df_RFV['Frequency'].apply(freq_val_class, args=('Frequency', quartile))
        df_RFV['V_Quartile'] = df_RFV['Value'].apply(freq_val_class, args=('Value', quartile))
        df_RFV['RFV_Score'] = (df_RFV.R_Quartile + df_RFV.F_Quartile + df_RFV.V_Quartile)
        st.write(df_RFV.head())

        st.write('Number of clients per Rank')
        st.write(df_RFV['RFV_Score'].value_counts())

        st.write('### TOP 10 clients')
        st.write(df_RFV[df_RFV['RFV_Score']=='AAA'].sort_values('Value', ascending=False).head(10))
        
        actions_dict = {
                'AAA': 'Fidelity program | Refer to friends = special bonus | New product = free samples',
                'BAA': 'Fidelity program | Refer to friends = bonus',
                'ABB': 'Exclusive Discount Cupons | Refer to friends = bonus',
                'BBB': 'Discount Cupons | Refer to friends = bonus',
                'DDD': 'Total Churn! Send a special offer to encourage new purchase',
                'DDC': 'Total Churn! Send a special offer to encourage new purchase',
                'CDD': 'Total Churn! Send a special offer to encourage new purchase',
                }
        
        st.write('### MKT/CRM Actions Preview')
        df_RFV['actions'] = df_RFV['RFV_Score'].map(actions_dict)
        st.write(df_RFV.head())
        
        df_xlsx = to_excel(df_RFV)
        st.download_button(label='👉 Download here 👈', data=df_xlsx, file_name='RFV_.xlsx')

        st.write('Number of clients by type of action')
        st.write(df_RFV['actions'].value_counts(dropna=False))

if __name__ == '__main__':
    main()
        