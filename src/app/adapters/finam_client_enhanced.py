"""
Улучшенный клиент для работы с Finam TradeAPI с поддержкой JWT токенов
Использует библиотеку finam-trade-api для автоматического обновления токенов
"""
import os
from datetime import datetime, timedelta
from typing import Any, Optional

from finam_trade_api.account import GetTradesRequest

from app.adapters import FinamAPIClient
import httpx
from dotenv import load_dotenv
from finam_trade_api import Client, TokenManager
from finam_trade_api.instruments.model import BarsRequest, TimeFrame

load_dotenv()


class FinamAPIClientEnhanced:
    """
    Улучшенный клиент для взаимодействия с Finam TradeAPI
    с автоматическим управлением JWT токенами
    
    Документация: https://tradeapi.finam.ru/
    """

    def __init__(self, token: Optional[str] = None) -> None:
        """
        Инициализация клиента с TokenManager
        
        Args:
            token: Секретный токен для доступа к API (из переменной окружения FINAM_ACCESS_TOKEN)
        """
        self.token = token or os.getenv("FINAM_ACCESS_TOKEN", "")
        if not self.token:
            raise ValueError("FINAM_ACCESS_TOKEN не установлен в переменных окружения")

        # Инициализация TokenManager и Client
        self.token_manager = TokenManager(self.token)
        self.client = Client(self.token_manager)
        self.finam_client = FinamAPIClient(self.token)
        self._initialized = False

        # Базовый URL для прямых HTTP запросов
        self.api_base_url = os.getenv("FINAM_API_BASE_URL", "https://api.finam.ru")

    async def _ensure_initialized(self) -> None:
        """
        Убеждается, что клиент инициализирован и JWT токен установлен
        """
        if not self._initialized:
            await self.client.access_tokens.set_jwt_token()
            self._initialized = True

    async def get_jwt_token_details(self) -> dict[str, Any]:
        """
        Получить детали текущего JWT токена
        
        Returns:
            Словарь с информацией о JWT токене
        """
        await self._ensure_initialized()
        try:
            details = await self.client.access_tokens.get_jwt_token_details()
            return {
                "status": "success",
                "token_details": details,
                "message": "JWT токен получен успешно"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при получении JWT токена: {e!s}"
            }

    async def refresh_jwt_token(self) -> dict[str, Any]:
        """
        Обновить JWT токен
        
        Returns:
            Словарь с результатом обновления токена
        """
        try:
            await self.client.access_tokens.set_jwt_token()
            self._initialized = True
            return {
                "status": "success",
                "message": "JWT токен обновлен успешно"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при обновлении JWT токена: {e!s}"
            }

    async def get_accounts(self) -> dict[str, Any]:
        """
        Получить список доступных счетов
        
        Returns:
            Словарь со списком счетов или ошибкой
        """
        await self._ensure_initialized()
        try:
            accounts = await self.client.access_tokens.get_jwt_token_details()
            return {
                "status": "success",
                "accounts": accounts.account_ids,
                "message": f"Найдено счетов: {len(accounts) if isinstance(accounts, list) else 'неизвестно'}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при получении списка счетов: {e!s}"
            }

    async def get_account_info(self, account_id: str) -> dict[str, Any]:
        """
        Получить информацию о конкретном счете
        
        Args:
            account_id: Идентификатор счета
            
        Returns:
            Словарь с информацией о счете или ошибкой
        """
        await self._ensure_initialized()
        try:
            account_info = await self.client.account.get_account_info(account_id)
            return {
                "status": "success",
                "account_info": account_info,
                "account_id": account_id,
                "message": "Информация о счете получена успешно"
            }
        except Exception as e:
            return {
                "status": "error",
                "account_id": account_id,
                "message": f"Ошибка при получении информации о счете: {e!s}"
            }

    async def get_portfolio(self, account_id: str) -> dict[str, Any]:
        """
        Получить портфель по счету
        
        Args:
            account_id: Идентификатор счета
            
        Returns:
            Словарь с информацией о портфеле (балансе и позициях)
        """
        await self._ensure_initialized()
        try:
            # Получаем полную информацию о счете (включает портфель)
            account_info = await self.client.account.get_account_info(account_id)
            return {
                "status": "success",
                "portfolio": account_info,
                "account_id": account_id,
                "message": "Портфель получен успешно"
            }
        except Exception as e:
            return {
                "status": "error",
                "account_id": account_id,
                "message": f"Ошибка при получении портфеля: {e!s}"
            }

    async def get_trades(self, account_id: str) -> dict[str, Any]:
        """
        Получить список сделок по счету

        Args:
            account_id: Идентификатор счета

        Returns:
            Словарь со списком сделок или ошибкой
        """
        await self._ensure_initialized()
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            # Format dates as strings (YYYY-MM-DD format)
            start_date_str = str(int(start_date.timestamp()))
            end_date_str = str(int(end_date.timestamp()))
            # orders = await self.client.account.get_trades(GetTradesRequest(
            #     account_id=account_id, start_time=start_date, end_time=end_date))
            orders = list()
            return {
                "status": "success",
                "trades": [],
                "account_id": account_id,
                "message": f"Получение сделок недоступно для демо-счетов. Для работы с ордерами используйте реальный счет и торговый терминал."
                # "message": f"Найдено заявок: {len(orders) if isinstance(orders, list) else 'неизвестно'}"
            }
        except Exception as e:
            return {
                "status": "error",
                "account_id": account_id,
                "message": f"Ошибка при получении заявок: {e!s}"
            }

    async def get_orders(self, account_id: str) -> dict[str, Any]:
        """
        Получить список заявок по счету
        
        Note: Методы работы с ордерами (get_orders, place_order, cancel_order)
        не реализованы в текущей версии finam-trade-api и недоступны через REST API
        для демо-счетов. Возвращаем пустой список.

        Args:
            account_id: Идентификатор счета
            
        Returns:
            Словарь с пустым списком заявок и информационным сообщением
        """
        await self._ensure_initialized()

        return {
            "status": "success",
            "orders": [],
            "account_id": account_id,
            "message": "Получение ордеров недоступно для демо-счетов. Для работы с ордерами используйте реальный счет и торговый терминал."
        }

    async def get_instruments(self, query: str = "") -> dict[str, Any]:
        """
        Поиск инструментов
        
        Note: В finam-trade-api нет метода для получения полного списка инструментов.
        Возвращаем список популярных российских акций и информацию по запросу через get_asset.

        Args:
            query: Поисковый запрос (тикер, например "SBER", "YNDX")
            
        Returns:
            Словарь со списком найденных инструментов
        """
        await self._ensure_initialized()
        try:
            demo_account_id = os.getenv("FINAM_DEMO_ACCOUNT_ID", "")

            if not demo_account_id:
                return {
                    "status": "error",
                    "query": query,
                    "message": "FINAM_DEMO_ACCOUNT_ID не установлен. Требуется для получения информации об инструментах."
                }

            # Список популярных тикеров (можно расширить)
            popular_tickers = [
                "SBER@MISX", "GAZP@MISX", "LKOH@MISX", "YNDX@MISX",
                "GMKN@MISX", "NVTK@MISX", "ROSN@MISX", "MGNT@MISX",
                "TATN@MISX", "SNGS@MISX", "MTSS@MISX", "ALRS@MISX"
            ]

            instruments = []

            # Если указан запрос, фильтруем тикеры или пробуем найти конкретный инструмент
            if query:
                query_upper = query.upper()

                # Проверяем, если это полный тикер формата SYMBOL@EXCHANGE
                if "@" in query_upper:
                    try:
                        asset = await self.client.assets.get_asset(query_upper, demo_account_id)
                        instruments.append(asset.model_dump())
                    except:
                        pass
                else:
                    # Добавляем @MISX и пробуем
                    try:
                        full_ticker = f"{query_upper}@MISX"
                        asset = await self.client.assets.get_asset(full_ticker, demo_account_id)
                        instruments.append(asset.model_dump())
                    except:
                        pass

                # Фильтруем популярные тикеры по запросу
                for ticker in popular_tickers:
                    if query_upper in ticker:
                        try:
                            asset = await self.client.assets.get_asset(ticker, demo_account_id)
                            asset_dict = asset.model_dump()
                            if asset_dict not in instruments:  # Избегаем дубликатов
                                instruments.append(asset_dict)
                        except:
                            continue
            else:
                # Без запроса возвращаем популярные инструменты
                for ticker in popular_tickers[:10]:  # Ограничим 10 для производительности
                    try:
                        asset = await self.client.assets.get_asset(ticker, demo_account_id)
                        instruments.append(asset.model_dump())
                    except:
                        continue

            return {
                "status": "success",
                "instruments": instruments,
                "query": query,
                "message": f"Найдено инструментов: {len(instruments)}. Используйте формат TICKER@MISX для точного поиска."
            }

        except Exception as e:
            return {
                "status": "error",
                "query": query,
                "message": f"Ошибка при поиске инструментов: {e!s}"
            }

    async def get_quotes(self, symbol: str) -> dict[str, Any]:
        """
        Получить котировки инструмента
        
        Args:
            symbol: Тикер инструмента (например, "SBER@MISX")
            
        Returns:
            Словарь с котировками или ошибкой
        """
        await self._ensure_initialized()
        try:
            quotes = await self.client.instruments.get_last_quote(symbol)
            return {
                "status": "success",
                "quotes": quotes,
                "symbol": symbol,
                "message": "Котировки получены успешно"
            }
        except Exception as e:
            return {
                "status": "error",
                "symbol": symbol,
                "message": f"Ошибка при получении котировок: {e!s}"
            }

    async def get_orderbook(self, symbol: str, depth: int = 10) -> dict[str, Any]:
        """
        Получить стакан заявок
        
        Args:
            symbol: Тикер инструмента
            depth: Глубина стакана
            
        Returns:
            Словарь со стаканом заявок или ошибкой
        """
        await self._ensure_initialized()
        try:
            orderbook = await self.client.instruments.get_order_book(symbol)

            limited_orderbook = orderbook.model_copy(deep=True)
            limited_orderbook.orderbook = limited_orderbook.orderbook.model_copy(deep=True)
            limited_orderbook.orderbook.rows = limited_orderbook.orderbook.rows[:depth]

            return {
                "status": "success",
                "orderbook": limited_orderbook.model_dump(),
                "symbol": symbol,
                "depth": depth,
                "message": "Стакан заявок получен успешно"
            }
        except Exception as e:
            return {
                "status": "error",
                "symbol": symbol,
                "message": f"Ошибка при получении стакана заявок: {e!s}"
            }

    async def get_candles(
            self,
            symbol: str,
            timeframe: str = "D",
            start: Optional[str] = None,
            end: Optional[str] = None
    ) -> dict[str, Any]:
        """
        Получить исторические свечи

        Args:
            symbol: Тикер инструмента
            timeframe: Таймфрейм (D, H, M, 1H, 5M и т.д.)
            start: Начальная дата в ISO формате (например, "2024-01-01T00:00:00Z")
            end: Конечная дата в ISO формате (например, "2024-01-31T23:59:59Z")

        Returns:
            Словарь со свечами или ошибкой
        """
        await self._ensure_initialized()
        try:
            # Конвертируем строковый timeframe в enum TimeFrame
            timeframe_map = {
                "D": TimeFrame.TIME_FRAME_D,
                "H": TimeFrame.TIME_FRAME_H1,
                "1H": TimeFrame.TIME_FRAME_H1,
                "2H": TimeFrame.TIME_FRAME_H2,
                "4H": TimeFrame.TIME_FRAME_H4,
                "8H": TimeFrame.TIME_FRAME_H8,
                "M": TimeFrame.TIME_FRAME_M1,
                "1M": TimeFrame.TIME_FRAME_M1,
                "5M": TimeFrame.TIME_FRAME_M5,
                "15M": TimeFrame.TIME_FRAME_M15,
                "30M": TimeFrame.TIME_FRAME_M30,
                "W": TimeFrame.TIME_FRAME_W,
                "MN": TimeFrame.TIME_FRAME_MN,
            }

            tf_enum = timeframe_map.get(timeframe.upper(), TimeFrame.TIME_FRAME_D)

            # Устанавливаем даты по умолчанию если не указаны
            if not end:
                end = datetime.utcnow().isoformat() + "Z"
            if not start:
                # По умолчанию - последние 30 дней
                start = (datetime.utcnow() - timedelta(days=30)).isoformat() + "Z"

            # Создаем объект запроса
            bars_request = BarsRequest(
                symbol=symbol,
                timeframe=tf_enum,
                start_time=start,
                end_time=end
            )

            # Получаем свечи
            response = await self.client.instruments.get_bars(bars_request)

            # Обрабатываем ответ
            if hasattr(response, 'model_dump'):
                result_data = response.model_dump()
            else:
                result_data = response

            # Извлекаем список свечей (ключ называется 'bars', а не 'candles')
            bars_list = result_data.get('bars', []) if isinstance(result_data, dict) else []

            return {
                "status": "success",
                "candles": bars_list,
                "symbol": symbol,
                "timeframe": timeframe,
                "message": f"Получено свечей: {len(bars_list)}"
            }
        except Exception as e:
            return {
                "status": "error",
                "symbol": symbol,
                "message": f"Ошибка при получении свечей: {e!s}"
            }

    async def get_assets(self) -> dict[str, Any]:
        """
        Получить список доступных активов/инструментов

        Note: Метод client.assets.get_assets() не реализован в текущей версии библиотеки.
        Используем get_instruments() как альтернативу.

        Returns:
            Словарь со списком активов
        """
        # Просто вызываем get_instruments без фильтра
        return await self.get_instruments("")
