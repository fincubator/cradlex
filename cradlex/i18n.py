from pathlib import Path

from aiogram.contrib.middlewares.i18n import I18nMiddleware


_ = i18n = I18nMiddleware("cradlex", Path(__file__).parents[1] / "locales", "ru")
