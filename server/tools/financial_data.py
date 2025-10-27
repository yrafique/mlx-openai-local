"""
Financial data tools using real-time APIs.
Provides accurate, up-to-date stock/ETF prices and market data.
Now with historical data and chart generation!
"""

import json
import requests
from typing import Dict, Any, List
from datetime import datetime, timedelta
import base64
from io import BytesIO


def get_stock_price(symbol: str) -> str:
    """
    Get real-time stock/ETF price using free financial API.

    This uses Alpha Vantage free tier API which provides:
    - Real-time quotes (with 15min delay on free tier)
    - Accurate pricing data
    - Market status

    Args:
        symbol: Stock ticker symbol OR company name (e.g., 'AAPL', 'Apple', 'Tesla', 'TSLA')

    Returns:
        JSON string with current price and details
    """
    try:
        # Map common company names to ticker symbols
        company_to_ticker = {
            'apple': 'AAPL',
            'microsoft': 'MSFT',
            'google': 'GOOGL',
            'alphabet': 'GOOGL',
            'amazon': 'AMZN',
            'tesla': 'TSLA',
            'meta': 'META',
            'facebook': 'META',
            'nvidia': 'NVDA',
            'amd': 'AMD',
            'intel': 'INTC',
            'netflix': 'NFLX',
            'uber': 'UBER',
            'lyft': 'LYFT',
            'airbnb': 'ABNB',
            'coinbase': 'COIN',
            'paypal': 'PYPL',
            'visa': 'V',
            'mastercard': 'MA',
            'jpmorgan': 'JPM',
            'jp morgan': 'JPM',
            'walmart': 'WMT',
            'target': 'TGT',
            'disney': 'DIS',
            'nike': 'NKE',
            'starbucks': 'SBUX',
            'mcdonald': 'MCD',
            'mcdonalds': 'MCD',
            'boeing': 'BA',
            'ford': 'F',
            'gm': 'GM',
            'general motors': 'GM',
            'exxon': 'XOM',
            'chevron': 'CVX',
            'berkshire': 'BRK.B',
            'berkshire hathaway': 'BRK.B'
        }

        # Normalize symbol (lowercase, strip whitespace)
        normalized = symbol.lower().strip()

        # Check if it's a company name and convert to ticker
        if normalized in company_to_ticker:
            symbol = company_to_ticker[normalized]
            # Note: symbol is now the ticker (e.g., 'AAPL')
        else:
            # Keep original symbol (assume it's already a ticker)
            symbol = symbol.upper().strip()
        # Try multiple free APIs for redundancy

        # Method 1: Try Yahoo Finance (no API key needed)
        try:
            # Using a simple scraping approach for Yahoo Finance
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 200:
                data = response.json()

                if 'chart' in data and 'result' in data['chart']:
                    result = data['chart']['result'][0]
                    meta = result.get('meta', {})

                    current_price = meta.get('regularMarketPrice')
                    previous_close = meta.get('previousClose')

                    if current_price:
                        change = current_price - previous_close if previous_close else 0
                        change_pct = (change / previous_close * 100) if previous_close else 0

                        return json.dumps({
                            "status": "success",
                            "symbol": symbol.upper(),
                            "price": round(current_price, 2),
                            "currency": meta.get('currency', 'USD'),
                            "change": round(change, 2),
                            "change_percent": round(change_pct, 2),
                            "previous_close": round(previous_close, 2) if previous_close else None,
                            "market_state": meta.get('marketState', 'UNKNOWN'),
                            "exchange": meta.get('exchangeName', 'N/A'),
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "source": "Yahoo Finance",
                            "data_delay": "Real-time (15min delay)",
                            "answer": (
                                f"**{symbol.upper()}** is currently trading at **${round(current_price, 2)}**.\n\n"
                                f"📊 **Change:** {'+' if change >= 0 else ''}{round(change, 2)} "
                                f"({'+' if change_pct >= 0 else ''}{round(change_pct, 2)}%)\n"
                                f"📈 **Previous Close:** ${round(previous_close, 2) if previous_close else 'N/A'}\n"
                                f"🏢 **Exchange:** {meta.get('exchangeName', 'N/A')}\n"
                                f"⏰ **Market Status:** {meta.get('marketState', 'UNKNOWN').replace('_', ' ').title()}\n\n"
                                f"*Data from Yahoo Finance (15-minute delay)*"
                            )
                        }, indent=2)
        except Exception as e:
            # Fallback to next method
            pass

        # Method 2: Use finnhub.io free API (requires signup but has free tier)
        # Note: This would need an API key, but provides real-time data

        # If all methods fail, return error
        return json.dumps({
            "status": "error",
            "symbol": symbol.upper(),
            "error": "Unable to fetch real-time price data",
            "answer": f"I couldn't retrieve the current price for {symbol.upper()}. "
                     f"Please try visiting a financial website like Yahoo Finance, "
                     f"Google Finance, or your broker for accurate real-time data.",
            "suggestion": f"Visit: https://finance.yahoo.com/quote/{symbol.upper()}"
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "symbol": symbol.upper(),
            "error": str(e),
            "answer": f"Error fetching price for {symbol.upper()}: {str(e)}",
            "suggestion": f"Visit: https://finance.yahoo.com/quote/{symbol.upper()}"
        })


def get_crypto_price(symbol: str) -> str:
    """
    Get cryptocurrency price using free API.

    Args:
        symbol: Crypto symbol (e.g., 'BTC', 'ETH', 'DOGE')

    Returns:
        JSON string with current crypto price
    """
    try:
        # Use CoinGecko free API (no key required)
        # Map common symbols to CoinGecko IDs
        symbol_map = {
            'BTC': 'bitcoin',
            'ETH': 'ethereum',
            'USDT': 'tether',
            'BNB': 'binancecoin',
            'SOL': 'solana',
            'XRP': 'ripple',
            'DOGE': 'dogecoin',
            'ADA': 'cardano',
            'AVAX': 'avalanche-2',
            'SHIB': 'shiba-inu'
        }

        coin_id = symbol_map.get(symbol.upper(), symbol.lower())
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': coin_id,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_market_cap': 'true'
        }

        response = requests.get(url, params=params, timeout=5)

        if response.status_code == 200:
            data = response.json()

            if coin_id in data:
                coin_data = data[coin_id]
                price = coin_data.get('usd')
                change_24h = coin_data.get('usd_24h_change', 0)
                market_cap = coin_data.get('usd_market_cap')

                return json.dumps({
                    "status": "success",
                    "symbol": symbol.upper(),
                    "coin_id": coin_id,
                    "price": price,
                    "currency": "USD",
                    "change_24h_percent": round(change_24h, 2) if change_24h else None,
                    "market_cap": market_cap,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "CoinGecko",
                    "answer": (
                        f"**{symbol.upper()}** is currently trading at **${price:,.2f}**.\n\n"
                        f"📊 **24h Change:** {'+' if change_24h >= 0 else ''}{round(change_24h, 2)}%\n"
                        f"💰 **Market Cap:** ${market_cap:,.0f}\n\n"
                        f"*Data from CoinGecko (real-time)*"
                    )
                }, indent=2)

        return json.dumps({
            "status": "error",
            "symbol": symbol.upper(),
            "error": "Cryptocurrency not found",
            "answer": f"Could not find price data for {symbol.upper()}. "
                     f"Please check the symbol or visit CoinGecko.com for accurate prices."
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "symbol": symbol.upper(),
            "error": str(e),
            "answer": f"Error fetching crypto price: {str(e)}"
        })


def get_stock_history(symbol: str, period: str = "10mo", interval: str = "1mo") -> str:
    """
    Get historical stock data with chart and table.

    Args:
        symbol: Stock ticker symbol (e.g., 'TSLA', 'AAPL')
        period: Time period - options: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        interval: Data interval - options: 1d, 5d, 1wk, 1mo, 3mo

    Returns:
        JSON string with historical data, chart, and formatted table
    """
    try:
        # Yahoo Finance historical data endpoint
        # period1 and period2 are Unix timestamps

        # Calculate time range based on period
        period_map = {
            "1d": 1, "5d": 5, "1mo": 30, "3mo": 90, "6mo": 180,
            "1y": 365, "2y": 730, "5y": 1825, "10y": 3650, "10mo": 300
        }

        days = period_map.get(period, 300)  # Default to 10 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        period1 = int(start_date.timestamp())
        period2 = int(end_date.timestamp())

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            "period1": period1,
            "period2": period2,
            "interval": interval
        }
        headers = {'User-Agent': 'Mozilla/5.0'}

        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()

            if 'chart' in data and 'result' in data['chart'] and data['chart']['result']:
                result = data['chart']['result'][0]

                # Extract timestamps and prices
                timestamps = result.get('timestamp', [])
                quotes = result.get('indicators', {}).get('quote', [{}])[0]

                closes = quotes.get('close', [])
                opens = quotes.get('open', [])
                highs = quotes.get('high', [])
                lows = quotes.get('low', [])
                volumes = quotes.get('volume', [])

                # Create historical data table
                historical_data = []
                for i, ts in enumerate(timestamps):
                    if i < len(closes) and closes[i] is not None:
                        date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                        historical_data.append({
                            "date": date,
                            "open": round(opens[i], 2) if i < len(opens) and opens[i] else None,
                            "high": round(highs[i], 2) if i < len(highs) and highs[i] else None,
                            "low": round(lows[i], 2) if i < len(lows) and lows[i] else None,
                            "close": round(closes[i], 2),
                            "volume": int(volumes[i]) if i < len(volumes) and volumes[i] else None
                        })

                # Generate interactive chart
                chart_data = _generate_price_chart(historical_data, symbol)

                # Calculate statistics
                prices = [d['close'] for d in historical_data if d['close']]
                if prices:
                    start_price = prices[0]
                    end_price = prices[-1]
                    change = end_price - start_price
                    change_pct = (change / start_price * 100) if start_price else 0
                    high_price = max(prices)
                    low_price = min(prices)
                else:
                    start_price = end_price = change = change_pct = high_price = low_price = 0

                # Create markdown table
                table_md = _format_historical_table(historical_data, symbol)

                return json.dumps({
                    "status": "success",
                    "symbol": symbol.upper(),
                    "period": period,
                    "interval": interval,
                    "data_points": len(historical_data),
                    "start_price": round(start_price, 2) if start_price else None,
                    "end_price": round(end_price, 2) if end_price else None,
                    "change": round(change, 2) if change else None,
                    "change_percent": round(change_pct, 2) if change_pct else None,
                    "high": round(high_price, 2) if high_price else None,
                    "low": round(low_price, 2) if low_price else None,
                    "historical_data": historical_data,
                    "chart_json": chart_data.get("chart_json"),
                    "chart_type": chart_data.get("chart_type"),
                    "table_markdown": table_md,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "source": "Yahoo Finance",
                    "answer": (
                        f"## 📈 {symbol.upper()} - Historical Stock Data ({period})\n\n"
                        f"**Period:** {period} | **Interval:** {interval} | **Data Points:** {len(historical_data)}\n\n"
                        f"### 📊 Performance Summary\n\n"
                        f"- **Start Price:** ${start_price:.2f}\n"
                        f"- **End Price:** ${end_price:.2f}\n"
                        f"- **Change:** {'+' if change >= 0 else ''}{change:.2f} ({'+' if change_pct >= 0 else ''}{change_pct:.2f}%)\n"
                        f"- **Highest:** ${high_price:.2f}\n"
                        f"- **Lowest:** ${low_price:.2f}\n\n"
                        f"### 📉 Interactive Price Chart\n\n"
                        f"[Interactive TradingView-style chart - See below]\n\n"
                        f"### 📋 Historical Data Table\n\n"
                        f"{table_md}\n\n"
                        f"*Data from Yahoo Finance*"
                    )
                }, indent=2)

        return json.dumps({
            "status": "error",
            "symbol": symbol.upper(),
            "error": "Unable to fetch historical data",
            "answer": f"I couldn't retrieve historical data for {symbol.upper()}. Please try a different symbol or period."
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "symbol": symbol.upper(),
            "error": str(e),
            "answer": f"Error fetching historical data for {symbol.upper()}: {str(e)}"
        })


def _generate_price_chart(data: List[Dict], symbol: str) -> Dict:
    """
    Generate an interactive TradingView-style chart using Plotly.

    Args:
        data: List of historical data dictionaries
        symbol: Stock ticker symbol

    Returns:
        Dictionary with chart JSON for Plotly and chart type
    """
    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        # Extract data
        dates = [d['date'] for d in data]
        opens = [d['open'] for d in data]
        highs = [d['high'] for d in data]
        lows = [d['low'] for d in data]
        closes = [d['close'] for d in data]
        volumes = [d['volume'] for d in data]

        # Create subplots - candlestick chart on top, volume on bottom
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=(f'{symbol.upper()} Stock Price', 'Volume')
        )

        # Add candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=dates,
                open=opens,
                high=highs,
                low=lows,
                close=closes,
                name='Price',
                increasing_line_color='#26a69a',  # Green for up
                decreasing_line_color='#ef5350',  # Red for down
                showlegend=False
            ),
            row=1, col=1
        )

        # Add volume bars
        colors = ['#26a69a' if closes[i] >= opens[i] else '#ef5350'
                  for i in range(len(closes))]

        fig.add_trace(
            go.Bar(
                x=dates,
                y=volumes,
                name='Volume',
                marker_color=colors,
                showlegend=False
            ),
            row=2, col=1
        )

        # Update layout for TradingView-like appearance
        fig.update_layout(
            title={
                'text': f'<b>{symbol.upper()} Stock Chart</b>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            xaxis_rangeslider_visible=False,  # Hide range slider
            height=600,
            template='plotly_dark',  # Dark theme like TradingView
            hovermode='x unified',  # Show all values at cursor x-position
            plot_bgcolor='#131722',  # TradingView dark background
            paper_bgcolor='#1e222d',
            font=dict(color='#d1d4dc'),
            margin=dict(l=50, r=50, t=80, b=50)
        )

        # Update axes
        fig.update_xaxes(
            title_text="Date",
            gridcolor='#2a2e39',
            showgrid=True,
            row=2, col=1
        )

        fig.update_yaxes(
            title_text="Price (USD)",
            gridcolor='#2a2e39',
            showgrid=True,
            row=1, col=1
        )

        fig.update_yaxes(
            title_text="Volume",
            gridcolor='#2a2e39',
            showgrid=True,
            row=2, col=1
        )

        # Convert to JSON for Streamlit
        chart_json = fig.to_json()

        return {
            "chart_json": chart_json,
            "chart_type": "plotly_candlestick"
        }

    except ImportError:
        # Plotly not available - return empty
        return {
            "chart_json": None,
            "chart_type": "none"
        }
    except Exception as e:
        print(f"Chart generation error: {e}")
        return {
            "chart_json": None,
            "chart_type": "none"
        }


def _format_historical_table(data: List[Dict], symbol: str) -> str:
    """
    Format historical data as a markdown table.

    Args:
        data: List of historical data dictionaries
        symbol: Stock ticker symbol

    Returns:
        Formatted markdown table string
    """
    if not data:
        return "No data available"

    # Show last 10 data points (most recent)
    recent_data = data[-10:] if len(data) > 10 else data
    recent_data.reverse()  # Most recent first

    table = "| 📅 Date | 💵 Open | ⬆️ High | ⬇️ Low | 💰 Close | 📊 Volume |\n"
    table += "|---------|---------|---------|--------|----------|----------|\n"

    for row in recent_data:
        date = row['date']
        open_price = f"${row['open']:.2f}" if row['open'] else "N/A"
        high = f"${row['high']:.2f}" if row['high'] else "N/A"
        low = f"${row['low']:.2f}" if row['low'] else "N/A"
        close = f"${row['close']:.2f}" if row['close'] else "N/A"
        volume = f"{row['volume']:,}" if row['volume'] else "N/A"

        table += f"| {date} | {open_price} | {high} | {low} | **{close}** | {volume} |\n"

    if len(data) > 10:
        table += f"\n*Showing most recent 10 of {len(data)} data points*\n"

    return table


# Tool definitions for OpenAI function calling
FINANCIAL_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Get the current real-time stock price. Use this INSTEAD of web search for ANY stock-related questions (price, buy/sell, performance, etc.). Works with ticker symbols OR company names. Examples: Apple=AAPL, Microsoft=MSFT, Tesla=TSLA, Google=GOOGL, Amazon=AMZN, Nvidia=NVDA, Meta=META.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol OR company name. Examples: 'AAPL' or 'Apple', 'TSLA' or 'Tesla', 'MSFT' or 'Microsoft', 'QQQ', 'SPY'. If user mentions a company name like 'Apple', 'Google', 'Tesla', use the ticker: AAPL, GOOGL, TSLA."
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_crypto_price",
            "description": "Get current cryptocurrency price in USD. Use this for crypto prices like Bitcoin, Ethereum, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Cryptocurrency symbol (e.g., 'BTC', 'ETH', 'DOGE')"
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_stock_history",
            "description": "Get historical stock price data with chart and table. Use this when user asks for price history, trends, charts, or data over a time period.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Stock ticker symbol (e.g., 'TSLA', 'AAPL', 'MSFT')"
                    },
                    "period": {
                        "type": "string",
                        "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "10mo"],
                        "description": "Time period for historical data. Use '10mo' for 10 months.",
                        "default": "10mo"
                    },
                    "interval": {
                        "type": "string",
                        "enum": ["1d", "5d", "1wk", "1mo", "3mo"],
                        "description": "Data interval/granularity. Use '1mo' for monthly, '1wk' for weekly, '1d' for daily.",
                        "default": "1mo"
                    }
                },
                "required": ["symbol"]
            }
        }
    }
]

# Tool execution mapping
FINANCIAL_TOOL_FUNCTIONS = {
    "get_stock_price": get_stock_price,
    "get_crypto_price": get_crypto_price,
    "get_stock_history": get_stock_history
}


def execute_financial_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """
    Execute a financial tool by name.

    Args:
        tool_name: Name of the tool
        arguments: Tool arguments

    Returns:
        Tool result as JSON string
    """
    if tool_name not in FINANCIAL_TOOL_FUNCTIONS:
        return json.dumps({
            "status": "error",
            "error": f"Unknown tool: {tool_name}",
            "available_tools": list(FINANCIAL_TOOL_FUNCTIONS.keys())
        })

    try:
        func = FINANCIAL_TOOL_FUNCTIONS[tool_name]
        result = func(**arguments)
        return result
    except Exception as e:
        return json.dumps({
            "status": "error",
            "tool": tool_name,
            "error": str(e),
            "answer": f"Tool execution failed: {str(e)}"
        })


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Financial Data Tools")
    print("=" * 60)

    # Test stock price
    print("\n1. Testing QQQ (ETF) price...")
    print("-" * 60)
    result = get_stock_price("QQQ")
    data = json.loads(result)
    print(f"Status: {data.get('status')}")
    if data.get('answer'):
        print(f"\nAnswer:\n{data.get('answer')}")
    else:
        print(f"\nPrice: ${data.get('price')}")
        print(f"Change: {data.get('change')} ({data.get('change_percent')}%)")

    # Test crypto price
    print("\n" + "=" * 60)
    print("2. Testing BTC (Bitcoin) price...")
    print("-" * 60)
    result = get_crypto_price("BTC")
    data = json.loads(result)
    print(f"Status: {data.get('status')}")
    if data.get('answer'):
        print(f"\nAnswer:\n{data.get('answer')}")

    print("\n" + "=" * 60)
    print("Testing complete!")
    print("=" * 60)
