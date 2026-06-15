"""Toy data browser widget for the DearCyFi demo.

Replace this module with a real database-backed browser when integrating live data.
"""

import dearcygui as dcg


# =========================
# TOY DATA PLACEHOLDER ONLY
# Replace this catalog with real symbol metadata from Postgres.
# =========================
TOY_DATA_TREE = {
    "Mega Cap Tech": {
        "AAPL": {
            "description": "Steady large-cap uptrend with moderate volatility.",
            "base_price": 190.0,
            "volatility": 0.011,
            "seed": 11,
            "start_date": "2024-01-02",
        },
        "MSFT": {
            "description": "Higher price level with smoother swings.",
            "base_price": 420.0,
            "volatility": 0.009,
            "seed": 17,
            "start_date": "2024-02-05",
        },
        "NVDA": {
            "description": "Fast-moving momentum profile with wider ranges.",
            "base_price": 870.0,
            "volatility": 0.023,
            "seed": 29,
            "start_date": "2024-03-18",
        },
    },
    "Energy": {
        "XOM": {
            "description": "Lower-volatility commodity-linked trend.",
            "base_price": 108.0,
            "volatility": 0.008,
            "seed": 41,
            "start_date": "2024-01-08",
        },
        "CVX": {
            "description": "Energy name with slightly larger pullbacks.",
            "base_price": 152.0,
            "volatility": 0.010,
            "seed": 53,
            "start_date": "2024-04-01",
        },
    },
    "Index ETFs": {
        "SPY": {
            "description": "Broad-market baseline series for comparisons.",
            "base_price": 510.0,
            "volatility": 0.007,
            "seed": 67,
            "start_date": "2024-01-02",
        },
        "QQQ": {
            "description": "Index proxy with stronger tech-style swings.",
            "base_price": 438.0,
            "volatility": 0.012,
            "seed": 79,
            "start_date": "2024-02-12",
        },
    },
}


class ToyDataBrowser(dcg.ChildWindow):
    """Resizable toy symbol browser used as a stand-in for a future DB browser."""

    def __init__(self, context, *, data_tree=None, on_symbol_selected=None, **kwargs):
        super().__init__(context, **kwargs)
        self.on_symbol_selected = on_symbol_selected
        self.toy_symbol_nodes = {}
        self.data_tree = TOY_DATA_TREE if data_tree is None else data_tree
        self.symbol_profiles = {
            symbol: {"group": group, **profile}
            for group, symbols in self.data_tree.items()
            for symbol, profile in symbols.items()
        }
        self.selected_symbol = next(iter(self.symbol_profiles))

        with self:
            self.selected_symbol_text = dcg.Text(context, value="")
            dcg.Text(
                context,
                value="Select a toy symbol to load a distinct candle series into both charts.",
                wrap=280,
            )
            self.toy_data_tree = dcg.TreeNode(context, label="Toy Symbols", value=True)

        self._build_tree()
        self._update_selected_text()

    def get_selected_profile(self):
        return self.symbol_profiles[self.selected_symbol]

    def _build_tree(self):
        with self.toy_data_tree:
            for group, symbols in self.data_tree.items():
                with dcg.TreeNode(self.context, label=group, value=True):
                    for symbol, profile in symbols.items():
                        node = dcg.Selectable(
                            self.context,
                            label=symbol,
                            value=symbol == self.selected_symbol,
                            user_data=symbol,
                            callback=self._select_symbol,
                        )
                        self.toy_symbol_nodes[symbol] = node
                        with dcg.Tooltip(self.context, target=node):
                            dcg.Text(self.context, value=profile["description"])
                            dcg.Text(
                                self.context,
                                value=(
                                    f"Base: {profile['base_price']:.2f}\n"
                                    f"Volatility: {profile['volatility']:.3f}\n"
                                    f"Default start: {profile['start_date']}"
                                ),
                            )

    def _update_selected_text(self):
        profile = self.get_selected_profile()
        self.selected_symbol_text.value = (
            f"Selected: {self.selected_symbol}"
            f" ({profile['group']})"
        )

    def _select_symbol(self, sender, app_data, user_data):
        symbol = sender.user_data
        if not sender.value:
            if symbol == self.selected_symbol:
                sender.value = True
            return

        self.selected_symbol = symbol
        for other_symbol, node in self.toy_symbol_nodes.items():
            if other_symbol != symbol:
                node.value = False

        self._update_selected_text()
        if callable(self.on_symbol_selected):
            self.on_symbol_selected(self, symbol, self.get_selected_profile())