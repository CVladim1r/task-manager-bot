-- upgrade --
ALTER TABLE `users` MODIFY COLUMN `last_name` VARCHAR(50);
ALTER TABLE `users` MODIFY COLUMN `first_name` VARCHAR(50);
-- downgrade --
ALTER TABLE `users` MODIFY COLUMN `last_name` VARCHAR(50) NOT NULL;
ALTER TABLE `users` MODIFY COLUMN `first_name` VARCHAR(50) NOT NULL;
