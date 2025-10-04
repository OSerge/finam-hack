"""
Улучшенный клиент для работы с Finam TradeAPI с поддержкой JWT токенов
Использует библиотеку finam-trade-api для автоматического обновления токенов
"""

import asyncio
import os
from typing import Any, Optional

import httpx
import nest_asyncio
from dotenv import load_dotenv
from finam_trade_api import Client, TokenManager

# Загружаем переменные окружения из .env файла
load_dotenv()

# Применяем nest_asyncio для поддержки вложенных event loops
nest_asyncio.apply()


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
            token: Секретный токен для доступа к API (из переменной окружения FINAM_TOKEN)
        """
        self.token = token or os.getenv("FINAM_TOKEN", "")
        if not self.token:
            raise ValueError("FINAM_TOKEN не установлен в переменных окружения")

        # Инициализация TokenManager и Client
        self.token_manager = TokenManager(self.token)
        self.client = Client(self.token_manager)
        self._initialized = False

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
            accounts = await self.client.accounts.get_accounts()
            return {
                "status": "success",
                "accounts": accounts,
                "message": f"Найдено счетов: {len(accounts) if isinstance(accounts, list) else 'неизвестно'}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при получении счетов: {e!s}"
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
            account_info = await self.client.accounts.get_account_info(account_id)
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
            Словарь с информацией о портфеле или ошибкой
        """
        await self._ensure_initialized()
        try:
            portfolio = await self.client.accounts.get_portfolio(account_id)
            return {
                "status": "success",
                "portfolio": portfolio,
                "account_id": account_id,
                "message": "Портфель получен успешно"
            }
        except Exception as e:
            return {
                "status": "error",
                "account_id": account_id,
                "message": f"Ошибка при получении портфеля: {e!s}"
            }

    async def get_orders(self, account_id: str) -> dict[str, Any]:
        """
        Получить список заявок по счету
        
        Args:
            account_id: Идентификатор счета
            
        Returns:
            Словарь со списком заявок или ошибкой
        """
        await self._ensure_initialized()
        try:
            orders = await self.client.orders.get_orders(account_id)
            return {
                "status": "success",
                "orders": orders,
                "account_id": account_id,
                "message": f"Найдено заявок: {len(orders) if isinstance(orders, list) else 'неизвестно'}"
            }
        except Exception as e:
            return {
                "status": "error",
                "account_id": account_id,
                "message": f"Ошибка при получении заявок: {e!s}"
            }

    async def get_instruments(self, query: str = "") -> dict[str, Any]:
        """
        Поиск инструментов
        
        Args:
            query: Поисковый запрос (например, "SBER")
            
        Returns:
            Словарь со списком найденных инструментов или ошибкой
        """
        await self._ensure_initialized()
        try:
            instruments = await self.client.instruments.get_instruments(query)
            return {
                "status": "success",
                "instruments": instruments,
                "query": query,
                "message": f"Найдено инструментов: {len(instruments) if isinstance(instruments, list) else 'неизвестно'}"
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
            return {
                "status": "success",
                "orderbook": orderbook,
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
            timeframe: Таймфрейм (D, H, M)
            start: Начальная дата (ISO формат)
            end: Конечная дата (ISO формат)

        Returns:
            Словарь со свечами или ошибкой
        """
        await self._ensure_initialized()
        try:
            candles = await self.client.instruments.get_bars(
                symbol, timeframe, start, end
            )
            return {
                "status": "success",
                "candles": candles,
                "symbol": symbol,
                "timeframe": timeframe,
                "message": f"Получено свечей: {len(candles) if isinstance(candles, list) else 'неизвестно'}"
            }
        except Exception as e:
            return {
                "status": "error",
                "symbol": symbol,
                "message": f"Ошибка при получении свечей: {e!s}"
            }

    async def get_assets(self) -> dict[str, Any]:
        """
        Получить список всех доступных активов/инструментов

        Returns:
            Словарь со списком активов или ошибкой
        """
        await self._ensure_initialized()
        try:
            # Используем _exec_request для автоматического управления JWT токеном
            # _exec_request уже добавляет /v1 префикс и возвращает (data, success)
            result = await self.client.assets._exec_request(
                method=self.client.assets.RequestMethod.GET,
                url="/assets"
            )

            # _exec_request возвращает кортеж (data, success)
            assets_data = result[0] if isinstance(result, tuple) else result

            # Извлекаем список активов из ответа
            assets_list = assets_data.get("assets", []) if isinstance(assets_data, dict) else assets_data

            return {
                "status": "success",
                "assets": assets_list,
                "message": f"Найдено активов: {len(assets_list) if isinstance(assets_list, list) else 'неизвестно'}"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Ошибка при получении списка активов: {e!s}"
            }

    # Синхронные обертки для совместимости с существующим кодом
    def _run_async(self, coro) -> Any:
        """
        Запускает асинхронную функцию в синхронном контексте
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(coro)

    def get_jwt_token_details_sync(self) -> dict[str, Any]:
        """Синхронная версия получения JWT токена"""
        return self._run_async(self.get_jwt_token_details())

    def refresh_jwt_token_sync(self) -> dict[str, Any]:
        """Синхронная версия обновления JWT токена"""
        return self._run_async(self.refresh_jwt_token())

    def get_accounts_sync(self) -> dict[str, Any]:
        """Синхронная версия получения счетов"""
        return self._run_async(self.get_accounts())

    def get_account_info_sync(self, account_id: str) -> dict[str, Any]:
        """Синхронная версия получения информации о счете"""
        return self._run_async(self.get_account_info(account_id))

    def get_portfolio_sync(self, account_id: str) -> dict[str, Any]:
        """Синхронная версия получения портфеля"""
        return self._run_async(self.get_portfolio(account_id))

    def get_orders_sync(self, account_id: str) -> dict[str, Any]:
        """Синхронная версия получения заявок"""
        return self._run_async(self.get_orders(account_id))

    def get_instruments_sync(self, query: str = "") -> dict[str, Any]:
        """Синхронная версия поиска инструментов"""
        return self._run_async(self.get_instruments(query))

    def get_quotes_sync(self, symbol: str) -> dict[str, Any]:
        """Синхронная версия получения котировок"""
        return self._run_async(self.get_quotes(symbol))

    def get_orderbook_sync(self, symbol: str, depth: int = 10) -> dict[str, Any]:
        """Синхронная версия получения стакана заявок"""
        return self._run_async(self.get_orderbook(symbol, depth))

    def get_candles_sync(
        self,
        symbol: str,
        timeframe: str = "D",
        start: Optional[str] = None,
        end: Optional[str] = None
    ) -> dict[str, Any]:
        """Синхронная версия получения свечей"""
        return self._run_async(self.get_candles(symbol, timeframe, start, end))

    def get_assets_sync(self) -> dict[str, Any]:
        """Синхронная версия получения списка активов"""
        return self._run_async(self.get_assets())
