-- 修改 private_messages 表的字段类型
ALTER TABLE private_messages ALTER COLUMN content TYPE TEXT;
ALTER TABLE private_messages ALTER COLUMN reply_to_id TYPE INTEGER USING reply_to_id::INTEGER;
ALTER TABLE private_messages ALTER COLUMN forward_from_id TYPE INTEGER USING forward_from_id::INTEGER;

-- 添加新字段
ALTER TABLE private_messages ADD COLUMN IF NOT EXISTS forward_date TIMESTAMP WITH TIME ZONE;

-- 修改 group_messages 表的字段类型
ALTER TABLE group_messages ALTER COLUMN content TYPE TEXT;
ALTER TABLE group_messages ALTER COLUMN reply_to_id TYPE INTEGER USING reply_to_id::INTEGER;
ALTER TABLE group_messages ALTER COLUMN forward_from_id TYPE INTEGER USING forward_from_id::INTEGER;

-- 添加新字段
ALTER TABLE group_messages ADD COLUMN IF NOT EXISTS forward_date TIMESTAMP WITH TIME ZONE;
