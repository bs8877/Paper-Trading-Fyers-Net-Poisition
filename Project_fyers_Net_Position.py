import dash
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output
import pandas as pd
from fyers_apiv3 import fyersModel


client_id = "YOUR CLIENT ID "  #INPUT FYERS CLIENT ID FROM FYERS API
access_token = "YOUR ACCESS TOKEN" #GENERATE ACCESS TOKEN USING FYERS 
fyers = fyersModel.FyersModel(client_id=client_id, token=access_token, is_async=False, log_path="")


positions = {}

def get_strike_and_option_type(symbol):
    try:
        if len(symbol) >= 7:
            last_part = symbol[-7:]
            strike_price = last_part[:-2]
            option_type = last_part[-2:]
            if option_type not in ['CE', 'PE']:
                option_type = 'Unknown'
            return f"{strike_price}{option_type}"
    except Exception as e:
        print(f"Error parsing symbol '{symbol}': {e}")
    return '0Unknown'

def update_position(symbol, qty, limit_price, order_side, positions):
    if symbol not in positions:
        positions[symbol] = {'buy_qty': 0, 'sell_qty': 0, 'buy_value': 0, 'sell_value': 0, 'last_traded_price': 0}
    
    if order_side == 1:
        positions[symbol]['buy_qty'] += qty
        positions[symbol]['buy_value'] += qty * limit_price
    elif order_side == -1:
        positions[symbol]['sell_qty'] += qty
        positions[symbol]['sell_value'] += qty * limit_price

def get_mtm_data():
    mtm_data = []
    for symbol, details in positions.items():
        buy_qty = details['buy_qty']
        sell_qty = details['sell_qty']
        buy_value = details['buy_value']
        sell_value = details['sell_value']
        last_traded_price = details['last_traded_price']
        
        avg_buy_price = buy_value / buy_qty if buy_qty > 0 else 0
        avg_sell_price = sell_value / sell_qty if sell_qty > 0 else 0
        
        mtm = 0
        if buy_qty > 0:
            mtm = (last_traded_price - avg_buy_price) * buy_qty
        if sell_qty > 0:
            mtm += (avg_sell_price - last_traded_price) * sell_qty

        net_value = buy_value - sell_value
        net_qty = buy_qty - sell_qty

        strike_price_option_type = get_strike_and_option_type(symbol)
        
        mtm_data.append((symbol, strike_price_option_type, net_qty, avg_buy_price, avg_sell_price, net_value, mtm, buy_value, sell_value))
    
    ce_data = [item for item in mtm_data if item[1].endswith('CE')]
    pe_data = [item for item in mtm_data if item[1].endswith('PE')]
    
    ce_data.sort(key=lambda x: int(x[1][:-2]))
    pe_data.sort(key=lambda x: int(x[1][:-2]))
    
    mtm_data_sorted = ce_data + pe_data
    
    return mtm_data_sorted

def check_rejected_orders():
    global positions
    try:
        response = fyers.orderbook()
        
        if response.get("code") == 200 and response.get("s") == "ok":
            orders = response.get("orderBook", [])
            new_positions = {}
            
            for order in orders:
                symbol = order.get("symbol")
                qty = order.get("qty")
                limit_price = order.get("limitPrice")
                last_traded_price = order.get("lp")
                order_side = order.get("side")
                status = order.get("status")
                
                if status == 5:
                    update_position(symbol, qty, limit_price, order_side, new_positions)
                    new_positions[symbol]['last_traded_price'] = last_traded_price
            
            if new_positions:
                positions = new_positions
                
    except Exception as e:
        print(f"An error occurred: {e}")


app = dash.Dash(__name__)


app.layout = html.Div([
    html.H1("Real-Time MTM Values with Buy/Sell Details"),
    dash_table.DataTable(id='mtm-table',
                         columns=[
                             {'name': 'Symbol', 'id': 'symbol'},
                             {'name': 'Strike Price', 'id': 'strike_price'},
                             {'name': 'Net Qty', 'id': 'net_qty'},
                             {'name': 'Net Value', 'id': 'net_value'},
                             {'name': 'MTM', 'id': 'mtm'},
                             {'name': 'Buy Avg', 'id': 'buy_avg'},  
                             {'name': 'Sell Avg', 'id': 'sell_avg'},  
                             {'name': 'Buy Value', 'id': 'buy_value'},
                             {'name': 'Sell Value', 'id': 'sell_value'}
                         ],
                         style_table={'overflowX': 'auto', 'maxWidth': '100%'},
                         style_cell={
                             'textAlign': 'center',  
                             'padding': '8px',
                             'fontSize': 12,
                             'fontFamily': 'Arial'
                         },
                         style_header={
                             'backgroundColor': 'lightgrey',
                             'fontWeight': 'bold',
                             'fontSize': 14,
                             'fontFamily': 'Arial'
                         },
                         style_data_conditional=[
                             {
                                 'if': {'filter_query': '{symbol} = Total'},
                                 'fontWeight': 'bold',
                                 'color': 'darkblue',
                                 'fontSize': '16px',
                             },
                             {
                                 'if': {'column_id': 'net_qty'},
                                 'fontWeight': 'bold',
                                 'fontSize': '14px'
                             },
                             {
                                 'if': {'column_id': 'net_value'},
                                 'fontWeight': 'bold',
                                 'fontSize': '14px'
                             },
                             {
                                 'if': {'column_id': 'mtm'},
                                 'fontWeight': 'bold',
                                 'fontSize': '14px'
                             },
                             {
                                 'if': {'column_id': 'buy_value'},
                                 'fontWeight': 'bold',
                                 'fontSize': '14px'
                             },
                             {
                                 'if': {'column_id': 'sell_value'},
                                 'fontWeight': 'bold',
                                 'fontSize': '14px'
                             },
                             {
                                 'if': {'column_id': 'buy_avg'},
                                 'fontWeight': 'bold',
                                 'fontSize': '14px'
                             },
                             {
                                 'if': {'column_id': 'sell_avg'},
                                 'fontWeight': 'bold',
                                 'fontSize': '14px'
                             },
                             {
                                 'if': {'column_id': 'strike_price'},
                                 'fontFamily': 'Arial Black',
                                 'fontWeight': 'bold',
                                 'fontSize': '14px'
                             }
                         ]
    ),
    dcc.Interval(id='interval-component', interval=1*1000, n_intervals=0)
])

@app.callback(
    Output('mtm-table', 'data'),
    [Input('interval-component', 'n_intervals')]
)
def update_table(n_intervals):
    check_rejected_orders()  # Update positions with new data
    mtm_data = get_mtm_data()
    
    if not mtm_data:
        return []

    symbols, strike_prices, net_qtys, buy_avgs, sell_avgs, net_values, mtm_values, buy_values, sell_values = zip(*mtm_data)

    total_net_qty = sum(net_qtys)
    total_net_value = sum(net_values)
    total_mtm = sum(mtm_values)
    total_buy_value = sum(buy_values)
    total_sell_value = sum(sell_values)
    
    # We do not calculate totals for Buy Avg and Sell Avg
    total_buy_avg = ''
    total_sell_avg = ''

    data = [{'symbol': symbol,
             'strike_price': strike_price,
             'net_qty': net_qty,
             'buy_avg': f'{buy_avg:.2f}',
             'sell_avg': f'{sell_avg:.2f}',
             'net_value': f'{net_value:.2f}',
             'mtm': f'{mtm:.2f}',
             'buy_value': f'{buy_value:.2f}',
             'sell_value': f'{sell_value:.2f}'} for symbol, strike_price, net_qty, buy_avg, sell_avg, net_value, mtm, buy_value, sell_value in mtm_data]

    data.append({'symbol': 'Total',
                 'strike_price': '',
                 'net_qty': total_net_qty,
                 'buy_avg': total_buy_avg,
                 'sell_avg': total_sell_avg,
                 'net_value': f'{total_net_value:.2f}',
                 'mtm': f'{total_mtm:.2f}',
                 'buy_value': f'{total_buy_value:.2f}',
                 'sell_value': f'{total_sell_value:.2f}'})

    return data

if __name__ == '__main__':
    app.run_server(debug=True)
