CREATE TABLE user (
    [id] CHAR(32) PRIMARY KEY NOT NULL,
    [email] VARCHAR(128) UNIQUE,
    [password] CHAR(64) NOT NULL,
    [alias] VARCHAR(64) NOT NULL,
    [active] SMALLINT(1) DEFAULT 1 NOT NULL
);

CREATE TABLE captcha_tokens (
    id CHAR(32) PRIMARY KEY NOT NULL,
    answer VARCHAR(12) NOT NULL,
    time TIMESTAMP NOT NULL
);

CREATE TABLE profile (
    [user_id] CHAR(32) PRIMARY KEY NOT NULL,
    [image] VARCHAR(128),
    [timezone] VARCHAR(16) NOT NULL DEFAULT '',
    [status] VARCHAR(129) NOT NULL DEFAULT '',
    CONSTRAINT users_profiles_fk1 FOREIGN KEY (user_id) REFERENCES [user](id)
);

CREATE TABLE campaign (
    [id] INTEGER PRIMARY KEY AUTOINCREMENT,
    [name] VARCHAR(64) NOT NULL,
    [description] VARCHAR(256),
    [public] SMALLINT DEFAULT 0,
    [start_tick] INTEGER NOT NULL DEFAULT 1000
);

INSERT INTO campaign ([name], [description])
VALUES
('Cult of the Liar', 'A mysterious cult is rising in the underdark, inciting upheaval in the realms and tampering with long-forgotten artifacts'),
('The Materium of Freedom', 'A strange, possibly ancient new substance is abundantly available in the town of Freedom, built on the ruins of some forgotten civilization.');

CREATE TABLE user_campaign_map (
    [user_id] CHAR(32) NOT NULL,
    [campaign_id] INTEGER NOT NULL,
    [is_master] SMALLINT(1) DEFAULT 0 NOT NULL,
    CONSTRAINT user_campaign_fk1 FOREIGN KEY (user_id) REFERENCES [user](id),
    CONSTRAINT user_campaign_fk2 FOREIGN KEY (campaign_id) REFERENCES [campaign](id),
    PRIMARY KEY (user_id, campaign_id)
);

CREATE TABLE campaign_referral (
    [code] VARCHAR(16) NOT NULL PRIMARY KEY,
    [campaign_id] INTEGER NOT NULL,
    CONSTRAINT campaign_referral_fk1 FOREIGN KEY (campaign_id) REFERENCES [campaign](id)
);

CREATE TABLE chronicle_entry (
    [id] CHAR(32) PRIMARY KEY NOT NULL,
    [title] VARCHAR(64),
    [tick] INT NOT NULL,
    [external_file_name] CHAR(64) NOT NULL,
    [relation_type] VARCHAR(10) NOT NULL DEFAULT 'domain',
    [campaign_id] INTEGER NOT NULL,
    [creator_id] CHAR(32) NOT NULL,
    [is_public] TINYINT(1) NOT NULL,
    CONSTRAINT chronicle_campaign_fk1 FOREIGN KEY ([campaign_id]) REFERENCES [campaign](id),
    CONSTRAINT chronicle_creator_fk1 FOREIGN KEY ([creator_id]) REFERENCES [user](id)
);

CREATE TABLE character (
    [id] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    [name] VARCHAR(32) NOT NULL,
    [race] VARCHAR(16),
    [level] INTEGER(3),
    [primary_class] VARCHAR(16),
    [primary_class_level] INTEGER(2),
    [secondary_class] VARCHAR(16),
    [secondary_class_level] INTEGER(2),
    [alignment] VARCHAR(16),
    [attr_str_1] INTEGER(3),
    [attr_dex_2] INTEGER(3),
    [attr_con_3] INTEGER(3),
    [attr_int_4] INTEGER(3),
    [attr_wis_5] INTEGER(3),
    [attr_cha_6] INTEGER(3),
    [attr_stats_other] VARCHAR(32),
    [attributes_public] TINYINT(1) NOT NULL,
    [is_public] TINYINT(1) NOT NULL,
    [is_pc] TINYINT(1) NOT NULL,
    [creator_id] CHAR(32) NOT NULL,
    [campaign_id] INTEGER NOT NULL,
    [description] VARCHAR(256), -- large, nullable fields last to potentially save space
    [notes] VARCHAR(256),
    [img_url] VARCHAR(128),
    [sheet_url] VARCHAR(128),
    CONSTRAINT character_creator_fk1 FOREIGN KEY (creator_id) REFERENCES [user](id)
    CONSTRAINT character_campaign_fk1 FOREIGN KEY (campaign_id) REFERENCES [campaign](id)
    CONSTRAINT character_name_creator_campaign_unq1 UNIQUE ([name], [creator_id], [campaign_id])
);

CREATE TABLE character_chronicle (
    [id] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    [character_id] INTEGER NOT NULL,
    [chronicle_entry_id] CHAR(32) NOT NULL,
    CONSTRAINT character_chronicle_fk1 FOREIGN KEY (character_id) REFERENCES [character](id),
    CONSTRAINT character_chronicle_fk2 FOREIGN KEY (chronicle_entry_id) REFERENCES [chronicle_entry](id)
);
