import os
from typing import List

class Config:
    """Конфигурация для Telegram бота BlackLeaf Shop"""
    
    # Токен бота (получить у @BotFather)
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8333018588:AAHKuqcxw7qYLO_Y2Lzl-3LbjQpAdu3taeo")
    
    # URL веб-приложения
    WEB_APP_URL: str = os.getenv("WEB_APP_URL", "https://shop-green-kappa.vercel.app/")
    
    # Supabase настройки
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://owrdpczlmrruxrwuvsow.supabase.co")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im93cmRwY3psbXJydXhyd3V2c293Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjY5NTgyNDMsImV4cCI6MjA4MjUzNDI0M30.l7DYgkTBK_O3AwKqYpCNipz_ajdSlSH1CTSavcIGhBI")
    
    # ID администраторов
    ADMIN_IDS: List[int] = [844012884, 8227295387, 8162019020]
    
    # Настройки логирования
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "WARNING")
    
    @classmethod
    def validate(cls) -> bool:
        """Проверка корректности конфигурации"""
        if cls.BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            print("❌ Ошибка: Необходимо установить BOT_TOKEN")
            return False
        if cls.WEB_APP_URL == "https://your-domain.com":
            print("❌ Ошибка: Необходимо установить WEB_APP_URL")
            return False
        return True
