-- upgrade --
ALTER TABLE `tasks` ADD `completed` BOOL NOT NULL  DEFAULT 0;
-- downgrade --
ALTER TABLE `tasks` DROP COLUMN `completed`;
