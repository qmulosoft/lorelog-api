CREATE TABLE [faction] (
      [id] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
      [name] VARCHAR(32) NOT NULL,
      [description] VARCHAR(250),
      [external_file_name] VARCHAR(64),
      [is_public] TINYINT(1) NOT NULL,
      [campaign_id] INTEGER NOT NULL,
      [creator_id] CHAR(32) NOT NULL,
      CONSTRAINT [faction_name_campaign_unique1] UNIQUE ([name], [campaign_id]),
      CONSTRAINT [faction_campaign_fk1] FOREIGN KEY ([campaign_id]) REFERENCES campaign ([id])
);

CREATE TABLE [character_faction] (
    [character_id] CHAR(32) NOT NULL,
    [faction_id] INTEGER NOT NULL,
    [is_public] TINYINT(1) NOT NULL DEFAULT 0,
    [role] VARCHAR(16),
    [reputation] VARCHAR(16), --- can store numbers or a word e.g. "friendly" if more appropriate
    CONSTRAINT [character_faction_fk1] FOREIGN KEY ([character_id]) REFERENCES [character] ([id]),
    CONSTRAINT [character_faction_fk2] FOREIGN KEY ([faction_id]) REFERENCES [faction] ([id]),
    PRIMARY KEY ([character_id], [faction_id])
);

CREATE TABLE [place] (
    [id] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    [name] VARCHAR(32) NOT NULL,
    [type] VARCHAR(16) NOT NULL,
    [map_url] VARCHAR(128),
    [is_public] TINYINT(1) NOT NULL,
    [campaign_id] INTEGER NOT NULL,
    [creator_id] CHAR(32) NOT NULL,
    [description] VARCHAR(256),
    [external_file_name] VARCHAR(64),
    CONSTRAINT place_campaign_fk1 FOREIGN KEY ([campaign_id]) REFERENCES campaign(id),
    CONSTRAINT place_creator_fk1 FOREIGN KEY (creator_id) REFERENCES user(id),
    CONSTRAINT place_unique_name UNIQUE ([name], [campaign_id])
);

CREATE TABLE [faction_chronicle] (
    [id] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    [faction_id] INTEGER NOT NULL,
    [chronicle_entry_id] CHAR(32) NOT NULL,
    CONSTRAINT faction_chronicle_fk1 FOREIGN KEY (faction_id) REFERENCES faction(id),
    CONSTRAINT faction_chronicle_fk2 FOREIGN KEY (chronicle_entry_id) REFERENCES chronicle_entry(id)
);

CREATE TABLE [place_chronicle] (
    [id] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    [place_id] INTEGER NOT NULL,
    [chronicle_entry_id] CHAR(32) NOT NULL,
    CONSTRAINT place_chronicle_fk1 FOREIGN KEY (place_id) REFERENCES place(id),
    CONSTRAINT place_chronicle_fk2 FOREIGN KEY (chronicle_entry_id) REFERENCES chronicle_entry(id)
);

CREATE TABLE [region_city] (
    [region_id] INTEGER NOT NULL,
    [city_id] INTEGER NOT NULL UNIQUE, -- A city cannot exist in more than one place
    [remark] VARCHAR(20),
    CONSTRAINT region_city_fk1 FOREIGN KEY (region_id) REFERENCES place(id),
    CONSTRAINT region_city_fk2 FOREIGN KEY (city_id) REFERENCES place(id),
    PRIMARY KEY (region_id, city_id)
);

CREATE TABLE [dungeon_place] (
    [dungeon_id] INTEGER NOT NULL,
    [place_id] INTEGER NOT NULL,
    [remark] VARCHAR(20),
    CONSTRAINT dungeon_place_fk1 FOREIGN KEY (dungeon_id) REFERENCES place(id),
    CONSTRAINT dungeon_place_fk2 FOREIGN KEY (place_id) REFERENCES place(id),
    PRIMARY KEY (dungeon_id, place_id)
);

CREATE TABLE [thing] (
    [id] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    [name] VARCHAR(32) NOT NULL,
    [type] VARCHAR(12) NOT NULL,
    [weight] DECIMAL,
    [price] INTEGER,
    [price_unit] CHAR(2),
    [description] VARCHAR(256),
    [external_file_name] VARCHAR(64),
    [is_public] TINYINT NOT NULL,
    [owner_id] INTEGER,
    [campaign_id] INTEGER NOT NULL,
    [creator_id] CHAR(32) NOT NULL,
    CONSTRAINT thing_unique UNIQUE ([name], [campaign_id]),
    CONSTRAINT thing_owner_fk1 FOREIGN KEY (owner_id) REFERENCES [character](id),
    CONSTRAINT thing_creator_fk1 FOREIGN KEY (creator_id) REFERENCES [user](id),
    CONSTRAINT thing_campaign_fk1 FOREIGN KEY (campaign_id) REFERENCES campaign(id)
);

CREATE TABLE [inventory] (
    [character_id] INTEGER NOT NULL,
    [thing_id] INTEGER NOT NULL,
    [quantity] INTEGER NOT NULL DEFAULT 1,
    [is_public] TINYINT(1) NOT NULL,
    PRIMARY KEY (character_id, thing_id),
    CONSTRAINT inventory_character_fk1 FOREIGN KEY (character_id) REFERENCES [character](id),
    CONSTRAINT inventory_item_fk1 FOREIGN KEY (thing_id) REFERENCES thing(id)
);

CREATE TABLE [thing_chronicle] (
    [id] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    [thing_id] INTEGER NOT NULL,
    [chronicle_entry_id] CHAR(32) NOT NULL,
    CONSTRAINT thing_chronicle_fk1 FOREIGN KEY (thing_id) REFERENCES thing(id),
    CONSTRAINT thing_chronicle_fk2 FOREIGN KEY (chronicle_entry_id) REFERENCES chronicle_entry(id)
);