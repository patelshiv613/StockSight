import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])
server = app.server

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>StockSight - Stock Market Analytics</title>
        {%favicon%}
        {%css%}
        <style>
            .card {
                background-color: #2b2b2b;
                border: 1px solid #404040;
            }
            .card-header {
                background-color: #343a40;
                border-bottom: 1px solid #404040;
            }
            .stock-input {
                background-color: #2b2b2b;
                border: 1px solid #404040;
                color: white;
            }
            .stock-input:focus {
                background-color: #2b2b2b;
                border-color: #007bff;
                color: white;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("StockSight", className="text-center text-primary my-4"),
            html.H4("Interactive Stock Market Analytics", className="text-center text-light mb-4")
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Stock Search"),
                dbc.CardBody([
                    dbc.Input(
                        id="stock-input",
                        type="text",
                        placeholder="Enter stock symbol (e.g., AAPL)",
                        className="stock-input mb-3"
                    ),
                    dbc.Button("Analyze", id="analyze-button", color="primary", className="w-100")
                ])
            ], className="mb-4")
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Stock Analysis"),
                dbc.CardBody([
                    dcc.Graph(id="stock-chart", style={"height": "500px"}),
                    html.Div(id="stock-info", className="mt-4")
                ])
            ])
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Investment Recommendation"),
                dbc.CardBody(id="recommendation-card")
            ])
        ], width=12)
    ], className="mt-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Company Financials"),
                dbc.CardBody(id="financials-card")
            ])
        ], width=12)
    ], className="mt-4")
], fluid=True, className="py-4")

def get_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1y")
        info = stock.info
        return hist, info
    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        return None, None

def calculate_recommendation(info):
    if not info:
        return "Unable to calculate recommendation"
    
    try:
        scores = {
            'valuation': 0,
            'profitability': 0,
            'growth': 0,
            'financial_health': 0,
            'market_sentiment': 0
        }
        
        pe_ratio = info.get('trailingPE', 0)
        forward_pe = info.get('forwardPE', 0)
        price_to_book = info.get('priceToBook', 0)
        price_to_sales = info.get('priceToSalesTrailing12Months', 0)
        
        if 0 < pe_ratio < 20:
            scores['valuation'] += 7
        elif 20 <= pe_ratio < 30:
            scores['valuation'] += 4
        elif pe_ratio > 30:
            scores['valuation'] -= 2
            
        if 0 < forward_pe < pe_ratio * 1.1: 
            scores['valuation'] += 4
        elif forward_pe > pe_ratio * 1.5:
            scores['valuation'] -= 2
            
        if 0 < price_to_book < 3: 
            scores['valuation'] += 5
        elif 3 <= price_to_book < 5:
            scores['valuation'] += 2
        elif price_to_book > 8:
            scores['valuation'] -= 2
            
        if 0 < price_to_sales < 4: 
            scores['valuation'] += 4
        elif 4 <= price_to_sales < 6:
            scores['valuation'] += 2
        elif price_to_sales > 10:
            scores['valuation'] -= 2

        profit_margins = info.get('profitMargins', 0)
        operating_margins = info.get('operatingMargins', 0)
        roe = info.get('returnOnEquity', 0)
        roa = info.get('returnOnAssets', 0)
        
        if profit_margins > 0.15:  
            scores['profitability'] += 5
        elif profit_margins > 0.08:
            scores['profitability'] += 3
        elif profit_margins < 0:
            scores['profitability'] -= 2
            
        if operating_margins > 0.15:  
            scores['profitability'] += 5
        elif operating_margins > 0.08:
            scores['profitability'] += 3
        elif operating_margins < 0:
            scores['profitability'] -= 2
            
        if roe > 0.15: 
            scores['profitability'] += 5
        elif roe > 0.08:
            scores['profitability'] += 3
        elif roe < 0:
            scores['profitability'] -= 2
            
        if roa > 0.08: 
            scores['profitability'] += 5
        elif roa > 0.04:
            scores['profitability'] += 3
        elif roa < 0:
            scores['profitability'] -= 2

        revenue_growth = info.get('revenueGrowth', 0)
        earnings_growth = info.get('earningsGrowth', 0)
        earnings_quarterly_growth = info.get('earningsQuarterlyGrowth', 0)
        
        if revenue_growth > 0.15:  
            scores['growth'] += 7
        elif revenue_growth > 0.08:
            scores['growth'] += 4
        elif revenue_growth < -0.1:  
            scores['growth'] -= 2
            
        if earnings_growth > 0.15: 
            scores['growth'] += 7
        elif earnings_growth > 0.08:
            scores['growth'] += 4
        elif earnings_growth < -0.1: 
            scores['growth'] -= 2
            
       
        if earnings_quarterly_growth > 0.15:  
            scores['growth'] += 6
        elif earnings_quarterly_growth > 0.08:
            scores['growth'] += 3
        elif earnings_quarterly_growth < -0.1: 
            scores['growth'] -= 2

        current_ratio = info.get('currentRatio', 0)
        debt_to_equity = info.get('debtToEquity', 0)
        quick_ratio = info.get('quickRatio', 0)
        
       
        if current_ratio > 1.5:  
            scores['financial_health'] += 7
        elif current_ratio > 1:
            scores['financial_health'] += 4
        elif current_ratio < 0.8:
            scores['financial_health'] -= 2
            
        if debt_to_equity < 1:  
            scores['financial_health'] += 7
        elif debt_to_equity < 1.5:
            scores['financial_health'] += 4
        elif debt_to_equity > 2.5:  
            scores['financial_health'] -= 2
            
        if quick_ratio > 1.2: 
            scores['financial_health'] += 6
        elif quick_ratio > 0.8:
            scores['financial_health'] += 3
        elif quick_ratio < 0.5: 
            scores['financial_health'] -= 2

        
        beta = info.get('beta', 0)
        dividend_yield = info.get('dividendYield', 0)
        short_ratio = info.get('shortRatio', 0)
        
       
        if 0.8 <= beta <= 1.2:
            scores['market_sentiment'] += 7
        elif 0.5 <= beta <= 1.5:
            scores['market_sentiment'] += 4
        elif beta > 2:
            scores['market_sentiment'] -= 2
            
        
        if dividend_yield > 0.03:  
            scores['market_sentiment'] += 7
        elif dividend_yield > 0.015:
            scores['market_sentiment'] += 4
        elif dividend_yield > 0:
            scores['market_sentiment'] += 2
            
        
        if short_ratio < 3: 
            scores['market_sentiment'] += 6
        elif short_ratio < 5:
            scores['market_sentiment'] += 3
        elif short_ratio > 10:  
            scores['market_sentiment'] -= 2

       
        total_score = sum(scores.values())
        
        
        recommendation = {
            'score': total_score,
            'category_scores': scores,
            'rating': '',
            'details': []
        }
        
       
        if total_score >= 60: 
            recommendation['rating'] = "Strong Buy"
        elif total_score >= 40:
            recommendation['rating'] = "Buy"
        elif total_score >= 20:
            recommendation['rating'] = "Hold"
        elif total_score >= 0:
            recommendation['rating'] = "Sell"
        else:
            recommendation['rating'] = "Strong Sell"
            
        
        for category, score in scores.items():
            if score >= 15:
                recommendation['details'].append(f"Strong {category.replace('_', ' ').title()}")
            elif score >= 10:
                recommendation['details'].append(f"Good {category.replace('_', ' ').title()}")
            elif score < 0:
                recommendation['details'].append(f"Poor {category.replace('_', ' ').title()}")
                
        return recommendation
        
    except Exception as e:
        print(f"Error calculating recommendation: {str(e)}")
        return "Unable to calculate recommendation"

@app.callback(
    [Output('stock-chart', 'figure'),
     Output('stock-info', 'children'),
     Output('recommendation-card', 'children'),
     Output('financials-card', 'children')],
    [Input('analyze-button', 'n_clicks')],
    [State('stock-input', 'value')]
)
def update_stock_analysis(n_clicks, symbol):
    if not n_clicks or not symbol:
        return {}, {}, {}, {}
    
    try:
        stock_data = get_stock_data(symbol)
        if not stock_data:
            return {}, {}, {}, {}
            
        fig = go.Figure(data=[go.Candlestick(
            x=stock_data[0].index,
            open=stock_data[0]['Open'],
            high=stock_data[0]['High'],
            low=stock_data[0]['Low'],
            close=stock_data[0]['Close']
        )])
        
        fig.update_layout(
            title=f'{symbol} Stock Price',
            yaxis_title='Price',
            template='plotly_dark',
            xaxis_rangeslider_visible=False
        )
        
        info = stock_data[1]
        if not info:
            return fig, {}, {}, {}
            
        stock_info = html.Div([
            html.H4('Company Information'),
            html.P(f"Current Price: ${info.get('currentPrice', 'N/A')}"),
            html.P(f"Market Cap: ${info['marketCap']:,.2f}" if 'marketCap' in info and info['marketCap'] is not None else 'N/A'),
            html.P(f"52 Week High: ${info.get('fiftyTwoWeekHigh', 'N/A')}"),
            html.P(f"52 Week Low: ${info.get('fiftyTwoWeekLow', 'N/A')}"),
            html.P(f"Volume: {info['volume']:,}" if 'volume' in info and info['volume'] is not None else 'N/A'),
            html.P(f"P/E Ratio: {info.get('trailingPE', 'N/A')}"),
            html.P(f"Dividend Yield: {info.get('dividendYield', 'N/A')}%")
        ])
        
        recommendation = calculate_recommendation(info)
        if isinstance(recommendation, dict):
            recommendation_div = html.Div([
                html.H4('Investment Recommendation'),
                html.H3(recommendation['rating'], style={'color': 'green' if recommendation['score'] >= 40 else 'red'}),
                html.P(f"Total Score: {recommendation['score']}/100"),
                html.H5('Category Scores:'),
                html.P(f"Valuation: {recommendation['category_scores']['valuation']}/20"),
                html.P(f"Profitability: {recommendation['category_scores']['profitability']}/20"),
                html.P(f"Growth: {recommendation['category_scores']['growth']}/20"),
                html.P(f"Financial Health: {recommendation['category_scores']['financial_health']}/20"),
                html.P(f"Market Sentiment: {recommendation['category_scores']['market_sentiment']}/20"),
                html.H5('Strengths:'),
                html.Ul([html.Li(detail) for detail in recommendation['details']])
            ])
        else:
            recommendation_div = html.Div([
                html.H4('Investment Recommendation'),
                html.P(recommendation)
            ])
        
        financials = html.Div([
            html.H4("Key Financial Metrics"),
            html.Div([
                html.Div([
                    html.H6("Valuation"),
                    html.P(f"P/E Ratio: {info.get('trailingPE', 'N/A')}"),
                    html.P(f"Forward P/E: {info.get('forwardPE', 'N/A')}"),
                    html.P(f"P/B Ratio: {info.get('priceToBook', 'N/A')}")
                ], className="col-md-3"),
                html.Div([
                    html.H6("Profitability"),
                    html.P(f"Profit Margin: {info['profitMargins']*100:.2f}%" if 'profitMargins' in info and info['profitMargins'] is not None else "N/A"),
                    html.P(f"Operating Margin: {info['operatingMargins']*100:.2f}%" if 'operatingMargins' in info and info['operatingMargins'] is not None else "N/A"),
                    html.P(f"ROE: {info['returnOnEquity']*100:.2f}%" if 'returnOnEquity' in info and info['returnOnEquity'] is not None else "N/A")
                ], className="col-md-3"),
                html.Div([
                    html.H6("Growth"),
                    html.P(f"Revenue Growth: {info['revenueGrowth']*100:.2f}%" if 'revenueGrowth' in info and info['revenueGrowth'] is not None else "N/A"),
                    html.P(f"Earnings Growth: {info['earningsGrowth']*100:.2f}%" if 'earningsGrowth' in info and info['earningsGrowth'] is not None else "N/A"),
                    html.P(f"Quarterly Growth: {info['earningsQuarterlyGrowth']*100:.2f}%" if 'earningsQuarterlyGrowth' in info and info['earningsQuarterlyGrowth'] is not None else "N/A")
                ], className="col-md-3"),
                html.Div([
                    html.H6("Financial Health"),
                    html.P(f"Current Ratio: {info.get('currentRatio', 'N/A')}"),
                    html.P(f"Debt/Equity: {info.get('debtToEquity', 'N/A')}"),
                    html.P(f"Quick Ratio: {info.get('quickRatio', 'N/A')}")
                ], className="col-md-3")
            ], className="row")
        ])
        
        return fig, stock_info, recommendation_div, financials
        
    except Exception as e:
        print(f"Error in update_stock_analysis: {str(e)}")
        return {}, {}, {}, {}

if __name__ == '__main__':
    app.run_server(debug=True) 
