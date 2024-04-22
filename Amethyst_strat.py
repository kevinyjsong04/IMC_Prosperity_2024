import numpy as np
import pandas as pd
import json
from datamodel import Order, OrderDepth, ProsperityEncoder, TradingState, Symbol, Listing, Trade, Observation
from typing import Any, Dict, List
import jsonpickle


##################################################################################

class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(self.to_json([
            self.compress_state(state, ""),
            self.compress_orders(orders),
            conversions,
            "",
            "",
        ]))

        # We truncate state.traderData, trader_data, and self.logs to the same max. length to fit the log limit
        max_item_length = (self.max_log_length - base_length) // 3

        print(self.to_json([
            self.compress_state(state, self.truncate(state.traderData, max_item_length)),
            self.compress_orders(orders),
            conversions,
            self.truncate(trader_data, max_item_length),
            self.truncate(self.logs, max_item_length),
        ]))

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing["symbol"], listing["product"], listing["denomination"]])

        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append([
                    trade.symbol,
                    trade.price,
                    trade.quantity,
                    trade.buyer,
                    trade.seller,
                    trade.timestamp,
                ])

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sunlight,
                observation.humidity,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value

        return value[:max_length - 3] + "..."

logger = Logger()





class Trader:
    def __init__(self):
        self.holdings = 0
        self.last_trade = 0

    def run(self, state: TradingState) -> Dict[Symbol, List[Order]]:

        """
        Takes all buy and sell orders for all symbols as an input,
        and outputs a list of orders to be sent
        """
        
        result = {}
        
        
        for product in state.order_depths.keys():
            if product == 'AMETHYSTS':
                spread = 1
                open_spread = 3
                start_trading = 0
                position_limit = 20
                position_spread = 15
                current_position = state.position.get(product,0)
                order_depth: OrderDepth = state.order_depths[product]
                orders: list[Order] = []
                
                    
                if state.timestamp >= start_trading:
                    if len(order_depth.sell_orders) > 0:
                        best_ask = min(order_depth.sell_orders.keys())
                        
                        if best_ask <= 10000-spread:
                            best_ask_volume = order_depth.sell_orders[best_ask]
                            print("BEST_ASK_VOLUME", best_ask_volume)
                        else:
                            best_ask_volume = 0
                    else:
                        best_ask_volume = 0
                         
                    if len(order_depth.buy_orders) > 0:
                        best_bid = max(order_depth.buy_orders.keys())
                    
                        if best_bid >= 10000+spread:
                            best_bid_volume = order_depth.buy_orders[best_bid]
                            print("BEST_BID_VOLUME", best_bid_volume)
                        else:
                            best_bid_volume = 0 
                    else:
                        best_bid_volume = 0
                    
                    if current_position - best_ask_volume > position_limit:
                        best_ask_volume = current_position - position_limit
                        open_ask_volume = 0
                    else:
                        open_ask_volume = current_position - position_spread - best_ask_volume
                        
                    if current_position - best_bid_volume < -position_limit:
                        best_bid_volume = current_position + position_limit
                        open_bid_volume = 0
                    else:
                        open_bid_volume = current_position + position_spread - best_bid_volume
                        
                    if -open_ask_volume < 0:
                        open_ask_volume = 0         
                    if open_bid_volume < 0:
                        open_bid_volume = 0

                    if -best_ask_volume > 0:
                        print("BUY", product, str(-best_ask_volume) + "x", best_ask)
                        orders.append(Order(product, best_ask, -best_ask_volume))
                    if -open_ask_volume > 0:
                        print("BUY", product, str(-open_ask_volume) + "x", 10000-open_spread)
                        orders.append(Order(product, 10000-open_spread, -open_ask_volume))

                    if best_bid_volume > 0:
                        print("SELL", product, str(best_bid_volume) + "x", best_bid)
                        orders.append(Order(product, best_bid, -best_bid_volume))
                    if open_bid_volume > 0:
                        print("SELL", product, str(open_bid_volume) + "x", 10000+open_spread)
                        orders.append(Order(product, 10000+open_spread, -open_bid_volume))
                        
                result[product] = orders

        logger.flush(state, result, 0, state.traderData) # type: ignore
        return result, 0, state.traderData