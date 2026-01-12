-- Таблица воркеров
CREATE TABLE IF NOT EXISTS workers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица мамонтов (клиенты воркеров)
CREATE TABLE IF NOT EXISTS mammoths (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    worker_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица товаров воркеров
CREATE TABLE IF NOT EXISTS worker_products (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    worker_id TEXT NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    price INTEGER NOT NULL,
    weight TEXT NOT NULL,
    image TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица реквизитов для оплаты
CREATE TABLE IF NOT EXISTS payment_details (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    card_number TEXT NOT NULL,
    card_holder TEXT,
    bank_name TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица заказов
CREATE TABLE IF NOT EXISTS orders (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT,
    username TEXT,
    first_name TEXT,
    worker_id TEXT,
    city TEXT,
    items JSONB NOT NULL,
    total INTEGER NOT NULL,
    screenshot_url TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_mammoths_worker_id ON mammoths(worker_id);
CREATE INDEX IF NOT EXISTS idx_worker_products_worker_id ON worker_products(worker_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_worker_id ON orders(worker_id);

-- RLS политики (Row Level Security)
ALTER TABLE workers ENABLE ROW LEVEL SECURITY;
ALTER TABLE mammoths ENABLE ROW LEVEL SECURITY;
ALTER TABLE worker_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Политики для публичного доступа (для anon ключа)
CREATE POLICY "Allow all for workers" ON workers FOR ALL USING (true);
CREATE POLICY "Allow all for mammoths" ON mammoths FOR ALL USING (true);
CREATE POLICY "Allow all for worker_products" ON worker_products FOR ALL USING (true);
CREATE POLICY "Allow all for payment_details" ON payment_details FOR ALL USING (true);
CREATE POLICY "Allow all for orders" ON orders FOR ALL USING (true);

-- Вставка тестовых реквизитов
INSERT INTO payment_details (card_number, card_holder, bank_name) 
VALUES ('2200 0000 0000 0000', 'IVAN IVANOV', 'Сбербанк')
ON CONFLICT DO NOTHING;

-- Таблица настроек
CREATE TABLE IF NOT EXISTS settings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    key TEXT UNIQUE NOT NULL,
    value TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

ALTER TABLE settings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all for settings" ON settings FOR ALL USING (true);

-- Вставка дефолтной поддержки
INSERT INTO settings (key, value) VALUES ('telegram_support', '@support')
ON CONFLICT (key) DO NOTHING;


-- Таблица уведомлений для Telegram
CREATE TABLE IF NOT EXISTS telegram_notifications (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    type TEXT NOT NULL,
    order_id UUID REFERENCES orders(id),
    recipient_id TEXT,
    message TEXT,
    screenshot_url TEXT,
    sent BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_notifications_sent ON telegram_notifications(sent);
CREATE INDEX IF NOT EXISTS idx_notifications_recipient ON telegram_notifications(recipient_id);

ALTER TABLE telegram_notifications ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all for telegram_notifications" ON telegram_notifications FOR ALL USING (true);

-- Создание Storage bucket для скриншотов (выполнить в Supabase Dashboard -> Storage)
-- 1. Создать bucket "screenshots"
-- 2. Сделать его публичным
