
import streamlit as st
import pandas as pd
import numpy as np

st.title('GSLDS Order Export Formatter')

donations = pd.read_csv('donations.csv')

uploaded_file = st.file_uploader("Upload order export .csv:")
if uploaded_file is not None:
    # Can be used wherever a "file-like" object is accepted:
    df_raw = pd.read_csv(uploaded_file)

    # relabel payment methods
    payments = {'cod' : 'Cash/Check', 
                'woocommerce_payments' : 'Paid', 
                'bacs': 'Zelle'}
    df_raw = df_raw.replace({'payment_method': payments})

    # relabel shipping methods
    shipping = {'Local pickup' : 'Local pickup',
                'Flat Rate based on number of plants': 'Shipping'}
    df_raw = df_raw.replace({'shipping_method': shipping})

    # create customer name
    df_raw['customer'] = df_raw['billing_first_name'] + ' ' + df_raw['billing_last_name']

    # subset columns
    item_cols = [col for col in df_raw if col.startswith('line_item')]
    id_cols = ['customer', 'payment_method', 'order_id', 'shipping_method']
    cols = id_cols + item_cols
    df_orders = df_raw[cols]

    # transpose to long format
    df_long = pd.melt(df_orders, id_vars = id_cols, value_vars = item_cols)
    line_item_cols = ['product', 'id', 'sku', 'quantity', 'total', 'subtotal', 'stock_reduction']
    df_long[line_item_cols] = df_long.value.str.split("|", expand = True)
    df_long['product'] = df_long['product'].replace('name:', '', regex=True)
    df_long['quantity'] = df_long['quantity'].replace('quantity:', '', regex=True)

    # make final dataframe
    df = df_long[id_cols + ['product', 'quantity']]
    df = df.dropna()

    # summary for digging
    df['quantity'] = pd.to_numeric(df['quantity'])
    dig = df[['product', 'quantity']].groupby('product').sum()
    dig.index.name = 'product'
    dig.reset_index(inplace=True)
    dig = dig.merge(donations, how = 'left', on = 'product')

    ## printable tables
    tab1, tab2 = st.tabs(['Packing Slips', 'Digging Lists'])

    with tab1:
        ## packing list
        customers = df_raw['customer'].to_list()
        for c in customers:
            dat = df[df['customer'] == c]
            orders = dat['order_id'].unique().tolist()
            n_orders = len(orders)
            for o in range(n_orders):
                paid = dat['payment_method'].unique().tolist()[0]
                ship = dat['shipping_method'].unique().tolist()[0]
                st.header(c)
                st.subheader(paid + ', ' + ship)
                d = dat[dat['order_id'] == orders[o]]
                d.index = np.arange(1, d.shape[0]+1).tolist()
                if n_orders > 1:
                    st.subheader(orders[o])
                st.table(d[['product', 'quantity']])
            st.write('- ' * 20)

    with tab2:
        ## packing list
        donators = dig['donator'].unique().tolist()
        for d in donators:
            data = dig[dig['donator'] == d]
            st.header(d)
            data.index = np.arange(1, data.shape[0]+1).tolist()    
            st.table(data[['product', 'quantity']])
            st.write('- ' * 20)

    
    