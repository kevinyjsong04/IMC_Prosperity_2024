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

##################################################################################

class Trader:
    def __init__(self):
        self.basket_prev = None
        self.chocolate_prev = None
        self.strawberry_prev = None
        self.rose_prev = None
        self.etf_returns = np.array([])
        self.asset_returns = np.array([])

    def run(self, state: TradingState) -> Dict[Symbol, List[Order]]:
        result = {}
        
        for product in state.order_depths.keys():
            orders_gift_basket: list[Order] = []
            orders_chocolate: list[Order] = []
            orders_strawberry: list[Order] = []
            orders_rose: list[Order] = []

            if product == 'GIFT_BASKET':
                # current positions
                basket_pos = state.position.get("GIFT_BASKET", 0)
                chocolate_pos = state.position.get("CHOCOLATE", 0)
                strawberry_pos = state.position.get("STRAWBERRY", 0)
                rose_pos = state.position.get("ROSE", 0)

##################################################################################
                
                basket_buy_orders: Dict[int, int] = state.order_depths[product].buy_orders
                basket_sell_orders: Dict[int, int] = state.order_depths[product].sell_orders

                basket_best_bid: float = max(basket_buy_orders)
                basket_best_ask: float = min(basket_sell_orders)

                # Finding price / NAV ratio
                basket_price: float = (basket_best_bid + basket_best_ask) / 2

                chocolate_buy_orders: Dict[int, int] = state.order_depths['CHOCOLATE'].buy_orders
                chocolate_sell_orders: Dict[int, int] = state.order_depths['CHOCOLATE'].sell_orders

                chocolate_best_bid: float = max(chocolate_buy_orders)
                chocolate_best_ask: float = min(chocolate_sell_orders)

                chocolate_price: float = (chocolate_best_bid + chocolate_best_ask) / 2
 
                strawberry_buy_orders: Dict[int, int] = state.order_depths['STRAWBERRIES'].buy_orders
                strawberry_sell_orders: Dict[int, int] = state.order_depths['STRAWBERRIES'].sell_orders

                strawberry_best_bid: float = max(strawberry_buy_orders)
                strawberry_best_ask: float = min(strawberry_sell_orders)

                strawberry_price: float = (strawberry_best_bid + strawberry_best_ask) / 2

                rose_buy_orders: Dict[int, int] = state.order_depths['ROSES'].buy_orders
                rose_sell_orders: Dict[int, int] = state.order_depths['ROSES'].sell_orders

                rose_best_bid: float = max(rose_buy_orders)
                rose_best_ask: float = min(rose_sell_orders)

                rose_price: float = (rose_best_bid + rose_best_ask) / 2

                est_price: float = 6 * strawberry_price + 4 * chocolate_price + rose_price

                price_nav_ratio: float = basket_price / est_price

##################################################################################

                self.etf_returns = np.append(self.etf_returns, basket_price)
                self.asset_returns = np.append(self.asset_returns, est_price)

                rolling_mean_etf = np.mean(self.etf_returns[-10:])
                rolling_std_etf = np.std(self.etf_returns[-10:])

                rolling_mean_asset = np.mean(self.asset_returns[-10:])
                rolling_std_asset = np.std(self.asset_returns[-10:])

                z_score_etf = (self.etf_returns[-1] - rolling_mean_etf) / rolling_std_etf
                z_score_asset = (self.asset_returns[-1] - rolling_mean_asset) / rolling_std_asset

                z_score_diff = z_score_etf - z_score_asset

                logger.print(f'ZSCORE DIFF = {z_score_diff}')

                # implement stop loss
                # stop_loss = 0.01

                #if price_nav_ratio < self.basket_pnav_ratio - self.basket_eps:
                if z_score_diff < -2:
                    # stop_loss_price = self.etf_returns[-2] 


                    # ETF is undervalued! -> we buy ETF and sell individual assets!
                    # Finds volume to buy that is within position limit
                    #basket_best_ask_vol = max(basket_pos-self.basket_limit, state.order_depths['gift_basket'].sell_orders[basket_best_ask])
                    basket_best_ask_vol = state.order_depths['GIFT_BASKET'].sell_orders[basket_best_ask]
                    chocolate_best_bid_vol =  state.order_depths['CHOCOLATE'].buy_orders[chocolate_best_bid]
                    strawberry_best_bid_vol = state.order_depths['STRAWBERRIES'].buy_orders[strawberry_best_bid]
                    rose_best_bid_vol = state.order_depths['ROSES'].buy_orders[rose_best_bid]

                    limit_mult = min(-basket_best_ask_vol, rose_best_bid_vol, 
                                     round(chocolate_best_bid_vol / 4), round(strawberry_best_bid_vol / 6))

                    logger.print(f'LIMIT: {limit_mult}')

                    logger.print("BUY", 'GIFT_BASKET', limit_mult, "x", basket_best_ask)
                    orders_gift_basket.append(Order('GIFT_BASKET', basket_best_ask, limit_mult))
                    
                     
                #elif price_nav_ratio > self.basket_pnav_ratio + self.basket_eps:
                elif z_score_diff > 2:
                    # ETF is overvalued! -> we sell ETF and buy individual assets!
                    # Finds volume to buy that is within position limit
                    #basket_best_bid_vol = min(self.basket_limit-basket_pos, state.order_depths['gift_basket'].buy_orders[basket_best_bid])
                    basket_best_bid_vol = state.order_depths['GIFT_BASKET'].buy_orders[basket_best_bid]
                    chocolate_best_ask_vol = state.order_depths['CHOCOLATE'].sell_orders[chocolate_best_ask]
                    strawberry_best_ask_vol = state.order_depths['STRAWBERRIES'].sell_orders[strawberry_best_ask]
                    rose_best_ask_vol = state.order_depths['ROSES'].sell_orders[rose_best_ask]

                    limit_mult = min(basket_best_bid_vol, -rose_best_ask_vol, 
                                     round(-chocolate_best_ask_vol / 2), round(-strawberry_best_ask_vol / 4))

                    logger.print(f'LIMIT: {limit_mult}')

                    logger.print("SELL", 'GIFT_BASKET', limit_mult, "x", basket_best_bid)
                    orders_gift_basket.append(Order('GIFT_BASKET', basket_best_bid, -limit_mult))

                result['GIFT_BASKET'] = orders_gift_basket
                result['CHOCOLATE'] = orders_chocolate
                result['STRAWBERRIES'] = orders_strawberry
                result['ROSES'] = orders_rose
        logger.flush(state, result, 0, state.traderData) # type: ignore
        return result, 0, state.traderData