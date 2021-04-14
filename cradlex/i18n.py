from pathlib import Path

from aiogram.contrib.middlewares.i18n import I18nMiddleware


class I18nMiddlewareProxy(I18nMiddleware):
    async def get_user_locale(self, *args, **kwargs) -> str:
        # Fixes https://github.com/aiogram/aiogram/issues/562
        language = await super().get_user_locale(*args, **kwargs)
        return language if language and language in self.locales else self.default


_ = i18n = I18nMiddlewareProxy("cradlex", Path(__file__).parents[1] / "locales", "ru")