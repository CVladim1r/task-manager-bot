-- upgrade --
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `telegram_id` BIGINT NOT NULL UNIQUE,
    `first_name` VARCHAR(50) NOT NULL,
    `last_name` VARCHAR(50) NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `organizations` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `description` LONGTEXT,
    `created_by_id` INT NOT NULL,
    CONSTRAINT `fk_organiza_users_5b8e57eb` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `tasks` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `name` VARCHAR(100) NOT NULL,
    `description` LONGTEXT,
    `deadline` DATETIME(6) NOT NULL,
    `reminder_time` DATETIME(6) NOT NULL,
    `reminder_sent` BOOL NOT NULL  DEFAULT FALSE,
    `created_by_id` INT NOT NULL,
    `organization_id` INT,
    CONSTRAINT `fk_tasks_users_76c4fbd4` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_tasks_organiza_0806189b` FOREIGN KEY (`organization_id`) REFERENCES `organizations` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(20) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `tasks_users` (
    `tasks_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    FOREIGN KEY (`tasks_id`) REFERENCES `tasks` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    UNIQUE KEY `uidx_tasks_users_tasks_i_e4bab8` (`tasks_id`, `user_id`)
) CHARACTER SET utf8mb4;
