"""Commodities tab — market prices, best locations, trade routes."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QFrame, QAbstractItemView
)
from PyQt6.QtCore import Qt, QSortFilterProxyModel
from PyQt6.QtGui import QColor, QFont
from core.data import (
    COMMODITIES, LOCATION_BY_ID,
    get_commodities,
    get_best_buy, get_best_sell, get_profit_margin, get_top_routes
)


def _colored_item(text: str, color: str = None, align=None, bold=False) -> QTableWidgetItem:
    item = QTableWidgetItem(str(text))
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    if color:
        item.setForeground(QColor(color))
    if align:
        item.setTextAlignment(align)
    if bold:
        f = item.font()
        f.setBold(True)
        item.setFont(f)
    return item


class CommoditiesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        title = QLabel("Commodity Market")
        title.setObjectName("section-title")
        root.addWidget(title)

        # Sub-tabs: Market | Trade Routes
        tabs = QTabWidget()
        tabs.addTab(self._build_market(),      "Market Overview")
        tabs.addTab(self._build_locations(),   "Best Locations")
        tabs.addTab(self._build_routes(),      "Trade Routes")
        root.addWidget(tabs)

    # ── Market Overview ───────────────────────────────────────────
    def _build_market(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(12, 12, 12, 12)
        vl.setSpacing(10)

        # Filter bar
        bar = QHBoxLayout()
        self._market_search = QLineEdit()
        self._market_search.setPlaceholderText("Search commodities…")
        self._market_search.setFixedWidth(220)
        self._market_search.textChanged.connect(self._filter_market)

        self._market_cat = QComboBox()
        self._market_cat.addItem("All Categories")
        cats = sorted(set(c["category"] for c in COMMODITIES))
        self._market_cat.addItems(cats)
        self._market_cat.currentTextChanged.connect(self._filter_market)

        self._market_sort = QComboBox()
        self._market_sort.addItems([
            "Highest Profit/SCU",
            "Highest Margin %",
            "Name A–Z",
            "Highest Sell Price",
        ])
        self._market_sort.currentTextChanged.connect(self._filter_market)

        bar.addWidget(QLabel("Search:"))
        bar.addWidget(self._market_search)
        bar.addWidget(QLabel("Category:"))
        bar.addWidget(self._market_cat)
        bar.addWidget(QLabel("Sort:"))
        bar.addWidget(self._market_sort)
        bar.addStretch()
        vl.addLayout(bar)

        # Table
        self._market_table = QTableWidget()
        self._market_table.setColumnCount(7)
        self._market_table.setHorizontalHeaderLabels([
            "Commodity", "Category",
            "Best Buy (aUEC)", "Buy Location",
            "Best Sell (aUEC)", "Sell Location",
            "Profit/SCU",
        ])
        self._market_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._market_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._market_table.verticalHeader().setVisible(False)
        self._market_table.setAlternatingRowColors(True)
        self._market_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._market_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._market_table.setSortingEnabled(False)
        vl.addWidget(self._market_table)

        self._populate_market(get_commodities())
        return w

    def _sorted_commodities(self, comms):
        sort = self._market_sort.currentText()
        if sort == "Highest Profit/SCU":
            return sorted(comms, key=get_profit_margin, reverse=True)
        elif sort == "Highest Margin %":
            def margin_pct(c):
                _, buy = get_best_buy(c)
                profit = get_profit_margin(c)
                return (profit / buy * 100) if buy else 0
            return sorted(comms, key=margin_pct, reverse=True)
        elif sort == "Name A–Z":
            return sorted(comms, key=lambda c: c["name"])
        elif sort == "Highest Sell Price":
            return sorted(comms, key=lambda c: get_best_sell(c)[1], reverse=True)
        return comms

    def _populate_market(self, comms):
        comms = self._sorted_commodities(comms)
        self._market_table.setRowCount(len(comms))
        max_profit = max((get_profit_margin(c) for c in comms), default=1)

        for row, c in enumerate(comms):
            buy_loc, buy_price = get_best_buy(c)
            sell_loc, sell_price = get_best_sell(c)
            profit = get_profit_margin(c)
            margin_pct = (profit / buy_price * 100) if buy_price else 0

            self._market_table.setItem(row, 0, _colored_item(c["name"], "#e8f4ff", bold=True))
            self._market_table.setItem(row, 1, _colored_item(c["category"], "#3d6b88"))
            self._market_table.setItem(row, 2, _colored_item(
                f"{buy_price:,.2f}", "#b0d4e8",
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter))
            self._market_table.setItem(row, 3, _colored_item(buy_loc, "#6a9ab8"))
            self._market_table.setItem(row, 4, _colored_item(
                f"{sell_price:,.2f}", "#00e5ff",
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter))
            self._market_table.setItem(row, 5, _colored_item(sell_loc, "#6a9ab8"))

            profit_color = "#00e676" if profit > 0 else "#3d6b88"
            self._market_table.setItem(row, 6, _colored_item(
                f"+{profit:,.2f}  ({margin_pct:.1f}%)",
                profit_color,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                bold=True))

    def _filter_market(self):
        search = self._market_search.text().lower()
        cat = self._market_cat.currentText()
        filtered = [
            c for c in get_commodities()
            if (search in c["name"].lower())
            and (cat == "All Categories" or c["category"] == cat)
        ]
        self._populate_market(filtered)

    # ── Best Locations ────────────────────────────────────────────
    def _build_locations(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(12, 12, 12, 12)
        vl.setSpacing(10)

        info = QLabel(
            "Shows the single best place to buy and sell each commodity. "
            "Use this to quickly find where to source or offload a specific item."
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        vl.addWidget(info)

        bar = QHBoxLayout()
        self._loc_search = QLineEdit()
        self._loc_search.setPlaceholderText("Search…")
        self._loc_search.setFixedWidth(200)
        self._loc_search.textChanged.connect(self._filter_locations)
        self._loc_cat = QComboBox()
        self._loc_cat.addItem("All Categories")
        self._loc_cat.addItems(sorted(set(c["category"] for c in COMMODITIES)))
        self._loc_cat.currentTextChanged.connect(self._filter_locations)
        bar.addWidget(QLabel("Search:"))
        bar.addWidget(self._loc_search)
        bar.addWidget(QLabel("Category:"))
        bar.addWidget(self._loc_cat)
        bar.addStretch()
        vl.addLayout(bar)

        self._loc_table = QTableWidget()
        self._loc_table.setColumnCount(5)
        self._loc_table.setHorizontalHeaderLabels([
            "Commodity", "Category",
            "Best Buy At", "Best Sell At", "Profit/SCU",
        ])
        self._loc_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._loc_table.verticalHeader().setVisible(False)
        self._loc_table.setAlternatingRowColors(True)
        self._loc_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._loc_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        vl.addWidget(self._loc_table)

        self._populate_locations(get_commodities())
        return w

    def _populate_locations(self, comms):
        comms = sorted(comms, key=get_profit_margin, reverse=True)
        self._loc_table.setRowCount(len(comms))
        for row, c in enumerate(comms):
            buy_loc, buy_price = get_best_buy(c)
            sell_loc, sell_price = get_best_sell(c)
            profit = get_profit_margin(c)
            self._loc_table.setItem(row, 0, _colored_item(c["name"], "#e8f4ff", bold=True))
            self._loc_table.setItem(row, 1, _colored_item(c["category"], "#3d6b88"))
            self._loc_table.setItem(row, 2, _colored_item(
                f"{buy_loc}  ({buy_price:,.2f} aUEC)", "#b0d4e8"))
            self._loc_table.setItem(row, 3, _colored_item(
                f"{sell_loc}  ({sell_price:,.2f} aUEC)", "#00e5ff"))
            profit_color = "#00e676" if profit > 0 else "#3d6b88"
            self._loc_table.setItem(row, 4, _colored_item(
                f"+{profit:,.2f}",
                profit_color,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                bold=True))

    def _filter_locations(self):
        search = self._loc_search.text().lower()
        cat = self._loc_cat.currentText()
        filtered = [
            c for c in get_commodities()
            if (search in c["name"].lower())
            and (cat == "All Categories" or c["category"] == cat)
        ]
        self._populate_locations(filtered)

    # ── Trade Routes ─────────────────────────────────────────────
    def _build_routes(self) -> QWidget:
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(12, 12, 12, 12)
        vl.setSpacing(10)

        info = QLabel(
            "Best trade routes sorted by profit per SCU. "
            "Buy at the listed source location and sell at the destination for maximum return."
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        vl.addWidget(info)

        bar = QHBoxLayout()
        self._route_search = QLineEdit()
        self._route_search.setPlaceholderText("Filter routes…")
        self._route_search.setFixedWidth(200)
        self._route_search.textChanged.connect(self._filter_routes)

        self._route_sort = QComboBox()
        self._route_sort.addItems(["Highest Profit/SCU", "Highest Margin %"])
        self._route_sort.currentTextChanged.connect(self._filter_routes)

        bar.addWidget(QLabel("Filter:"))
        bar.addWidget(self._route_search)
        bar.addWidget(QLabel("Sort:"))
        bar.addWidget(self._route_sort)
        bar.addStretch()
        vl.addLayout(bar)

        self._routes_table = QTableWidget()
        self._routes_table.setColumnCount(7)
        self._routes_table.setHorizontalHeaderLabels([
            "Commodity", "Category",
            "Buy At", "Buy Price",
            "Sell At", "Sell Price",
            "Profit/SCU",
        ])
        self._routes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._routes_table.verticalHeader().setVisible(False)
        self._routes_table.setAlternatingRowColors(True)
        self._routes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._routes_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        vl.addWidget(self._routes_table)

        self._all_routes = get_top_routes(100)
        self._populate_routes(self._all_routes)
        return w

    def _populate_routes(self, routes):
        sort = self._route_sort.currentText() if hasattr(self, "_route_sort") else "Highest Profit/SCU"
        if sort == "Highest Margin %":
            routes = sorted(routes, key=lambda r: r["margin_pct"], reverse=True)
        else:
            routes = sorted(routes, key=lambda r: r["profit"], reverse=True)

        self._routes_table.setRowCount(len(routes))
        for row, r in enumerate(routes):
            self._routes_table.setItem(row, 0, _colored_item(r["commodity"], "#e8f4ff", bold=True))
            self._routes_table.setItem(row, 1, _colored_item(r["category"], "#3d6b88"))
            self._routes_table.setItem(row, 2, _colored_item(
                f"{r['buy_loc']}  ({r['buy_body']})", "#b0d4e8"))
            self._routes_table.setItem(row, 3, _colored_item(
                f"{r['buy_price']:,.2f}",
                "#b0d4e8",
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter))
            self._routes_table.setItem(row, 4, _colored_item(
                f"{r['sell_loc']}  ({r['sell_body']})", "#00e5ff"))
            self._routes_table.setItem(row, 5, _colored_item(
                f"{r['sell_price']:,.2f}",
                "#00e5ff",
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter))
            profit_str = f"+{r['profit']:,.2f}  ({r['margin_pct']:.1f}%)"
            self._routes_table.setItem(row, 6, _colored_item(
                profit_str, "#00e676",
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                bold=True))

    def _filter_routes(self):
        search = self._route_search.text().lower() if hasattr(self, "_route_search") else ""
        filtered = [
            r for r in self._all_routes
            if search in r["commodity"].lower()
            or search in r["buy_loc"].lower()
            or search in r["sell_loc"].lower()
        ]
        self._populate_routes(filtered)

    def refresh(self):
        """Called by MainWindow when live commodity/price data arrives."""
        from core.data import get_commodities, get_top_routes
        self._all_routes = get_top_routes(100)
        self._filter_market()
        self._filter_locations()
        self._filter_routes()
